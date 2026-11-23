#!/usr/bin/env python3
"""
CampusSolve To-Do List Manager
Entry point with graceful shutdown (KeyboardInterrupt handling).
"""

import sys
import os

# Ensure the todo_manager package is importable when run from the project root.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.cli import run_app


if __name__ == "__main__":
    try:
        run_app()
    except KeyboardInterrupt:
        print("\n\nInterrupted by user. Goodbye!\n")
        sys.exit(0)
    except Exception as exc:  # noqa: BLE001
        print(f"\nFatal error: {exc}\n")
        import traceback
        traceback.print_exc()
        sys.exit(1)
