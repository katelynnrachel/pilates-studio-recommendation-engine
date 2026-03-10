# AFTER CREATING pilates_studio_profiles.csv IN STEP 02, CLEANING CSV

import pandas as pd

IN_PATH = "data/processed/pilates_studio_profiles.csv"
OUT_PATH = "data/processed/pilates_studio_profiles_clean.csv"

def main():
    df = pd.read_csv(IN_PATH)

    # Columns to keep
    keep_cols = [
        "business_id",
        "name",
        "rating",
        "review_count",

        # VADER sentiment dimensions
        "overall_sentiment_vader",
        "instructor_sentiment_vader",
        "cleanliness_sentiment_vader",
        "intensity_sentiment_vader",
        "vibe_sentiment_vader",
        "customer_service_sentiment_vader",
        "space_equipment_sentiment_vader",
        "parking_sentiment_vader",
        "price_sentiment_vader",
        "variety_sentiment_vader",
        "crowdedness_sentiment_vader",
        "music_sentiment_vader",
    ]

    df_clean = df[keep_cols]

    df_clean.to_csv(OUT_PATH, index=False)
    print(f"✨ Saved CLEAN dataset → {OUT_PATH}")
    print(f"Rows: {df_clean.shape[0]}, Columns: {df_clean.shape[1]}")

if __name__ == "__main__":
    main()
