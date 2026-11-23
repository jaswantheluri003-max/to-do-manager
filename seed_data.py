from logic import TaskManager

m = TaskManager()
samples = [
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
for t in samples:
    m.add_task(*t)
print(f"Added {len(m.tasks)} sample tasks")
summary = m.get_summary()
print(f"Total: {summary['total']}, Completed: {summary['completed']}, Pending: {summary['pending']}, Overdue: {summary['overdue']}")