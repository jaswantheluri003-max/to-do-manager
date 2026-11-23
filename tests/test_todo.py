import unittest
import tempfile
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from models import Task
from storage import save_tasks_json, load_tasks_json, save_tasks_csv, load_tasks_csv
from logic import TaskManager
from validation import validate_title, validate_description, validate_category, validate_priority, validate_due_date


class TestTaskModel(unittest.TestCase):
    def test_task_creation(self):
        task = Task(title="Test Task", priority=3)
        self.assertEqual(task.title, "Test Task")
        self.assertEqual(task.priority, 3)
        self.assertFalse(task.completed)
        self.assertIsNotNone(task.id)
        self.assertIsNotNone(task.created_at)

    def test_task_completion(self):
        task = Task(title="Test")
        self.assertFalse(task.completed)
        task.mark_complete()
        self.assertTrue(task.completed)
        self.assertIsNotNone(task.completed_at)
        task.mark_incomplete()
        self.assertFalse(task.completed)
        self.assertIsNone(task.completed_at)

    def test_task_to_dict(self):
        task = Task(title="Test", category="Work", priority=2)
        data = task.to_dict()
        self.assertEqual(data["title"], "Test")
        self.assertEqual(data["category"], "Work")
        self.assertEqual(data["priority"], 2)

    def test_task_from_dict(self):
        data = {"id": "abc123", "title": "Test", "category": "Work", "priority": 2}
        task = Task.from_dict(data)
        self.assertEqual(task.id, "abc123")
        self.assertEqual(task.title, "Test")

    def test_overdue_detection(self):
        from datetime import datetime, timedelta
        past = (datetime.now() - timedelta(days=1)).date().isoformat()
        future = (datetime.now() + timedelta(days=1)).date().isoformat()
        
        task_overdue = Task(title="Overdue", due_date=past)
        task_future = Task(title="Future", due_date=future)
        task_completed = Task(title="Done", due_date=past)
        task_completed.mark_complete()
        
        self.assertTrue(task_overdue.is_overdue())
        self.assertFalse(task_future.is_overdue())
        self.assertFalse(task_completed.is_overdue())


class TestValidation(unittest.TestCase):
    def test_validate_title(self):
        valid, result = validate_title("Valid Title")
        self.assertTrue(valid)
        self.assertEqual(result, "Valid Title")
        
        valid, result = validate_title("")
        self.assertFalse(valid)
        
        valid, result = validate_title("x" * 101)
        self.assertFalse(valid)

    def test_validate_description(self):
        valid, result = validate_description("Valid description")
        self.assertTrue(valid)
        
        valid, result = validate_description("x" * 501)
        self.assertFalse(valid)

    def test_validate_category(self):
        valid, result = validate_category("work")
        self.assertTrue(valid)
        self.assertEqual(result, "Work")
        
        valid, result = validate_category("")
        self.assertFalse(valid)

    def test_validate_priority(self):
        valid, result = validate_priority("3")
        self.assertTrue(valid)
        self.assertEqual(result, 3)
        
        valid, result = validate_priority("0")
        self.assertFalse(valid)
        
        valid, result = validate_priority("6")
        self.assertFalse(valid)
        
        valid, result = validate_priority("abc")
        self.assertFalse(valid)

    def test_validate_due_date(self):
        valid, result = validate_due_date("2026-12-31")
        self.assertTrue(valid)
        self.assertEqual(result, "2026-12-31")
        
        valid, result = validate_due_date("")
        self.assertTrue(valid)
        self.assertIsNone(result)
        
        valid, result = validate_due_date("invalid")
        self.assertFalse(valid)


class TestStorage(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.json_path = os.path.join(self.temp_dir, "test_tasks.json")
        self.csv_path = os.path.join(self.temp_dir, "test_tasks.csv")

    def tearDown(self):
        import shutil
        shutil.rmtree(self.temp_dir)

    def test_json_save_load(self):
        tasks = [
            Task(title="Task 1", category="Work", priority=3),
            Task(title="Task 2", category="Personal", priority=1),
        ]
        tasks[0].mark_complete()
        
        save_tasks_json(tasks, self.json_path)
        loaded = load_tasks_json(self.json_path)
        
        self.assertEqual(len(loaded), 2)
        self.assertEqual(loaded[0].title, "Task 1")
        self.assertTrue(loaded[0].completed)
        self.assertFalse(loaded[1].completed)

    def test_csv_save_load(self):
        tasks = [
            Task(title="Task 1", category="Work", priority=3),
            Task(title="Task 2", category="Personal", priority=1),
        ]
        
        save_tasks_csv(tasks, self.csv_path)
        loaded = load_tasks_csv(self.csv_path)
        
        self.assertEqual(len(loaded), 2)
        self.assertEqual(loaded[0].title, "Task 1")
        self.assertEqual(loaded[0].category, "Work")

    def test_load_nonexistent(self):
        loaded = load_tasks_json(os.path.join(self.temp_dir, "nonexistent.json"))
        self.assertEqual(loaded, [])
        
        loaded = load_tasks_csv(os.path.join(self.temp_dir, "nonexistent.csv"))
        self.assertEqual(loaded, [])


class TestTaskManager(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.json_path = os.path.join(self.temp_dir, "test_tasks.json")
        self.manager = TaskManager(json_path=self.json_path)

    def tearDown(self):
        import shutil
        shutil.rmtree(self.temp_dir)

    def test_add_task(self):
        task = self.manager.add_task("New Task", "Description", "Work", 4, "2026-12-31")
        self.assertEqual(task.title, "New Task")
        self.assertEqual(task.category, "Work")
        self.assertEqual(task.priority, 4)
        self.assertEqual(task.due_date, "2026-12-31")
        self.assertEqual(len(self.manager.tasks), 1)

    def test_complete_task(self):
        task = self.manager.add_task("Task to complete")
        result = self.manager.complete_task(task.id)
        self.assertTrue(result)
        self.assertTrue(self.manager.get_task(task.id).completed)

    def test_uncomplete_task(self):
        task = self.manager.add_task("Task")
        self.manager.complete_task(task.id)
        result = self.manager.uncomplete_task(task.id)
        self.assertTrue(result)
        self.assertFalse(self.manager.get_task(task.id).completed)

    def test_delete_task(self):
        task = self.manager.add_task("Task to delete")
        result = self.manager.delete_task(task.id)
        self.assertTrue(result)
        self.assertIsNone(self.manager.get_task(task.id))
        self.assertEqual(len(self.manager.tasks), 0)

    def test_search_tasks(self):
        self.manager.add_task("Write report", "Quarterly report", "Work", 3)
        self.manager.add_task("Buy groceries", "Milk and eggs", "Personal", 2)
        self.manager.add_task("Read book", "Python guide", "Learning", 1)
        
        results = self.manager.search_tasks("report")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].title, "Write report")
        
        results = self.manager.search_tasks("python")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].title, "Read book")

    def test_filter_by_category(self):
        self.manager.add_task("Task 1", category="Work")
        self.manager.add_task("Task 2", category="Work")
        self.manager.add_task("Task 3", category="Personal")
        
        work_tasks = self.manager.filter_by_category("Work")
        self.assertEqual(len(work_tasks), 2)

    def test_get_summary(self):
        self.manager.add_task("Task 1", priority=3)
        self.manager.add_task("Task 2", priority=5)
        task3 = self.manager.add_task("Task 3", priority=1)
        self.manager.complete_task(task3.id)
        
        summary = self.manager.get_summary()
        self.assertEqual(summary["total"], 3)
        self.assertEqual(summary["completed"], 1)
        self.assertEqual(summary["pending"], 2)
        self.assertEqual(summary["priority_breakdown"][5], 1)
        self.assertEqual(summary["priority_breakdown"][3], 1)

    def test_persistence(self):
        self.manager.add_task("Persistent Task", category="Test")
        self.manager.save()
        
        new_manager = TaskManager(json_path=self.json_path)
        self.assertEqual(len(new_manager.tasks), 1)
        self.assertEqual(new_manager.tasks[0].title, "Persistent Task")


if __name__ == "__main__":
    unittest.main()