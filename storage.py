import json
import csv
import os
from typing import List, Optional
from models import Task


DEFAULT_JSON_PATH = os.path.join(os.path.dirname(__file__), "data", "tasks.json")
DEFAULT_CSV_PATH = os.path.join(os.path.dirname(__file__), "data", "tasks.csv")


def ensure_data_dir():
    data_dir = os.path.join(os.path.dirname(__file__), "data")
    os.makedirs(data_dir, exist_ok=True)


def load_tasks_json(filepath: str = DEFAULT_JSON_PATH) -> List[Task]:
    ensure_data_dir()
    if not os.path.exists(filepath):
        return []
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
        return [Task.from_dict(item) for item in data]
    except (json.JSONDecodeError, KeyError, TypeError):
        return []


def save_tasks_json(tasks: List[Task], filepath: str = DEFAULT_JSON_PATH):
    ensure_data_dir()
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump([t.to_dict() for t in tasks], f, indent=2, ensure_ascii=False)


def load_tasks_csv(filepath: str = DEFAULT_CSV_PATH) -> List[Task]:
    ensure_data_dir()
    if not os.path.exists(filepath):
        return []
    tasks = []
    try:
        with open(filepath, "r", encoding="utf-8", newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                row["priority"] = int(row.get("priority", 1))
                row["completed"] = row.get("completed", "False").lower() == "true"
                tasks.append(Task.from_dict(row))
    except (csv.Error, KeyError, ValueError):
        pass
    return tasks


def save_tasks_csv(tasks: List[Task], filepath: str = DEFAULT_CSV_PATH):
    ensure_data_dir()
    fieldnames = ["id", "title", "description", "category", "priority", "completed", "created_at", "completed_at", "due_date"]
    with open(filepath, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for task in tasks:
            writer.writerow(task.to_dict())


def export_tasks_markdown(tasks: List[Task], filepath: str):
    ensure_data_dir()
    with open(filepath, "w", encoding="utf-8") as f:
        f.write("# Task Report\n\n")
        f.write(f"Generated: {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        f.write("## Pending Tasks\n\n")
        pending = [t for t in tasks if not t.completed]
        if pending:
            f.write("| ID | Title | Category | Priority | Due Date |\n")
            f.write("|----|-------|----------|----------|----------|\n")
            for task in pending:
                due = task.due_date or "N/A"
                f.write(f"| {task.id} | {task.title} | {task.category} | {task.priority} | {due} |\n")
        else:
            f.write("No pending tasks.\n")
        
        f.write("\n## Completed Tasks\n\n")
        completed = [t for t in tasks if t.completed]
        if completed:
            f.write("| ID | Title | Category | Completed At |\n")
            f.write("|----|-------|----------|--------------|\n")
            for task in completed:
                f.write(f"| {task.id} | {task.title} | {task.category} | {task.completed_at or 'N/A'} |\n")
        else:
            f.write("No completed tasks.\n")


def export_tasks_text(tasks: List[Task], filepath: str):
    ensure_data_dir()
    with open(filepath, "w", encoding="utf-8") as f:
        f.write("TASK REPORT\n")
        f.write("=" * 50 + "\n\n")
        
        pending = [t for t in tasks if not t.completed]
        f.write(f"Pending Tasks: {len(pending)}\n")
        for task in pending:
            due = f" (Due: {task.due_date})" if task.due_date else ""
            overdue = " [OVERDUE]" if task.is_overdue() else ""
            f.write(f"  [{task.id}] {task.title} [{task.category}] Priority: {task.priority}{due}{overdue}\n")
        
        f.write("\n")
        completed = [t for t in tasks if t.completed]
        f.write(f"Completed Tasks: {len(completed)}\n")
        for task in completed:
            f.write(f"  [{task.id}] {task.title} [{task.category}] Completed: {task.completed_at}\n")