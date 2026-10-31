# Global Seismic Trends: Data-Driven Earthquake Insights

A student capstone project that pulls global earthquake data from the USGS
API, cleans and enriches it with Python/Pandas/Regex, analyzes it with 30
MySQL queries, and visualizes it with a Streamlit dashboard.

The dashboard reads straight from the cleaned Excel/CSV output — it does
**not** require MySQL to run. MySQL is only needed for the SQL-queries
deliverable (Part B below).

## Folder Structure

```
seismic-trends/
├── config.py                   # env-driven settings
├── main.py                     # orchestrator: fetch -> clean -> load
├── src/
│   ├── fetch_data.py           # Step 1: pull from USGS API
│   ├── clean_data.py           # Step 2: cleaning, regex, derived columns
│   └── db_loader.py            # Step 3: load into MySQL
├── sql/
│   ├── 01_create_table.sql     # table schema
│   └── 02_analysis_queries.sql # all 30 analysis queries
├── app/
│   └── streamlit_app.py        # dashboard
├── data/
│   ├── raw/                    # cached monthly API responses
│   └── processed/               # cleaned_earthquakes.csv / .xlsx
└── docs/
    ├── findings.md             # write-up template for key insights
    └── SETUP_OTHER_SYSTEM.md   # guide to set this up on another machine
```

## Setup (local)

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Running the pipeline (fetch + clean)

```bash
python main.py --skip-db
```

This fetches earthquakes (mag >= 4.5, last 5 years by default — configurable
via `.env` or `--start-date`/`--end-date` flags), cleans them, prints a
data-quality report, and saves the result to `data/processed/` as both
`cleaned_earthquakes.csv` and `cleaned_earthquakes.xlsx`.

Raw API responses are cached month-by-month in `data/raw/`, so re-running
the pipeline won't re-fetch months you already have.

## Running the dashboard

```bash
streamlit run app/streamlit_app.py
```

Reads directly from `data/processed/cleaned_earthquakes.xlsx` — no database
needed. Filter by date range, magnitude, continent, and depth category;
explore the map, trends, magnitude/depth distributions, data-quality
metrics, and top lists.

## Implementing the SQL part (MySQL)

1. `cp .env.example .env` and fill in your MySQL credentials.
2. Create the database once: `mysql -u root -p -e "CREATE DATABASE IF NOT EXISTS seismic_db;"`
3. Load the already-cleaned data in: `python src/db_loader.py` (creates the
   table from `sql/01_create_table.sql` automatically). Or run
   `python main.py` without `--skip-db` to fetch, clean, *and* load in one
   step.
4. Run the 30 queries in `sql/02_analysis_queries.sql` against `seismic_db`
   in MySQL Workbench / the `mysql` CLI / any client. They're grouped into
   sections (magnitude & depth, time trends, quality metrics, geography)
   matching the project brief.

> **Note on "casualties"/"economic loss" queries (#11-13):** the USGS API
> doesn't provide casualty or economic-loss data at all. Those 3 queries
> are implemented using `sig` (USGS's own significance/impact score) as a
> documented proxy — see the comment above each one in the SQL file.

## Setting this up on another machine

See [`docs/SETUP_OTHER_SYSTEM.md`](docs/SETUP_OTHER_SYSTEM.md) for a full
step-by-step guide to manually copy this project and get both the
dashboard and the MySQL/SQL part running there.

## Deliverables Mapping

| Brief deliverable | File(s) |
|---|---|
| MySQL database, fully cleaned | `src/clean_data.py`, `src/db_loader.py`, `sql/01_create_table.sql` |
| SQL queries | `sql/02_analysis_queries.sql` |
| Python analysis (Pandas, Regex) | `src/clean_data.py` |
| Streamlit dashboard | `app/streamlit_app.py` |
| Documentation | `README.md`, `docs/findings.md` |
