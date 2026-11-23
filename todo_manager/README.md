# CampusSolve To-Do List Manager

Zero-dependency, production-grade CLI + web task manager for CampusSolve (Project #101). Python 3.10+, Standard Library only.

## Directory Structure

```text
todo_manager/
├── main.py                  # Entry point & graceful shutdown
├── web_server.py            # stdlib HTTP server + REST API (localhost:8000)
├── src/
│   ├── __init__.py
│   ├── models.py            # Task dataclass, Priority/Status enums
│   ├── validators.py        # Defensive input wrappers
│   ├── storage.py           # Atomic JSON, auto-recovery, CSV import/export
│   ├── engine.py            # Core business logic
│   ├── analytics.py         # Metrics, breakdowns, overdue risk
│   ├── exporter.py          # Markdown, CSV, plain-text audit log
│   └── cli.py               # ANSI TUI, paginated tables, menu loop
├── data/
│   ├── tasks.json           # Active datastore
│   └── seed_tasks.csv       # 40 sample tasks (incl. edge cases)
├── exports/                 # Generated reports
├── scripts/
│   └── seed_data.py         # Generate 40 sample tasks (JSON + CSV)
├── web/
│   ├── index.html           # Dark-mode luxury frontend
│   ├── styles.css           # Design tokens + layout
│   └── app.js               # API-driven SPA logic
└── tests/
    ├── test_engine.py
    ├── test_storage.py
    ├── test_validators.py
    └── test_analytics.py
```

## Quick Start

### CLI
```bash
cd todo_manager
python main.py
```

### Web Server + Frontend
```bash
cd todo_manager
python web_server.py
# Open http://localhost:8000
```

### Seed Data
```bash
python scripts/seed_data.py
```

### Run Tests
```bash
python -m unittest discover -s tests -v
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/tasks` | List tasks (q, category, priority, status, overdue_only) |
| POST | `/api/tasks` | Create a task |
| PATCH | `/api/tasks/<id>/complete` | Mark complete |
| DELETE | `/api/tasks/<id>` | Delete a task |
| GET | `/api/analytics` | Executive summary metrics |
| POST | `/api/import-csv` | Bulk CSV import (file upload) |
| GET | `/api/export/:format` | Export (md, csv, txt) |
| GET | `/api/health` | Health check |

## Features

- Atomic JSON writes with `.bak` auto-recovery
- Schema validation on read/write
- Priority (1–5) & Status enums
- Overdue detection & risk leveling
- Completion rate, category & priority breakdown
- Avg turnaround time
- Markdown / CSV / plain-text export
- CSV bulk import with row-by-row error log
- Dark-mode editorial web UI (IntersectionObserver reveal, responsive to 1024px)
- Zero `pip` dependencies

## Validation Rules

- Title: 1–100 chars, required
- Description: max 300 chars
- Category: max 30 chars
- Priority: integer 1–5
- Due date: YYYY-MM-DD or empty

## License

Internal CampusSolve productivity tool.
