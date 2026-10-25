from abc import ABC, abstractmethod

from app.domain.entities import Intent


class IntentClassifier(ABC):
    """Outbound port: text to intent with calibrated confidence and extracted entities."""

    @abstractmethod
    def classify(self, text: str) -> Intent:
        """Raises ClassificationError when the model is unavailable."""
