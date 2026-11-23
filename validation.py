import re
from datetime import datetime
from typing import Optional, Tuple


def validate_title(title: str) -> Tuple[bool, str]:
    title = title.strip()
    if not title:
        return False, "Title cannot be empty."
    if len(title) > 100:
        return False, "Title must be 100 characters or less."
    return True, title


def validate_description(desc: str) -> Tuple[bool, str]:
    desc = desc.strip()
    if len(desc) > 500:
        return False, "Description must be 500 characters or less."
    return True, desc


def validate_category(category: str) -> Tuple[bool, str]:
    category = category.strip().title()
    if not category:
        return False, "Category cannot be empty."
    if len(category) > 30:
        return False, "Category must be 30 characters or less."
    return True, category


def validate_priority(priority_str: str) -> Tuple[bool, int]:
    try:
        priority = int(priority_str)
        if priority < 1 or priority > 5:
            return False, "Priority must be between 1 and 5."
        return True, priority
    except ValueError:
        return False, "Priority must be a number between 1 and 5."


def validate_due_date(date_str: str) -> Tuple[bool, Optional[str]]:
    date_str = date_str.strip()
    if not date_str:
        return True, None
    try:
        datetime.fromisoformat(date_str)
        return True, date_str
    except ValueError:
        return False, "Invalid date format. Use YYYY-MM-DD."


def validate_task_id(task_id: str, existing_ids: set) -> Tuple[bool, str]:
    task_id = task_id.strip()
    if not task_id:
        return False, "Task ID cannot be empty."
    if task_id not in existing_ids:
        return False, f"Task ID '{task_id}' not found."
    return True, task_id


def validate_search_query(query: str) -> Tuple[bool, str]:
    query = query.strip()
    if not query:
        return False, "Search query cannot be empty."
    return True, query.lower()


def get_valid_input(prompt: str, validator, error_msg: str = "Invalid input. Please try again.") -> any:
    while True:
        try:
            user_input = input(prompt).strip()
            valid, result = validator(user_input)
            if valid:
                return result
            print(f"  Error: {result}")
        except (KeyboardInterrupt, EOFError):
            print("\n  Operation cancelled.")
            return None
        except Exception as e:
            print(f"  Error: {error_msg}")


def confirm_action(prompt: str) -> bool:
    while True:
        try:
            response = input(f"{prompt} (y/n): ").strip().lower()
            if response in ('y', 'yes'):
                return True
            if response in ('n', 'no'):
                return False
            print("  Please enter 'y' or 'n'.")
        except (KeyboardInterrupt, EOFError):
            return False