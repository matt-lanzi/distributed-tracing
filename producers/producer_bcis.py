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

# ---------- BCIS Configuration ----------
CHECKPOINTS = [
    "BCIS_INITIALIZED",
    "BCIS_CHECKPOINT_1",
    "BCIS_CHECKPOINT_2",
    "BCIS_CHECKPOINT_3",
    "BCIS_FINALIZED"
]

FAILURE_REASONS = [
    "BCIS_FAILURE_REASON_1",
    "BCIS_FAILURE_REASON_2",
    "BCIS_FAILURE_REASON_3"
]

# ---------- Logging Function ----------
def log_checkpoint(correlation_id, checkpoint, status, failure_reason=None):
    timestamp = time.strftime('%Y-%m-%dT%H:%M:%S')

    if status == "FAILURE" and failure_reason:
        log_line = f"[ERROR] {timestamp} BCIS: {checkpoint} - FAILURE (ID: {correlation_id}) - {failure_reason}"
    else:
        log_line = f"[INFO] {timestamp} BCIS: {checkpoint} - SUCCESS (ID: {correlation_id})"

    producer.send("raw-logs", value=log_line)
    logger.info(f"📝 BCIS log sent: {log_line}")

# ---------- Flow Engine ----------
engine = FlowEngine(
    system_name="bcis",
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
