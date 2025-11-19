from dataclasses import dataclass
from typing import Any, Dict
from datetime import datetime
from enum import StrEnum


class TaskStatus(StrEnum):
    PENDING = "pending"
    QUEUED = "queued"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELLED = "cancelled"
    RETRYING = "retrying"
    TIMEOUT = "timeout"

@dataclass
class MLTask:
    task_id: str
    result: Any
    input_data: Dict[str, Any]
    status_type: TaskStatus
    timestamp: datetime = None
    id: str = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()
            return self.timestamp
        if self.id is None:
            self.id = f"pred_{self.timestamp.timestamp()}"
        return None

    @property
    def task_id(self) -> str:
        return self.task_id

    @property
    def result(self) -> Any:
        return self.result

    @property
    def input_data(self) -> Dict[str, Any]:
        return self.input_data