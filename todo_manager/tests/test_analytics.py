import unittest
import tempfile
import os
import sys
from datetime import datetime, timedelta

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.engine import TaskEngine
from src.analytics import (
    completion_rate, category_breakdown, priority_breakdown,
    overdue_alerts, overdue_risk_level, avg_turnaround_hours,
    total_tasks,
)


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

    def test_empty_rate(self):
        self.assertEqual(completion_rate(self.engine), 0.0)

    def test_category_breakdown(self):
        self.engine.add_task("A", category="Work")
        self.engine.add_task("B", category="Work")
        self.engine.add_task("C", category="Personal")
        cb = category_breakdown(self.engine)
        self.assertEqual(cb["Work"], 2)
        self.assertEqual(cb["Personal"], 1)

    def test_priority_breakdown(self):
        self.engine.add_task("A", priority=5)
        self.engine.add_task("B", priority=5)
        self.engine.add_task("C", priority=2)
        pb = priority_breakdown(self.engine)
        self.assertEqual(pb[5], 2)
        self.assertEqual(pb[2], 1)

    def test_overdue_alerts(self):
        past = (datetime.now() - timedelta(days=2)).date().isoformat()
        future = (datetime.now() + timedelta(days=2)).date().isoformat()
        self.engine.add_task("Overdue", due_date=past)
        self.engine.add_task("Future", due_date=future)
        alerts = overdue_alerts(self.engine)
        self.assertEqual(len(alerts), 1)
        self.assertEqual(alerts[0].title, "Overdue")

    def test_overdue_risk_level(self):
        past = (datetime.now() - timedelta(days=1)).date().isoformat()
        for _ in range(4):
            self.engine.add_task("O", due_date=past)
        self.engine.add_task("P")
        self.assertEqual(overdue_risk_level(self.engine), "critical")

    def test_avg_turnaround(self):
        now = datetime.now()
        t = self.engine.add_task("A")
        t.created_at = (now - timedelta(hours=5)).isoformat()
        t.mark_complete()
        t.completed_at = now.isoformat()
        self.engine._save()
        hrs = avg_turnaround_hours(self.engine)
        self.assertAlmostEqual(hrs, 5.0, places=1)

    def test_total_tasks(self):
        self.assertEqual(total_tasks(self.engine), 0)
        self.engine.add_task("A")
        self.assertEqual(total_tasks(self.engine), 1)


if __name__ == "__main__":
    unittest.main()
