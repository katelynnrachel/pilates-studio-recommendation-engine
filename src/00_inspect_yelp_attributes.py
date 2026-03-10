import os, sys, time, json
from collections import Counter, defaultdict
from typing import Dict, Any, List

import requests
import pandas as pd
from tqdm import tqdm

# so we can import config.py from project root
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from find_your_fit.src.config import YELP_API_KEY

BASE_URL = "https://api.yelp.com/v3"
HEADERS = {"Authorization": f"Bearer {YELP_API_KEY}"}

# Yelp constraint: limit + offset <= 240
LIMIT = 50
OFFSETS = [0, 50, 100, 150, 190]  # last valid with LIMIT=50

# Fan-out list (cover Greater LA). Feel free to add/remove.
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

def yelp_get(endpoint: str, params: Dict[str, Any]) -> Dict[str, Any]:
    url = f"{BASE_URL}{endpoint}"
    for attempt in range(5):
        r = requests.get(url, headers=HEADERS, params=params, timeout=30)
        if r.status_code == 200:
            return r.json()
        if r.status_code in (429, 500, 502, 503, 504):
            time.sleep(2 ** attempt); continue
        try: detail = r.json()
        except: detail = r.text
        raise RuntimeError(f"{r.status_code}: {detail}")
    raise RuntimeError("Yelp GET failed after retries")

def search_area(area: str) -> List[Dict[str, Any]]:
    results = []
    for off in OFFSETS:
        data = yelp_get("/businesses/search", {
            "term": "pilates",
            "location": area,
            "categories": "pilates",
            "radius": 40000,    # ~40km
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

def fetch_details(bid: str) -> Dict[str, Any]:
    try:
        return yelp_get(f"/businesses/{bid}", params={})
    except RuntimeError as e:
        # skip restricted businesses instead of halting
        if "BUSINESS_UNAVAILABLE" in str(e) or "403" in str(e):
            return {}
        raise

def main():
    os.makedirs("data/raw", exist_ok=True)

    # 1) Gather businesses from many areas (respect 240 cap per area)
    all_biz = {}
    for area in tqdm(AREAS, desc="Areas"):
        area_biz = search_area(area)
        for b in area_biz:
            all_biz[b["id"]] = b  # de-dupe by id

    businesses = list(all_biz.values())
    print(f"\nUnique businesses collected across areas: {len(businesses)}")

    # Keep strict LA city only for attribute sweep (optional)
    businesses = [b for b in businesses
                  if (b.get("location", {}).get("city") or "").lower() == "los angeles"]
    print(f"Businesses with city == 'Los Angeles': {len(businesses)}")

    # 2) Pull details/attributes and compute coverage
    attr_counter = Counter()
    sample_values = defaultdict(list)
    details_rows = []
    have_attrs = 0

    for b in tqdm(businesses, desc="Details"):
        bid = b["id"]
        d = fetch_details(bid)
        attrs = d.get("attributes") or {}
        details_rows.append({"id": bid, "name": d.get("name"), "attributes": attrs})
        if attrs:
            have_attrs += 1
            for k, v in attrs.items():
                attr_counter[k] += 1
                sv = json.dumps(v, ensure_ascii=False)
                if sv not in sample_values[k] and len(sample_values[k]) < 3:
                    sample_values[k].append(sv)
        time.sleep(0.06)

    total = len(businesses)
    rows = []
    for k, cnt in attr_counter.items():
        rows.append({
            "attribute": k,
            "count_with_attribute": cnt,
            "coverage_pct": round(100.0 * cnt / total, 2) if total else 0.0,
            "sample_values": " | ".join(sample_values[k]),
        })
    df = pd.DataFrame(rows).sort_values(["coverage_pct","attribute"], ascending=[False, True])

    out_csv = "data/raw/yelp_la_pilates_attribute_coverage.csv"
    df.to_csv(out_csv, index=False)
    print(f"\n✅ Saved coverage table → {out_csv}")
    print(f"Studios scanned: {total} | Studios with any attributes: {have_attrs}")
    print("\nTop 15 attributes by coverage:")
    print(df.head(15).to_string(index=False))

if __name__ == "__main__":
    main()
