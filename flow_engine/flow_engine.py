import time
import uuid
import random
import logging
from collections import OrderedDict

logger = logging.getLogger(__name__)
class FlowEngine:
    def __init__(
        self,
        system_name,
        checkpoints,
        failure_reasons,
        log_checkpoint_fn,
        log_failure_fn=None
    ):
        self.system = system_name
        self.checkpoints = checkpoints
        self.failure_reasons = failure_reasons
        self.log_checkpoint = log_checkpoint_fn
        self.log_failure = log_failure_fn
        self.flows = OrderedDict()

    def start_new_flow(self):
        correlation_id = str(uuid.uuid4())
        self.flows[correlation_id] = {
            "checkpoint_index": 0,
            "failed_attempts": 0
        }
        return correlation_id

    def should_fail(self, attempts):
        return (
            (attempts == 0 and random.random() < 0.5) or
            (attempts == 1 and random.random() < 0.3)
        )

    def run_flow(self, correlation_id):
        """Run a single flow to completion for a given correlation_id."""
        self.flows[correlation_id] = {
            "checkpoint_index": 0,
            "failed_attempts": 0
        }

        while correlation_id in self.flows:
            self._step_flow(correlation_id)
            time.sleep(1.5)

    def _step_flow(self, correlation_id):
        state = self.flows[correlation_id]
        checkpoint = self.checkpoints[state["checkpoint_index"]]
        should_fail = self.should_fail(state["failed_attempts"])
        status = "FAILURE" if should_fail else "SUCCESS"

        # Emit event
        failure_reason = None
        if status == "FAILURE":
            failure_reason = random.choice(self.failure_reasons)
        self.log_checkpoint(correlation_id, checkpoint, status, failure_reason)

        # Optional extra failure log
        if status == "FAILURE" and self.log_failure:
            self.log_failure(correlation_id, failure_reason)

        # State update
        if status == "SUCCESS":
            state["checkpoint_index"] += 1
            state["failed_attempts"] = 0
            if state["checkpoint_index"] >= len(self.checkpoints):
                logger.info(f"✅ {self.system} flow complete: {correlation_id}")
                del self.flows[correlation_id]
        else:
            state["failed_attempts"] += 1

    def run(self, interval_sec=3):
        logger.info(f"🚀 Starting {self.system} producer (loop mode)...")
        while True:
            # if not self.flows or (len(self.flows) < 3 and random.random() < 0.3):
            if len(self.flows) < 1:
                cid = self.start_new_flow()
            else:
                cid = next(iter(self.flows))

            self._step_flow(cid)
            time.sleep(interval_sec)
