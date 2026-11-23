from typing import List, Optional, Dict, Any
from datetime import datetime
from models import Task
from storage import load_tasks_json, save_tasks_json, load_tasks_csv, save_tasks_csv
from validation import validate_title, validate_description, validate_category, validate_priority, validate_due_date, validate_task_id, validate_search_query


class TaskManager:
    def __init__(self, json_path: str = None, csv_path: str = None):
        self.json_path = json_path
        self.csv_path = csv_path
        self.tasks: List[Task] = []
        self.load()

    def load(self):
        if self.json_path:
            self.tasks = load_tasks_json(self.json_path)
        elif self.csv_path:
            self.tasks = load_tasks_csv(self.csv_path)
        else:
            from storage import DEFAULT_JSON_PATH
            self.tasks = load_tasks_json(DEFAULT_JSON_PATH)

    def save(self):
        if self.json_path:
            save_tasks_json(self.tasks, self.json_path)
        elif self.csv_path:
            save_tasks_csv(self.tasks, self.csv_path)
        else:
            from storage import DEFAULT_JSON_PATH
            save_tasks_json(self.tasks, DEFAULT_JSON_PATH)

    def add_task(self, title: str, description: str = "", category: str = "General", 
                 priority: int = 1, due_date: str = None) -> Task:
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
            due_date=due_date
        )
        self.tasks.append(task)
        self.save()
        return task

    def complete_task(self, task_id: str) -> bool:
        task = self.get_task(task_id)
        if task:
            task.mark_complete()
            self.save()
            return True
        return False

    def uncomplete_task(self, task_id: str) -> bool:
        task = self.get_task(task_id)
        if task:
            task.mark_incomplete()
            self.save()
            return True
        return False

    def delete_task(self, task_id: str) -> bool:
        task = self.get_task(task_id)
        if task:
            self.tasks.remove(task)
            self.save()
            return True
        return False

    def get_task(self, task_id: str) -> Optional[Task]:
        for task in self.tasks:
            if task.id == task_id:
                return task
        return None

    def search_tasks(self, query: str, category: str = None) -> List[Task]:
        valid, query = validate_search_query(query)
        if not valid:
            return []
        
        results = []
        for task in self.tasks:
            if query in task.title.lower() or query in task.description.lower():
                if category is None or task.category.lower() == category.lower():
                    results.append(task)
        return results

    def filter_by_category(self, category: str) -> List[Task]:
        return [t for t in self.tasks if t.category.lower() == category.lower()]

    def filter_by_status(self, completed: bool) -> List[Task]:
        return [t for t in self.tasks if t.completed == completed]

    def filter_overdue(self) -> List[Task]:
        return [t for t in self.tasks if t.is_overdue()]

    def get_categories(self) -> List[str]:
        categories = set()
        for task in self.tasks:
            categories.add(task.category)
        return sorted(categories)

    def get_summary(self) -> Dict[str, Any]:
        total = len(self.tasks)
        completed = len([t for t in self.tasks if t.completed])
        pending = total - completed
        overdue = len(self.filter_overdue())
        
        priority_counts = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
        for task in self.tasks:
            if not task.completed:
                priority_counts[task.priority] += 1
        
        category_counts = {}
        for task in self.tasks:
            if not task.completed:
                category_counts[task.category] = category_counts.get(task.category, 0) + 1
        
        return {
            "total": total,
            "completed": completed,
            "pending": pending,
            "overdue": overdue,
            "completion_rate": (completed / total * 100) if total > 0 else 0,
            "priority_breakdown": priority_counts,
            "category_breakdown": category_counts,
        }

    def get_all_tasks(self) -> List[Task]:
        return sorted(self.tasks, key=lambda t: (t.completed, -t.priority, t.created_at))

    def get_pending_tasks(self) -> List[Task]:
        return sorted([t for t in self.tasks if not t.completed], 
                      key=lambda t: (-t.priority, t.due_date or "zzzz"))

    def get_completed_tasks(self) -> List[Task]:
        return sorted([t for t in self.tasks if t.completed], 
                      key=lambda t: t.completed_at or "", reverse=True)