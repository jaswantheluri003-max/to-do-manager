from dataclasses import dataclass, asdict, field
from datetime import datetime
from typing import Optional
import uuid


@dataclass
class Task:
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    title: str = ""
    description: str = ""
    category: str = "General"
    priority: int = 1
    completed: bool = False
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    completed_at: Optional[str] = None
    due_date: Optional[str] = None

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> 'Task':
        return cls(**data)

    def mark_complete(self):
        self.completed = True
        self.completed_at = datetime.now().isoformat()

    def mark_incomplete(self):
        self.completed = False
        self.completed_at = None

    def is_overdue(self) -> bool:
        if self.completed or not self.due_date:
            return False
        try:
            due = datetime.fromisoformat(self.due_date)
            return datetime.now() > due
        except ValueError:
            return False

    def days_until_due(self) -> Optional[int]:
        if not self.due_date:
            return None
        try:
            due = datetime.fromisoformat(self.due_date)
            delta = due - datetime.now()
            return delta.days
        except ValueError:
            return None