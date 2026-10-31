"""Step 3: load the cleaned DataFrame into MySQL."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pandas as pd
from sqlalchemy import create_engine, text

import config

SQL_DIR = Path(__file__).resolve().parent.parent / "sql"


def get_engine():
    return create_engine(config.db_url())


def ensure_table_exists(engine) -> None:
    """Create the `earthquakes` table from the schema file if needed."""
    schema_sql = (SQL_DIR / "01_create_table.sql").read_text()
    with engine.begin() as conn:
        for statement in schema_sql.split(";"):
            statement = statement.strip()
            if statement:
                conn.execute(text(statement))


def load(df: pd.DataFrame) -> None:
    engine = get_engine()
    ensure_table_exists(engine)  # CREATE TABLE IF NOT EXISTS, with real types + indexes

    # Mapping categorical dtypes back to plain strings for MySQL.
    for col in ("depth_category", "mag_category"):
        if col in df.columns:
            df[col] = df[col].astype(str)

    with engine.begin() as conn:
        conn.execute(text("TRUNCATE TABLE earthquakes"))  # idempotent re-run, keeps schema/indexes

    df.to_sql("earthquakes", engine, if_exists="append", index=False, chunksize=1000)
    print(f"Loaded {len(df)} rows into '{config.DB_NAME}.earthquakes'.")


if __name__ == "__main__":
    cleaned = pd.read_csv(config.CLEANED_CSV_PATH)
    load(cleaned)
