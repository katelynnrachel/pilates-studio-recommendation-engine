import os
import pandas as pd

# paths
BIZ_PATH   = "data/raw/yelp_pilates_la_businesses_premium.csv"
FEAT_PATH  = "data/processed/pilates_studio_features.csv"
SENT_PATH  = "data/processed/studio_sentiment_vader_full.csv"
OUT_PATH   = "data/processed/pilates_studio_profiles.csv"

os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)

def main():
    # 1. business metadata (names, ratings, etc.)
    biz = pd.read_csv(BIZ_PATH)

    # adjust this list once you see the actual column names in biz.columns
    keep_cols = ["id", "name", "rating", "review_count", "price"]
    keep_cols = [c for c in keep_cols if c in biz.columns]

    biz_small = biz[keep_cols].rename(columns={"id": "business_id"})

    # 2. engineered studio features (but drop OLD sentiment cols)
    feats = pd.read_csv(FEAT_PATH)
    feats = feats.drop(
        columns=["instructor_sentiment", "cleanliness_sentiment", "community_sentiment"],
        errors="ignore"
    )

    # 3. new VADER sentiment features
    sent = pd.read_csv(SENT_PATH)

    # 4. merge everything
    profiles = (
        biz_small
        .merge(feats, on="business_id", how="left")
        .merge(sent, on="business_id", how="left")
    )

    profiles.to_csv(OUT_PATH, index=False)
    print(f"✅ Saved studio profiles → {OUT_PATH} with shape {profiles.shape}")

if __name__ == "__main__":
    main()
