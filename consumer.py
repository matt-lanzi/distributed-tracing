import json
import os
import sqlite3
import logging
from typing import Any, Dict, Optional
from kafka import KafkaConsumer

from log_parsers.structured import parse_structured
from log_parsers.orders import parse_order
from log_parsers.payments import parse_payments

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
buffered_systems = {"inventory", "payments"}
buffer: Dict[str, Dict[str, Any]] = {}

def insert_event(entry: Dict[str, Any]) -> None:
    """
    Insert a normalized event into the SQLite database and log the operation.
    Args:
        entry: Dictionary containing normalized event fields.
    """
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

def handle_log(entry: Dict[str, Any]) -> None:
    """
    Handle a parsed log entry, performing hybrid join logic for buffered systems.
    Args:
        entry: Dictionary containing normalized event fields.
    """
    correlation_id = entry.get("correlation_id")
    system = entry.get("system_id")
    status = entry.get("status")
    has_error = entry.get("failure_reason") is not None

    if system in buffered_systems:
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

def parse_log(raw: str) -> Optional[Dict[str, Any]]:
    """
    Parse a raw log line (JSON or text) into a normalized event dictionary.
    Args:
        raw: Raw log line as a string.
    Returns:
        Normalized event dictionary, or None if parsing fails.
    """
    raw = raw.strip()
    try:
        log = json.loads(raw)
        return parse_structured(log)
    except json.JSONDecodeError:
        pass
    if "ORDER:" in raw:
        return parse_order(raw)
    elif "PAYMENTS" in raw:
        return parse_payments(raw)
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
