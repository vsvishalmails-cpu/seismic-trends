-- Schema for the cleaned earthquake dataset.
-- Run this manually once (or let src/db_loader.py run it for you) after
-- creating the database itself, e.g.:
--   CREATE DATABASE IF NOT EXISTS seismic_db;

CREATE TABLE IF NOT EXISTS earthquakes (
    -- --- 26 source features from the USGS API ---
    id              VARCHAR(40)  PRIMARY KEY,
    time            DATETIME,
    updated         DATETIME,
    latitude        DOUBLE,
    longitude       DOUBLE,
    depth_km        DOUBLE,
    mag             DOUBLE,
    magType         VARCHAR(20),
    place           VARCHAR(255),
    status          VARCHAR(20),
    tsunami         TINYINT,
    sig             INT,
    net             VARCHAR(10),
    nst             DOUBLE,
    dmin            DOUBLE,
    rms             DOUBLE,
    gap             DOUBLE,
    magError        DOUBLE,
    depthError      DOUBLE,
    magNst          DOUBLE,
    locationSource  VARCHAR(20),
    magSource       VARCHAR(20),
    types           VARCHAR(255),
    ids             VARCHAR(255),
    sources         VARCHAR(100),
    type            VARCHAR(30),
    alert           VARCHAR(10),

    -- --- derived columns (src/clean_data.py) ---
    country         VARCHAR(100),
    continent       VARCHAR(30),
    year            INT,
    month           INT,
    day             INT,
    day_of_week     VARCHAR(10),
    hour            INT,
    depth_category  VARCHAR(20),
    mag_category    VARCHAR(20),
    is_shallow      TINYINT,
    is_deep         TINYINT,
    is_strong       TINYINT,
    is_destructive  TINYINT,

    INDEX idx_time (time),
    INDEX idx_country (country),
    INDEX idx_mag (mag)
);
