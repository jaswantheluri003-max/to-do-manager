"""Dataclasses, Enums, and serialization helpers for tasks."""

from __future__ import annotations

from dataclasses import dataclass, asdict, field
from datetime import datetime
from enum import IntEnum, Enum
from typing import Optional
import uuid


class Priority(IntEnum):
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4
    URGENT = 5

    @classmethod
    def labels(cls) -> dict[int, str]:
        return {
            1: "Low",
            2: "Medium",
            3: "High",
            4: "Critical",
            5: "Urgent",
        }


class Status(Enum):
    PENDING = "pending"
    COMPLETED = "completed"

    @classmethod
    def from_bool(cls, completed: bool) -> "Status":
        return cls.COMPLETED if completed else cls.PENDING


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
    def from_dict(cls, data: dict) -> "Task":
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})

    def mark_complete(self) -> None:
        self.completed = True
        self.completed_at = datetime.now().isoformat()

    def mark_incomplete(self) -> None:
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

    def priority_label(self) -> str:
        return Priority.labels().get(self.priority, str(self.priority))

    def status(self) -> Status:
        return Status.from_bool(self.completed)
