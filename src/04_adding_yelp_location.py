# ADDING yelp location INFO TO MASTER CSV

import pandas as pd

IN_PROFILES = "data/processed/pilates_studio_profiles_clean.csv"
BIZ_PATH = "data/raw/yelp_pilates_la_businesses_premium.csv"
OUT_PATH = "data/processed/pilates_studio_profiles_yelploc.csv"


def main():
    print("📄 Loading profiles and business metadata...")
    profiles = pd.read_csv(IN_PROFILES)
    biz = pd.read_csv(BIZ_PATH)

    print("Business columns:")
    print(list(biz.columns))

    # These are the *typical* Yelp Fusion column names.
    # If you get a KeyError, open the printed column list above
    # and adjust these strings to match your actual names.
    ID_COL = "id"
    CITY_COL = "city"
    ADDR_COL = "address1"
    LAT_COL = "latitude"
    LON_COL = "longitude"


    loc = biz[[ID_COL, CITY_COL, ADDR_COL, LAT_COL, LON_COL]].copy()
    loc = loc.rename(
        columns={
            ID_COL: "business_id",
            CITY_COL: "city",
            ADDR_COL: "address",
            LAT_COL: "latitude",
            LON_COL: "longitude",
        }
    )

    print("🔗 Merging location into profiles on business_id...")
    merged = profiles.merge(loc, on="business_id", how="left")

    merged.to_csv(OUT_PATH, index=False)
    print(f"✅ Saved profiles with location → {OUT_PATH}")
    print(f"   Rows: {merged.shape[0]}, Columns: {merged.shape[1]}")


if __name__ == "__main__":
    main()
