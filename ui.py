import os
import sys
from typing import List, Optional
from logic import TaskManager
from models import Task
from validation import get_valid_input, confirm_action, validate_title, validate_description, validate_category, validate_priority, validate_due_date, validate_task_id, validate_search_query


class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    END = '\033[0m'
    DIM = '\033[2m'


def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')


def print_header(title: str):
    print(f"\n{Colors.CYAN}{Colors.BOLD}{'=' * 60}{Colors.END}")
    print(f"{Colors.CYAN}{Colors.BOLD}{title.center(60)}{Colors.END}")
    print(f"{Colors.CYAN}{Colors.BOLD}{'=' * 60}{Colors.END}\n")


def print_menu():
    print(f"{Colors.BOLD}MAIN MENU{Colors.END}")
    print(f"  {Colors.GREEN}1.{Colors.END} Add Task")
    print(f"  {Colors.GREEN}2.{Colors.END} List Tasks")
    print(f"  {Colors.GREEN}3.{Colors.END} Complete Task")
    print(f"  {Colors.GREEN}4.{Colors.END} Uncomplete Task")
    print(f"  {Colors.GREEN}5.{Colors.END} Delete Task")
    print(f"  {Colors.GREEN}6.{Colors.END} Search Tasks")
    print(f"  {Colors.GREEN}7.{Colors.END} View Summary")
    print(f"  {Colors.GREEN}8.{Colors.END} Export Report")
    print(f"  {Colors.GREEN}9.{Colors.END} Settings")
    print(f"  {Colors.RED}0.{Colors.END} Exit")
    print()


def print_task_list(tasks: List[Task], title: str = "Tasks", show_completed: bool = True):
    if not tasks:
        print(f"  {Colors.YELLOW}No tasks found.{Colors.END}")
        return
    
    print(f"\n{Colors.BOLD}{title} ({len(tasks)}){Colors.END}")
    print(f"  {'ID':<10} {'Status':<10} {'Priority':<10} {'Category':<15} {'Title'}")
    print(f"  {'-' * 80}")
    
    for task in tasks:
        status = f"{Colors.GREEN}Done{Colors.END}" if task.completed else f"{Colors.YELLOW}Pending{Colors.END}"
        priority_color = {1: Colors.BLUE, 2: Colors.CYAN, 3: Colors.YELLOW, 4: Colors.RED, 5: Colors.RED + Colors.BOLD}.get(task.priority, Colors.END)
        priority_str = f"{priority_color}{task.priority}{Colors.END}"
        
        due_str = ""
        if task.due_date and not task.completed:
            if task.is_overdue():
                due_str = f" {Colors.RED}[OVERDUE: {task.due_date}]{Colors.END}"
            else:
                days = task.days_until_due()
                if days is not None and days <= 3:
                    due_str = f" {Colors.YELLOW}[Due: {task.due_date}]{Colors.END}"
                else:
                    due_str = f" {Colors.DIM}[Due: {task.due_date}]{Colors.END}"
        
        title_display = task.title[:45] + "..." if len(task.title) > 45 else task.title
        print(f"  {task.id:<10} {status:<10} {priority_str:<10} {task.category:<15} {title_display}{due_str}")


def print_task_detail(task: Task):
    print(f"\n{Colors.BOLD}Task Details{Colors.END}")
    print(f"  {Colors.CYAN}ID:{Colors.END} {task.id}")
    print(f"  {Colors.CYAN}Title:{Colors.END} {task.title}")
    print(f"  {Colors.CYAN}Description:{Colors.END} {task.description or '(none)'}")
    print(f"  {Colors.CYAN}Category:{Colors.END} {task.category}")
    print(f"  {Colors.CYAN}Priority:{Colors.END} {task.priority}")
    print(f"  {Colors.CYAN}Status:{Colors.END} {'Completed' if task.completed else 'Pending'}")
    print(f"  {Colors.CYAN}Created:{Colors.END} {task.created_at[:19].replace('T', ' ')}")
    if task.completed_at:
        print(f"  {Colors.CYAN}Completed:{Colors.END} {task.completed_at[:19].replace('T', ' ')}")
    if task.due_date:
        overdue_str = " (OVERDUE!)" if task.is_overdue() else ""
        print(f"  {Colors.CYAN}Due Date:{Colors.END} {task.due_date}{overdue_str}")


def print_summary(summary: dict):
    print(f"\n{Colors.BOLD}TASK SUMMARY{Colors.END}")
    print(f"  {Colors.CYAN}Total Tasks:{Colors.END} {summary['total']}")
    print(f"  {Colors.GREEN}Completed:{Colors.END} {summary['completed']}")
    print(f"  {Colors.YELLOW}Pending:{Colors.END} {summary['pending']}")
    print(f"  {Colors.RED}Overdue:{Colors.END} {summary['overdue']}")
    print(f"  {Colors.CYAN}Completion Rate:{Colors.END} {summary['completion_rate']:.1f}%")
    
    print(f"\n  {Colors.BOLD}Pending by Priority:{Colors.END}")
    for p in range(5, 0, -1):
        count = summary['priority_breakdown'].get(p, 0)
        if count > 0:
            color = {1: Colors.BLUE, 2: Colors.CYAN, 3: Colors.YELLOW, 4: Colors.RED, 5: Colors.RED + Colors.BOLD}.get(p, Colors.END)
            print(f"    {color}Priority {p}:{Colors.END} {count}")
    
    print(f"\n  {Colors.BOLD}Pending by Category:{Colors.END}")
    for cat, count in sorted(summary['category_breakdown'].items(), key=lambda x: -x[1]):
        print(f"    {cat}: {count}")


def prompt_add_task(manager: TaskManager) -> Optional[Task]:
    print_header("ADD NEW TASK")
    
    title = get_valid_input("  Title: ", validate_title)
    if title is None:
        return None
    
    description = get_valid_input("  Description (optional): ", validate_description)
    if description is None:
        return None
    
    category = get_valid_input("  Category [General]: ", validate_category)
    if category is None:
        return None
    if not category:
        category = "General"
    
    priority_str = get_valid_input("  Priority 1-5 [1]: ", validate_priority)
    if priority_str is None:
        return None
    priority = priority_str if priority_str else 1
    
    due_date = get_valid_input("  Due Date YYYY-MM-DD (optional): ", validate_due_date)
    if due_date is None:
        return None
    
    try:
        task = manager.add_task(title, description, category, priority, due_date)
        print(f"\n  {Colors.GREEN}Task added successfully!{Colors.END} (ID: {task.id})")
        return task
    except ValueError as e:
        print(f"\n  {Colors.RED}Error: {e}{Colors.END}")
        return None


def prompt_complete_task(manager: TaskManager):
    print_header("COMPLETE TASK")
    pending = manager.get_pending_tasks()
    if not pending:
        print(f"  {Colors.YELLOW}No pending tasks to complete.{Colors.END}")
        return
    
    print_task_list(pending, "Pending Tasks")
    
    task_id = get_valid_input("\n  Enter Task ID to complete: ", 
                              lambda x: validate_task_id(x, {t.id for t in pending}))
    if task_id is None:
        return
    
    if manager.complete_task(task_id):
        print(f"\n  {Colors.GREEN}Task marked as complete!{Colors.END}")
    else:
        print(f"\n  {Colors.RED}Failed to complete task.{Colors.END}")


def prompt_uncomplete_task(manager: TaskManager):
    print_header("UNCOMPLETE TASK")
    completed = manager.get_completed_tasks()
    if not completed:
        print(f"  {Colors.YELLOW}No completed tasks to uncomplete.{Colors.END}")
        return
    
    print_task_list(completed, "Completed Tasks")
    
    task_id = get_valid_input("\n  Enter Task ID to uncomplete: ",
                              lambda x: validate_task_id(x, {t.id for t in completed}))
    if task_id is None:
        return
    
    if manager.uncomplete_task(task_id):
        print(f"\n  {Colors.GREEN}Task marked as pending!{Colors.END}")
    else:
        print(f"\n  {Colors.RED}Failed to uncomplete task.{Colors.END}")


def prompt_delete_task(manager: TaskManager):
    print_header("DELETE TASK")
    tasks = manager.get_all_tasks()
    if not tasks:
        print(f"  {Colors.YELLOW}No tasks to delete.{Colors.END}")
        return
    
    print_task_list(tasks, "All Tasks")
    
    task_id = get_valid_input("\n  Enter Task ID to delete: ",
                              lambda x: validate_task_id(x, {t.id for t in tasks}))
    if task_id is None:
        return
    
    task = manager.get_task(task_id)
    print_task_detail(task)
    
    if confirm_action("  Are you sure you want to delete this task?"):
        if manager.delete_task(task_id):
            print(f"\n  {Colors.GREEN}Task deleted!{Colors.END}")
        else:
            print(f"\n  {Colors.RED}Failed to delete task.{Colors.END}")


def prompt_search_tasks(manager: TaskManager):
    print_header("SEARCH TASKS")
    
    query = get_valid_input("  Search query: ", validate_search_query)
    if query is None:
        return
    
    print(f"  Categories: {', '.join(manager.get_categories()) or '(none)'}")
    category = input("  Filter by category (optional): ").strip()
    category = category if category else None
    
    results = manager.search_tasks(query, category)
    print_task_list(results, f"Search Results for '{query}'")


def prompt_view_summary(manager: TaskManager):
    print_header("TASK SUMMARY")
    summary = manager.get_summary()
    print_summary(summary)
    
    overdue = manager.filter_overdue()
    if overdue:
        print(f"\n  {Colors.RED}{Colors.BOLD}⚠ OVERDUE TASKS:{Colors.END}")
        for task in overdue:
            print(f"    [{task.id}] {task.title} (Due: {task.due_date})")


def prompt_export_report(manager: TaskManager):
    print_header("EXPORT REPORT")
    print(f"  {Colors.GREEN}1.{Colors.END} Markdown Report")
    print(f"  {Colors.GREEN}2.{Colors.END} Plain Text Report")
    print(f"  {Colors.GREEN}3.{Colors.END} CSV Export")
    print()
    
    choice = input("  Select format (1-3): ").strip()
    
    from storage import export_tasks_markdown, export_tasks_text, save_tasks_csv, DEFAULT_CSV_PATH
    tasks = manager.get_all_tasks()
    
    if choice == "1":
        filepath = os.path.join(os.path.dirname(__file__), "data", "report.md")
        export_tasks_markdown(tasks, filepath)
        print(f"\n  {Colors.GREEN}Markdown report exported to {filepath}{Colors.END}")
    elif choice == "2":
        filepath = os.path.join(os.path.dirname(__file__), "data", "report.txt")
        export_tasks_text(tasks, filepath)
        print(f"\n  {Colors.GREEN}Text report exported to {filepath}{Colors.END}")
    elif choice == "3":
        save_tasks_csv(tasks, DEFAULT_CSV_PATH)
        print(f"\n  {Colors.GREEN}CSV exported to {DEFAULT_CSV_PATH}{Colors.END}")
    else:
        print(f"\n  {Colors.RED}Invalid choice.{Colors.END}")


def prompt_settings(manager: TaskManager):
    print_header("SETTINGS")
    print(f"  {Colors.CYAN}Current Storage:{Colors.END} JSON (tasks.json)")
    print(f"  {Colors.CYAN}Total Tasks:{Colors.END} {len(manager.tasks)}")
    print()
    print(f"  {Colors.GREEN}1.{Colors.END} Reload from disk")
    print(f"  {Colors.GREEN}2.{Colors.END} Save to disk")
    print(f"  {Colors.GREEN}3.{Colors.END} Generate sample data")
    print()
    
    choice = input("  Select option (1-3): ").strip()
    
    if choice == "1":
        manager.load()
        print(f"\n  {Colors.GREEN}Reloaded {len(manager.tasks)} tasks.{Colors.END}")
    elif choice == "2":
        manager.save()
        print(f"\n  {Colors.GREEN}Saved {len(manager.tasks)} tasks.{Colors.END}")
    elif choice == "3":
        generate_sample_data(manager)
    else:
        print(f"\n  {Colors.RED}Invalid choice.{Colors.END}")


def generate_sample_data(manager: TaskManager):
    sample_tasks = [
        ("Complete project proposal", "Write and submit Q4 project proposal", "Work", 5, "2026-11-20"),
        ("Team meeting", "Weekly sync with development team", "Work", 3, "2026-11-18"),
        ("Code review", "Review PR #234 for authentication module", "Work", 4, "2026-11-17"),
        ("Buy groceries", "Milk, eggs, bread, vegetables", "Personal", 2, "2026-11-16"),
        ("Gym session", "Cardio and strength training", "Health", 3, "2026-11-16"),
        ("Read book", "Finish chapter 5 of 'Clean Code'", "Learning", 2, "2026-11-25"),
        ("Call dentist", "Schedule annual checkup", "Health", 1, "2026-11-30"),
        ("Pay bills", "Electricity, internet, phone", "Personal", 4, "2026-11-15"),
        ("Plan vacation", "Research destinations for December", "Personal", 1, "2026-12-01"),
        ("Learn Python", "Complete async/await tutorial", "Learning", 3, "2026-11-22"),
    ]
    
    for title, desc, cat, priority, due in sample_tasks:
        manager.add_task(title, desc, cat, priority, due)
    
    print(f"\n  {Colors.GREEN}Generated {len(sample_tasks)} sample tasks!{Colors.END}")


def run_app():
    manager = TaskManager()
    
    clear_screen()
    print_header("WELCOME TO TODO MANAGER")
    print(f"  Loaded {len(manager.tasks)} tasks from storage.\n")
    
    while True:
        print_menu()
        choice = input("  Select option (0-9): ").strip()
        
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
            print(f"\n  {Colors.CYAN}Goodbye!{Colors.END}\n")
            break
        else:
            print(f"\n  {Colors.RED}Invalid option. Please try again.{Colors.END}")
        
        input(f"\n  {Colors.DIM}Press Enter to continue...{Colors.END}")
        clear_screen()


if __name__ == "__main__":
    try:
        run_app()
    except KeyboardInterrupt:
        print(f"\n\n{Colors.CYAN}Goodbye!{Colors.END}\n")
    except Exception as e:
        print(f"\n{Colors.RED}Fatal error: {e}{Colors.END}")
        import traceback
        traceback.print_exc()