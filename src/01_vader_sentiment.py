import os, re
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

import pandas as pd
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from tqdm import tqdm

REV_PATH = "data/raw/yelp_pilates_la_reviews_premium.csv"
OUT_PATH = "data/processed/studio_sentiment_vader_full.csv"
os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)

# --------------------------
# 1. Define ALL attributes
# --------------------------
ATTRIBUTE_TERMS = {
    "instructor": [
        "instructor","teacher","coach","trainer","staff","owner",
        "cue","cues","cueing","hands-on","adjustments","modify"
    ],
    "cleanliness": [
        "clean", "dirty", "dusty", "sanitized", "smell", "odor",
        "bathroom", "locker room", "floors", "tidy", "messy"
    ],
    "intensity": [
        "intense","hard","challenging","easy","sweat","burn",
        "advanced","beginner","intermediate","too much","light"
    ],
    "vibe": [
        "vibe","energy","community","welcoming","friendly","inclusive",
        "culture","atmosphere","environment"
    ],
    "customer_service": [
        "front desk","rude","nice","helpful","service","support",
        "communication","responsive","unprofessional"
    ],
    "space_equipment": [
        "space","equipment","machines","reformer","layout","room",
        "studio size","spring","props"
    ],
    "parking": [
        "parking","garage","street parking","valet","easy to park",
        "hard to park","convenient","location","traffic"
    ],
    "price": [
        "price","expensive","cheap","worth","value","cost","pricing",
        "affordable"
    ],
    "variety": [
        "variety","schedule","times","classes","options","availability",
        "booking","cancel","waitlist"
    ],
    "crowdedness": [
        "crowded","packed","full","busy","overcrowded","small space",
        "no room"
    ],
    "music": [
        "music","playlist","loud","quiet","energy","soundtrack"
    ]
}

def split_sentences(text: str):
    return [s.strip() for s in re.split(r'[.!?]\s*', text or "") if s.strip()]

# VADER returns a "compound" score in [-1, 1]
analyzer = SentimentIntensityAnalyzer()

def signed_sentiment(text: str) -> float:
    if not text or not text.strip():
        return 0.0
    vs = analyzer.polarity_scores(text[:400])
    return vs["compound"]

def main():
    # --- Load reviews ---
    print("📥 Reading reviews CSV...")
    df = pd.read_csv(REV_PATH).fillna("")
    print(f"   Loaded {len(df)} review rows from {REV_PATH}")

    reviews = (
        df.groupby("business_id")["text"]
          .apply(lambda s: " ".join(s.astype(str)))
          .reset_index()
    )
    print(f"   Aggregated to {len(reviews)} unique businesses")

    rows = []

    # --- Main loop ---
    print("✨ Starting full VADER sentiment profiler loop...")
    for _, row in tqdm(
        reviews.iterrows(),
        total=len(reviews),
        desc="VADER full sentiment"
    ):
        bid, text = row["business_id"], row["text"]

        sentences = split_sentences(text)

        # ----- overall sentiment -----
        overall_scores = [signed_sentiment(s) for s in sentences]
        overall_score = (
            sum(overall_scores) / len(overall_scores)
            if overall_scores else 0.0
        )

        result = {
            "business_id": bid,
            "overall_sentiment_vader": overall_score,
        }

        # ----- attribute-specific sentiment -----
        for attr, keywords in ATTRIBUTE_TERMS.items():
            matched_sents = [
                s for s in sentences
                if any(k in s.lower() for k in keywords)
            ]

            if not matched_sents:
                matched_sents = [text]  # fallback to whole text

            attr_scores = [signed_sentiment(s) for s in matched_sents]
            result[f"{attr}_sentiment_vader"] = (
                sum(attr_scores) / len(attr_scores)
                if attr_scores else 0.0
            )

        rows.append(result)

    out = pd.DataFrame(rows)
    out.to_csv(OUT_PATH, index=False)
    print(f"🔥 Full VADER profiler saved to {OUT_PATH} with shape {out.shape}")

if __name__ == "__main__":
    main()
