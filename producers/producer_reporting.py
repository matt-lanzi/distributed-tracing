from kafka import KafkaProducer
import json
import time
import logging
from flow_engine.flow_engine import FlowEngine

# ---------- Logging Setup ----------
logging.basicConfig(level=logging.INFO, format="[%(asctime)s] %(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

# ---------- Kafka Setup ----------
producer = KafkaProducer(
    bootstrap_servers='localhost:9092',
    value_serializer=lambda v: json.dumps(v).encode('utf-8')
)

# ---------- Reporting Configuration ----------
CHECKPOINTS = [
    "REPORTING_INITIALIZED",
    "REPORTING_CHECKPOINT_1",
    "REPORTING_CHECKPOINT_2",
    "REPORTING_CHECKPOINT_3",
    "REPORTING_FINALIZED"
]

FAILURE_REASONS = [
    "REPORTING_FAILURE_REASON_1",
    "REPORTING_FAILURE_REASON_2",
    "REPORTING_FAILURE_REASON_3"
]

# ---------- Logging Function ----------
def log_checkpoint(correlation_id, checkpoint, status, failure_reason=None):
    timestamp = time.strftime('%Y-%m-%dT%H:%M:%S')

    log_event = {
        "system": "reporting",
        "checkpoint": checkpoint,
        "status": status,
        "timestamp": timestamp,
        "correlation_id": correlation_id
    }

    if status == "FAILURE" and failure_reason:
        log_event["failure_reason"] = failure_reason

    producer.send("raw-logs", value=log_event)
    logger.info(f"📦 Reporting log sent: {log_event}")

# ---------- Flow Engine ----------
engine = FlowEngine(
    system_name="reporting",
    checkpoints=CHECKPOINTS,
    failure_reasons=FAILURE_REASONS,
    log_checkpoint_fn=log_checkpoint,
    log_failure_fn=None  # Inline failure_reason in same JSON event
)

# ---------- Entry Point ----------
if __name__ == "__main__":
    engine.run()  # Looping standalone mode

# For orchestrator:
# from producer_reporting import engine
# engine.run_flow(correlation_id)
