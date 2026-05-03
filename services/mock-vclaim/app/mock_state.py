"""
Pramana AI — Mock VClaim Simulation State.

Holds the dynamic configuration for error and delay simulation.
"""

class MockState:
    def __init__(self):
        self.reset()

    def reset(self):
        self.error_rate = 0.0
        self.response_delay_ms = 0
        self.force_error_on_noka = []
        self.simulate_timeout = False

    def get_status(self):
        return {
            "error_rate": self.error_rate,
            "response_delay_ms": self.response_delay_ms,
            "force_error_on_noka": self.force_error_on_noka,
            "simulate_timeout": self.simulate_timeout
        }

    def update(self, config: dict):
        if "error_rate" in config:
            self.error_rate = float(config["error_rate"])
        if "response_delay_ms" in config:
            self.response_delay_ms = int(config["response_delay_ms"])
        if "force_error_on_noka" in config:
            self.force_error_on_noka = list(config["force_error_on_noka"])
        if "simulate_timeout" in config:
            self.simulate_timeout = bool(config["simulate_timeout"])


state = MockState()
