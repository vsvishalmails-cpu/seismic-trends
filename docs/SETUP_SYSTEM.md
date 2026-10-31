# Setting Up This Project on Another System

Steps to get this running on a different Mac (e.g. your brother's MacBook
Pro) by manually copying the project folder over — no git required. The
dashboard and the SQL deliverable are two independent tracks: do Part A
alone if you just want to show the dashboard, or both if you also need the
MySQL/SQL part working there.

## 0. Copy the project folder over

Zip up the whole `seismic-trends/` folder and move it across with AirDrop,
a USB drive, or a cloud drive (Google Drive/Dropbox) — whichever's easiest
between the two Macs.

```bash
cd /Users/thirumurugan/Desktop/GUVI
zip -r seismic-trends.zip seismic-trends -x "seismic-trends/venv/*" "seismic-trends/__pycache__/*"
```

AirDrop/copy `seismic-trends.zip`, then on the other Mac:

```bash
unzip seismic-trends.zip -d ~/Desktop/
cd ~/Desktop/seismic-trends
```

**Include `data/processed/cleaned_earthquakes.xlsx` and `.csv` in the copy**
— they're already-cleaned, ready-to-use data, so his machine doesn't need
to re-fetch anything from the USGS API. (`data/raw/` is optional — only
useful if he wants to re-run `python main.py` from scratch later.)

## 1. Install Python and the project's dependencies

Check Python is there: `python3 --version` (need 3.10+; macOS ships with a
usable one, or `brew install python3`).

```bash
cd ~/Desktop/seismic-trends
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

---

## Part A — View the Streamlit Dashboard (no MySQL needed)

The dashboard reads straight from `data/processed/cleaned_earthquakes.xlsx`
— as long as that file came over in the copy, this is all that's needed:

```bash
streamlit run app/streamlit_app.py
```

It opens in the browser automatically. If the xlsx file didn't come over,
regenerate it (re-fetches from USGS, ~2-5 min):

```bash
python main.py --skip-db
```

---

## Part B — Implement the SQL part (MySQL)

### B1. Install MySQL

```bash
brew install mysql
brew services start mysql
```

Set a root password (skip if MySQL asks you to set one during install):

```bash
mysql_secure_installation
```

Or set/change it directly:

```bash
mysql -u root
```
```sql
ALTER USER 'root'@'localhost' IDENTIFIED BY 'mypassword';
```

### B2. Create the database

```bash
mysql -u root -p -e "CREATE DATABASE IF NOT EXISTS seismic_db;"
```

### B3. Configure `.env`

```bash
cp .env.example .env
```

Edit `.env`:

```
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=mypassword
DB_NAME=seismic_db
```

### B4. Load the data into MySQL

Fastest path — the cleaned CSV already came over in the copy, so just load
it (creates the table from `sql/01_create_table.sql` automatically):

```bash
python src/db_loader.py
```

(Alternative: `python main.py` re-fetches from USGS and loads in one step —
only needed if you don't have the cleaned CSV, or want fresher data.)

Check it worked:

```bash
mysql -u root -p seismic_db -e "SELECT COUNT(*) FROM earthquakes;"
```

### B5. Run the 30 analysis queries

Open `sql/02_analysis_queries.sql` in any MySQL client (MySQL Workbench,
DBeaver, or the `mysql` CLI) connected to `seismic_db` — each query is a
standalone, commented `SELECT`, grouped by theme (magnitude/depth, time
trends, quality metrics, geography). Run them one at a time, or all at
once:

```bash
mysql -u root -p seismic_db < sql/02_analysis_queries.sql
```

---

## Troubleshooting

- **`Access denied` / auth plugin errors**: newer MySQL defaults to
  `caching_sha2_password`, which some older client libraries don't support.
  If `PyMySQL` fails to connect, run on the server:
  ```sql
  ALTER USER 'root'@'localhost' IDENTIFIED WITH mysql_native_password BY 'mypassword';
  ```
- **`Can't connect to MySQL server`**: confirm `brew services list` shows
  mysql as `started`, and that `DB_HOST`/`DB_PORT` in `.env` match
  (`localhost`/`3306`).
- **`ModuleNotFoundError`**: the virtual environment isn't activated —
  run `source venv/bin/activate` again in that terminal.
- **Streamlit shows "No data found"**: `data/processed/cleaned_earthquakes.xlsx`
  wasn't copied over — run `python main.py --skip-db` to regenerate it.
