# CALL YELP API AND PUT DATA INTO CSV FILE

import sys, os, time, math, json
sys.path.append(os.path.dirname(os.path.dirname(__file__)))  # let us import config.py from project root
from find_your_fit.src.config import YELP_API_KEY

from typing import Dict, Any, List
import requests
import pandas as pd
from tqdm import tqdm


BASE_URL = "https://api.yelp.com/v3"
HEADERS = {"Authorization": f"Bearer {YELP_API_KEY}"}

RAW_DIR = os.path.join("data", "raw")
os.makedirs(RAW_DIR, exist_ok=True)

# ---------- helpers ----------
def yelp_get(endpoint: str, params: Dict[str, Any]) -> Dict[str, Any]:
    url = f"{BASE_URL}{endpoint}"
    for attempt in range(5):
        r = requests.get(url, headers=HEADERS, params=params, timeout=30)
        if r.status_code == 200:
            return r.json()
        # handle rate/temporary errors with backoff
        if r.status_code in (429, 500, 502, 503, 504):
            time.sleep(2 ** attempt); continue
        try: detail = r.json()
        except: detail = r.text
        raise RuntimeError(f"{r.status_code}: {detail}")
    raise RuntimeError("Yelp GET failed after retries")

LIMIT = 50
OFFSETS = [0, 50, 100, 150, 190]  # respects Yelp's 240 cap

AREAS = [
    "Los Angeles, CA",
    "Downtown Los Angeles, CA",
    "Hollywood, Los Angeles, CA",
    "West Hollywood, CA",
    "Koreatown, Los Angeles, CA",
    "Silver Lake, Los Angeles, CA",
    "Echo Park, Los Angeles, CA",
    "Brentwood, Los Angeles, CA",
    "Westwood, Los Angeles, CA",
    "Santa Monica, CA",
    "Venice, CA",
    "Marina del Rey, CA",
    "Culver City, CA",
    "Beverly Hills, CA",
    "Studio City, CA",
    "Sherman Oaks, CA",
    "North Hollywood, CA",
    "Burbank, CA",
    "Glendale, CA",
    "Pasadena, CA",
    "Manhattan Beach, CA",
    "El Segundo, CA",
]

# ---------- business search (paginated up to 1000 results) ----------
def search_area(area: str) -> List[Dict[str, Any]]:
    """Fetch up to 240 results for a single area, respecting Yelp cap."""
    results = []
    for off in OFFSETS:
        data = yelp_get("/businesses/search", {
            "term": "pilates",
            "location": area,
            "categories": "pilates",
            "radius": 40000,   # ~40km
            "limit": LIMIT,
            "offset": off,
            "sort_by": "best_match",
        })
        batch = data.get("businesses", []) or []
        results.extend(batch)
        if len(batch) < LIMIT:
            break
        time.sleep(0.1)
    return results

def fetch_businesses() -> List[Dict[str, Any]]:
    """Fan out over many LA areas, then de-dupe by business id."""
    all_biz = {}
    for area in tqdm(AREAS, desc="Fetching businesses across LA"):
        for b in search_area(area):
            all_biz[b["id"]] = b
    return list(all_biz.values())

# ---------- business details (to pull attributes) ----------
def fetch_business_details(business_id: str) -> dict:
    try:
        return yelp_get(f"/businesses/{business_id}", params={})
    except RuntimeError as e:
        if "BUSINESS_UNAVAILABLE" in str(e) or "403" in str(e):
            return {}  # skip silently
        raise


# ---------- review excerpts (up to 7 with Premium) ----------
def fetch_review_excerpts(business_id: str) -> List[Dict[str, Any]]:
    # Some plans call this "reviews" but return 'excerpts' with a higher cap.
    # If your plan returns only 3, code still works—just fewer rows.
    data = yelp_get(f"/businesses/{business_id}/reviews", params={"limit": 7})
    return data.get("reviews", [])

# ---------- flatteners ----------
def flatten_businesses(biz: List[Dict[str, Any]]) -> pd.DataFrame:
    rows = []
    for b in biz:
        loc = b.get("location") or {}
        coords = b.get("coordinates") or {}
        cats = ", ".join([c.get("title","") for c in b.get("categories", [])])
        rows.append({
            "id": b.get("id"),
            "name": b.get("name"),
            "rating": b.get("rating"),
            "review_count": b.get("review_count"),
            "price": b.get("price"),
            "categories": cats,
            "phone": b.get("display_phone"),
            "url": b.get("url"),
            "city": (loc.get("city") or "").strip(),
            "state": loc.get("state"),
            "zip_code": loc.get("zip_code"),
            "address1": loc.get("address1"),
            "address2": loc.get("address2"),
            "address3": loc.get("address3"),
            "latitude": coords.get("latitude"),
            "longitude": coords.get("longitude"),
            "is_closed": b.get("is_closed"),
        })
    df = pd.DataFrame(rows).drop_duplicates(subset=["id"]).reset_index(drop=True)
    # Keep only "Los Angeles" city values (you can relax this later to LA County by lat/long)
    #df = df[df["city"].str.lower() == "los angeles"]
    return df

def pick_attributes(attr: dict) -> dict:
    import json
    if not isinstance(attr, dict):
        return {}

    parking = attr.get("BusinessParking") or {}
    if isinstance(parking, str):
        try:
            parking = json.loads(parking.replace("'", '"'))
        except Exception:
            parking = {}

    return {
        # --- existing ---
        "attr_business_parking_garage": parking.get("garage") if isinstance(parking, dict) else None,
        "attr_business_parking_street": parking.get("street") if isinstance(parking, dict) else None,
        "attr_business_parking_lot": parking.get("lot") if isinstance(parking, dict) else None,
        "attr_business_parking_valet": parking.get("valet") if isinstance(parking, dict) else None,
        "attr_business_parking_validated": parking.get("validated") if isinstance(parking, dict) else None,
        "attr_bike_parking": attr.get("BikeParking"),
        "attr_wifi": attr.get("WiFi"),
        "attr_good_for_kids": attr.get("GoodForKids"),
        "attr_dogs_allowed": attr.get("DogsAllowed"),
        "attr_waitlist_reservation": attr.get("WaitlistReservation"),
        "attr_accepts_credit_cards": attr.get("BusinessAcceptsCreditCards"),
        "attr_year_established": attr.get("AboutThisBizYearEstablished"),

        # --- NEW: about text fields (names vary, these are common) ---
        "text_about_specialties": attr.get("AboutThisBizSpecialties"),
        "text_about_history": attr.get("AboutThisBizHistory"),
        "text_about_bio": attr.get("AboutThisBizBio"),
    }

# ---------- main ----------
def main():
    print("Step 1/4: Searching LA Pilates studios…")
    biz = fetch_businesses()
    print(f"Raw listings found: {len(biz)}")
    with open(os.path.join(RAW_DIR, "yelp_pilates_raw_search.json"), "w") as f:
        json.dump(biz, f)

    print("Step 2/4: Flattening + LA filter…")
    df = flatten_businesses(biz)
    print(f"Studios with city == 'Los Angeles': {len(df)}")

    # Enrich with attributes via details endpoint
    print("Step 3/4: Fetching attributes (Premium)…")
    attr_rows = []
    for bid in tqdm(df["id"].tolist(), desc="Details"):
        try:
            detail = fetch_business_details(bid)
            attrs = pick_attributes(detail.get("attributes") or {})
            attrs["id"] = bid
            attr_rows.append(attrs)
        except Exception:
            attr_rows.append({"id": bid})  # keep row; missing attrs set to NaN
        time.sleep(0.06)

    attr_df = pd.DataFrame(attr_rows)
    df_full = df.merge(attr_df, on="id", how="left")
    biz_csv = os.path.join(RAW_DIR, "yelp_pilates_la_businesses_premium.csv")
    df_full.to_csv(biz_csv, index=False)
    print(f"Saved businesses+attributes → {biz_csv}")

    # Review excerpts (up to 7). If your plan returns 3, that's fine.
    print("Step 4/4: Fetching review excerpts…")
    review_rows = []
    for bid in tqdm(df["id"].tolist(), desc="Reviews"):
        try:
            for r in fetch_review_excerpts(bid):
                review_rows.append({
                    "business_id": bid,
                    "review_id": r.get("id"),
                    "rating": r.get("rating"),
                    "text": r.get("text"),
                    "time_created": r.get("time_created"),
                    "user_name": (r.get("user") or {}).get("name"),
                })
        except Exception:
            pass
        time.sleep(0.06)

    if review_rows:
        rev_df = pd.DataFrame(review_rows)
        rev_csv = os.path.join(RAW_DIR, "yelp_pilates_la_reviews_premium.csv")
        rev_df.to_csv(rev_csv, index=False)
        print(f"Saved review excerpts ({len(rev_df)}) → {rev_csv}")
    else:
        print("No reviews returned (check plan/endpoints).")

if __name__ == "__main__":
    main()