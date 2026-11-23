"""Atomic JSON persistence, schema validation, auto-recovery, CSV bulk import."""

from __future__ import annotations

import csv
import json
import os
import shutil
import tempfile
from typing import List, Optional, Tuple

from .models import Task


DEFAULT_JSON_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "tasks.json")
DEFAULT_CSV_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "seed_tasks.csv")
EXPECTED_FIELDS = [
    "id", "title", "description", "category", "priority",
    "completed", "created_at", "completed_at", "due_date",
]


def ensure_dir(path: str) -> None:
    directory = os.path.dirname(os.path.abspath(path))
    if directory:
        os.makedirs(directory, exist_ok=True)


def _atomic_write_json(filepath: str, payload: list) -> None:
    ensure_dir(filepath)
    directory = os.path.dirname(os.path.abspath(filepath))
    fd, tmp_path = tempfile.mkstemp(prefix=".tasks_", suffix=".json", dir=directory)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2, ensure_ascii=False)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp_path, filepath)
    except Exception:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
        raise


def load_tasks_json(filepath: str = DEFAULT_JSON_PATH) -> List[Task]:
    if not os.path.exists(filepath):
        return []
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (json.JSONDecodeError, OSError, UnicodeDecodeError):
        return _attempt_recovery(filepath)
    if not isinstance(data, list):
        return []
    tasks: List[Task] = []
    for item in data:
        if not isinstance(item, dict):
            continue
        try:
            tasks.append(Task.from_dict(item))
        except TypeError:
            continue
    return tasks


def _attempt_recovery(filepath: str) -> List[Task]:
    backup = filepath + ".bak"
    if os.path.exists(backup):
        try:
            shutil.copy2(backup, filepath)
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, list):
                return [Task.from_dict(i) for i in data if isinstance(i, dict)]
        except Exception:
            pass
    return []


def save_tasks_json(tasks: List[Task], filepath: str = DEFAULT_JSON_PATH) -> None:
    backup = filepath + ".bak"
    if os.path.exists(filepath):
        shutil.copy2(filepath, backup)
    _atomic_write_json(filepath, [t.to_dict() for t in tasks])


def load_tasks_csv(filepath: str = DEFAULT_CSV_PATH) -> List[Task]:
    if not os.path.exists(filepath):
        return []
    tasks: List[Task] = []
    try:
        with open(filepath, "r", encoding="utf-8", newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                try:
                    row["priority"] = int(row.get("priority", 1) or 1)
                    row["completed"] = str(row.get("completed", "False")).lower() == "true"
                    tasks.append(Task.from_dict(row))
                except (ValueError, KeyError, TypeError):
                    continue
    except (csv.Error, OSError, UnicodeDecodeError):
        pass
    return tasks


def save_tasks_csv(tasks: List[Task], filepath: str = DEFAULT_CSV_PATH) -> None:
    ensure_dir(filepath)
    with open(filepath, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=EXPECTED_FIELDS)
        writer.writeheader()
        for task in tasks:
            writer.writerow(task.to_dict())


def import_csv_bulk(filepath: str) -> Tuple[int, List[dict]]:
    """Bulk import CSV. Returns (imported_count, error_log)."""
    imported = 0
    errors: List[dict] = []
    if not os.path.exists(filepath):
        return 0, [{"row": 0, "error": "File not found."}]
    with open(filepath, "r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for line_no, row in enumerate(reader, start=2):
            row_errors: List[str] = []
            title = (row.get("title") or "").strip()
            if not title:
                row_errors.append("Title is empty.")
            if len(title) > 100:
                row_errors.append("Title exceeds 100 characters.")
            category = (row.get("category") or "General").strip().title()
            if len(category) > 30:
                row_errors.append("Category exceeds 30 characters.")
            try:
                priority = int(row.get("priority", 1) or 1)
                if priority < 1 or priority > 5:
                    row_errors.append("Priority out of range 1-5.")
            except ValueError:
                row_errors.append("Priority is not a valid integer.")
                priority = 1
            due_date = (row.get("due_date") or "").strip() or None
            if due_date:
                try:
                    from datetime import datetime
                    datetime.fromisoformat(due_date[:10])
                except ValueError:
                    row_errors.append("Invalid due_date format (YYYY-MM-DD).")
                    due_date = None
            if row_errors:
                errors.append({"row": line_no, "errors": row_errors, "title": title})
                continue
            task = Task(
                title=title,
                description=(row.get("description") or "").strip(),
                category=category,
                priority=priority,
                due_date=due_date,
                completed=str(row.get("completed", "False")).lower() == "true",
            )
            tasks_existing = load_tasks_json()
            tasks_existing.append(task)
            save_tasks_json(tasks_existing)
            imported += 1
    return imported, errors


def export_tasks_markdown(tasks: List[Task], filepath: str) -> None:
    ensure_dir(filepath)
    from datetime import datetime
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    lines: List[str] = ["# Task Report", "", f"Generated: {now}", ""]
    pending = [t for t in tasks if not t.completed]
    completed = [t for t in tasks if t.completed]
    lines.append("## Pending Tasks")
    lines.append("")
    if pending:
        lines.append("| ID | Title | Category | Priority | Due Date |")
        lines.append("|----|-------|----------|----------|----------|")
        for t in pending:
            lines.append(f"| {t.id} | {t.title} | {t.category} | {t.priority} | {t.due_date or 'N/A'} |")
    else:
        lines.append("No pending tasks.")
    lines.append("")
    lines.append("## Completed Tasks")
    lines.append("")
    if completed:
        lines.append("| ID | Title | Category | Completed At |")
        lines.append("|----|-------|----------|--------------|")
        for t in completed:
            lines.append(f"| {t.id} | {t.title} | {t.category} | {t.completed_at or 'N/A'} |")
    else:
        lines.append("No completed tasks.")
    with open(filepath, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")


def export_tasks_text(tasks: List[Task], filepath: str) -> None:
    ensure_dir(filepath)
    from datetime import datetime
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    lines: List[str] = ["TASK REPORT", "=" * 50, "", f"Generated: {now}", ""]
    pending = [t for t in tasks if not t.completed]
    completed = [t for t in tasks if t.completed]
    lines.append(f"Pending Tasks: {len(pending)}")
    for t in pending:
        due = f" (Due: {t.due_date})" if t.due_date else ""
        overdue = " [OVERDUE]" if t.is_overdue() else ""
        lines.append(f"  [{t.id}] {t.title} [{t.category}] Priority: {t.priority}{due}{overdue}")
    lines.append("")
    lines.append(f"Completed Tasks: {len(completed)}")
    for t in completed:
        lines.append(f"  [{t.id}] {t.title} [{t.category}] Completed: {t.completed_at}")
    with open(filepath, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
