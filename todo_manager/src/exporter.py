"""Multi-format exports: Markdown report, CSV, and plain-text audit log."""

from __future__ import annotations

import csv
import os
from datetime import datetime
from typing import List

from .models import Task
from .storage import ensure_dir


def export_markdown(tasks: List[Task], filepath: str) -> None:
    ensure_dir(filepath)
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


def export_csv(tasks: List[Task], filepath: str) -> None:
    ensure_dir(filepath)
    fieldnames = [
        "id", "title", "description", "category", "priority",
        "completed", "created_at", "completed_at", "due_date",
    ]
    with open(filepath, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for task in tasks:
            writer.writerow(task.to_dict())


def export_audit_log(tasks: List[Task], filepath: str) -> None:
    ensure_dir(filepath)
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    lines: List[str] = ["TASK AUDIT LOG", "=" * 50, "", f"Generated: {now}", ""]
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
