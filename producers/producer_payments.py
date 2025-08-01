from kafka import KafkaProducer
import time
import logging
from typing import Optional
from flow_engine.flow_engine import FlowEngine

# ---------- Logging Setup ----------
logging.basicConfig(level=logging.INFO, format="[%(asctime)s] %(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

# ---------- Kafka Setup ----------
producer = KafkaProducer(
    bootstrap_servers='localhost:9092',
    value_serializer=lambda v: v.encode('utf-8')
)

# ---------- PAYMENTS Configuration ----------
CHECKPOINTS = [
    "PAYMENTS_INITIATED",
    "PAYMENTS_CHECKPOINT_1",
    "PAYMENTS_CHECKPOINT_2",
    "PAYMENTS_CHECKPOINT_3",
    "PAYMENTS_FINALIZED"
]

FAILURE_REASONS = [
    "PAYMENTS_FAILURE_REASON_1",
    "PAYMENTS_FAILURE_REASON_2",
    "PAYMENTS_FAILURE_REASON_3"
]

def log_checkpoint(correlation_id: str, checkpoint: str, status: str, failure_reason: Optional[str] = None) -> None:
    """
    Log a checkpoint event for the payments system to Kafka.
    Args:
        correlation_id: Unique identifier for the flow.
        checkpoint: Name of the checkpoint.
        status: 'SUCCESS' or 'FAILURE'.
        failure_reason: Optional failure reason if status is 'FAILURE'.
    """
    timestamp = time.strftime('%Y-%m-%dT%H:%M:%S')
    log_line = f"{timestamp} PAYMENTS: {checkpoint} - {status} (ID: {correlation_id})"
    producer.send("raw-logs", value=log_line)
    logger.info(f"💸 PAYMENTS checkpoint log sent: {log_line}")

def log_failure(correlation_id: str, reason: str) -> None:
    """
    Log a failure event for the payments system to Kafka.
    Args:
        correlation_id: Unique identifier for the flow.
        reason: Failure reason string.
    """
    timestamp = time.strftime('%Y-%m-%dT%H:%M:%S')
    error_line = f"{timestamp} PAYMENTS PAYMENTS_ERROR: (ID: {correlation_id}) - {reason}"
    producer.send("raw-logs", value=error_line)
    logger.info(f"❗ PAYMENTS failure reason sent: {error_line}")

# ---------- Flow Engine ----------
engine = FlowEngine(
    system_name="payments",
    checkpoints=CHECKPOINTS,
    failure_reasons=FAILURE_REASONS,
    log_checkpoint_fn=log_checkpoint,
    log_failure_fn=log_failure  # PAYMENTS logs failure separately
)

# ---------- Entry Point ----------
if __name__ == "__main__":
    engine.run()  # Standalone loop mode

# For orchestrator usage:
# from producer_payments import engine
# engine.run_flow(correlation_id)
