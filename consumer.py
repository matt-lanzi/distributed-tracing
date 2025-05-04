import json
import os
import sqlite3
import logging
from kafka import KafkaConsumer

from log_parsers.structured import parse_structured
from log_parsers.bcis import parse_bcis
from log_parsers.cmf import parse_cmf
import json

# ---------- Logging Setup ----------
log_level = logging.INFO
logging.basicConfig(level=log_level, format="[%(asctime)s] %(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

# ---------- SQLite Setup ----------
DB_PATH = "db/event_history.db"
if not os.path.exists(DB_PATH):
    raise FileNotFoundError("❌ SQLite DB not found. Run `db/schema_setup.py` first.")
conn = sqlite3.connect(DB_PATH)
c = conn.cursor()

# ---------- Kafka Setup ----------
consumer = KafkaConsumer(
    'raw-logs',
    bootstrap_servers='localhost:9092',
    value_deserializer=lambda m: m.decode('utf-8')
)

# ---------- Buffered Systems ----------
buffered_systems = {"fedebom", "cmf"}
buffer = {}

# ---------- Insert Logic ----------
def insert_event(entry):
    try:
        row = (
            entry.get("system_id"),
            entry.get("checkpoint_id"),
            entry.get("timestamp"),
            entry.get("status"),
            entry.get("correlation_id"),
            entry.get("failure_reason")
        )
        c.execute("INSERT INTO events VALUES (?, ?, ?, ?, ?, ?)", row)
        conn.commit()

        checkpoint = entry.get("checkpoint_id", "UNKNOWN_CHECKPOINT")
        status = entry.get("status", "UNKNOWN_STATUS")
        correlation_id = entry.get("correlation_id", "UNKNOWN_ID")
        reason = entry.get("failure_reason")

        message = f"✅ Inserted event: {correlation_id} at {checkpoint} — {status}"
        if status == "FAILURE" and reason:
            message += f" | Reason: {reason}"

        logger.info(message)

    except Exception as e:
        logger.error("❌ Failed to insert event: %s", e)

# ---------- Hybrid Join Logic ----------
def handle_log(entry):
    correlation_id = entry.get("correlation_id")
    system = entry.get("system_id")
    status = entry.get("status")
    has_error = entry.get("failure_reason") is not None

    if system in buffered_systems: # Failure events dont contain full event data, need to buffer and join on the main event
        buffer.setdefault(correlation_id, {}).update(entry)
        joined = buffer[correlation_id]

        if "status" in joined and (
            joined["status"] == "SUCCESS" or
            (joined["status"] == "FAILURE" and "failure_reason" in joined and joined["failure_reason"])
        ):
            insert_event(joined)
            buffer.pop(correlation_id, None)

    else:
        if status == "SUCCESS" or (status == "FAILURE" and has_error):
            insert_event(entry)
        else:
            logger.debug("⏳ Incomplete non-buffered event skipped: %s", correlation_id)


def parse_log(raw):
    raw = raw.strip()

    try:
        log = json.loads(raw)
        return parse_structured(log)
    except json.JSONDecodeError:
        pass

    if "BCIS:" in raw:
        return parse_bcis(raw)
    elif "CMF" in raw:
        return parse_cmf(raw)

    return None

if __name__ == "__main__":
    logger.info("👂 Listening for logs on topic 'raw-logs'...")

    for msg in consumer:
        raw = msg.value
        parsed = parse_log(raw)
        
        if not parsed:
            logger.warning("⚠️ Could not parse log: %s", raw)
            continue

        handle_log(parsed)
