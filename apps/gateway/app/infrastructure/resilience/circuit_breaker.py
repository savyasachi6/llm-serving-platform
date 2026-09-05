import time


class CircuitBreakerOpenException(Exception):
    pass


class CircuitBreaker:
    """
    A simple resilience pattern to stop sending requests to a backend
    if it is continuously failing, allowing it time to recover.
    """

    def __init__(self, failure_threshold: int = 5, recovery_timeout_sec: float = 30.0):
        self.failure_threshold = failure_threshold
        self.recovery_timeout_sec = recovery_timeout_sec
        self.failures = 0
        self.last_failure_time = 0.0
        self.is_open = False

    def record_failure(self):
        self.failures += 1
        self.last_failure_time = time.time()
        if self.failures >= self.failure_threshold:
            self.is_open = True

    def record_success(self):
        self.failures = 0
        self.is_open = False

    def check_state(self):
        if self.is_open:
            if time.time() - self.last_failure_time > self.recovery_timeout_sec:
                # Half-open state
                self.is_open = False
                self.failures = self.failure_threshold - 1  # Next failure opens it again
            else:
                raise CircuitBreakerOpenException("Circuit breaker is OPEN. Backend is unhealthy.")
