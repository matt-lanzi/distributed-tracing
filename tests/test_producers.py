import pytest
from producers.producer_inventory import log_checkpoint, log_failure
from producers.producer_payments import log_checkpoint as log_checkpoint_payments, log_failure as log_failure_payments
from unittest.mock import patch

def test_log_checkpoint_inventory_success():
    with patch('producers.producer_inventory.producer.send') as mock_send, \
         patch('producers.producer_inventory.logger.info') as mock_info:
        log_checkpoint('abc-123', 'CHECKPOINT_1', 'SUCCESS')
        mock_send.assert_called_once()
        mock_info.assert_called()

def test_log_checkpoint_inventory_failure():
    with patch('producers.producer_inventory.producer.send') as mock_send, \
         patch('producers.producer_inventory.logger.info') as mock_info:
        log_checkpoint('abc-123', 'CHECKPOINT_1', 'FAILURE', 'FAILURE_REASON_1')
        mock_send.assert_called_once()
        mock_info.assert_called()

def test_log_failure_inventory():
    with patch('producers.producer_inventory.producer.send') as mock_send, \
         patch('producers.producer_inventory.logger.info') as mock_info:
        log_failure('abc-123', 'FAILURE_REASON_1')
        mock_send.assert_called_once()
        mock_info.assert_called()

def test_log_checkpoint_payments_success():
    with patch('producers.producer_payments.producer.send') as mock_send, \
         patch('producers.producer_payments.logger.info') as mock_info:
        log_checkpoint_payments('xyz-789', 'PAYMENTS_CHECKPOINT_1', 'SUCCESS')
        mock_send.assert_called_once()
        mock_info.assert_called()

def test_log_checkpoint_payments_failure():
    with patch('producers.producer_payments.producer.send') as mock_send, \
         patch('producers.producer_payments.logger.info') as mock_info:
        log_checkpoint_payments('xyz-789', 'PAYMENTS_CHECKPOINT_2', 'FAILURE', 'PAYMENTS_FAILURE_REASON_1')
        mock_send.assert_called_once()
        mock_info.assert_called()

def test_log_failure_payments():
    with patch('producers.producer_payments.producer.send') as mock_send, \
         patch('producers.producer_payments.logger.info') as mock_info:
        log_failure_payments('xyz-789', 'PAYMENTS_FAILURE_REASON_1')
        mock_send.assert_called_once()
        mock_info.assert_called()
