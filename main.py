"""Orchestrates the full pipeline: fetch -> clean -> load into MySQL.

Usage:
    python main.py
    python main.py --start-date 2021-01-01 --end-date 2021-12-31
    python main.py --skip-db   # fetch + clean only, skip the MySQL step
"""
import argparse

import config
from src import clean_data, db_loader, fetch_data


def run(start_date: str, end_date: str, skip_db: bool) -> None:
    print(f"Pipeline window: {start_date} to {end_date} (min magnitude {config.MIN_MAGNITUDE})\n")

    raw_df = fetch_data.fetch_all(start_date, end_date)
    cleaned_df = clean_data.clean(raw_df)

    config.PROCESSED_DATA_DIR.mkdir(parents=True, exist_ok=True)
    cleaned_df.to_csv(config.CLEANED_CSV_PATH, index=False)
    print(f"Saved cleaned data to {config.CLEANED_CSV_PATH}")

    # Excel has no timezone-aware datetime type. Store timestamps as naive UTC;
    # the dashboard reads them back with utc=True.
    excel_df = cleaned_df.copy()
    for column in ("time", "updated"):
        if column in excel_df and excel_df[column].dt.tz is not None:
            excel_df[column] = excel_df[column].dt.tz_localize(None)
    excel_df.to_excel(config.CLEANED_XLSX_PATH, index=False, engine="openpyxl")
    print(f"Saved cleaned data to {config.CLEANED_XLSX_PATH}")
    print("(The Streamlit dashboard reads from this Excel file directly — no MySQL required to view it.)")

    if skip_db:
        print("Skipping MySQL load (--skip-db).")
        return

    db_loader.load(cleaned_df)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Global Seismic Trends pipeline")
    parser.add_argument("--start-date", default=config.START_DATE)
    parser.add_argument("--end-date", default=config.END_DATE)
    parser.add_argument("--skip-db", action="store_true")
    args = parser.parse_args()

    run(args.start_date, args.end_date, args.skip_db)
