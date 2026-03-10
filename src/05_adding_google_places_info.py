# Enriching with Google Places API Information 

import time
import pandas as pd
import googlemaps
from config import GOOGLE_PLACES_API_KEY

IN_PATH = "data/processed/pilates_studio_profiles_yelploc.csv"
OUT_PATH = "data/processed/pilates_studio_profiles_final.csv"


def main():
    print("📄 Loading studio profiles with Yelp-based location info...")
    df = pd.read_csv(IN_PATH)
    print(f"Studios to enrich: {len(df)}")

    gmaps = googlemaps.Client(key=GOOGLE_PLACES_API_KEY)

    # If old price-related columns exist from previous runs, drop them
    for col in ["google_price_level", "price_tier"]:
        if col in df.columns:
            print(f"🧹 Dropping existing column: {col}")
            df.drop(columns=[col], inplace=True)

    # Make sure the Google-related columns exist
    for col in ["google_place_id", "google_rating", "google_user_ratings_total"]:
        if col not in df.columns:
            df[col] = None

    for idx, row in df.iterrows():
        name = row.get("name", "")
        city = row.get("city", "")

        query = f"{name} Pilates {city}"
        print(f"🔍 [{idx+1}/{len(df)}] Searching Google Places for: {query}")

        try:
            resp = gmaps.places(query=query)
            results = resp.get("results", [])

            if not results:
                print("   → No result found")
                continue

            top = results[0]

            # Fill/overwrite Google fields
            df.at[idx, "google_place_id"] = top.get("place_id")
            df.at[idx, "google_rating"] = top.get("rating")
            df.at[idx, "google_user_ratings_total"] = top.get("user_ratings_total")

            print(
                f"   ✓ {top.get('name')} | "
                f"rating={top.get('rating')} "
                f"({top.get('user_ratings_total')} reviews)"
            )

        except Exception as e:
            print(f"   ⚠️ Error for {name}: {e}")

        # Be gentle with the API
        time.sleep(0.25)

    df.to_csv(OUT_PATH, index=False)
    print(f"\n🎉 Saved FINAL profiles with Google info → {OUT_PATH}")
    print(f"   Rows: {df.shape[0]}, Columns: {df.shape[1]}")


if __name__ == "__main__":
    main()
