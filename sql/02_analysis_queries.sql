-- 30 analytical queries over the `earthquakes` table.
-- Grouped to match the project brief's sections. MySQL 8+ syntax
-- (window functions used in a few places).

-- =====================================================
-- MAGNITUDE & DEPTH
-- =====================================================

-- 1. Top 10 strongest earthquakes
SELECT id, time, place, mag, depth_km
FROM earthquakes
ORDER BY mag DESC
LIMIT 10;

-- 2. Top 10 deepest earthquakes
SELECT id, time, place, mag, depth_km
FROM earthquakes
ORDER BY depth_km DESC
LIMIT 10;

-- 3. Shallow earthquakes (< 50 km) with mag > 7.5
SELECT id, time, place, mag, depth_km
FROM earthquakes
WHERE depth_km < 50 AND mag > 7.5
ORDER BY mag DESC;

-- 4. Average depth per continent
SELECT continent, ROUND(AVG(depth_km), 2) AS avg_depth_km
FROM earthquakes
GROUP BY continent
ORDER BY avg_depth_km DESC;

-- 5. Average magnitude per magnitude type
SELECT magType, ROUND(AVG(mag), 2) AS avg_mag, COUNT(*) AS n_events
FROM earthquakes
GROUP BY magType
ORDER BY avg_mag DESC;


-- =====================================================
-- TIME ANALYSIS
-- =====================================================

-- 6. Year with the most earthquakes
SELECT year, COUNT(*) AS n_events
FROM earthquakes
GROUP BY year
ORDER BY n_events DESC
LIMIT 1;

-- 7. Month with the highest number of earthquakes (across all years)
SELECT month, COUNT(*) AS n_events
FROM earthquakes
GROUP BY month
ORDER BY n_events DESC
LIMIT 1;

-- 8. Day of week with the most earthquakes
SELECT day_of_week, COUNT(*) AS n_events
FROM earthquakes
GROUP BY day_of_week
ORDER BY n_events DESC
LIMIT 1;

-- 9. Count of earthquakes per hour of day
SELECT hour, COUNT(*) AS n_events
FROM earthquakes
GROUP BY hour
ORDER BY hour;

-- 10. Most active reporting network
SELECT net, COUNT(*) AS n_events
FROM earthquakes
GROUP BY net
ORDER BY n_events DESC
LIMIT 1;


-- =====================================================
-- "CASUALTIES & ECONOMIC LOSS" (11-13)
-- NOTE: the USGS API has no casualty or economic-loss fields at all
-- (confirmed against the 26 documented features). These 3 queries are
-- reimplemented using `sig` (USGS's own event-significance score) as a
-- documented stand-in for "impact" / "economic loss".
-- =====================================================

-- 11. Top 5 places with the highest average significance (casualty/impact proxy)
SELECT place, ROUND(AVG(sig), 1) AS avg_significance, COUNT(*) AS n_events
FROM earthquakes
GROUP BY place
ORDER BY avg_significance DESC
LIMIT 5;

-- 12. Total significance score per continent (economic-loss proxy)
SELECT continent, SUM(sig) AS total_significance
FROM earthquakes
GROUP BY continent
ORDER BY total_significance DESC;

-- 13. Average significance by alert level (economic-loss proxy)
SELECT alert, ROUND(AVG(sig), 1) AS avg_significance, COUNT(*) AS n_events
FROM earthquakes
GROUP BY alert
ORDER BY avg_significance DESC;


-- =====================================================
-- EVENT TYPE & QUALITY METRICS
-- =====================================================

-- 14. Count of reviewed vs automatic earthquakes
SELECT status, COUNT(*) AS n_events
FROM earthquakes
GROUP BY status;

-- 15. Count by earthquake type
SELECT type, COUNT(*) AS n_events
FROM earthquakes
GROUP BY type
ORDER BY n_events DESC;

-- 16. Number of earthquakes by data type combination
SELECT types, COUNT(*) AS n_events
FROM earthquakes
GROUP BY types
ORDER BY n_events DESC;

-- 17. Average RMS and gap per continent
SELECT continent, ROUND(AVG(rms), 3) AS avg_rms, ROUND(AVG(gap), 1) AS avg_gap
FROM earthquakes
GROUP BY continent
ORDER BY avg_rms;

-- 18. Events with high station coverage (nst > 50)
SELECT id, time, place, mag, nst
FROM earthquakes
WHERE nst > 50
ORDER BY nst DESC;

-- 19. Number of tsunamis triggered per year
SELECT year, SUM(tsunami) AS tsunami_count
FROM earthquakes
GROUP BY year
ORDER BY year;

-- 20. Count of earthquakes by alert level
SELECT alert, COUNT(*) AS n_events
FROM earthquakes
GROUP BY alert
ORDER BY n_events DESC;


-- =====================================================
-- TSUNAMIS, ALERTS & SEISMIC PATTERN TRENDS
-- =====================================================

-- 21. Top 5 countries with the highest average magnitude (past 5 years = whole table)
SELECT country, ROUND(AVG(mag), 2) AS avg_mag, COUNT(*) AS n_events
FROM earthquakes
GROUP BY country
HAVING COUNT(*) >= 5          -- avoid single-event outliers skewing the average
ORDER BY avg_mag DESC
LIMIT 5;

-- 22. Countries with both shallow and deep earthquakes in the same month
SELECT country, year, month
FROM earthquakes
GROUP BY country, year, month
HAVING SUM(is_shallow) > 0 AND SUM(is_deep) > 0
ORDER BY country, year, month;

-- 23. Year-over-year growth rate in total earthquakes globally
WITH yearly_counts AS (
    SELECT year, COUNT(*) AS n_events
    FROM earthquakes
    GROUP BY year
)
SELECT
    year,
    n_events,
    LAG(n_events) OVER (ORDER BY year) AS prev_year_events,
    ROUND(
        100.0 * (n_events - LAG(n_events) OVER (ORDER BY year))
        / LAG(n_events) OVER (ORDER BY year), 1
    ) AS yoy_growth_pct
FROM yearly_counts
ORDER BY year;

-- 24. 3 most seismically active regions (frequency + avg magnitude combined)
SELECT
    country,
    COUNT(*) AS n_events,
    ROUND(AVG(mag), 2) AS avg_mag,
    RANK() OVER (ORDER BY COUNT(*) * AVG(mag) DESC) AS activity_rank
FROM earthquakes
GROUP BY country
ORDER BY activity_rank
LIMIT 3;


-- =====================================================
-- DEPTH, LOCATION & DISTANCE-BASED ANALYSIS
-- =====================================================

-- 25. Average depth per country, within +-5 degrees latitude of the equator
SELECT country, ROUND(AVG(depth_km), 2) AS avg_depth_km, COUNT(*) AS n_events
FROM earthquakes
WHERE latitude BETWEEN -5 AND 5
GROUP BY country
ORDER BY avg_depth_km DESC;

-- 26. Countries with the highest ratio of shallow to deep earthquakes
SELECT
    country,
    SUM(is_shallow) AS shallow_count,
    SUM(is_deep) AS deep_count,
    ROUND(SUM(is_shallow) / GREATEST(SUM(is_deep), 1), 2) AS shallow_to_deep_ratio
FROM earthquakes
GROUP BY country
HAVING SUM(is_deep) > 0
ORDER BY shallow_to_deep_ratio DESC
LIMIT 10;

-- 27. Average magnitude difference: tsunami-alert events vs non-tsunami events
SELECT
    (SELECT AVG(mag) FROM earthquakes WHERE tsunami = 1) -
    (SELECT AVG(mag) FROM earthquakes WHERE tsunami = 0) AS avg_mag_difference;

-- 28. Events with the lowest data reliability (highest combined gap + rms error)
SELECT id, time, place, gap, rms, (gap + rms) AS error_score
FROM earthquakes
ORDER BY error_score DESC
LIMIT 10;

-- 29. Pairs of consecutive earthquakes within 50km and within 1 hour of each other
SELECT
    a.id AS event_1, b.id AS event_2,
    a.time AS time_1, b.time AS time_2,
    TIMESTAMPDIFF(MINUTE, a.time, b.time) AS minutes_apart,
    ROUND(
        6371 * ACOS(
            COS(RADIANS(a.latitude)) * COS(RADIANS(b.latitude)) * COS(RADIANS(b.longitude - a.longitude))
            + SIN(RADIANS(a.latitude)) * SIN(RADIANS(b.latitude))
        ), 2
    ) AS distance_km
FROM earthquakes a
JOIN earthquakes b
    ON a.id < b.id
    AND ABS(TIMESTAMPDIFF(SECOND, a.time, b.time)) <= 3600
HAVING distance_km <= 50
ORDER BY a.time;

-- 30. Regions with the highest frequency of deep-focus earthquakes (depth > 300km)
SELECT country, COUNT(*) AS deep_focus_count
FROM earthquakes
WHERE depth_km > 300
GROUP BY country
ORDER BY deep_focus_count DESC
LIMIT 10;
