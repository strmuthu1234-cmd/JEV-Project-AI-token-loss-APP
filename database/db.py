"""
SQLite database access layer for Jev AI Control Center.
Handles schema creation, seeding, and all read/write queries.
"""
import sqlite3
from datetime import datetime, date
from contextlib import contextmanager

from config.settings import DATABASE_PATH, DEFAULT_DEPARTMENTS, DEFAULT_PROJECTS, MONTHLY_AI_BUDGET


def get_connection():
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


@contextmanager
def get_cursor(commit=False):
    conn = get_connection()
    cur = conn.cursor()
    try:
        yield cur
        if commit:
            conn.commit()
    finally:
        conn.close()


SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    department TEXT,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS departments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS projects (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    department_id INTEGER,
    created_at TEXT NOT NULL,
    FOREIGN KEY (department_id) REFERENCES departments(id)
);

CREATE TABLE IF NOT EXISTS ai_requests (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    department TEXT,
    project TEXT,
    provider TEXT,
    model TEXT,
    prompt TEXT,
    response TEXT,
    complexity TEXT,
    route TEXT,
    human_review INTEGER DEFAULT 0,
    status TEXT,
    response_time REAL,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS token_usage (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    request_id INTEGER,
    input_tokens INTEGER,
    output_tokens INTEGER,
    total_tokens INTEGER,
    cached_tokens INTEGER DEFAULT 0,
    created_at TEXT NOT NULL,
    FOREIGN KEY (request_id) REFERENCES ai_requests(id)
);

CREATE TABLE IF NOT EXISTS cost_usage (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    request_id INTEGER,
    estimated_cost REAL,
    currency TEXT DEFAULT 'USD',
    created_at TEXT NOT NULL,
    FOREIGN KEY (request_id) REFERENCES ai_requests(id)
);

CREATE TABLE IF NOT EXISTS jev_decisions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    request_id INTEGER,
    complexity TEXT,
    route TEXT,
    confidence REAL,
    decision_source TEXT,
    created_at TEXT NOT NULL,
    FOREIGN KEY (request_id) REFERENCES ai_requests(id)
);

CREATE TABLE IF NOT EXISTS budgets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    department TEXT,
    monthly_budget REAL,
    month INTEGER,
    year INTEGER
);
"""


def init_db():
    """Create tables if they do not exist and seed default data."""
    with get_cursor(commit=True) as cur:
        cur.executescript(SCHEMA)

        # Seed departments
        for dept in DEFAULT_DEPARTMENTS:
            cur.execute(
                "INSERT OR IGNORE INTO departments (name) VALUES (?)", (dept,)
            )

        # Seed projects
        for project_name, dept_name in DEFAULT_PROJECTS:
            cur.execute("SELECT id FROM departments WHERE name = ?", (dept_name,))
            row = cur.fetchone()
            dept_id = row["id"] if row else None
            cur.execute(
                "SELECT id FROM projects WHERE name = ?", (project_name,)
            )
            if not cur.fetchone():
                cur.execute(
                    "INSERT INTO projects (name, department_id, created_at) VALUES (?, ?, ?)",
                    (project_name, dept_id, datetime.utcnow().isoformat()),
                )

        # Seed company-wide budget for current month if missing
        today = date.today()
        cur.execute(
            "SELECT id FROM budgets WHERE department = ? AND month = ? AND year = ?",
            ("__company__", today.month, today.year),
        )
        if not cur.fetchone():
            cur.execute(
                "INSERT INTO budgets (department, monthly_budget, month, year) VALUES (?, ?, ?, ?)",
                ("__company__", MONTHLY_AI_BUDGET, today.month, today.year),
            )


def get_departments():
    with get_cursor() as cur:
        cur.execute("SELECT * FROM departments ORDER BY name")
        return [dict(r) for r in cur.fetchall()]


def get_projects():
    with get_cursor() as cur:
        cur.execute(
            """
            SELECT p.id, p.name, p.created_at, d.name as department_name
            FROM projects p
            LEFT JOIN departments d ON p.department_id = d.id
            ORDER BY p.name
            """
        )
        return [dict(r) for r in cur.fetchall()]


def add_project(name, department_name):
    with get_cursor(commit=True) as cur:
        cur.execute("SELECT id FROM departments WHERE name = ?", (department_name,))
        row = cur.fetchone()
        dept_id = row["id"] if row else None
        cur.execute(
            "INSERT INTO projects (name, department_id, created_at) VALUES (?, ?, ?)",
            (name, dept_id, datetime.utcnow().isoformat()),
        )
        return cur.lastrowid


def create_ai_request(department, project, provider, model, prompt, response,
                       complexity, route, human_review, status, response_time):
    with get_cursor(commit=True) as cur:
        cur.execute(
            """
            INSERT INTO ai_requests
            (department, project, provider, model, prompt, response, complexity,
             route, human_review, status, response_time, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (department, project, provider, model, prompt, response, complexity,
             route, int(human_review), status, response_time, datetime.utcnow().isoformat()),
        )
        return cur.lastrowid


def add_token_usage(request_id, input_tokens, output_tokens, total_tokens, cached_tokens=0):
    with get_cursor(commit=True) as cur:
        cur.execute(
            """
            INSERT INTO token_usage
            (request_id, input_tokens, output_tokens, total_tokens, cached_tokens, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (request_id, input_tokens, output_tokens, total_tokens, cached_tokens,
             datetime.utcnow().isoformat()),
        )


def add_cost_usage(request_id, estimated_cost, currency="USD"):
    with get_cursor(commit=True) as cur:
        cur.execute(
            """
            INSERT INTO cost_usage (request_id, estimated_cost, currency, created_at)
            VALUES (?, ?, ?, ?)
            """,
            (request_id, estimated_cost, currency, datetime.utcnow().isoformat()),
        )


def add_jev_decision(request_id, complexity, route, confidence, decision_source):
    with get_cursor(commit=True) as cur:
        cur.execute(
            """
            INSERT INTO jev_decisions
            (request_id, complexity, route, confidence, decision_source, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (request_id, complexity, route, confidence, decision_source,
             datetime.utcnow().isoformat()),
        )


def get_company_budget():
    today = date.today()
    with get_cursor() as cur:
        cur.execute(
            "SELECT * FROM budgets WHERE department = ? AND month = ? AND year = ?",
            ("__company__", today.month, today.year),
        )
        row = cur.fetchone()
        return dict(row) if row else None


def set_company_budget(amount):
    today = date.today()
    with get_cursor(commit=True) as cur:
        cur.execute(
            "SELECT id FROM budgets WHERE department = ? AND month = ? AND year = ?",
            ("__company__", today.month, today.year),
        )
        row = cur.fetchone()
        if row:
            cur.execute("UPDATE budgets SET monthly_budget = ? WHERE id = ?", (amount, row["id"]))
        else:
            cur.execute(
                "INSERT INTO budgets (department, monthly_budget, month, year) VALUES (?, ?, ?, ?)",
                ("__company__", amount, today.month, today.year),
            )


def get_dashboard_summary():
    """Aggregate totals for dashboard top cards."""
    with get_cursor() as cur:
        cur.execute("SELECT COUNT(*) as c FROM ai_requests")
        total_requests = cur.fetchone()["c"]

        cur.execute("SELECT COALESCE(SUM(total_tokens), 0) as s FROM token_usage")
        total_tokens = cur.fetchone()["s"]

        cur.execute("SELECT COALESCE(SUM(estimated_cost), 0) as s FROM cost_usage")
        total_cost = cur.fetchone()["s"]

        cur.execute("SELECT COUNT(*) as c FROM jev_decisions")
        total_decisions = cur.fetchone()["c"]

        cur.execute("SELECT COUNT(*) as c FROM jev_decisions WHERE decision_source = 'demo'")
        demo_decisions = cur.fetchone()["c"]

        cur.execute("SELECT COUNT(*) as c FROM jev_decisions WHERE decision_source = 'real'")
        real_decisions = cur.fetchone()["c"]

    return {
        "total_requests": total_requests,
        "total_tokens": total_tokens,
        "total_cost": total_cost,
        "total_decisions": total_decisions,
        "demo_decisions": demo_decisions,
        "real_decisions": real_decisions,
    }


def get_provider_overview():
    with get_cursor() as cur:
        cur.execute(
            """
            SELECT r.provider,
                   COUNT(DISTINCT r.id) as requests,
                   COALESCE(SUM(t.total_tokens), 0) as tokens,
                   COALESCE(SUM(c.estimated_cost), 0) as cost
            FROM ai_requests r
            LEFT JOIN token_usage t ON t.request_id = r.id
            LEFT JOIN cost_usage c ON c.request_id = r.id
            GROUP BY r.provider
            """
        )
        return [dict(r) for r in cur.fetchall()]


def get_department_usage():
    with get_cursor() as cur:
        cur.execute(
            """
            SELECT r.department,
                   COUNT(DISTINCT r.id) as requests,
                   COALESCE(SUM(t.total_tokens), 0) as tokens,
                   COALESCE(SUM(c.estimated_cost), 0) as cost
            FROM ai_requests r
            LEFT JOIN token_usage t ON t.request_id = r.id
            LEFT JOIN cost_usage c ON c.request_id = r.id
            GROUP BY r.department
            ORDER BY cost DESC
            """
        )
        return [dict(r) for r in cur.fetchall()]


def get_project_usage():
    with get_cursor() as cur:
        cur.execute(
            """
            SELECT r.project, r.provider,
                   COUNT(DISTINCT r.id) as requests,
                   COALESCE(SUM(t.total_tokens), 0) as tokens,
                   COALESCE(SUM(c.estimated_cost), 0) as cost
            FROM ai_requests r
            LEFT JOIN token_usage t ON t.request_id = r.id
            LEFT JOIN cost_usage c ON c.request_id = r.id
            GROUP BY r.project, r.provider
            ORDER BY cost DESC
            """
        )
        return [dict(r) for r in cur.fetchall()]


def get_recent_activity(filters=None, limit=100):
    filters = filters or {}
    query = """
        SELECT r.id, r.created_at, r.department, r.project, r.provider, r.model,
               r.complexity, r.route, r.human_review, r.status,
               t.input_tokens, t.output_tokens, t.total_tokens,
               c.estimated_cost
        FROM ai_requests r
        LEFT JOIN token_usage t ON t.request_id = r.id
        LEFT JOIN cost_usage c ON c.request_id = r.id
        WHERE 1=1
    """
    params = []

    if filters.get("department"):
        query += " AND r.department = ?"
        params.append(filters["department"])
    if filters.get("project"):
        query += " AND r.project = ?"
        params.append(filters["project"])
    if filters.get("provider"):
        query += " AND r.provider = ?"
        params.append(filters["provider"])
    if filters.get("model"):
        query += " AND r.model = ?"
        params.append(filters["model"])
    if filters.get("complexity"):
        query += " AND r.complexity = ?"
        params.append(filters["complexity"])
    if filters.get("date"):
        query += " AND date(r.created_at) = ?"
        params.append(filters["date"])

    query += " ORDER BY r.created_at DESC LIMIT ?"
    params.append(limit)

    with get_cursor() as cur:
        cur.execute(query, params)
        return [dict(r) for r in cur.fetchall()]


def get_jev_decisions(limit=100):
    with get_cursor() as cur:
        cur.execute(
            """
            SELECT jd.*, r.department, r.project, r.provider, r.model
            FROM jev_decisions jd
            LEFT JOIN ai_requests r ON r.id = jd.request_id
            ORDER BY jd.created_at DESC
            LIMIT ?
            """,
            (limit,),
        )
        return [dict(r) for r in cur.fetchall()]


def get_distinct_values(column):
    allowed = {"department", "project", "provider", "model", "complexity"}
    if column not in allowed:
        return []
    with get_cursor() as cur:
        cur.execute(f"SELECT DISTINCT {column} FROM ai_requests WHERE {column} IS NOT NULL ORDER BY {column}")
        return [r[0] for r in cur.fetchall()]
