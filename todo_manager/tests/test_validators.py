import unittest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.validators import (
    validate_title, validate_description, validate_category,
    validate_priority, validate_due_date, validate_task_id,
    validate_search_query, validate_menu_bounds, is_valid_date,
)


class TestValidators(unittest.TestCase):
    def test_title(self):
        v, r = validate_title("Valid Title")
        self.assertTrue(v); self.assertEqual(r, "Valid Title")
        self.assertFalse(validate_title("")[0])
        self.assertFalse(validate_title("x" * 101)[0])

    def test_description(self):
        self.assertTrue(validate_description("desc")[0])
        self.assertFalse(validate_description("x" * 501)[0])

    def test_category(self):
        v, r = validate_category("work")
        self.assertTrue(v); self.assertEqual(r, "Work")
        self.assertFalse(validate_category("")[0])

    def test_priority(self):
        v, r = validate_priority("3")
        self.assertTrue(v); self.assertEqual(r, 3)
        self.assertFalse(validate_priority("0")[0])
        self.assertFalse(validate_priority("6")[0])
        self.assertFalse(validate_priority("abc")[0])

    def test_due_date(self):
        self.assertTrue(validate_due_date("2026-12-31")[0])
        self.assertTrue(validate_due_date("")[0])
        self.assertFalse(validate_due_date("bad")[0])
        self.assertTrue(is_valid_date("2026-12-31"))
        self.assertFalse(is_valid_date("nope"))

    def test_task_id(self):
        ids = {"a1", "b2"}
        self.assertTrue(validate_task_id("a1", ids)[0])
        self.assertFalse(validate_task_id("zz", ids)[0])

    def test_search_query(self):
        self.assertTrue(validate_search_query("q")[0])
        self.assertFalse(validate_search_query("")[0])

    def test_menu_bounds(self):
        self.assertTrue(validate_menu_bounds("3", 1, 5)[0])
        self.assertFalse(validate_menu_bounds("9", 1, 5)[0])
        self.assertFalse(validate_menu_bounds("x", 1, 5)[0])


if __name__ == "__main__":
    unittest.main()
