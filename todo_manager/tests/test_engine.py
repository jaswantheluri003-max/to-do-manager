import unittest
import tempfile
import os
import sys
from datetime import datetime, timedelta

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.models import Task, Priority, Status
from src.storage import save_tasks_json, load_tasks_json, import_csv_bulk
from src.engine import TaskEngine
from src.validators import (
    validate_title, validate_description, validate_category,
    validate_priority, validate_due_date, validate_task_id,
    validate_search_query, validate_menu_bounds, is_valid_date,
)
from src.analytics import overdue_risk_level, completion_rate, category_breakdown


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
        task.mark_complete()
        self.assertTrue(task.completed)
        self.assertIsNotNone(task.completed_at)
        task.mark_incomplete()
        self.assertFalse(task.completed)
        self.assertIsNone(task.completed_at)

    def test_priority_enum(self):
        self.assertEqual(Priority.CRITICAL, 4)
        self.assertEqual(Priority.URGENT, 5)
        self.assertEqual(Priority.labels()[5], "Urgent")

    def test_status_enum(self):
        self.assertEqual(Status.from_bool(True), Status.COMPLETED)
        self.assertEqual(Status.from_bool(False), Status.PENDING)

    def test_is_overdue(self):
        past = (datetime.now() - timedelta(days=1)).date().isoformat()
        future = (datetime.now() + timedelta(days=1)).date().isoformat()
        t_over = Task(title="Over", due_date=past)
        t_fut = Task(title="Future", due_date=future)
        t_done = Task(title="Done", due_date=past); t_done.mark_complete()
        self.assertTrue(t_over.is_overdue())
        self.assertFalse(t_fut.is_overdue())
        self.assertFalse(t_done.is_overdue())


class TestValidators(unittest.TestCase):
    def test_title(self):
        self.assertTrue(validate_title("Valid")[0])
        self.assertFalse(validate_title("")[0])
        self.assertFalse(validate_title("x" * 101)[0])

    def test_description(self):
        self.assertTrue(validate_description("ok")[0])
        self.assertFalse(validate_description("x" * 501)[0])

    def test_category(self):
        v, r = validate_category("work")
        self.assertTrue(v); self.assertEqual(r, "Work")
        self.assertFalse(validate_category("")[0])

    def test_priority(self):
        self.assertTrue(validate_priority("3")[0])
        self.assertFalse(validate_priority("0")[0])
        self.assertFalse(validate_priority("6")[0])
        self.assertFalse(validate_priority("abc")[0])

    def test_due_date(self):
        self.assertTrue(validate_due_date("2026-12-31")[0])
        self.assertTrue(validate_due_date("")[0])
        self.assertFalse(validate_due_date("bad")[0])
        self.assertTrue(is_valid_date("2026-12-31"))
        self.assertFalse(is_valid_date("not-a-date"))

    def test_task_id(self):
        ids = {"a1", "b2"}
        self.assertTrue(validate_task_id("a1", ids)[0])
        self.assertFalse(validate_task_id("zz", ids)[0])

    def test_search_query(self):
        self.assertTrue(validate_search_query("hello")[0])
        self.assertFalse(validate_search_query("")[0])

    def test_menu_bounds(self):
        self.assertTrue(validate_menu_bounds("3", 1, 5)[0])
        self.assertFalse(validate_menu_bounds("9", 1, 5)[0])
        self.assertFalse(validate_menu_bounds("x", 1, 5)[0])


class TestStorage(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.json_path = os.path.join(self.tmp, "tasks.json")

    def tearDown(self):
        import shutil; shutil.rmtree(self.tmp)

    def test_save_load(self):
        tasks = [Task(title="T1", category="Work", priority=4)]
        tasks[0].mark_complete()
        save_tasks_json(tasks, self.json_path)
        loaded = load_tasks_json(self.json_path)
        self.assertEqual(len(loaded), 1)
        self.assertTrue(loaded[0].completed)

    def test_load_nonexistent(self):
        self.assertEqual(load_tasks_json(os.path.join(self.tmp, "nope.json")), [])

    def test_corrupted_returns_empty(self):
        with open(self.json_path, "w") as f:
            f.write("{ not valid json")
        self.assertEqual(load_tasks_json(self.json_path), [])

    def test_import_csv_bulk(self):
        csv_path = os.path.join(self.tmp, "seed.csv")
        with open(csv_path, "w", newline="") as f:
            f.write("title,description,category,priority,completed,due_date\n")
            f.write("Imported Task,desc,Work,3,False,2026-12-01\n")
            f.write(",desc,Work,3,False,2026-12-01\n")  # bad row: empty title
        count, errors = import_csv_bulk(csv_path)
        self.assertEqual(count, 1)
        self.assertEqual(len(errors), 1)


class TestEngine(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.json_path = os.path.join(self.tmp, "tasks.json")
        self.engine = TaskEngine(json_path=self.json_path)

    def tearDown(self):
        import shutil; shutil.rmtree(self.tmp)

    def test_add_and_get(self):
        t = self.engine.add_task("Do thing", "desc", "Work", 4, "2026-12-01")
        self.assertEqual(t.title, "Do thing")
        got = self.engine.get_task(t.id)
        self.assertIsNotNone(got)
        self.assertEqual(got.title, "Do thing")

    def test_complete_delete(self):
        t = self.engine.add_task("Task")
        self.assertTrue(self.engine.complete_task(t.id))
        self.assertTrue(self.engine.get_task(t.id).completed)
        self.assertTrue(self.engine.delete_task(t.id))
        self.assertIsNone(self.engine.get_task(t.id))

    def test_update(self):
        t = self.engine.add_task("Old")
        self.engine.update_task(t.id, title="New", priority=2)
        got = self.engine.get_task(t.id)
        self.assertEqual(got.title, "New")
        self.assertEqual(got.priority, 2)

    def test_search(self):
        self.engine.add_task("Write report", "q4 report", "Work")
        self.engine.add_task("Buy milk", "dairy", "Personal")
        res = self.engine.search_tasks("report")
        self.assertEqual(len(res), 1)
        res = self.engine.search_tasks("milk", category="Personal")
        self.assertEqual(len(res), 1)

    def test_summary(self):
        self.engine.add_task("A", priority=5)
        self.engine.add_task("B", priority=1)
        s = self.engine.get_summary()
        self.assertEqual(s["total"], 2)
        self.assertEqual(s["priority_breakdown"][5], 1)

    def test_overdue(self):
        past = (datetime.now() - timedelta(days=2)).date().isoformat()
        self.engine.add_task("Overdue task", due_date=past)
        overdue = self.engine.filter_overdue()
        self.assertEqual(len(overdue), 1)


class TestAnalytics(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.json_path = os.path.join(self.tmp, "tasks.json")
        self.engine = TaskEngine(json_path=self.json_path)

    def tearDown(self):
        import shutil; shutil.rmtree(self.tmp)

    def test_completion_rate(self):
        self.engine.add_task("A")
        self.engine.add_task("B")
        self.engine.complete_task(self.engine.tasks[0].id)
        self.assertEqual(completion_rate(self.engine), 50.0)

    def test_category_breakdown(self):
        self.engine.add_task("A", category="Work")
        self.engine.add_task("B", category="Work")
        self.engine.add_task("C", category="Personal")
        cb = category_breakdown(self.engine)
        self.assertEqual(cb["Work"], 2)
        self.assertEqual(cb["Personal"], 1)

    def test_overdue_risk_level(self):
        past = (datetime.now() - timedelta(days=1)).date().isoformat()
        self.engine.add_task("O1", due_date=past)
        self.engine.add_task("O2", due_date=past)
        self.engine.add_task("O3", due_date=past)
        self.engine.add_task("O4", due_date=past)
        self.engine.add_task("P1")
        self.assertEqual(overdue_risk_level(self.engine), "critical")


if __name__ == "__main__":
    unittest.main()
