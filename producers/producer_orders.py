from kafka import KafkaProducer
import time
import logging
from flow_engine.flow_engine import FlowEngine

# ---------- Logging Setup ----------
logging.basicConfig(level=logging.INFO, format="[%(asctime)s] %(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

# ---------- Kafka Setup ----------
producer = KafkaProducer(
    bootstrap_servers='localhost:9092',
    value_serializer=lambda v: v.encode('utf-8')
)

# ---------- ORDER Configuration ----------
CHECKPOINTS = [
    "ORDER_INITIALIZED",
    "ORDER_CHECKPOINT_1",
    "ORDER_CHECKPOINT_2",
    "ORDER_CHECKPOINT_3",
    "ORDER_FINALIZED"
]

FAILURE_REASONS = [
    "ORDER_FAILURE_REASON_1",
    "ORDER_FAILURE_REASON_2",
    "ORDER_FAILURE_REASON_3"
]

# ---------- Logging Function ----------
def log_checkpoint(correlation_id, checkpoint, status, failure_reason=None):
    timestamp = time.strftime('%Y-%m-%dT%H:%M:%S')

    if status == "FAILURE" and failure_reason:
        log_line = f"[ERROR] {timestamp} ORDER: {checkpoint} - FAILURE (ID: {correlation_id}) - {failure_reason}"
    else:
        log_line = f"[INFO] {timestamp} ORDER: {checkpoint} - SUCCESS (ID: {correlation_id})"

    producer.send("raw-logs", value=log_line)
    logger.info(f"📝 ORDER log sent: {log_line}")

# ---------- Flow Engine ----------
engine = FlowEngine(
    system_name="orders",
    checkpoints=CHECKPOINTS,
    failure_reasons=FAILURE_REASONS,
    log_checkpoint_fn=log_checkpoint,
    log_failure_fn=None  # Inline error — no separate failure log
)

# ---------- Entry Point ----------
if __name__ == "__main__":
    engine.run()  # Standalone loop mode

# For orchestrated flow:
# from producer_bcis import engine
# engine.run_flow(correlation_id)
