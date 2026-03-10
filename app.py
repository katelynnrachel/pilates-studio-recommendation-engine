import os
import base64
import pandas as pd
import streamlit as st

DATA_PATH = "data/processed/pilates_studio_profiles_final.csv"

# Path to logo image
LOGO_PATH = "data/images/find_your_fit_logo.png"

SENT_COLS = [
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

# ----- SIMPLE LA REGION MAPPING -----
REGION_MAP = {
    # Westside
    "Santa Monica": "Westside",
    "Culver City": "Westside",
    "Venice": "Westside",
    "Marina del Rey": "Westside",
    "Playa Vista": "Westside",
    "Playa Del Rey": "Westside",
    "Brentwood": "Westside",
    "Pacific Palisades": "Westside",
    "Westwood": "Westside",

    # Central LA
    "Los Angeles": "Central LA",
    "West Hollywood": "Central LA",
    "Beverly Hills": "Central LA",
    "Hollywood": "Central LA",
    "Koreatown": "Central LA",
    "Downtown Los Angeles": "Central LA",

    # San Fernando Valley
    "Studio City": "San Fernando Valley",
    "Sherman Oaks": "San Fernando Valley",
    "Encino": "San Fernando Valley",
    "Tarzana": "San Fernando Valley",
    "Woodland Hills": "San Fernando Valley",
    "Calabasas": "San Fernando Valley",
    "Burbank": "San Fernando Valley",
    "North Hollywood": "San Fernando Valley",
    "Van Nuys": "San Fernando Valley",

    # San Gabriel Valley
    "Pasadena": "San Gabriel Valley",
    "Alhambra": "San Gabriel Valley",
    "Glendale": "San Gabriel Valley",
    "San Gabriel": "San Gabriel Valley",

    # South Bay / Beach Cities
    "Manhattan Beach": "South Bay",
    "Hermosa Beach": "South Bay",
    "Redondo Beach": "South Bay",
    "El Segundo": "South Bay",
    "Torrance": "South Bay",
    "San Pedro": "South Bay",
    "Long Beach": "South Bay",
    "Inglewood": "South Bay",

    # North LA County
    "Santa Clarita": "North LA County",
    "Valencia": "North LA County",
    "Newhall": "North LA County",
}

# ----- FRIENDLY COLUMN LABELS FOR TABLE -----
DISPLAY_COL_MAP = {
    "name": "Studio",
    "rating": "Yelp Rating",
    "google_rating": "Google Rating",
    "review_count": "Num. of Yelp Reviews",
    "google_user_ratings_total": "Num. of Google Reviews",
    "fit_score": "Fit Score",
    "region": "Region",
    "city": "City",
    "address": "Address",
    "instructor_sentiment_vader": "Instructor Sentiment",
    "cleanliness_sentiment_vader": "Cleanliness Sentiment",
    "intensity_sentiment_vader": "Intensity Sentiment",
    "vibe_sentiment_vader": "Vibe/Community Sentiment",
    "parking_sentiment_vader": "Parking Availability",
    "price_sentiment_vader": "Price/Value Sentiment",
}


@st.cache_data
def load_data(path=DATA_PATH):
    df = pd.read_csv(path)
    df[SENT_COLS] = df[SENT_COLS].fillna(0.0)

    if "city" in df.columns:
        df["region"] = df["city"].map(REGION_MAP).fillna("Other / LA County")
    else:
        df["region"] = "Other / LA County"

    return df


def compute_fit_score(df, weights):
    return (
        weights["instructor"] * df["instructor_sentiment_vader"]
        + weights["cleanliness"] * df["cleanliness_sentiment_vader"]
        + weights["intensity"] * df["intensity_sentiment_vader"]
        + weights["vibe"] * df["vibe_sentiment_vader"]
        + weights["parking"] * df["parking_sentiment_vader"]
        + weights["price"] * df["price_sentiment_vader"]
    )


def get_logo_base64(logo_path=LOGO_PATH):
    if not os.path.exists(logo_path):
        return None
    with open(logo_path, "rb") as f:
        img_bytes = f.read()
    return base64.b64encode(img_bytes).decode("utf-8")


def inject_css():
    st.markdown(
        """
        <style>
        .stApp {
            background: #f5e2c8;
            font-family: -apple-system, BlinkMacSystemFont, "SF Pro Text", system-ui, sans-serif;
            font-size: 16px;
        }

        section[data-testid="stSidebar"] {
            background: #f8ecdd;
            border-right: 1px solid #e1c8aa;
        }

        section[data-testid="stSidebar"] * {
            font-size: 0.92rem !important;
        }

        h1, h2, h3, h4 {
            font-family: Georgia, "Times New Roman", serif !important;
            color: #4a4036;
        }

        .hero-title {
            font-family: Georgia, "Times New Roman", serif;
            font-size: 2.2rem;
            font-weight: 600;
            letter-spacing: 0.03em;
            margin-bottom: 0.1rem;
            color: #4a4036;
        }

        .hero-subtitle {
            font-size: 0.85rem;
            text-transform: uppercase;
            letter-spacing: 0.12em;
            color: #8a7458;
        }

        .hero-tagline {
            font-size: 0.95rem;
            color: #5b4a3b;
            margin-top: 0.35rem;
        }

        .section-title {
            font-family: Georgia, "Times New Roman", serif;
            font-size: 1.1rem;
            font-weight: 600;
            color: #4a4036;
            margin: 0.2rem 0 0.6rem 0;
        }

        .info-card {
            background: #f9eddc;
            border-radius: 0.8rem;
            border: 1px solid #e3d1b8;
            padding: 0.85rem 1rem;
            font-size: 0.9rem;
            color: #4a4036;
        }

        .info-card strong {
            font-family: Georgia, "Times New Roman", serif;
            font-size: 1.0rem;
            color: #3d3329;
        }

        div[data-testid="stMetric"] {
            background-color: #f9eddc;
            padding: 0.6rem 0.9rem;
            border-radius: 0.9rem;
            box-shadow: 0 8px 18px rgba(88, 63, 28, 0.08);
            border: 1px solid #e3d1b8;
            min-width: 150px;
        }

        .metric-label {
            font-size: 0.95rem;
            text-transform: uppercase;
            letter-spacing: 0.06em;
            color: #8a7458;
            margin-bottom: 0.1rem;
            white-space: normal;
        }

        .metric-value {
            font-size: 1.4rem;
            font-weight: 600;
            color: #4b3b2a;
        }

        .studio-card {
            background: #f9eddc;
            border-radius: 1rem;
            padding: 0.9rem 1.1rem;
            margin-bottom: 0.75rem;
            box-shadow: 0 10px 26px rgba(88, 63, 28, 0.09);
            border: 1px solid #e4cfb0;
        }

        .studio-name {
            font-size: 1.05rem;
            font-weight: 650;
            color: #4a4036;
        }

        .chip {
            display: inline-block;
            padding: 0.12rem 0.55rem;
            border-radius: 999px;
            font-size: 0.74rem;
            background: #f2ddc0;
            color: #5b4632;
            margin-right: 0.3rem;
            border: 1px solid #e2c9a8;
        }

        .chip span {
            font-weight: 600;
            margin-right: 0.1rem;
        }

        .subtle-label {
            font-size: 0.8rem;
            text-transform: uppercase;
            letter-spacing: 0.08em;
            color: #8f7a62;
        }

        div[data-testid="stDataFrame"] * {
            font-size: 0.9rem !important;
        }

        .main-block {
            background: #f7e6cf;
            border-radius: 0.6rem;
            padding: 0.4rem 1.2rem 1rem 1.2rem;
            border: 1px solid #e1c7a7;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def main():
    st.set_page_config(
        page_title="Find Your Fit – Pilates Studio Profiler",
        page_icon="🧘‍♀️",
        layout="wide",
    )

    inject_css()
    df = load_data()
    logo_b64 = get_logo_base64()

    # ---------- HERO + METRICS ----------
    hero_col, metrics_col = st.columns([2, 2])

    with hero_col:
        inner_logo_col, inner_text_col = st.columns([1, 2])
        with inner_logo_col:
            if logo_b64:
                st.markdown(
                    f"""
                    <div style="display:flex; justify-content:center; align-items:center; height:100%;">
                        <img src="data:image/png;base64,{logo_b64}"
                             style="max-width:170px; height:auto;" />
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

        with inner_text_col:
            st.markdown(
                """
                <div style="padding-top:0.35rem;">
                    <div class="hero-title">Find Your Fit</div>
                    <div class="hero-subtitle">Review-Based Matching Engine</div>
                    <div class="hero-tagline">
                        Choose what you care about and we’ll do the rest.
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    with metrics_col:
        total = len(df)
        avg_rating = df["rating"].dropna().mean() if "rating" in df.columns else None
        avg_google = (
            df["google_rating"].dropna().mean()
            if "google_rating" in df.columns
            else None
        )
        avg_overall = df["overall_sentiment_vader"].mean()

        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Studios profiled", f"{total}")
        if avg_rating is not None:
            m2.metric("Avg. Yelp Rating", f"{avg_rating:.1f} ⭐")
        if avg_google is not None:
            m3.metric("Avg. Google Rating", f"{avg_google:.1f} ⭐")
        m4.metric("Avg. Review Sentiment", f"{avg_overall:.2f}")

    st.markdown("---")

    # ---------- EXPLANATION CARD ----------
    st.markdown(
        """
        <div class="info-card">
            <strong>How to read these scores:</strong><br/>
            <b>Fit Score</b> combines the review-based sentiment for instructor quality, cleanliness,
            intensity, vibe/community, parking, and price/value using the sliders you set in the sidebar.
            Higher scores mean a better match for your priorities.<br/>
            <b>Yelp & Google ratings</b> are standard 1–5 star averages from each platform.<br/>
            <b>Sentiment scores</b> (Instructor, Cleanliness, etc.) range roughly from 0 (more negative)
            to 1 (more positive) and come from how people actually talk about those dimensions in their reviews.
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("")

    # ---------- SIDEBAR: PREFERENCES ----------
    st.sidebar.header("Adjust Your Preferences")
    st.sidebar.write(
        "Higher values mean that dimension matters more to you in the recommendations."
    )

    w_instr = st.sidebar.slider("Instructor Quality", 0.0, 5.0, 3.0, 0.5)
    w_clean = st.sidebar.slider("Cleanliness", 0.0, 5.0, 3.0, 0.5)
    w_int = st.sidebar.slider("Intensity/Difficulty", 0.0, 5.0, 2.0, 0.5)
    w_vibe = st.sidebar.slider("Overall Vibe/Community", 0.0, 5.0, 2.5, 0.5)
    w_park = st.sidebar.slider("Parking Convenience", 0.0, 5.0, 1.5, 0.5)
    w_price = st.sidebar.slider("Perceived Value", 0.0, 5.0, 2.0, 0.5)

    # ---------- LOCATION FILTERS ----------
    st.sidebar.subheader("Location")

    location_mode = st.sidebar.radio(
        "Filter by area?", ["All LA areas", "Filter by region / city"], index=0
    )

    selected_regions = []
    selected_cities = []

    if location_mode == "Filter by region / city" and "region" in df.columns:
        region_options = sorted(df["region"].unique())
        selected_regions = st.sidebar.multiselect(
            "Regions",
            options=region_options,
            default=region_options,
        )

        if selected_regions:
            city_subset = df[df["region"].isin(selected_regions)]
        else:
            city_subset = df

        if "city" in city_subset.columns:
            city_options = sorted(city_subset["city"].dropna().unique())
        else:
            city_options = []

        with st.sidebar.expander("Filter by specific cities (optional)", expanded=False):
            selected_cities = st.multiselect(
                "Cities",
                options=city_options,
                default=[],
                placeholder="All cities in selected regions",
            )

    st.sidebar.markdown("---")
    min_rating = st.sidebar.slider("Minimum Yelp Rating", 0.0, 5.0, 4.0, 0.1)
    min_reviews = st.sidebar.slider("Minimum Number of Yelp Reviews", 0, 200, 10, 5)
    min_google_rating = st.sidebar.slider("Minimum Google Rating", 0.0, 5.0, 4.0, 0.1)
    min_google_reviews = st.sidebar.slider(
        "Minimum Number of Google Reviews", 0, 200, 10, 5
    )
    top_n = st.sidebar.slider("Results to show", 5, 50, 15, 5)

    weights = {
        "instructor": w_instr,
        "cleanliness": w_clean,
        "intensity": w_int,
        "vibe": w_vibe,
        "parking": w_park,
        "price": w_price,
    }

    # ---------- APPLY FILTERS & SCORE ----------
    filtered = df.copy()

    if location_mode == "Filter by region / city" and selected_regions:
        filtered = filtered[filtered["region"].isin(selected_regions)]

    if selected_cities:
        filtered = filtered[filtered["city"].isin(selected_cities)]

    if "rating" in filtered.columns:
        filtered = filtered[filtered["rating"].fillna(0) >= min_rating]
    if "review_count" in filtered.columns:
        filtered = filtered[filtered["review_count"].fillna(0) >= min_reviews]
    if "google_rating" in filtered.columns:
        filtered = filtered[filtered["google_rating"].fillna(0) >= min_google_rating]
    if "google_user_ratings_total" in filtered.columns:
        filtered = filtered[
            filtered["google_user_ratings_total"].fillna(0) >= min_google_reviews
        ]

    filtered["fit_score"] = compute_fit_score(filtered, weights)
    filtered = filtered.sort_values("fit_score", ascending=False)

    st.markdown(
        '<div class="section-title">Top Matches for Your Preferences</div>',
        unsafe_allow_html=True,
    )

    if filtered.empty:
        st.warning(
            "No studios match your filters. Try broadening the location or "
            "lowering the minimum rating / review count."
        )
        return

    # ---------- TABLE VIEW ----------
    table_cols = [
        "name",
        "rating",
        "google_rating",
        "review_count",
        "google_user_ratings_total",
        "fit_score",
        "region",
        "city",
        "address",
        "instructor_sentiment_vader",
        "cleanliness_sentiment_vader",
        "intensity_sentiment_vader",
        "vibe_sentiment_vader",
        "parking_sentiment_vader",
        "price_sentiment_vader",
    ]
    table_cols = [c for c in table_cols if c in filtered.columns]

    display_df = (
        filtered[table_cols]
        .head(top_n)
        .reset_index(drop=True)
        .rename(columns=DISPLAY_COL_MAP)
    )

    st.dataframe(display_df, use_container_width=True)

    # ---------- MAP VIEW ----------
    st.markdown(
        '<div class="section-title" style="margin-top: 1.2rem;">Map of Matching Studios</div>',
        unsafe_allow_html=True,
    )

    if {"latitude", "longitude"}.issubset(filtered.columns):
        map_df = filtered.head(top_n).copy()
        map_df = map_df.dropna(subset=["latitude", "longitude"])
        if not map_df.empty:
            map_df = map_df.rename(columns={"latitude": "lat", "longitude": "lon"})
            st.map(map_df[["lat", "lon"]])
        else:
            st.info("No studios with valid location for the current filters.")
    else:
        st.info("Location data not available for this dataset.")

    # ---------- CARD-STYLE PROFILES ----------
    st.markdown(
        '<div class="section-title" style="margin-top: 1.5rem;">Studio Profiles</div>',
        unsafe_allow_html=True,
    )

    for _, row in filtered.head(min(top_n, 10)).iterrows():
        st.markdown(
            f"""
            <div class="studio-card">
              <div class="studio-name">{row['name']}</div>
              <div style="margin-top:0.15rem; margin-bottom:0.35rem; font-size:0.85rem; color:#6b5a48;">
                <span class="chip"><span>⭐</span>Yelp {row.get('rating', 'N/A')}</span>
                <span class="chip"><span>⭐</span>Google {row.get('google_rating', 'N/A')}</span>
                <span class="chip">{int(row.get('review_count', 0))} Yelp reviews</span>
                <span class="chip">{int(row.get('google_user_ratings_total', 0))} Google reviews</span>
                <span class="chip">{row.get('region', '')}</span>
                <span class="chip">{row.get('city', '')}</span>
              </div>
              <div style="font-size:0.86rem; line-height:1.55; color:#4b3b2a;">
                <b>Instructor:</b> {row['instructor_sentiment_vader']:.2f} ·
                <b>Cleanliness:</b> {row['cleanliness_sentiment_vader']:.2f} ·
                <b>Intensity:</b> {row['intensity_sentiment_vader']:.2f}<br/>
                <b>Vibe/community:</b> {row['vibe_sentiment_vader']:.2f} ·
                <b>Parking:</b> {row['parking_sentiment_vader']:.2f} ·
                <b>Price/value:</b> {row['price_sentiment_vader']:.2f}
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # ---------- FOOTER ----------
    st.markdown(
        """
        <div style="
            text-align: center;
            margin-top: 3rem;
            padding: 1.25rem 0;
            font-family: Georgia, 'Times New Roman', serif;
            color: #4a4036;
            font-size: 1rem;
        ">
            Find Your Fit · Pilates Studio Profiler · COMM 587 Final Project
        </div>
        """,
        unsafe_allow_html=True,
    )


if __name__ == "__main__":
    main()
