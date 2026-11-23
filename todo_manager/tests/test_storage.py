import unittest
import tempfile
import os
import sys
from datetime import datetime, timedelta

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.models import Task
from src.storage import save_tasks_json, load_tasks_json, save_tasks_csv, load_tasks_csv
from src.validators import (
    validate_title, validate_description, validate_category,
    validate_priority, validate_due_date,
)


class TestStorage(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.json_path = os.path.join(self.tmp, "test_tasks.json")
        self.csv_path = os.path.join(self.tmp, "test_tasks.csv")

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmp)

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
        self.assertEqual(load_tasks_json(os.path.join(self.tmp, "nope.json")), [])
        self.assertEqual(load_tasks_csv(os.path.join(self.tmp, "nope.csv")), [])


class TestValidators(unittest.TestCase):
    def test_validate_title(self):
        self.assertTrue(validate_title("Valid Title")[0])
        self.assertFalse(validate_title("")[0])
        self.assertFalse(validate_title("x" * 101)[0])

    def test_validate_description(self):
        self.assertTrue(validate_description("ok")[0])
        self.assertFalse(validate_description("x" * 501)[0])

    def test_validate_category(self):
        v, r = validate_category("work")
        self.assertTrue(v); self.assertEqual(r, "Work")
        self.assertFalse(validate_category("")[0])

    def test_validate_priority(self):
        self.assertTrue(validate_priority("3")[0])
        self.assertFalse(validate_priority("0")[0])
        self.assertFalse(validate_priority("6")[0])
        self.assertFalse(validate_priority("abc")[0])

    def test_validate_due_date(self):
        self.assertTrue(validate_due_date("2026-12-31")[0])
        self.assertTrue(validate_due_date("")[0])
        self.assertFalse(validate_due_date("invalid")[0])


if __name__ == "__main__":
    unittest.main()
