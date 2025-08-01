import pytest
from unittest.mock import MagicMock
import consumer

def test_insert_event_success(monkeypatch):
    # Setup
    entry = {
        "system_id": "inventory",
        "checkpoint_id": "CHECKPOINT_1",
        "timestamp": "2025-08-01T12:00:00",
        "status": "SUCCESS",
        "correlation_id": "abc-123",
        "failure_reason": None
    }
    # Patch DB cursor and logger
    monkeypatch.setattr(consumer, "c", MagicMock())
    monkeypatch.setattr(consumer, "conn", MagicMock())
    monkeypatch.setattr(consumer.logger, "info", MagicMock())
    # Should not raise
    consumer.insert_event(entry)
    consumer.c.execute.assert_called_once()
    consumer.conn.commit.assert_called_once()
    consumer.logger.info.assert_called()

def test_insert_event_failure(monkeypatch):
    entry = {"system_id": "inventory"}  # Incomplete
    mock_cursor = MagicMock()
    mock_cursor.execute.side_effect = Exception("fail")
    monkeypatch.setattr(consumer, "c", mock_cursor)
    monkeypatch.setattr(consumer, "conn", MagicMock())
    monkeypatch.setattr(consumer.logger, "error", MagicMock())
    # Should log error
    consumer.insert_event(entry)
    consumer.logger.error.assert_called()

def test_handle_log_buffered_success(monkeypatch):
    # Simulate a buffered system event
    entry = {
        "system_id": "inventory",
        "checkpoint_id": "CHECKPOINT_1",
        "timestamp": "2025-08-01T12:00:00",
        "status": "SUCCESS",
        "correlation_id": "abc-123",
        "failure_reason": None
    }
    monkeypatch.setattr(consumer, "insert_event", MagicMock())
    consumer.buffer.clear()
    consumer.handle_log(entry)
    consumer.insert_event.assert_called_once()

def test_handle_log_nonbuffered_success(monkeypatch):
    entry = {
        "system_id": "orders",
        "checkpoint_id": "CHECKPOINT_1",
        "timestamp": "2025-08-01T12:00:00",
        "status": "SUCCESS",
        "correlation_id": "abc-123",
        "failure_reason": None
    }
    monkeypatch.setattr(consumer, "insert_event", MagicMock())
    consumer.handle_log(entry)
    consumer.insert_event.assert_called_once()

def test_parse_log_structured(monkeypatch):
    log = '{"system": "inventory", "checkpoint": "CHECKPOINT_1", "status": "SUCCESS", "timestamp": "2025-08-01T12:00:00", "correlation_id": "abc-123"}'
    result = consumer.parse_log(log)
    assert result["system_id"] == "inventory"

def test_parse_log_order():
    log = "2025-08-01T12:00:00 ORDER: CHECKPOINT_A - SUCCESS (ID: abc-123)"
    result = consumer.parse_log(log)
    assert result["system_id"] == "orders"

def test_parse_log_payments():
    log = "2025-08-01T12:00:00 PAYMENTS: PAYMENTS_CHECKPOINT_1 - SUCCESS (ID: xyz-789)"
    result = consumer.parse_log(log)
    assert result["system_id"] == "payments"

def test_parse_log_unrecognized():
    log = "2025-08-01T12:00:00 UNKNOWN: ..."
    result = consumer.parse_log(log)
    assert result is None
