import pytest
from log_parsers.structured import parse_structured
from log_parsers.orders import parse_order
from log_parsers.payments import parse_payments

# --- Structured Parser Tests ---
def test_parse_structured_full():
    log = {
        "system": "inventory",
        "checkpoint": "CHECKPOINT_1",
        "status": "SUCCESS",
        "timestamp": "2025-08-01T12:00:00",
        "correlation_id": "abc-123"
    }
    result = parse_structured(log)
    assert result["system_id"] == "inventory"
    assert result["checkpoint_id"] == "CHECKPOINT_1"
    assert result["status"] == "SUCCESS"
    assert result["correlation_id"] == "abc-123"
    assert result["failure_reason"] is None

def test_parse_structured_error():
    log = {
        "system": "inventory",
        "correlation_id": "abc-123",
        "failure_reason": "FAILURE_REASON_1"
    }
    result = parse_structured(log)
    assert result["system_id"] == "inventory"
    assert result["correlation_id"] == "abc-123"
    assert result["failure_reason"] == "FAILURE_REASON_1"

# --- Orders Parser Tests ---
def test_parse_order_success():
    line = "2025-08-01T12:00:00 ORDER: CHECKPOINT_A - SUCCESS (ID: abc-123)"
    result = parse_order(line)
    assert result["system_id"] == "orders"
    assert result["checkpoint_id"] == "CHECKPOINT_A"
    assert result["status"] == "SUCCESS"
    assert result["correlation_id"] == "abc-123"
    assert result["failure_reason"] is None

def test_parse_order_failure():
    line = "2025-08-01T12:00:00 ORDER: CHECKPOINT_B - FAILURE (ID: def-456) - FAILURE_REASON_X"
    result = parse_order(line)
    assert result["system_id"] == "orders"
    assert result["checkpoint_id"] == "CHECKPOINT_B"
    assert result["status"] == "FAILURE"
    assert result["correlation_id"] == "def-456"
    assert result["failure_reason"] == "FAILURE_REASON_X"

# --- Payments Parser Tests ---
def test_parse_payments_success():
    line = "2025-08-01T12:00:00 PAYMENTS: PAYMENTS_CHECKPOINT_1 - SUCCESS (ID: xyz-789)"
    result = parse_payments(line)
    assert result["system_id"] == "payments"
    assert result["checkpoint_id"] == "PAYMENTS_CHECKPOINT_1"
    assert result["status"] == "SUCCESS"
    assert result["correlation_id"] == "xyz-789"
    assert result["failure_reason"] is None

def test_parse_payments_failure():
    line = "2025-08-01T12:00:00 PAYMENTS: PAYMENTS_CHECKPOINT_2 - FAILURE (ID: xyz-789)"
    result = parse_payments(line)
    assert result["system_id"] == "payments"
    assert result["checkpoint_id"] == "PAYMENTS_CHECKPOINT_2"
    assert result["status"] == "FAILURE"
    assert result["correlation_id"] == "xyz-789"
    assert result["failure_reason"] is None

def test_parse_payments_error_log():
    line = "2025-08-01T12:00:01 PAYMENTS PAYMENTS_ERROR: (ID: xyz-789) - PAYMENTS_FAILURE_REASON_1"
    result = parse_payments(line)
    assert result["system_id"] == "payments"
    assert result["correlation_id"] == "xyz-789"
    assert result["failure_reason"] == "PAYMENTS_FAILURE_REASON_1"
    assert "timestamp" in result
