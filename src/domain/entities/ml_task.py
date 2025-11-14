from typing import Any, Dict
from datetime import datetime

class MLTask:
    """История задач/предсказаний."""
    def __init__(self, task_id: str, result: Any, input_data: Dict[str, Any]):
        self._id: str = f"pred_{datetime.utcnow().timestamp()}"
        self._task_id: str = task_id
        self._result: Any = result
        self._input_data: Dict[str, Any] = input_data
        self._timestamp: datetime = datetime.utcnow()

    @property
    def task_id(self) -> str:
        return self._task_id

    @property
    def result(self) -> Any:
        return self._result

    @property
    def timestamp(self) -> datetime:
        return self._timestamp

    @property
    def input_data(self) -> Dict[str, Any]:
        return self._input_data