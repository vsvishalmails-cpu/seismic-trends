"""Global Seismic Trends dashboard.

Run from the project root:
    streamlit run app/streamlit_app.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pandas as pd
import plotly.express as px
import streamlit as st

import config

st.set_page_config(page_title="Global Seismic Trends", layout="wide")


@st.cache_data(ttl=600)
def load_data() -> pd.DataFrame:
    """Reads the cleaned dataset straight from Excel — no database required.

    (Once MySQL is set up for the SQL-query deliverable, this can be swapped
    for a `pd.read_sql("SELECT * FROM earthquakes", create_engine(config.db_url()))`
    call instead — the rest of the dashboard doesn't care where the
    DataFrame came from.)
    """
    if not config.CLEANED_XLSX_PATH.exists():
        return pd.DataFrame()

    df = pd.read_excel(config.CLEANED_XLSX_PATH)
    # Timestamps round-trip through Excel as text with inconsistent
    # fractional-second precision, so a single fixed format won't parse all
    # rows — "mixed" infers each one individually.
    df["time"] = pd.to_datetime(df["time"], format="mixed", utc=True)
    return df


def apply_filters(df: pd.DataFrame) -> pd.DataFrame:
    st.sidebar.header("Filters")

    min_date, max_date = df["time"].min().date(), df["time"].max().date()
    date_range = st.sidebar.date_input("Date range", (min_date, max_date), min_value=min_date, max_value=max_date)

    mag_min, mag_max = float(df["mag"].min()), float(df["mag"].max())
    mag_range = st.sidebar.slider("Magnitude range", mag_min, mag_max, (mag_min, mag_max))

    continents = sorted(df["continent"].dropna().unique())
    selected_continents = st.sidebar.multiselect("Continent", continents, default=continents)

    depth_categories = sorted(df["depth_category"].dropna().unique())
    selected_depths = st.sidebar.multiselect("Depth category", depth_categories, default=depth_categories)

    if len(date_range) == 2:
        start, end = date_range
        df = df[(df["time"].dt.date >= start) & (df["time"].dt.date <= end)]

    df = df[
        df["mag"].between(mag_range[0], mag_range[1])
        & df["continent"].isin(selected_continents)
        & df["depth_category"].isin(selected_depths)
    ]
    return df


def render_overview(df: pd.DataFrame) -> None:
    st.subheader("Overview")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total events", f"{len(df):,}")
    col2.metric("Average magnitude", f"{df['mag'].mean():.2f}")
    col3.metric("Tsunamis triggered", int(df["tsunami"].sum()))
    strongest = df.loc[df["mag"].idxmax()] if len(df) else None
    col4.metric("Strongest event", f"M{strongest['mag']:.1f}" if strongest is not None else "N/A")


def render_map(df: pd.DataFrame) -> None:
    st.subheader("Earthquake Map")
    fig = px.scatter_geo(
        df, lat="latitude", lon="longitude",
        color="mag", size="sig",
        color_continuous_scale="OrRd",
        hover_name="place",
        hover_data={"mag": True, "depth_km": True, "time": True},
        projection="natural earth",
    )
    st.plotly_chart(fig, width="stretch")


def render_trends(df: pd.DataFrame) -> None:
    st.subheader("Trends Over Time")
    col1, col2 = st.columns(2)

    yearly = df.groupby("year").size().reset_index(name="n_events")
    fig1 = px.bar(yearly, x="year", y="n_events", title="Earthquakes per year")
    col1.plotly_chart(fig1, width="stretch")

    yearly["yoy_growth_pct"] = yearly["n_events"].pct_change() * 100
    fig2 = px.line(yearly, x="year", y="yoy_growth_pct", title="Year-over-year growth (%)", markers=True)
    col2.plotly_chart(fig2, width="stretch")


def render_magnitude_depth(df: pd.DataFrame) -> None:
    st.subheader("Magnitude & Depth Analysis")
    col1, col2 = st.columns(2)

    fig1 = px.histogram(df, x="mag", nbins=30, title="Magnitude distribution")
    col1.plotly_chart(fig1, width="stretch")

    fig2 = px.box(df, x="depth_category", y="mag", title="Magnitude by depth category")
    col2.plotly_chart(fig2, width="stretch")


def render_quality_metrics(df: pd.DataFrame) -> None:
    st.subheader("Data Quality Metrics")
    col1, col2 = st.columns(2)

    by_continent = df.groupby("continent")[["rms", "gap"]].mean().round(3).reset_index()
    fig1 = px.bar(by_continent, x="continent", y="rms", title="Average RMS by continent")
    col1.plotly_chart(fig1, width="stretch")

    status_counts = df["status"].value_counts().reset_index()
    status_counts.columns = ["status", "n_events"]
    fig2 = px.pie(status_counts, names="status", values="n_events", title="Reviewed vs automatic")
    col2.plotly_chart(fig2, width="stretch")


def render_top_lists(df: pd.DataFrame) -> None:
    st.subheader("Top Lists")
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**Top 10 strongest earthquakes**")
        st.dataframe(df.nlargest(10, "mag")[["time", "place", "mag", "depth_km"]], hide_index=True)

    with col2:
        st.markdown("**Most active countries**")
        active = df.groupby("country").size().reset_index(name="n_events").sort_values("n_events", ascending=False).head(10)
        st.dataframe(active, hide_index=True)


def main() -> None:
    st.title("🌍 Global Seismic Trends: Data-Driven Earthquake Insights")

    raw_df = load_data()
    if raw_df.empty:
        st.warning("No data found. Run `python main.py --skip-db` first to generate the cleaned dataset.")
        return

    df = apply_filters(raw_df)

    render_overview(df)
    render_map(df)
    render_trends(df)
    render_magnitude_depth(df)
    render_quality_metrics(df)
    render_top_lists(df)


if __name__ == "__main__":
    main()
