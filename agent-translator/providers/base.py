from abc import ABC, abstractmethod

class Provider(ABC):
    def __init__(self, config: dict):
        self.config = config
        self.name = config.get("name", "unknown")
        self.model = config.get("model", "")
        self.api_key = config.get("api_key", "")
        self.last_entropy = 0.0  # Average logprob of the last generation
        self.last_input_tokens = 0   # Input (prompt) token count of the last generation
        self.last_output_tokens = 0  # Output (completion) token count of the last generation

    @abstractmethod
    def complete(self, system: str, user: str) -> str:
        """Sends a completion request to the provider and returns the resulting text."""
        pass
