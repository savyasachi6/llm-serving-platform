import time

import pytest
from app.infrastructure.resilience.circuit_breaker import (
    CircuitBreaker,
    CircuitBreakerOpenException,
)


def test_circuit_breaker_initially_closed():
    cb = CircuitBreaker(failure_threshold=3, recovery_timeout_sec=10.0)
    assert not cb.is_open
    assert cb.failures == 0
    # check_state should not raise when closed
    cb.check_state()


def test_circuit_breaker_trips_after_threshold():
    cb = CircuitBreaker(failure_threshold=2, recovery_timeout_sec=10.0)
    cb.record_failure()
    assert not cb.is_open
    assert cb.failures == 1

    cb.record_failure()
    assert cb.is_open
    assert cb.failures == 2

    with pytest.raises(CircuitBreakerOpenException, match="Circuit breaker is OPEN"):
        cb.check_state()


def test_circuit_breaker_success_resets_failures():
    cb = CircuitBreaker(failure_threshold=3, recovery_timeout_sec=10.0)
    cb.record_failure()
    cb.record_failure()
    assert cb.failures == 2

    cb.record_success()
    assert cb.failures == 0
    assert not cb.is_open


def test_circuit_breaker_recovers_after_timeout():
    cb = CircuitBreaker(failure_threshold=1, recovery_timeout_sec=0.05)
    cb.record_failure()
    assert cb.is_open

    # Wait for recovery timeout to elapse
    time.sleep(0.06)

    # In half-open state, check_state resets is_open to False
    cb.check_state()
    assert not cb.is_open
    assert cb.failures == 0  # failure_threshold - 1 = 0

    # A subsequent success fully clears failures
    cb.record_success()
    assert cb.failures == 0
