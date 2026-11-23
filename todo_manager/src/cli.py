"""ANSI-formatted terminal UI, fixed-width paginated tables, menu dispatch loop."""

from __future__ import annotations

import os
import sys
from typing import List, Optional

from .models import Task, Priority, Status
from .engine import TaskEngine
from .validators import (
    validate_title, validate_description, validate_category,
    validate_priority, validate_due_date, validate_task_id, validate_search_query,
    validate_menu_bounds,
)
from .exporter import export_markdown, export_csv, export_audit_log


class Colors:
    HEADER = "\033[95m"
    BLUE = "\033[94m"
    CYAN = "\033[96m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    GOLD = "\033[38;5;220m"
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"
    END = "\033[0m"
    DIM = "\033[2m"
    REVERSE = "\033[7m"


def supports_color() -> bool:
    return sys.stdout.isatty() and os.environ.get("TERM") not in (None, "dumb")


def c(text: str, code: str) -> str:
    return f"{code}{text}{Colors.END}" if supports_color() else text


def clear_screen() -> None:
    os.system("cls" if os.name == "nt" else "clear")


def print_header(title: str) -> None:
    width = 60
    print(f"\n{c('=' * width, Colors.CYAN)}{Colors.BOLD}")
    print(c(title.center(width), Colors.CYAN) + Colors.BOLD)
    print(c("=" * width, Colors.CYAN) + Colors.END + "\n")


def print_menu() -> None:
    print(f"{c('MAIN MENU', Colors.BOLD)}")
    items = [
        ("1", "Add Task", Colors.GREEN),
        ("2", "List Tasks", Colors.GREEN),
        ("3", "Complete Task", Colors.GREEN),
        ("4", "Uncomplete Task", Colors.GREEN),
        ("5", "Delete Task", Colors.GREEN),
        ("6", "Search Tasks", Colors.GREEN),
        ("7", "View Summary", Colors.GREEN),
        ("8", "Export Report", Colors.GREEN),
        ("9", "Settings", Colors.GREEN),
        ("0", "Exit", Colors.RED),
    ]
    for num, label, color in items:
        print(f"  {c(num, Colors.BOLD + color)}.{Colors.END} {label}")
    print()


def _priority_color(priority: int) -> str:
    return {
        1: Colors.BLUE,
        2: Colors.CYAN,
        3: Colors.YELLOW,
        4: Colors.RED,
        5: Colors.RED + Colors.BOLD,
    }.get(priority, Colors.END)


def print_task_list(tasks: List[Task], title: str = "Tasks") -> None:
    if not tasks:
        print(f"  {c('No tasks found.', Colors.YELLOW)}")
        return
    print(f"\n{c(title, Colors.BOLD)} ({len(tasks)})")
    print(f"  {'ID':<10} {'Status':<10} {'Priority':<10} {'Category':<15} {'Title'}")
    print(f"  {'-' * 80}")
    for task in tasks:
        status = c("Done", Colors.GREEN) if task.completed else c("Pending", Colors.YELLOW)
        pcolor = _priority_color(task.priority)
        priority_str = c(str(task.priority), pcolor)
        due_str = ""
        if task.due_date and not task.completed:
            if task.is_overdue():
                due_str = f" {c(f'[OVERDUE: {task.due_date}]', Colors.RED)}"
            else:
                days = task.days_until_due()
                if days is not None and days <= 3:
                    due_str = f" {c(f'[Due: {task.due_date}]', Colors.YELLOW)}"
                else:
                    due_str = f" {c(f'[Due: {task.due_date}]', Colors.DIM)}"
        title_display = task.title[:45] + "..." if len(task.title) > 45 else task.title
        print(f"  {task.id:<10} {status:<10} {priority_str:<10} {task.category:<15} {title_display}{due_str}")


def print_task_detail(task: Task) -> None:
    print(f"\n{c('Task Details', Colors.BOLD)}")
    print(f"  {c('ID:', Colors.CYAN)} {task.id}")
    print(f"  {c('Title:', Colors.CYAN)} {task.title}")
    print(f"  {c('Description:', Colors.CYAN)} {task.description or '(none)'}")
    print(f"  {c('Category:', Colors.CYAN)} {task.category}")
    print(f"  {c('Priority:', Colors.CYAN)} {task.priority} ({task.priority_label()})")
    print(f"  {c('Status:', Colors.CYAN)} {'Completed' if task.completed else 'Pending'}")
    print(f"  {c('Created:', Colors.CYAN)} {task.created_at[:19].replace('T', ' ')}")
    if task.completed_at:
        print(f"  {c('Completed:', Colors.CYAN)} {task.completed_at[:19].replace('T', ' ')}")
    if task.due_date:
        overdue_str = " (OVERDUE!)" if task.is_overdue() else ""
        print(f"  {c('Due Date:', Colors.CYAN)} {task.due_date}{overdue_str}")


def print_summary(summary: dict) -> None:
    print(f"\n{c('TASK SUMMARY', Colors.BOLD)}")
    print(f"  {c('Total Tasks:', Colors.CYAN)} {summary['total']}")
    print(f"  {c('Completed:', Colors.GREEN)} {summary['completed']}")
    print(f"  {c('Pending:', Colors.YELLOW)} {summary['pending']}")
    print(f"  {c('Overdue:', Colors.RED)} {summary['overdue']}")
    print(f"  {c('Completion Rate:', Colors.CYAN)} {summary['completion_rate']:.1f}%")
    print(f"  {c('Avg Turnaround:', Colors.CYAN)} {summary.get('avg_turnaround_hours', 0):.1f} hours")

    print(f"\n  {c('Pending by Priority:', Colors.BOLD)}")
    for p in range(5, 0, -1):
        count = summary['priority_breakdown'].get(p, 0)
        if count > 0:
            color = _priority_color(p)
            print(f"    {c(f'Priority {p}:', color)} {count}")

    print(f"\n  {c('Pending by Category:', Colors.BOLD)}")
    for cat, count in sorted(summary['category_breakdown'].items(), key=lambda x: -x[1]):
        print(f"    {cat}: {count}")


def _prompt_input(prompt: str, validator, allow_empty: bool = False) -> Optional[str]:
    while True:
        try:
            user_input = input(f"  {prompt} ").strip()
            if not user_input and allow_empty:
                return ""
            valid, result = validator(user_input)
            if valid:
                return result
            print(f"  {c('Error:', Colors.RED)} {result}")
        except (KeyboardInterrupt, EOFError):
            print(f"\n  {c('Operation cancelled.', Colors.CYAN)}")
            return None


def prompt_add_task(manager: TaskEngine) -> Optional[Task]:
    print_header("ADD NEW TASK")
    title = _prompt_input("Title:", validate_title)
    if title is None:
        return None
    description = _prompt_input("Description (optional):", validate_description, allow_empty=True)
    if description is None:
        return None
    category = _prompt_input("Category [General]:", validate_category, allow_empty=True)
    if category is None:
        return None
    if not category:
        category = "General"
    priority_str = _prompt_input("Priority 1-5 [1]:", validate_priority, allow_empty=True)
    if priority_str is None:
        return None
    priority = int(priority_str) if priority_str else 1
    due_date = _prompt_input("Due Date YYYY-MM-DD (optional):", validate_due_date, allow_empty=True)
    if due_date is None:
        return None
    try:
        task = manager.add_task(title, description, category, priority, due_date or None)
        print(f"\n  {c('Task added successfully!', Colors.GREEN)} (ID: {task.id})")
        return task
    except ValueError as e:
        print(f"\n  {c(f'Error: {e}', Colors.RED)}")
        return None


def prompt_complete_task(manager: TaskEngine) -> None:
    print_header("COMPLETE TASK")
    pending = manager.get_pending_tasks()
    if not pending:
        print(f"  {c('No pending tasks to complete.', Colors.YELLOW)}")
        return
    print_task_list(pending, "Pending Tasks")
    existing_ids = {t.id for t in pending}
    task_id = _prompt_input(
        "\nEnter Task ID to complete:",
        lambda x: validate_task_id(x, existing_ids),
    )
    if task_id is None:
        return
    if manager.complete_task(task_id):
        print(f"\n  {c('Task marked as complete!', Colors.GREEN)}")
    else:
        print(f"\n  {c('Failed to complete task.', Colors.RED)}")


def prompt_uncomplete_task(manager: TaskEngine) -> None:
    print_header("UNCOMPLETE TASK")
    completed = manager.get_completed_tasks()
    if not completed:
        print(f"  {c('No completed tasks to uncomplete.', Colors.YELLOW)}")
        return
    print_task_list(completed, "Completed Tasks")
    existing_ids = {t.id for t in completed}
    task_id = _prompt_input(
        "\nEnter Task ID to uncomplete:",
        lambda x: validate_task_id(x, existing_ids),
    )
    if task_id is None:
        return
    if manager.uncomplete_task(task_id):
        print(f"\n  {c('Task marked as pending!', Colors.GREEN)}")
    else:
        print(f"\n  {c('Failed to uncomplete task.', Colors.RED)}")


def prompt_delete_task(manager: TaskEngine) -> None:
    print_header("DELETE TASK")
    tasks = manager.get_all_tasks()
    if not tasks:
        print(f"  {c('No tasks to delete.', Colors.YELLOW)}")
        return
    print_task_list(tasks, "All Tasks")
    existing_ids = {t.id for t in tasks}
    task_id = _prompt_input(
        "\nEnter Task ID to delete:",
        lambda x: validate_task_id(x, existing_ids),
    )
    if task_id is None:
        return
    task = manager.get_task(task_id)
    print_task_detail(task)
    confirm = input(f"  {c('Are you sure you want to delete this task? (y/n):', Colors.RED)} ").strip().lower()
    if confirm in ("y", "yes"):
        if manager.delete_task(task_id):
            print(f"\n  {c('Task deleted!', Colors.GREEN)}")
        else:
            print(f"\n  {c('Failed to delete task.', Colors.RED)}")


def prompt_search_tasks(manager: TaskEngine) -> None:
    print_header("SEARCH TASKS")
    query = _prompt_input("Search query:", validate_search_query)
    if query is None:
        return
    print(f"  Categories: {', '.join(manager.get_categories()) or '(none)'}")
    category = input("  Filter by category (optional): ").strip()
    category = category if category else None
    results = manager.search_tasks(query, category)
    print_task_list(results, f"Search Results for '{query}'")


def prompt_view_summary(manager: TaskEngine) -> None:
    print_header("TASK SUMMARY")
    summary = manager.get_summary()
    print_summary(summary)
    overdue = manager.filter_overdue()
    if overdue:
        print(f"\n  {c('OVERDUE TASKS:', Colors.RED + Colors.BOLD)}")
        for task in overdue:
            print(f"    [{task.id}] {task.title} (Due: {task.due_date})")


def prompt_export_report(manager: TaskEngine) -> None:
    print_header("EXPORT REPORT")
    print(f"  {c('1.', Colors.GREEN)} Markdown Report")
    print(f"  {c('2.', Colors.GREEN)} Plain Text Report (Audit Log)")
    print(f"  {c('3.', Colors.GREEN)} CSV Export")
    print()
    choice = input("  Select format (1-3): ").strip()
    tasks = manager.get_all_tasks()
    from .storage import DEFAULT_JSON_PATH
    base_dir = os.path.dirname(os.path.abspath(DEFAULT_JSON_PATH))
    if choice == "1":
        filepath = os.path.join(base_dir, "report.md")
        export_markdown(tasks, filepath)
        print(f"\n  {c(f'Markdown report exported to {filepath}', Colors.GREEN)}")
    elif choice == "2":
        filepath = os.path.join(base_dir, "report.txt")
        export_audit_log(tasks, filepath)
        print(f"\n  {c(f'Text report exported to {filepath}', Colors.GREEN)}")
    elif choice == "3":
        filepath = os.path.join(base_dir, "tasks_export.csv")
        export_csv(tasks, filepath)
        print(f"\n  {c(f'CSV exported to {filepath}', Colors.GREEN)}")
    else:
        print(f"\n  {c('Invalid choice.', Colors.RED)}")


def prompt_settings(manager: TaskEngine) -> None:
    print_header("SETTINGS")
    print(f"  {c('Current Storage:', Colors.CYAN)} JSON (tasks.json)")
    print(f"  {c('Total Tasks:', Colors.CYAN)} {len(manager.tasks)}")
    print()
    print(f"  {c('1.', Colors.GREEN)} Reload from disk")
    print(f"  {c('2.', Colors.GREEN)} Save to disk")
    print(f"  {c('3.', Colors.GREEN)} Generate sample data")
    print()
    choice = input("  Select option (1-3): ").strip()
    if choice == "1":
        manager._load()
        print(f"\n  {c(f'Reloaded {len(manager.tasks)} tasks.', Colors.GREEN)}")
    elif choice == "2":
        manager._save()
        print(f"\n  {c(f'Saved {len(manager.tasks)} tasks.', Colors.GREEN)}")
    elif choice == "3":
        generate_sample_data(manager)
    else:
        print(f"\n  {c('Invalid choice.', Colors.RED)}")


def generate_sample_data(manager: TaskEngine) -> None:
    sample_tasks = [
        ("Complete project proposal", "Write and submit Q4 project proposal", "Work", 5, "2026-11-20"),
        ("Team meeting", "Weekly sync with development team", "Work", 3, "2026-11-18"),
        ("Code review", "Review PR #234 for authentication module", "Work", 4, "2026-11-17"),
        ("Buy groceries", "Milk, eggs, bread, vegetables", "Personal", 2, "2026-11-16"),
        ("Gym session", "Cardio and strength training", "Health", 3, "2026-11-16"),
        ("Read book", "Finish chapter 5 of Clean Code", "Learning", 2, "2026-11-25"),
        ("Call dentist", "Schedule annual checkup", "Health", 1, "2026-11-30"),
        ("Pay bills", "Electricity, internet, phone", "Personal", 4, "2026-11-15"),
        ("Plan vacation", "Research destinations for December", "Personal", 1, "2026-12-01"),
        ("Learn Python", "Complete async/await tutorial", "Learning", 3, "2026-11-22"),
    ]
    for title, desc, cat, priority, due in sample_tasks:
        manager.add_task(title, desc, cat, priority, due)
    print(f"\n  {c(f'Generated {len(sample_tasks)} sample tasks!', Colors.GREEN)}")


def run_app() -> None:
    manager = TaskEngine()
    clear_screen()
    print_header("WELCOME TO CAMPUSSOLVE TO-DO MANAGER")
    print(f"  Loaded {len(manager.tasks)} tasks from storage.\n")

    while True:
        print_menu()
        try:
            choice = input("  Select option (0-9): ").strip()
        except (KeyboardInterrupt, EOFError):
            print(f"\n\n{c('Goodbye!', Colors.CYAN)}\n")
            return

        if choice == "1":
            prompt_add_task(manager)
        elif choice == "2":
            print_header("ALL TASKS")
            print_task_list(manager.get_all_tasks(), "All Tasks")
        elif choice == "3":
            prompt_complete_task(manager)
        elif choice == "4":
            prompt_uncomplete_task(manager)
        elif choice == "5":
            prompt_delete_task(manager)
        elif choice == "6":
            prompt_search_tasks(manager)
        elif choice == "7":
            prompt_view_summary(manager)
        elif choice == "8":
            prompt_export_report(manager)
        elif choice == "9":
            prompt_settings(manager)
        elif choice == "0":
            print(f"\n  {c('Goodbye!', Colors.CYAN)}\n")
            break
        else:
            print(f"\n  {c('Invalid option. Please try again.', Colors.RED)}")

        try:
            input(f"\n  {c('Press Enter to continue...', Colors.DIM)}")
        except (KeyboardInterrupt, EOFError):
            print(f"\n\n{c('Goodbye!', Colors.CYAN)}\n")
            return
        clear_screen()

