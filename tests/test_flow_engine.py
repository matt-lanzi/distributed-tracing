import pytest
from flow_engine.flow_engine import FlowEngine

CHECKPOINTS = ["STEP_1", "STEP_2", "FINALIZED"]
FAILURE_REASONS = ["ERROR_1", "ERROR_2"]

def build_engine_with_hooks(logs, failures, should_fail_fn=None):
    def log_checkpoint(corr_id, checkpoint, status, failure_reason=None):
        logs.append((checkpoint, status, failure_reason))

    def log_failure(corr_id, reason):
        failures.append((corr_id, reason))

    engine = FlowEngine(
        system_name="test_sys",
        checkpoints=CHECKPOINTS,
        failure_reasons=FAILURE_REASONS,
        log_checkpoint_fn=log_checkpoint,
        log_failure_fn=log_failure
    )

    if should_fail_fn:
        engine.should_fail = should_fail_fn

    return engine


def test_successful_flow(monkeypatch):
    logs = []
    failures = []

    engine = build_engine_with_hooks(logs, failures)
    monkeypatch.setattr(engine, "should_fail", lambda cid: False)

    engine.run_flow("corr-1")

    assert logs == [
        ("STEP_1", "SUCCESS", None),
        ("STEP_2", "SUCCESS", None),
        ("FINALIZED", "SUCCESS", None),
    ]
    assert failures == []


def test_fails_then_recovers():
    logs = []
    failures = []

    state = {"attempt": 0}

    def should_fail(correlation_id):
        state["attempt"] += 1
        return state["attempt"] == 1  # Fail only on first step

    engine = build_engine_with_hooks(logs, failures, should_fail)

    engine.run_flow("corr-2")

    # Should retry STEP_1
    assert any(l[1] == "FAILURE" for l in logs)
    assert ("STEP_1", "SUCCESS", None) in logs
    assert logs[-1][0] == "FINALIZED"
    assert len(failures) >= 1


def test_flow_completes_and_cleans_up():
    logs = []
    engine = build_engine_with_hooks(logs, failures=[])

    engine.should_fail = lambda cid: False

    engine.run_flow("corr-3")

    # Ensure FINALIZED is reached
    assert logs[-1][0] == "FINALIZED"


def test_failure_reason_logged():
    logs = []
    failures = []

    def should_fail_always(correlation_id):
        return True if len(logs) < 2 else False  # Fail once, then recover

    engine = build_engine_with_hooks(logs, failures, should_fail_always)
    engine.run_flow("corr-4")

    # Should log at least one failure reason
    assert any(f for _, f in failures)
    assert any(l[1] == "FAILURE" and l[2] is not None for l in logs)
