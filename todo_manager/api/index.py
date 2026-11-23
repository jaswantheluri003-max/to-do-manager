"""Vercel serverless entry point for CampusSolve To-Do Manager."""

from http.server import BaseHTTPRequestHandler
import json
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.engine import TaskEngine
from src.storage import DEFAULT_JSON_PATH
from src.models import Task

_engine = TaskEngine(json_path=DEFAULT_JSON_PATH)


def _task_to_dict(task: Task) -> dict:
    return task.to_dict()


class Handler(BaseHTTPRequestHandler):
    """Single serverless handler proxying /api/* to the TaskEngine."""

    def log_message(self, *args):  # noqa: ARG002
        pass

    def _read_body(self) -> dict:
        try:
            length = int(self.headers.get("Content-Length", 0))
            raw = self.rfile.read(length) if length else b"{}"
            return json.loads(raw.decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError, ValueError):
            return {}

    def _respond(self, status: int, payload: dict) -> None:
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    # ---- GET ----
    def do_GET(self):  # noqa: N802
        path = self.path.rstrip("/") or "/"

        if path == "/api/tasks":
            tasks = [_task_to_dict(t) for t in _engine.get_all_tasks()]
            self._respond(200, {"tasks": tasks})
            return

        if path == "/api/analytics":
            self._respond(200, _engine.get_summary())
            return

        if path == "/api/health":
            self._respond(200, {"status": "ok"})
            return

        self._respond(404, {"error": "not found"})

    # ---- POST ----
    def do_POST(self):  # noqa: N802
        path = self.path.rstrip("/")

        if path == "/api/tasks":
            data = self._read_body()
            try:
                task = _engine.add_task(
                    title=data.get("title", ""),
                    description=data.get("description", ""),
                    category=data.get("category", "General"),
                    priority=int(data.get("priority", 1)),
                    due_date=data.get("due_date") or None,
                )
                self._respond(201, {"task": _task_to_dict(task)})
            except ValueError as exc:
                self._respond(400, {"error": str(exc)})
            return

        self._respond(404, {"error": "not found"})

    # ---- PATCH ----
    def do_PATCH(self):  # noqa: N802
        path = self.path.rstrip("/")
        if path.startswith("/api/tasks/") and path.endswith("/complete"):
            task_id = path.split("/")[-2]
            if _engine.complete_task(task_id):
                task = _engine.get_task(task_id)
                self._respond(200, {"task": _task_to_dict(task)})
            else:
                self._respond(404, {"error": "task not found"})
            return
        self._respond(404, {"error": "not found"})

    # ---- DELETE ----
    def do_DELETE(self):  # noqa: N802
        path = self.path.rstrip("/")
        if path.startswith("/api/tasks/"):
            task_id = path.split("/")[-1]
            if _engine.delete_task(task_id):
                self._respond(200, {"deleted": task_id})
            else:
                self._respond(404, {"error": "task not found"})
            return
        self._respond(404, {"error": "not found"})

    # ---- OPTIONS (CORS preflight) ----
    def do_OPTIONS(self):  # noqa: N802
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, PATCH, DELETE, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()


# Vercel expects a top-level callable named `handler`
handler = Handler
