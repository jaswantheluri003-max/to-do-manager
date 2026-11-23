#!/usr/bin/env python3
"""
CampusSolve To-Do List Manager — zero-dependency HTTP server.
Serves the web/ frontend and exposes a JSON REST API backed by src/ modules.
Run:  python web_server.py   (serves http://localhost:8000)
"""

from __future__ import annotations

import csv
import io
import json
import mimetypes
import os
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse, parse_qs

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.engine import TaskEngine
from src.storage import (
    DEFAULT_JSON_PATH, import_csv_bulk, load_tasks_json, save_tasks_json,
)
from src.exporter import export_markdown, export_csv, export_audit_log
from src.models import Task

WEB_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "web")
PORT = 8000
HOST = "127.0.0.1"

_engine = TaskEngine(json_path=DEFAULT_JSON_PATH)


def _json_response(handler: BaseHTTPRequestHandler, status: int, payload: dict) -> None:
    body = json.dumps(payload).encode("utf-8")
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json; charset=utf-8")
    handler.send_header("Content-Length", str(len(body)))
    handler.send_header("Access-Control-Allow-Origin", "*")
    handler.end_headers()
    handler.wfile.write(body)


def _task_to_dict(task: Task) -> dict:
    return task.to_dict()


class APIHandler(BaseHTTPRequestHandler):
    server_version = "CampusSolve/1.0"

    def log_message(self, fmt, *args):  # noqa: ARG002
        pass  # keep console quiet

    def _read_body(self) -> dict:
        length = int(self.headers.get("Content-Length", 0))
        raw = self.rfile.read(length) if length else b"{}"
        try:
            return json.loads(raw.decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError):
            return {}

    def _tasks_list(self) -> list[dict]:
        return [_task_to_dict(t) for t in _engine.get_all_tasks()]

    # ---- routing ----
    def do_GET(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        path = parsed.path.rstrip("/") or "/"
        params = parse_qs(parsed.query)

        if path == "/api/tasks":
            tasks = _engine.get_all_tasks()
            q = params.get("q", [None])[0]
            category = params.get("category", [None])[0]
            priority = params.get("priority", [None])[0]
            status = params.get("status", [None])[0]
            overdue_only = params.get("overdue_only", ["false"])[0].lower() == "true"

            if q:
                tasks = _engine.search_tasks(q, category)
            elif category:
                tasks = _engine.filter_by_category(category)
            elif status == "completed":
                tasks = _engine.get_completed_tasks()
            elif status == "pending":
                tasks = _engine.get_pending_tasks()

            if priority is not None:
                try:
                    tasks = [t for t in tasks if t.priority == int(priority)]
                except ValueError:
                    pass

            if overdue_only:
                tasks = _engine.filter_overdue()

            _json_response(self, 200, {"tasks": [_task_to_dict(t) for t in tasks]})
            return

        if path == "/api/analytics":
            _json_response(self, 200, _engine.get_summary())
            return

        if path == "/api/health":
            _json_response(self, 200, {"status": "ok"})
            return

        if path.startswith("/api/export/"):
            fmt = path.rsplit("/", 1)[-1]
            tasks = _engine.get_all_tasks()
            if fmt == "md":
                out_path = os.path.join(os.path.dirname(DEFAULT_JSON_PATH), "report.md")
                export_markdown(tasks, out_path)
                _json_response(self, 200, {"format": "md", "path": out_path})
            elif fmt == "csv":
                out_path = os.path.join(os.path.dirname(DEFAULT_JSON_PATH), "tasks_export.csv")
                export_csv(tasks, out_path)
                _json_response(self, 200, {"format": "csv", "path": out_path})
            elif fmt == "txt":
                out_path = os.path.join(os.path.dirname(DEFAULT_JSON_PATH), "report.txt")
                export_audit_log(tasks, out_path)
                _json_response(self, 200, {"format": "txt", "path": out_path})
            else:
                _json_response(self, 400, {"error": "Unsupported export format. Use md, csv, or txt."})
            return

        # static file serving
        self._serve_static(parsed.path)
        return

    def do_POST(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        path = parsed.path.rstrip("/") or "/"

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
                _json_response(self, 201, {"task": _task_to_dict(task)})
            except ValueError as exc:
                _json_response(self, 400, {"error": str(exc)})
            return

        if path == "/api/import-csv":
            data = self._read_body()
            filepath = data.get("filepath") or DEFAULT_JSON_PATH.replace(".json", "_import.csv")
            imported, errors = import_csv_bulk(filepath)
            _json_response(self, 200, {"imported": imported, "errors": errors})
            return

        _json_response(self, 404, {"error": "Not found."})

    def do_PATCH(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        path = parsed.path.rstrip("/")
        if path.startswith("/api/tasks/") and path.endswith("/complete"):
            task_id = path.split("/")[-2]
            if _engine.complete_task(task_id):
                task = _engine.get_task(task_id)
                _json_response(self, 200, {"task": _task_to_dict(task)})
            else:
                _json_response(self, 404, {"error": "Task not found."})
            return
        _json_response(self, 404, {"error": "Not found."})

    def do_DELETE(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        path = parsed.path.rstrip("/")
        if path.startswith("/api/tasks/"):
            task_id = path.split("/")[-1]
            if _engine.delete_task(task_id):
                _json_response(self, 200, {"deleted": task_id})
            else:
                _json_response(self, 404, {"error": "Task not found."})
            return
        _json_response(self, 404, {"error": "Not found."})

    def do_OPTIONS(self) -> None:  # noqa: N802
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, PATCH, DELETE, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def _serve_static(self, req_path: str) -> None:
        if req_path == "/" or req_path == "":
            req_path = "/index.html"
        file_path = os.path.join(WEB_DIR, req_path.lstrip("/"))
        if not os.path.isfile(file_path):
            file_path = os.path.join(WEB_DIR, "index.html")
        try:
            with open(file_path, "rb") as f:
                content = f.read()
            content_type, _ = mimetypes.guess_type(file_path)
            self.send_response(200)
            self.send_header("Content-Type", content_type or "application/octet-stream")
            self.send_header("Content-Length", str(len(content)))
            self.end_headers()
            self.wfile.write(content)
        except OSError:
            self.send_response(404)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.end_headers()
            self.wfile.write(b"Not found")


def main() -> None:
    server = ThreadingHTTPServer((HOST, PORT), APIHandler)
    print(f"CampusSolve API server running at http://{HOST}:{PORT}")
    print(f"Data store: {DEFAULT_JSON_PATH}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down server...")
        server.shutdown()


if __name__ == "__main__":
    main()
