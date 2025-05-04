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

# ---------- CMF Configuration ----------
CHECKPOINTS = [
    "CMF_INITIATED",
    "CMF_CHECKPOINT_1",
    "CMF_CHECKPOINT_2",
    "CMF_CHECKPOINT_3",
    "CMF_FINALIZED"
]

FAILURE_REASONS = [
    "CMF_FAILURE_REASON_1",
    "CMF_FAILURE_REASON_2",
    "CMF_FAILURE_REASON_3"
]

# ---------- Logging Functions ----------
def log_checkpoint(correlation_id, checkpoint, status, failure_reason=None):
    timestamp = time.strftime('%Y-%m-%dT%H:%M:%S')
    log_line = f"{timestamp} CMF: {checkpoint} - {status} (ID: {correlation_id})"
    producer.send("raw-logs", value=log_line)
    logger.info(f"📦 CMF checkpoint log sent: {log_line}")

def log_failure(correlation_id, reason):
    timestamp = time.strftime('%Y-%m-%dT%H:%M:%S')
    error_line = f"{timestamp} CMF CMF_ERROR: (ID: {correlation_id}) - {reason}"
    producer.send("raw-logs", value=error_line)
    logger.info(f"❗ CMF failure reason sent: {error_line}")

# ---------- Flow Engine ----------
engine = FlowEngine(
    system_name="cmf",
    checkpoints=CHECKPOINTS,
    failure_reasons=FAILURE_REASONS,
    log_checkpoint_fn=log_checkpoint,
    log_failure_fn=log_failure  # CMF logs failure separately
)

# ---------- Entry Point ----------
if __name__ == "__main__":
    engine.run()  # Standalone loop mode

# For orchestrator usage:
# from producer_cmf import engine
# engine.run_flow(correlation_id)
