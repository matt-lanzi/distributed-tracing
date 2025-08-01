import uuid
import time
import logging
import threading
import random

from producers.producer_inventory import engine as inventory_engine
from producers.producer_payments import engine as payments_engine
from producers.producer_orders import engine as order_engine
from producers.producer_reporting import engine as reporting_engine

# ---------- Logging Setup ----------
logging.basicConfig(level=logging.INFO, format="[%(asctime)s] %(levelname)s: %(message)s")
logger = logging.getLogger("orchestrator")

# ---------- Config ----------
SLEEP_BETWEEN_SYSTEMS = 2  # seconds


def run_full_flow():
    correlation_id = str(uuid.uuid4())
    logger.info(f"🚀 Starting full flow for correlation_id: {correlation_id}")

    logger.info("➡️ Inventory flow...")
    inventory_engine.run_flow(correlation_id)

    time.sleep(SLEEP_BETWEEN_SYSTEMS)

    if random.random() < 0.5:
        logger.info("➡️ Payments flow...")
        payments_engine.run_flow(correlation_id)
        time.sleep(SLEEP_BETWEEN_SYSTEMS)
    else:
        logger.info("🛑 Payments flow skipped")

    time.sleep(SLEEP_BETWEEN_SYSTEMS)

    logger.info("➡️ Reporting and ORDER flows in parallel...")

    reporting_thread = threading.Thread(target=reporting_engine.run_flow, args=(correlation_id,))
    order_thread = threading.Thread(target=order_engine.run_flow, args=(correlation_id,))

    reporting_thread.start()
    order_thread.start()

    reporting_thread.join()
    order_thread.join()

    logger.info(f"✅ Flow complete for correlation_id: {correlation_id}")


if __name__ == "__main__":
    while True:
        run_full_flow()
        time.sleep(5)  # Optional pause between different flows
