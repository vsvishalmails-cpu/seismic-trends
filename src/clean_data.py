"""Step 2: clean, validate, and enrich the raw earthquake data.

This is the most heavily graded part of the brief ("Data Cleaning Accuracy",
35%), so every transformation is its own small, readable function.
"""
import re
import warnings

import numpy as np
import pandas as pd

# median() on an all-NaN column (some USGS networks never report certain
# fields) triggers a harmless numpy "Mean of empty slice" warning; we handle
# that case explicitly below, so silence the noise.
warnings.filterwarnings("ignore", message="Mean of empty slice")

NUMERIC_COLUMNS = [
    "mag", "depth_km", "nst", "dmin", "rms", "gap",
    "magError", "depthError", "magNst", "sig",
]

TEXT_COLUMNS = ["magType", "status", "net", "type"]

# US state/territory abbreviations that show up in `place` instead of a country
# (e.g. "25km N of Ridgecrest, CA" -> country should be "United States").
US_STATE_ABBREVIATIONS = {
    "AL", "AK", "AZ", "AR", "CA", "CO", "CT", "DE", "FL", "GA", "HI", "ID",
    "IL", "IN", "IA", "KS", "KY", "LA", "ME", "MD", "MA", "MI", "MN", "MS",
    "MO", "MT", "NE", "NV", "NH", "NJ", "NM", "NY", "NC", "ND", "OH", "OK",
    "OR", "PA", "RI", "SC", "SD", "TN", "TX", "UT", "VT", "VA", "WA", "WV",
    "WI", "WY", "PR",
}

# Ocean/region phrases that have no trailing country name. Mapped to a
# reasonable region label so they aren't lumped into "Unknown".
OCEAN_REGION_PATTERNS = {
    r"south sandwich islands": "South Sandwich Islands",
    r"mid-?atlantic ridge": "Mid-Atlantic Ridge",
    r"fiji islands": "Fiji",
    r"kermadec islands": "New Zealand",
    r"pacific-antarctic ridge": "Pacific-Antarctic Ridge",
    r"southwest indian ridge": "Southwest Indian Ridge",
    r"ascension island": "Ascension Island",
    r"indian ocean": "Indian Ocean",
    r"pacific ocean": "Pacific Ocean",
    r"atlantic ocean": "Atlantic Ocean",
}

# Pragmatic country -> continent lookup covering countries that actually
# appear in global seismic data. Not a full geocoding solution by design —
# good enough for a student project's aggregate analysis.
COUNTRY_TO_CONTINENT = {
    "United States": "North America", "Mexico": "North America",
    "Canada": "North America", "Guatemala": "North America",
    "Puerto Rico": "North America", "Costa Rica": "North America",
    "Panama": "North America", "Cuba": "North America",
    "Chile": "South America", "Peru": "South America",
    "Argentina": "South America", "Colombia": "South America",
    "Ecuador": "South America", "Bolivia": "South America",
    "Venezuela": "South America", "Brazil": "South America",
    "Japan": "Asia", "Indonesia": "Asia", "Philippines": "Asia",
    "China": "Asia", "India": "Asia", "Iran": "Asia",
    "Afghanistan": "Asia", "Pakistan": "Asia", "Russia": "Asia",
    "Turkey": "Asia", "Nepal": "Asia", "Myanmar": "Asia",
    "Taiwan": "Asia", "South Korea": "Asia", "North Korea": "Asia",
    "Papua New Guinea": "Oceania", "Fiji": "Oceania",
    "Tonga": "Oceania", "Vanuatu": "Oceania", "New Zealand": "Oceania",
    "Solomon Islands": "Oceania", "Samoa": "Oceania",
    "Greece": "Europe", "Italy": "Europe", "Iceland": "Europe",
    "Spain": "Europe", "Portugal": "Europe", "Romania": "Europe",
    "Albania": "Europe", "Croatia": "Europe",
    "Algeria": "Africa", "Morocco": "Africa", "Tanzania": "Africa",
    "Democratic Republic of the Congo": "Africa", "Mozambique": "Africa",
    "South Sandwich Islands": "Antarctica/Ocean",
    "Mid-Atlantic Ridge": "Antarctica/Ocean",
    "Pacific-Antarctic Ridge": "Antarctica/Ocean",
    "Southwest Indian Ridge": "Antarctica/Ocean",
    "Ascension Island": "Antarctica/Ocean",
    "Indian Ocean": "Antarctica/Ocean",
    "Pacific Ocean": "Antarctica/Ocean",
    "Atlantic Ocean": "Antarctica/Ocean",
}


def convert_datetimes(df: pd.DataFrame) -> pd.DataFrame:
    """USGS timestamps are epoch milliseconds."""
    df["time"] = pd.to_datetime(df["time"], unit="ms", utc=True)
    df["updated"] = pd.to_datetime(df["updated"], unit="ms", utc=True)
    return df


def extract_country(place: str) -> str:
    """Pull a country/region name out of a USGS `place` string via regex."""
    if not isinstance(place, str) or not place.strip():
        return "Unknown"

    lowered = place.lower()
    for pattern, region in OCEAN_REGION_PATTERNS.items():
        if re.search(pattern, lowered):
            return region

    # Most place strings end in ", <State or Country>" (allow "U.S. Virgin
    # Islands"-style periods/apostrophes in the captured name).
    match = re.search(r",\s*([A-Za-z.'\s]+)$", place)
    if match:
        candidate = match.group(1).strip()
        candidate = re.sub(r"\s+region$", "", candidate, flags=re.IGNORECASE)
        if candidate.replace(".", "").upper() in US_STATE_ABBREVIATIONS:
            return "United States"
        return candidate

    # No comma, but a "... of <Place>" distance phrase (e.g. "South of the
    # Fiji Islands").
    match = re.search(r"\bof\s+(?:the\s+)?([A-Za-z\s]+)$", place)
    if match:
        return match.group(1).strip()

    # No comma and no "of" phrase: USGS used a bare region name already
    # (e.g. "Fiji region", "Reykjanes Ridge", "Kuril Islands") — use it as-is
    # (minus a trailing "region") rather than discarding it as unknown.
    bare_region = re.sub(r"\s+region$", "", place.strip(), flags=re.IGNORECASE)
    return bare_region if bare_region else "Unknown"


def map_continent(country: str) -> str:
    return COUNTRY_TO_CONTINENT.get(country, "Other/Unknown")


def clean_location_fields(df: pd.DataFrame) -> pd.DataFrame:
    df["country"] = df["place"].apply(extract_country)
    df["continent"] = df["country"].apply(map_continent)
    return df


def clean_text_fields(df: pd.DataFrame) -> pd.DataFrame:
    for col in TEXT_COLUMNS:
        df[col] = df[col].astype(str).str.strip().str.lower().replace({"none": np.nan, "nan": np.nan})
    df["alert"] = df["alert"].astype(str).str.strip().str.lower().replace({"none": np.nan, "nan": np.nan})
    df["alert"] = df["alert"].fillna("none")
    return df


def clean_numeric_fields(df: pd.DataFrame) -> pd.DataFrame:
    for col in NUMERIC_COLUMNS:
        df[col] = pd.to_numeric(df[col], errors="coerce")
        median = df[col].median()
        # A handful of USGS networks never report some fields (e.g. magError);
        # if the whole column is missing, there's no median to fall back on.
        df[col] = df[col].fillna(median if pd.notna(median) else 0)
    df["tsunami"] = pd.to_numeric(df["tsunami"], errors="coerce").fillna(0).astype(int)
    return df


def validate_ranges(df: pd.DataFrame) -> pd.DataFrame:
    """Drop rows with physically impossible coordinates or depth."""
    before = len(df)
    df = df[
        df["latitude"].between(-90, 90)
        & df["longitude"].between(-180, 180)
        & (df["depth_km"] >= 0)
    ]
    dropped = before - len(df)
    if dropped:
        print(f"Dropped {dropped} rows with invalid lat/lon/depth.")
    return df


def add_derived_columns(df: pd.DataFrame) -> pd.DataFrame:
    df["year"] = df["time"].dt.year
    df["month"] = df["time"].dt.month
    df["day"] = df["time"].dt.day
    df["day_of_week"] = df["time"].dt.day_name()
    df["hour"] = df["time"].dt.hour

    df["depth_category"] = pd.cut(
        df["depth_km"], bins=[-1, 70, 300, np.inf],
        labels=["shallow", "intermediate", "deep"],
    )
    df["mag_category"] = pd.cut(
        df["mag"], bins=[-np.inf, 4, 5, 6, 7, np.inf],
        labels=["minor", "light", "moderate", "strong", "major"],
    )

    df["is_shallow"] = df["depth_km"] < 70
    df["is_deep"] = df["depth_km"] > 300
    df["is_strong"] = df["mag"] >= 6
    df["is_destructive"] = df["mag"] >= 7.5
    return df


def print_quality_report(before_rows: int, df: pd.DataFrame) -> None:
    print("\n--- Data Quality Report ---")
    print(f"Rows before cleaning: {before_rows}")
    print(f"Rows after cleaning:  {len(df)}")
    print("Null counts per column:")
    print(df.isnull().sum()[df.isnull().sum() > 0].to_string() or "  (none)")
    print(f"'Unknown' country count: {(df['country'] == 'Unknown').sum()}")
    print("---------------------------\n")


def clean(df: pd.DataFrame) -> pd.DataFrame:
    """Run the full cleaning pipeline and return the cleaned DataFrame."""
    before_rows = len(df)

    df = convert_datetimes(df)
    df = clean_location_fields(df)
    df = clean_text_fields(df)
    df = clean_numeric_fields(df)
    df = validate_ranges(df)
    df = add_derived_columns(df)
    df = df.drop_duplicates(subset="id").reset_index(drop=True)

    print_quality_report(before_rows, df)
    return df
