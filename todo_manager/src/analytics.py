"""Executive summary metrics, completion rates, category breakdown, overdue alerts."""

from __future__ import annotations

from typing import List, Dict, Any

from .models import Task
from .engine import TaskEngine


def compute_summary(engine: TaskEngine) -> Dict[str, Any]:
    return engine.get_summary()


def completion_rate(engine: TaskEngine) -> float:
    return engine.get_summary()["completion_rate"]


def category_breakdown(engine: TaskEngine) -> Dict[str, int]:
    return engine.get_summary()["category_breakdown"]


def priority_breakdown(engine: TaskEngine) -> Dict[int, int]:
    return engine.get_summary()["priority_breakdown"]


def overdue_alerts(engine: TaskEngine) -> List[Task]:
    return engine.filter_overdue()


def overdue_risk_level(engine: TaskEngine) -> str:
    """Return 'low', 'moderate', or 'critical' based on overdue share of pending."""
    summary = engine.get_summary()
    pending = summary["pending"]
    if pending == 0:
        return "low"
    overdue = summary["overdue"]
    ratio = overdue / pending
    if ratio > 0.30:
        return "critical"
    if ratio > 0.10:
        return "moderate"
    return "low"


def avg_turnaround_hours(engine: TaskEngine) -> float:
    return engine.get_summary()["avg_turnaround_hours"]


def total_tasks(engine: TaskEngine) -> int:
    return engine.get_summary()["total"]
