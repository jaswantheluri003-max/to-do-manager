"""Core business logic: add, complete, update, delete, search, filter."""

from __future__ import annotations

from datetime import datetime
from typing import List, Optional, Dict, Any

from .models import Task, Priority, Status
from .storage import load_tasks_json, save_tasks_json
from .validators import (
    validate_title, validate_description, validate_category,
    validate_priority, validate_due_date, validate_task_id, validate_search_query,
)


class TaskEngine:
    def __init__(self, json_path: Optional[str] = None):
        self.json_path = json_path
        self.tasks: List[Task] = []
        self._load()

    def _load(self) -> None:
        path = self.json_path
        if path is None:
            from .storage import DEFAULT_JSON_PATH
            path = DEFAULT_JSON_PATH
        self.tasks = load_tasks_json(path)

    def _save(self) -> None:
        path = self.json_path
        if path is None:
            from .storage import DEFAULT_JSON_PATH
            path = DEFAULT_JSON_PATH
        save_tasks_json(self.tasks, path)

    def add_task(
        self,
        title: str,
        description: str = "",
        category: str = "General",
        priority: int = 1,
        due_date: Optional[str] = None,
    ) -> Task:
        valid, title = validate_title(title)
        if not valid:
            raise ValueError(title)
        valid, description = validate_description(description)
        if not valid:
            raise ValueError(description)
        valid, category = validate_category(category)
        if not valid:
            raise ValueError(category)
        valid, priority = validate_priority(str(priority))
        if not valid:
            raise ValueError(priority)
        valid, due_date = validate_due_date(due_date or "")
        if not valid:
            raise ValueError(due_date)

        task = Task(
            title=title,
            description=description,
            category=category,
            priority=priority,
            due_date=due_date,
        )
        self.tasks.append(task)
        self._save()
        return task

    def complete_task(self, task_id: str) -> bool:
        task = self.get_task(task_id)
        if not task:
            return False
        task.mark_complete()
        self._save()
        return True

    def uncomplete_task(self, task_id: str) -> bool:
        task = self.get_task(task_id)
        if not task:
            return False
        task.mark_incomplete()
        self._save()
        return True

    def delete_task(self, task_id: str) -> bool:
        task = self.get_task(task_id)
        if not task:
            return False
        self.tasks.remove(task)
        self._save()
        return True

    def update_task(
        self,
        task_id: str,
        title: Optional[str] = None,
        description: Optional[str] = None,
        category: Optional[str] = None,
        priority: Optional[int] = None,
        due_date: Optional[str] = None,
    ) -> Optional[Task]:
        task = self.get_task(task_id)
        if not task:
            return None
        if title is not None:
            valid, title = validate_title(title)
            if not valid:
                raise ValueError(title)
            task.title = title
        if description is not None:
            valid, description = validate_description(description)
            if not valid:
                raise ValueError(description)
            task.description = description
        if category is not None:
            valid, category = validate_category(category)
            if not valid:
                raise ValueError(category)
            task.category = category
        if priority is not None:
            valid, priority = validate_priority(str(priority))
            if not valid:
                raise ValueError(priority)
            task.priority = priority
        if due_date is not None:
            valid, due_date = validate_due_date(due_date or "")
            if not valid:
                raise ValueError(due_date)
            task.due_date = due_date
        self._save()
        return task

    def get_task(self, task_id: str) -> Optional[Task]:
        for task in self.tasks:
            if task.id == task_id:
                return task
        return None

    def get_all_tasks(self) -> List[Task]:
        return sorted(
            self.tasks,
            key=lambda t: (t.completed, -t.priority, t.created_at),
        )

    def get_pending_tasks(self) -> List[Task]:
        return sorted(
            [t for t in self.tasks if not t.completed],
            key=lambda t: (-t.priority, t.due_date or "zzzz"),
        )

    def get_completed_tasks(self) -> List[Task]:
        return sorted(
            [t for t in self.tasks if t.completed],
            key=lambda t: t.completed_at or "",
            reverse=True,
        )

    def filter_overdue(self) -> List[Task]:
        return [t for t in self.tasks if t.is_overdue()]

    def search_tasks(self, query: str, category: Optional[str] = None) -> List[Task]:
        valid, query = validate_search_query(query)
        if not valid:
            return []
        results: List[Task] = []
        for task in self.tasks:
            if query in task.title.lower() or query in task.description.lower():
                if category is None or task.category.lower() == category.lower():
                    results.append(task)
        return results

    def filter_by_category(self, category: str) -> List[Task]:
        return [t for t in self.tasks if t.category.lower() == category.lower()]

    def filter_by_status(self, completed: bool) -> List[Task]:
        return [t for t in self.tasks if t.completed == completed]

    def get_categories(self) -> List[str]:
        return sorted({t.category for t in self.tasks})

    def get_summary(self) -> Dict[str, Any]:
        total = len(self.tasks)
        completed = len([t for t in self.tasks if t.completed])
        pending = total - completed
        overdue = len(self.filter_overdue())

        priority_counts = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
        for task in self.tasks:
            if not task.completed:
                priority_counts[task.priority] += 1

        category_counts: Dict[str, int] = {}
        for task in self.tasks:
            if not task.completed:
                category_counts[task.category] = category_counts.get(task.category, 0) + 1

        completion_rate = (completed / total * 100) if total > 0 else 0.0

        # Average turnaround (hours) for completed tasks with completed_at
        turnaround_hours: List[float] = []
        for task in self.tasks:
            if task.completed and task.completed_at and task.created_at:
                try:
                    start = datetime.fromisoformat(task.created_at)
                    end = datetime.fromisoformat(task.completed_at)
                    turnaround_hours.append((end - start).total_seconds() / 3600.0)
                except ValueError:
                    continue
        avg_turnaround = sum(turnaround_hours) / len(turnaround_hours) if turnaround_hours else 0.0

        return {
            "total": total,
            "completed": completed,
            "pending": pending,
            "overdue": overdue,
            "completion_rate": round(completion_rate, 2),
            "priority_breakdown": priority_counts,
            "category_breakdown": category_counts,
            "avg_turnaround_hours": round(avg_turnaround, 2),
        }
