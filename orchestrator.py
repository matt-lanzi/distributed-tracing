import uuid
import time
import logging

from producers.producer_fedebom import engine as fedebom_engine
from producers.producer_cmf import engine as cmf_engine
from producers.producer_bcis import engine as bcis_engine
from producers.producer_reporting import engine as reporting_engine

# ---------- Logging Setup ----------
logging.basicConfig(level=logging.INFO, format="[%(asctime)s] %(levelname)s: %(message)s")
logger = logging.getLogger("orchestrator")

# ---------- Config ----------
SLEEP_BETWEEN_SYSTEMS = 2  # seconds


def run_full_flow():
    correlation_id = str(uuid.uuid4())
    logger.info(f"🚀 Starting full flow for correlation_id: {correlation_id}")

    logger.info("➡️ Fedebom flow...")
    fedebom_engine.run_flow(correlation_id)

    time.sleep(SLEEP_BETWEEN_SYSTEMS)

    logger.info("➡️ CMF flow...")
    cmf_engine.run_flow(correlation_id)

    time.sleep(SLEEP_BETWEEN_SYSTEMS)

    logger.info("➡️ Reporting flow...")
    reporting_engine.run_flow(correlation_id)

    logger.info("➡️ BCIS flow...")
    bcis_engine.run_flow(correlation_id)

    logger.info(f"✅ Flow complete for correlation_id: {correlation_id}")


if __name__ == "__main__":
    while True:
        run_full_flow()
        time.sleep(5)  # Optional pause between different flows
