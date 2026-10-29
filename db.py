import os
import sqlite3

from flask import current_app, g
from werkzeug.security import generate_password_hash


SCHEMA = """
CREATE TABLE IF NOT EXISTS workspace (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS user_account (
    id INTEGER PRIMARY KEY,
    username TEXT NOT NULL UNIQUE,
    email TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL,
    password_hash TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
);

CREATE TABLE IF NOT EXISTS workspace_member (
    workspace_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    role TEXT NOT NULL CHECK (role IN ('admin', 'member')),
    PRIMARY KEY (workspace_id, user_id),
    FOREIGN KEY (workspace_id) REFERENCES workspace (id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES user_account (id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS project (
    id INTEGER PRIMARY KEY,
    workspace_id INTEGER NOT NULL,
    created_by_user_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    description TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    updated_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    UNIQUE (workspace_id, id),
    FOREIGN KEY (workspace_id) REFERENCES workspace (id) ON DELETE CASCADE,
    FOREIGN KEY (created_by_user_id) REFERENCES user_account (id)
);

CREATE TABLE IF NOT EXISTS task (
    id INTEGER PRIMARY KEY,
    workspace_id INTEGER NOT NULL,
    project_id INTEGER NOT NULL,
    title TEXT NOT NULL,
    description TEXT NOT NULL DEFAULT '',
    status TEXT NOT NULL DEFAULT 'TODO' CHECK (status IN ('TODO', 'IN_PROGRESS', 'DONE')),
    priority TEXT NOT NULL DEFAULT 'MEDIUM' CHECK (priority IN ('LOW', 'MEDIUM', 'HIGH')),
    due_date TEXT,
    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    updated_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    UNIQUE (workspace_id, id),
    FOREIGN KEY (workspace_id, project_id)
        REFERENCES project (workspace_id, id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS task_assignment (
    workspace_id INTEGER NOT NULL,
    task_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    assigned_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    PRIMARY KEY (task_id, user_id),
    FOREIGN KEY (workspace_id, task_id)
        REFERENCES task (workspace_id, id) ON DELETE CASCADE,
    FOREIGN KEY (workspace_id, user_id)
        REFERENCES workspace_member (workspace_id, user_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS comment (
    id INTEGER PRIMARY KEY,
    workspace_id INTEGER NOT NULL,
    task_id INTEGER NOT NULL,
    author_user_id INTEGER NOT NULL,
    content TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    FOREIGN KEY (workspace_id, task_id)
        REFERENCES task (workspace_id, id) ON DELETE CASCADE,
    FOREIGN KEY (workspace_id, author_user_id)
        REFERENCES workspace_member (workspace_id, user_id) ON DELETE RESTRICT
);

CREATE INDEX IF NOT EXISTS idx_project_workspace_name
    ON project (workspace_id, name);
CREATE INDEX IF NOT EXISTS idx_task_project_status_priority
    ON task (project_id, status, priority);
CREATE INDEX IF NOT EXISTS idx_comment_task_created
    ON comment (task_id, created_at);
"""


DEMO_USERS = (
    {
        "username": "ana",
        "email": "ana@example.test",
        "name": "Ana Silva",
        "password": "Matriz-demo-ana-2026",
        "workspace": "Equipa Produto",
        "role": "admin",
    },
    {
        "username": "bruno",
        "email": "bruno@example.test",
        "name": "Bruno Costa",
        "password": "Matriz-demo-bruno-2026",
        "workspace": "Equipa Produto",
        "role": "member",
    },
    {
        "username": "ines",
        "email": "ines@example.test",
        "name": "Ines Rocha",
        "password": "Matriz-demo-ines-2026",
        "workspace": "Equipa Design",
        "role": "admin",
    },
)


def get_db():
    if "db" not in g:
        connection = sqlite3.connect(current_app.config["DATABASE"])
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        connection.execute("PRAGMA busy_timeout = 5000")
        g.db = connection
    return g.db


def close_db(_error=None):
    connection = g.pop("db", None)
    if connection is not None:
        connection.close()


def init_db():
    connection = get_db()
    connection.executescript(SCHEMA)
    migrate_legacy_name_constraints(connection)
    connection.executescript(SCHEMA)


def migrate_legacy_name_constraints(connection):
    project_row = connection.execute(
        "SELECT sql FROM sqlite_master WHERE type = 'table' AND name = 'project'"
    ).fetchone()
    task_row = connection.execute(
        "SELECT sql FROM sqlite_master WHERE type = 'table' AND name = 'task'"
    ).fetchone()
    project_sql = " ".join((project_row["sql"] or "").lower().split())
    task_sql = " ".join((task_row["sql"] or "").lower().split())
    rebuild_project = "unique (workspace_id, name)" in project_sql
    rebuild_task = "unique (project_id, title)" in task_sql
    if not rebuild_project and not rebuild_task:
        return

    connection.commit()
    connection.execute("PRAGMA foreign_keys = OFF")
    try:
        connection.execute("BEGIN")
        if rebuild_project:
            connection.execute(
                """CREATE TABLE project_rebuild (
                    id INTEGER PRIMARY KEY,
                    workspace_id INTEGER NOT NULL,
                    created_by_user_id INTEGER NOT NULL,
                    name TEXT NOT NULL,
                    description TEXT NOT NULL DEFAULT '',
                    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
                    updated_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
                    UNIQUE (workspace_id, id),
                    FOREIGN KEY (workspace_id) REFERENCES workspace (id) ON DELETE CASCADE,
                    FOREIGN KEY (created_by_user_id) REFERENCES user_account (id)
                )"""
            )
            connection.execute(
                """INSERT INTO project_rebuild
                   (id, workspace_id, created_by_user_id, name, description, created_at, updated_at)
                   SELECT id, workspace_id, created_by_user_id, name, description, created_at, updated_at
                   FROM project"""
            )
            connection.execute("DROP TABLE project")
            connection.execute("ALTER TABLE project_rebuild RENAME TO project")
        if rebuild_task:
            connection.execute(
                """CREATE TABLE task_rebuild (
                    id INTEGER PRIMARY KEY,
                    workspace_id INTEGER NOT NULL,
                    project_id INTEGER NOT NULL,
                    title TEXT NOT NULL,
                    description TEXT NOT NULL DEFAULT '',
                    status TEXT NOT NULL DEFAULT 'TODO' CHECK (status IN ('TODO', 'IN_PROGRESS', 'DONE')),
                    priority TEXT NOT NULL DEFAULT 'MEDIUM' CHECK (priority IN ('LOW', 'MEDIUM', 'HIGH')),
                    due_date TEXT,
                    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
                    updated_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
                    UNIQUE (workspace_id, id),
                    FOREIGN KEY (workspace_id, project_id)
                        REFERENCES project (workspace_id, id) ON DELETE CASCADE
                )"""
            )
            connection.execute(
                """INSERT INTO task_rebuild
                   (id, workspace_id, project_id, title, description, status, priority, due_date, created_at, updated_at)
                   SELECT id, workspace_id, project_id, title, description, status, priority, due_date, created_at, updated_at
                   FROM task"""
            )
            connection.execute("DROP TABLE task")
            connection.execute("ALTER TABLE task_rebuild RENAME TO task")
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.execute("PRAGMA foreign_keys = ON")


def seed_demo():
    connection = get_db()
    legacy_demo = connection.execute(
        "SELECT id FROM user_account WHERE username = 'rita' AND email = 'rita@example.test'"
    ).fetchone()
    if legacy_demo is not None:
        connection.execute(
            """UPDATE user_account
               SET username = 'ines', email = 'ines@example.test', name = 'Ines Rocha', password_hash = ?
               WHERE id = ?""",
            (generate_password_hash("Matriz-demo-ines-2026"), legacy_demo["id"]),
        )
    for demo_user in DEMO_USERS:
        connection.execute(
            "INSERT OR IGNORE INTO workspace (name) VALUES (?)",
            (demo_user["workspace"],),
        )
        workspace = connection.execute(
            "SELECT id FROM workspace WHERE name = ?",
            (demo_user["workspace"],),
        ).fetchone()
        connection.execute(
            """INSERT OR IGNORE INTO user_account
               (username, email, name, password_hash) VALUES (?, ?, ?, ?)""",
            (
                demo_user["username"],
                demo_user["email"],
                demo_user["name"],
                generate_password_hash(demo_user["password"]),
            ),
        )
        user = connection.execute(
            "SELECT id FROM user_account WHERE username = ?",
            (demo_user["username"],),
        ).fetchone()
        connection.execute(
            """INSERT OR IGNORE INTO workspace_member
               (workspace_id, user_id, role) VALUES (?, ?, ?)""",
            (workspace["id"], user["id"], demo_user["role"]),
        )

    product_workspace = connection.execute(
        "SELECT id FROM workspace WHERE name = 'Equipa Produto'"
    ).fetchone()["id"]
    design_workspace = connection.execute(
        "SELECT id FROM workspace WHERE name = 'Equipa Design'"
    ).fetchone()["id"]
    ana_id = connection.execute(
        "SELECT id FROM user_account WHERE username = 'ana'"
    ).fetchone()["id"]
    ines_id = connection.execute(
        "SELECT id FROM user_account WHERE username = 'ines'"
    ).fetchone()["id"]

    product_project = connection.execute(
        "SELECT id FROM project WHERE workspace_id = ? AND name = 'Website institucional'",
        (product_workspace,),
    ).fetchone()
    if product_project is None:
        connection.execute(
            """INSERT INTO project
               (workspace_id, created_by_user_id, name, description)
               VALUES (?, ?, 'Website institucional', 'Projeto de demonstração da equipa Produto.')""",
            (product_workspace, ana_id),
        )
    design_project = connection.execute(
        "SELECT id FROM project WHERE workspace_id = ? AND name = 'Sistema visual'",
        (design_workspace,),
    ).fetchone()
    if design_project is None:
        connection.execute(
            """INSERT INTO project
               (workspace_id, created_by_user_id, name, description)
               VALUES (?, ?, 'Sistema visual', 'Projeto de demonstração da equipa Design.')""",
            (design_workspace, ines_id),
        )
    project_id = connection.execute(
        "SELECT id FROM project WHERE workspace_id = ? AND name = 'Website institucional'",
        (product_workspace,),
    ).fetchone()["id"]
    demo_tasks = (
        ("Preparar estrutura inicial", "Criar a base do projeto.", "IN_PROGRESS", "HIGH"),
        ("Rever requisitos", "Validar o âmbito com a equipa.", "TODO", "MEDIUM"),
    )
    for title, description, status, priority in demo_tasks:
        existing_task = connection.execute(
            "SELECT id FROM task WHERE project_id = ? AND title = ?",
            (project_id, title),
        ).fetchone()
        if existing_task is None:
            connection.execute(
                """INSERT INTO task
                   (workspace_id, project_id, title, description, status, priority)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (product_workspace, project_id, title, description, status, priority),
            )
    connection.commit()