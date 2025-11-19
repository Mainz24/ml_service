from abc import ABC, abstractmethod
from src.app.domain.entities.transaction import Transaction


class MLModelService(ABC):
    @abstractmethod
    def predict_fraud_score(self, transaction: Transaction) -> float:
        pass

    @abstractmethod
    def get_model_version(self) -> str:
        pass