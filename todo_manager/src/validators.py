"""Centralized defensive input wrappers: regex, date, range, menu bounds."""

from __future__ import annotations

import re
from datetime import datetime
from typing import Optional, Tuple


TITLE_MIN = 1
TITLE_MAX = 100
DESCRIPTION_MAX = 500
CATEGORY_MAX = 30
PRIORITY_MIN = 1
PRIORITY_MAX = 5


def validate_title(title: str) -> Tuple[bool, str]:
    title = (title or "").strip()
    if not title:
        return False, "Title cannot be empty."
    if len(title) > TITLE_MAX:
        return False, f"Title must be {TITLE_MAX} characters or less."
    return True, title


def validate_description(desc: str) -> Tuple[bool, str]:
    desc = (desc or "").strip()
    if len(desc) > DESCRIPTION_MAX:
        return False, f"Description must be {DESCRIPTION_MAX} characters or less."
    return True, desc


def validate_category(category: str) -> Tuple[bool, str]:
    category = (category or "").strip().title()
    if not category:
        return False, "Category cannot be empty."
    if len(category) > CATEGORY_MAX:
        return False, f"Category must be {CATEGORY_MAX} characters or less."
    return True, category


def validate_priority(priority_str: str) -> Tuple[bool, int]:
    try:
        priority = int(str(priority_str).strip())
    except (ValueError, TypeError):
        return False, f"Priority must be a number between {PRIORITY_MIN} and {PRIORITY_MAX}."
    if priority < PRIORITY_MIN or priority > PRIORITY_MAX:
        return False, f"Priority must be between {PRIORITY_MIN} and {PRIORITY_MAX}."
    return True, priority


def validate_due_date(date_str: str) -> Tuple[bool, Optional[str]]:
    date_str = (date_str or "").strip()
    if not date_str:
        return True, None
    try:
        datetime.fromisoformat(date_str)
        return True, date_str[:10]
    except ValueError:
        return False, "Invalid date format. Use YYYY-MM-DD."


def validate_task_id(task_id: str, existing_ids: set[str]) -> Tuple[bool, str]:
    task_id = (task_id or "").strip()
    if not task_id:
        return False, "Task ID cannot be empty."
    if task_id not in existing_ids:
        return False, f"Task ID '{task_id}' not found."
    return True, task_id


def validate_search_query(query: str) -> Tuple[bool, str]:
    query = (query or "").strip()
    if not query:
        return False, "Search query cannot be empty."
    return True, query.lower()


def validate_menu_bounds(choice: str, min_val: int, max_val: int) -> Tuple[bool, int]:
    try:
        val = int(choice.strip())
    except (ValueError, TypeError):
        return False, 0
    if val < min_val or val > max_val:
        return False, 0
    return True, val


def is_valid_date(value: str) -> bool:
    if not value:
        return False
    try:
        datetime.fromisoformat(value[:10])
        return True
    except ValueError:
        return False
