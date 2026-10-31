"""Central place for all environment-driven settings."""
from datetime import date
from pathlib import Path

from dotenv import load_dotenv
import os

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent
RAW_DATA_DIR = BASE_DIR / "data" / "raw"
PROCESSED_DATA_DIR = BASE_DIR / "data" / "processed"
CLEANED_CSV_PATH = PROCESSED_DATA_DIR / "cleaned_earthquakes.csv"
CLEANED_XLSX_PATH = PROCESSED_DATA_DIR / "cleaned_earthquakes.xlsx"

# --- MySQL ---
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "3306")
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")
DB_NAME = os.getenv("DB_NAME", "seismic_db")


def db_url() -> str:
    return f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"


# --- USGS data pull window ---
MIN_MAGNITUDE = float(os.getenv("MIN_MAGNITUDE", "4.5"))


def _default_start() -> str:
    today = date.today()
    return today.replace(year=today.year - 5).isoformat()


def _default_end() -> str:
    return date.today().isoformat()


START_DATE = os.getenv("START_DATE") or _default_start()
END_DATE = os.getenv("END_DATE") or _default_end()

USGS_API_URL = "https://earthquake.usgs.gov/fdsnws/event/1/query"
