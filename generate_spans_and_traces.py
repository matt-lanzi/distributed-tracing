import sqlite3

conn = sqlite3.connect("db/event_history.db")
c = conn.cursor()

print("♻️ Rebuilding spans...")

c.executescript("""
DROP TABLE IF EXISTS spans;
                
CREATE TABLE spans AS
SELECT
    correlation_id,
    system_id,
    MIN(timestamp) AS start_time,
    MAX(timestamp) AS end_time,
    CAST(
        (julianday(MAX(timestamp)) - julianday(MIN(timestamp))) * 86400000
        AS INTEGER
    ) AS duration_ms,
    ROUND(
        (julianday(MAX(timestamp)) - julianday(MIN(timestamp))) * 86400,
        2
    ) AS duration_sec,
    (
        SELECT status
        FROM events e2
        WHERE e2.correlation_id = e1.correlation_id
          AND e2.system_id = e1.system_id
        ORDER BY timestamp DESC
        LIMIT 1
    ) AS status
FROM events e1
GROUP BY correlation_id, system_id
ORDER BY
    correlation_id,
    CASE system_id
        WHEN 'inventory' THEN 1
        WHEN 'payments' THEN 2
        WHEN 'orders' THEN 3
        WHEN 'reporting' THEN 4
        ELSE 5
    END;
""")

print("✅ Spans updated.")

print("♻️ Rebuilding trace summaries...")

c.executescript("""
DROP TABLE IF EXISTS trace_summary;

CREATE TABLE trace_summary AS
WITH trace_start AS (
    SELECT
        correlation_id,
        start_time AS trace_start
    FROM spans
    WHERE system_id = 'inventory'
),
trace_end AS (
    SELECT
        correlation_id,
        MAX(end_time) AS trace_end,
        MAX(system_id) FILTER (
            WHERE end_time = (
                SELECT MAX(end_time)
                FROM spans s2
                WHERE s2.correlation_id = s1.correlation_id
            )
        ) AS last_system_reached
    FROM spans s1
    GROUP BY correlation_id
)
SELECT
    t.correlation_id,
    t.trace_start,
    e.trace_end,
    ROUND((julianday(e.trace_end) - julianday(t.trace_start)) * 86400, 2) AS trace_duration_sec,
    CASE
        WHEN EXISTS (
            SELECT 1 FROM spans
            WHERE correlation_id = t.correlation_id
              AND system_id = 'reporting'
              AND status = 'SUCCESS'
        ) THEN 'COMPLETE'
        ELSE 'IN_PROGRESS'
    END AS trace_status,
    e.last_system_reached
FROM trace_start t
JOIN trace_end e ON t.correlation_id = e.correlation_id;
""")

print("✅ Trace summary updated.")

conn.commit()
conn.close()
