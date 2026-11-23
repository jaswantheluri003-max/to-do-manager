#!/usr/bin/env python3
"""Generate 40 realistic sample tasks (JSON + CSV) with edge cases for testing."""

import csv
import os
import sys
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.models import Task
from src.storage import save_tasks_json, save_tasks_csv, DEFAULT_JSON_PATH, DEFAULT_CSV_PATH


SAMPLES = [
    ("Complete project proposal", "Write and submit Q4 project proposal", "Work", 5, "2026-11-20", False),
    ("Team meeting", "Weekly sync with development team", "Work", 3, "2026-11-18", False),
    ("Code review", "Review PR #234 for authentication module", "Work", 4, "2026-11-17", False),
    ("Buy groceries", "Milk, eggs, bread, vegetables", "Personal", 2, "2026-11-16", False),
    ("Gym session", "Cardio and strength training", "Health", 3, "2026-11-16", False),
    ("Read book", "Finish chapter 5 of Clean Code", "Learning", 2, "2026-11-25", False),
    ("Call dentist", "Schedule annual checkup", "Health", 1, "2026-11-30", False),
    ("Pay bills", "Electricity, internet, phone", "Personal", 4, "2026-11-15", True),
    ("Plan vacation", "Research destinations for December", "Personal", 1, "2026-12-01", False),
    ("Learn Python", "Complete async/await tutorial", "Learning", 3, "2026-11-22", False),
    ("Submit expense report", "Q3 travel reimbursement filing", "Work", 5, "2026-11-19", False),
    ("Update resume", "Add latest project experience", "Personal", 3, "2026-11-25", False),
    ("Doctor appointment", "Annual physical examination", "Health", 2, "2026-11-28", False),
    ("Fix login bug", "Resolve token refresh issue on mobile", "Work", 5, "2026-11-18", True),
    ("Water the plants", "Office and home potted plants", "Personal", 1, None, False),
    ("Prepare presentation", "Q4 all-hands deck slides", "Work", 4, "2026-11-23", False),
    ("Backup database", "Weekly production snapshot verification", "Work", 5, "2026-11-21", False),
    ("Call mom", "Birthday wish and catch-up", "Personal", 2, "2026-11-20", False),
    ("Read whitepaper", "Zero trust architecture overview", "Learning", 3, "2026-11-29", False),
    ("Schedule HVAC service", "Fall maintenance check", "Personal", 2, "2026-11-25", False),
    ("Submit timesheet", "Weekly hours entry", "Work", 4, "2026-11-18", False),
    ("Buy birthday gift", "Sister's 30th celebration", "Personal", 3, "2026-11-25", False),
    ("Dentist follow up", "Post-cleaning checkup", "Health", 2, "2026-12-05", False),
    ("Refactor auth module", "Extract shared middleware", "Work", 5, "2026-11-24", False),
    ("Laundry", "Wash and fold weekly load", "Personal", 1, None, False),
    ("Deposit checks", "Scan and upload via mobile app", "Personal", 2, "2026-11-22", False),
    ("Attend webinar", "Cloud security best practices", "Learning", 2, "2026-11-26", False),
    ("Renew car registration", "DMV annual renewal", "Personal", 4, "2026-11-20", False),
    ("Write blog post", "Lessons learned from migration", "Learning", 3, "2026-12-02", False),
    ("Buy cat food", "Restock premium kibble", "Personal", 1, None, False),
    ("Replace smoke detector batteries", "Home safety check", "Personal", 4, "2026-11-25", False),
    ("Deploy hotfix", "Critical production patch v1.2.1", "Work", 5, "2026-11-19", False),
    ("Review vendor contracts", "Annual SLA renegotiation", "Work", 3, "2026-12-01", False),
    ("Call plumber", "Kitchen sink leak repair", "Personal", 5, "2026-11-19", False),
    ("Schedule eye exam", "Annual vision check", "Health", 2, "2026-12-10", False),
    ("Prepare interview questions", "Senior engineer candidate screen", "Work", 4, "2026-11-23", False),
    ("Buy heating oil", "Winter tank refill", "Personal", 4, "2026-11-25", False),
    ("Update will", "Estate planning review", "Personal", 2, "2026-12-15", False),
    ("Malformed priority task", "Task with out-of-range priority", "Work", 9, "2026-11-20", False),
    ("Missing due date", "Task without a due date", "Personal", 2, None, False),
    ("Empty title edge", "", "General", 1, None, False),
]


def build_tasks() -> list[Task]:
    tasks: list[Task] = []
    base = datetime(2026, 11, 15, 9, 0, 0)
    for idx, (title, desc, cat, prio, due, completed) in enumerate(SAMPLES):
        if not title:
            continue
        task = Task(
            id=f"seed{idx:03d}",
            title=title,
            description=desc,
            category=cat,
            priority=min(max(prio, 1), 5),
            completed=completed,
            created_at=(base + timedelta(minutes=idx * 5)).isoformat(),
            due_date=due,
        )
        if completed:
            task.mark_complete()
        tasks.append(task)
    return tasks


def main() -> None:
    tasks = build_tasks()
    save_tasks_json(tasks, DEFAULT_JSON_PATH)
    save_tasks_csv(tasks, DEFAULT_CSV_PATH)
    print(f"Wrote {len(tasks)} tasks to {DEFAULT_JSON_PATH} and {DEFAULT_CSV_PATH}")


if __name__ == "__main__":
    main()
