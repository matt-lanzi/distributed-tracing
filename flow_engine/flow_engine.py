import time
import uuid
import random
import logging
from collections import OrderedDict
from typing import Callable, List, Optional, Dict

logger = logging.getLogger(__name__)

class FlowEngine:
    """
    Orchestrates the simulation of a distributed system's event flow, including
    checkpoint progression, random failures, and event logging.
    """
    def __init__(
        self,
        system_name: str,
        checkpoints: List[str],
        failure_reasons: List[str],
        log_checkpoint_fn: Callable[[str, str, str, Optional[str]], None],
        log_failure_fn: Optional[Callable[[str, str], None]] = None
    ):
        """
        Args:
            system_name: Name of the system (e.g., 'inventory', 'payments').
            checkpoints: List of checkpoint names for the flow.
            failure_reasons: List of possible failure reasons.
            log_checkpoint_fn: Function to log a checkpoint event.
            log_failure_fn: Optional function to log a failure event.
        """
        self.system = system_name
        self.checkpoints = checkpoints
        self.failure_reasons = failure_reasons
        self.log_checkpoint = log_checkpoint_fn
        self.log_failure = log_failure_fn
        self.flows: Dict[str, Dict[str, int]] = OrderedDict()

    def start_new_flow(self) -> str:
        """Start a new flow and return its correlation ID."""
        correlation_id = str(uuid.uuid4())
        self.flows[correlation_id] = {
            "checkpoint_index": 0,
            "failed_attempts": 0
        }
        return correlation_id

    def should_fail(self, attempts: int) -> bool:
        """Determine if the current step should fail, based on attempt count and randomness."""
        return (
            (attempts == 0 and random.random() < 0.5) or
            (attempts == 1 and random.random() < 0.3)
        )

    def run_flow(self, correlation_id: str) -> None:
        """Run a single flow to completion for a given correlation_id."""
        self.flows[correlation_id] = {
            "checkpoint_index": 0,
            "failed_attempts": 0
        }

        while correlation_id in self.flows:
            self._step_flow(correlation_id)
            time.sleep(1.5)

    def _step_flow(self, correlation_id: str) -> None:
        """Advance the flow by one checkpoint, logging events and handling failures."""
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

    def run(self, interval_sec: int = 3) -> None:
        """Continuously run flows in loop mode, simulating ongoing system activity."""
        logger.info(f"🚀 Starting {self.system} producer (loop mode)...")
        while True:
            if len(self.flows) < 1:
                cid = self.start_new_flow()
            else:
                cid = next(iter(self.flows))

            self._step_flow(cid)
            time.sleep(interval_sec)
