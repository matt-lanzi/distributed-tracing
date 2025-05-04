from kafka import KafkaProducer
import json
import time
import logging
from flow_engine.flow_engine import FlowEngine

# ---------- Logging Setup ----------
logging.basicConfig(level=logging.INFO, format="[%(asctime)s] %(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

# ---------- Kafka Producer Setup ----------
producer = KafkaProducer(
    bootstrap_servers='localhost:9092',
    value_serializer=lambda v: json.dumps(v).encode('utf-8')
)

# ---------- Fedebom Configuration ----------
CHECKPOINTS = ["INITIATED", "CHECKPOINT_1", "CHECKPOINT_2", "FINALIZED"]
FAILURE_REASONS = ["FAILURE_REASON_1", "FAILURE_REASON_2", "FAILURE_REASON_3"]

def log_checkpoint(correlation_id, checkpoint, status, failure_reason=None):
    timestamp = time.strftime('%Y-%m-%dT%H:%M:%S')
    event = {
        "system": "fedebom",
        "checkpoint": checkpoint,
        "status": status,
        "timestamp": timestamp,
        "correlation_id": correlation_id
    }
    producer.send("raw-logs", value=event)
    logger.info(f"📦 fedebom checkpoint log sent: {event}")

def log_failure(correlation_id, reason):
    error = {
        "system": "fedebom",
        "correlation_id": correlation_id,
        "failure_reason": reason
    }
    producer.send("raw-logs", value=error)
    logger.info(f"❗ fedebom failure reason sent: {error}")

# ---------- Engine Initialization ----------
engine = FlowEngine(
    system_name="fedebom",
    checkpoints=CHECKPOINTS,
    failure_reasons=FAILURE_REASONS,
    log_checkpoint_fn=log_checkpoint,
    log_failure_fn=log_failure
)

# ---------- Dual Entry Point ----------
if __name__ == "__main__":
    engine.run()  # Loop mode by default

# To use in orchestrator:
# from producer_fedebom import engine
# engine.run_flow(correlation_id)