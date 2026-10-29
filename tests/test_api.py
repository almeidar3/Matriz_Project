import os
import tempfile
import unittest

from app import create_app
from db import get_db, init_db, seed_demo
from werkzeug.security import generate_password_hash


class MatrixApiTests(unittest.TestCase):
    def setUp(self):
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.database_path = os.path.join(self.temporary_directory.name, "test.sqlite3")
        self.app = create_app({
            "TESTING": True,
            "DATABASE": self.database_path,
            "SECRET_KEY": "test-secret",
        })
        with self.app.app_context():
            seed_demo()
        self.client = self.app.test_client()
        self.csrf_token = self._login("ana", "Matriz-demo-ana-2026")

    def tearDown(self):
        self.temporary_directory.cleanup()

    def _login(self, username, password):
        token = self.client.get("/api/auth/csrf").get_json()["csrfToken"]
        response = self.client.post(
            "/api/auth/login",
            json={"username": username, "password": password},
            headers={"X-CSRF-Token": token},
        )
        if response.status_code == 200:
            self.csrf_token = response.get_json()["csrfToken"]
            return self.csrf_token
        return token

    def _headers(self):
        return {"X-CSRF-Token": self.csrf_token}

    def test_invalid_task_title_is_rejected(self):
        response = self.client.post(
            "/api/projects/1/tasks",
            json={"title": "   "},
            headers=self._headers(),
        )
        self.assertEqual(response.status_code, 422)
        self.assertEqual(response.get_json()["error"]["code"], "validation_error")

    def test_invalid_task_status_type_is_rejected(self):
        response = self.client.post(
            "/api/projects/1/tasks",
            json={"title": "Estado inválido", "status": []},
            headers=self._headers(),
        )
        self.assertEqual(response.status_code, 422)

    def test_project_crud_is_restricted_to_workspace_admin(self):
        member_client = self.app.test_client()
        token = member_client.get("/api/auth/csrf").get_json()["csrfToken"]
        login = member_client.post(
            "/api/auth/login",
            json={"username": "bruno", "password": "Matriz-demo-bruno-2026"},
            headers={"X-CSRF-Token": token},
        )
        self.assertEqual(login.status_code, 200)
        forbidden = member_client.post(
            "/api/workspaces/1/projects",
            json={"name": "Sem permissão"},
            headers={"X-CSRF-Token": login.get_json()["csrfToken"]},
        )
        self.assertEqual(forbidden.status_code, 403)

        created = self.client.post(
            "/api/workspaces/1/projects",
            json={"name": "Projeto de teste"},
            headers=self._headers(),
        )
        self.assertEqual(created.status_code, 201)
        project_id = created.get_json()["id"]
        updated = self.client.patch(
            f"/api/projects/{project_id}",
            json={"description": "Descrição atualizada"},
            headers=self._headers(),
        )
        self.assertEqual(updated.status_code, 200)
        self.assertEqual(updated.get_json()["description"], "Descrição atualizada")
        deleted = self.client.delete(
            f"/api/projects/{project_id}",
            headers=self._headers(),
        )
        self.assertEqual(deleted.status_code, 204)

    def test_other_workspace_resources_are_not_disclosed(self):
        response = self.client.get("/api/projects/2")
        self.assertEqual(response.status_code, 404)

    def test_task_creation_persists_after_new_app_instance(self):
        response = self.client.post(
            "/api/projects/1/tasks",
            json={"title": "Persistir tarefa", "priority": "HIGH"},
            headers=self._headers(),
        )
        self.assertEqual(response.status_code, 201, response.get_json())
        task_id = response.get_json()["id"]

        restarted_app = create_app({
            "TESTING": True,
            "DATABASE": self.database_path,
            "SECRET_KEY": "test-secret",
        })
        restarted_client = restarted_app.test_client()
        token = restarted_client.get("/api/auth/csrf").get_json()["csrfToken"]
        login = restarted_client.post(
            "/api/auth/login",
            json={"username": "ana", "password": "Matriz-demo-ana-2026"},
            headers={"X-CSRF-Token": token},
        )
        self.assertEqual(login.status_code, 200)
        found = restarted_client.get(f"/api/tasks/{task_id}")
        self.assertEqual(found.status_code, 200)
        self.assertEqual(found.get_json()["title"], "Persistir tarefa")

    def test_assignment_is_idempotent_and_comment_author_is_server_derived(self):
        created = self.client.post(
            "/api/projects/1/tasks",
            json={"title": "Colaboração"},
            headers=self._headers(),
        )
        task_id = created.get_json()["id"]
        first = self.client.put(
            f"/api/tasks/{task_id}/assignments/2",
            headers=self._headers(),
        )
        second = self.client.put(
            f"/api/tasks/{task_id}/assignments/2",
            headers=self._headers(),
        )
        self.assertEqual(first.status_code, 201)
        self.assertEqual(second.status_code, 200)
        cross_workspace = self.client.put(
            f"/api/tasks/{task_id}/assignments/3",
            headers=self._headers(),
        )
        self.assertEqual(cross_workspace.status_code, 404)

        forged = self.client.post(
            f"/api/tasks/{task_id}/comments",
            json={"content": "Comentário", "authorId": 3},
            headers=self._headers(),
        )
        self.assertEqual(forged.status_code, 400)
        comment = self.client.post(
            f"/api/tasks/{task_id}/comments",
            json={"content": "Comentário da equipa"},
            headers=self._headers(),
        )
        self.assertEqual(comment.status_code, 201)
        self.assertEqual(comment.get_json()["author"]["name"], "Ana Silva")

    def test_mutating_api_requires_csrf_and_authentication(self):
        anonymous = self.app.test_client()
        response = anonymous.get("/api/dashboard")
        self.assertEqual(response.status_code, 401)
        csrf = anonymous.get("/api/auth/csrf").get_json()["csrfToken"]
        login_without_csrf = anonymous.post(
            "/api/auth/login",
            json={"username": "ana", "password": "Matriz-demo-ana-2026"},
        )
        self.assertEqual(login_without_csrf.status_code, 400)
        self.assertTrue(csrf)

    def test_invalid_login_and_logout_invalidate_session(self):
        client = self.app.test_client()
        csrf = client.get("/api/auth/csrf").get_json()["csrfToken"]
        invalid = client.post(
            "/api/auth/login",
            json={"username": "ana", "password": "incorrecta"},
            headers={"X-CSRF-Token": csrf},
        )
        self.assertEqual(invalid.status_code, 401)

        csrf = client.get("/api/auth/csrf").get_json()["csrfToken"]
        login = client.post(
            "/api/auth/login",
            json={"username": "ana", "password": "Matriz-demo-ana-2026"},
            headers={"X-CSRF-Token": csrf},
        )
        self.assertEqual(login.status_code, 200)
        self.assertEqual(client.get("/api/auth/me").status_code, 200)
        logout = client.post(
            "/api/auth/logout",
            headers={"X-CSRF-Token": login.get_json()["csrfToken"]},
        )
        self.assertEqual(logout.status_code, 204)
        self.assertEqual(client.get("/api/auth/me").status_code, 401)

    def test_seed_migrates_legacy_demo_identity_without_deleting_projects(self):
        legacy_database = os.path.join(self.temporary_directory.name, "legacy.sqlite3")
        legacy_app = create_app({
            "TESTING": True,
            "DATABASE": legacy_database,
            "SECRET_KEY": "test-secret",
        })
        with legacy_app.app_context():
            connection = get_db()
            connection.execute("INSERT INTO workspace (id, name) VALUES (2, 'Equipa Design')")
            connection.execute(
                """INSERT INTO user_account
                   (id, username, email, name, password_hash)
                   VALUES (3, 'rita', 'rita@example.test', 'Rita Almeida', ?)""",
                (generate_password_hash("Matriz-demo-rita-2026"),),
            )
            connection.execute(
                "INSERT INTO workspace_member (workspace_id, user_id, role) VALUES (2, 3, 'admin')"
            )
            connection.execute(
                """INSERT INTO project (id, workspace_id, created_by_user_id, name)
                   VALUES (9, 2, 3, 'Projeto preexistente')"""
            )
            connection.commit()
            seed_demo()
            user = connection.execute(
                "SELECT id, username, name FROM user_account WHERE username = 'ines'"
            ).fetchone()
            self.assertEqual((user["id"], user["name"]), (3, "Ines Rocha"))
            self.assertEqual(
                connection.execute("SELECT COUNT(*) FROM user_account WHERE username = 'rita'").fetchone()[0],
                0,
            )
            self.assertEqual(
                connection.execute("SELECT COUNT(*) FROM project WHERE name = 'Projeto preexistente'").fetchone()[0],
                1,
            )

    def test_legacy_unique_name_constraints_migrate_without_data_loss(self):
        legacy_database = os.path.join(self.temporary_directory.name, "unique-legacy.sqlite3")
        legacy_app = create_app({
            "TESTING": True,
            "DATABASE": legacy_database,
            "SECRET_KEY": "test-secret",
        })
        with legacy_app.app_context():
            connection = get_db()
            connection.execute("PRAGMA foreign_keys = OFF")
            connection.executescript(
                """
                DROP TABLE comment;
                DROP TABLE task_assignment;
                DROP TABLE task;
                DROP TABLE project;
                CREATE TABLE project (
                    id INTEGER PRIMARY KEY,
                    workspace_id INTEGER NOT NULL,
                    created_by_user_id INTEGER NOT NULL,
                    name TEXT NOT NULL,
                    description TEXT NOT NULL DEFAULT '',
                    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
                    updated_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
                    UNIQUE (workspace_id, id),
                    UNIQUE (workspace_id, name),
                    FOREIGN KEY (workspace_id) REFERENCES workspace (id) ON DELETE CASCADE,
                    FOREIGN KEY (created_by_user_id) REFERENCES user_account (id)
                );
                CREATE TABLE task (
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
                    UNIQUE (project_id, title),
                    FOREIGN KEY (workspace_id, project_id)
                        REFERENCES project (workspace_id, id) ON DELETE CASCADE
                );
                CREATE TABLE task_assignment (
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
                CREATE TABLE comment (
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
                """
            )
            connection.execute("PRAGMA foreign_keys = ON")
            seed_demo()
            project = connection.execute(
                "SELECT id, workspace_id FROM project WHERE name = 'Website institucional'"
            ).fetchone()
            task = connection.execute(
                "SELECT id, workspace_id FROM task WHERE title = 'Rever requisitos'"
            ).fetchone()
            bruno = connection.execute(
                "SELECT id FROM user_account WHERE username = 'bruno'"
            ).fetchone()["id"]
            connection.execute(
                "INSERT INTO task_assignment (workspace_id, task_id, user_id) VALUES (?, ?, ?)",
                (task["workspace_id"], task["id"], bruno),
            )
            connection.execute(
                "INSERT INTO comment (workspace_id, task_id, author_user_id, content) VALUES (?, ?, 1, 'Preservado')",
                (task["workspace_id"], task["id"]),
            )
            connection.commit()

            init_db()

            duplicate_project = connection.execute(
                """INSERT INTO project (workspace_id, created_by_user_id, name)
                   VALUES (?, 1, 'Website institucional')""",
                (project["workspace_id"],),
            )
            duplicate_task = connection.execute(
                """INSERT INTO task (workspace_id, project_id, title)
                   VALUES (?, ?, 'Rever requisitos')""",
                (task["workspace_id"], project["id"]),
            )
            self.assertIsNotNone(duplicate_project.lastrowid)
            self.assertIsNotNone(duplicate_task.lastrowid)
            self.assertEqual(
                connection.execute("SELECT COUNT(*) FROM task_assignment WHERE task_id = ?", (task["id"],)).fetchone()[0],
                1,
            )
            self.assertEqual(
                connection.execute("SELECT content FROM comment WHERE task_id = ?", (task["id"],)).fetchone()[0],
                "Preservado",
            )
            self.assertEqual(connection.execute("PRAGMA foreign_key_check").fetchall(), [])


if __name__ == "__main__":
    unittest.main()