import os
import tempfile
import unittest

from app import create_app
from db import DEMO_USERS, get_db, seed_demo


class TaskCreationIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.database_path = os.path.join(self.temporary_directory.name, "tasks.sqlite3")
        self.app = create_app({
            "TESTING": True,
            "DATABASE": self.database_path,
            "SECRET_KEY": "integration-test-only",
        })
        with self.app.app_context():
            seed_demo()
        self.ana_client, self.ana_csrf = self._authenticated_client(self.app, "ana")

    def tearDown(self):
        self.temporary_directory.cleanup()

    def _authenticated_client(self, app, username):
        client = app.test_client()
        csrf = client.get("/api/auth/csrf").get_json()["csrfToken"]
        user = next(user for user in DEMO_USERS if user["username"] == username)
        login = client.post(
            "/api/auth/login",
            json={"username": username, "password": user["password"]},
            headers={"X-CSRF-Token": csrf},
        )
        self.assertEqual(login.status_code, 200, login.get_json())
        return client, login.get_json()["csrfToken"]

    def _task_count(self):
        with self.app.app_context():
            return get_db().execute("SELECT COUNT(*) FROM task").fetchone()[0]

    def test_create_and_read_task_from_a_new_app_instance(self):
        response = self.ana_client.post(
            "/api/projects/1/tasks",
            json={
                "title": "Tarefa de integração",
                "description": "Criada e consultada pela API.",
                "dueDate": "2026-11-30",
            },
            headers={"X-CSRF-Token": self.ana_csrf},
        )

        self.assertEqual(response.status_code, 201, response.get_json())
        created = response.get_json()
        self.assertTrue({
            "id", "workspaceId", "projectId", "title", "description",
            "status", "priority", "assignees",
        }.issubset(created))
        self.assertEqual(created["projectId"], 1)
        self.assertEqual(created["title"], "Tarefa de integração")
        self.assertEqual(created["description"], "Criada e consultada pela API.")
        self.assertEqual(created["status"], "TODO")
        self.assertEqual(created["priority"], "MEDIUM")
        self.assertEqual(created["dueDate"], "2026-11-30")
        self.assertEqual(created["assignees"], [])

        restarted_app = create_app({
            "TESTING": True,
            "DATABASE": self.database_path,
            "SECRET_KEY": "integration-test-only",
        })
        restarted_client, _ = self._authenticated_client(restarted_app, "ana")
        read_back = restarted_client.get(f"/api/tasks/{created['id']}")

        self.assertEqual(read_back.status_code, 200, read_back.get_json())
        self.assertEqual(read_back.get_json(), created)

    def test_invalid_title_returns_validation_error_without_persisting(self):
        task_count_before = self._task_count()
        response = self.ana_client.post(
            "/api/projects/1/tasks",
            json={"title": "   "},
            headers={"X-CSRF-Token": self.ana_csrf},
        )

        self.assertEqual(response.status_code, 422)
        self.assertEqual(response.get_json()["error"]["code"], "validation_error")
        self.assertEqual(self._task_count(), task_count_before)

    def test_other_workspace_user_cannot_read_or_change_task(self):
        created = self.ana_client.post(
            "/api/projects/1/tasks",
            json={"title": "Privada da Equipa Produto"},
            headers={"X-CSRF-Token": self.ana_csrf},
        )
        self.assertEqual(created.status_code, 201, created.get_json())
        task_id = created.get_json()["id"]
        ines_client, ines_csrf = self._authenticated_client(self.app, "ines")

        read_other_task = ines_client.get(f"/api/tasks/{task_id}")
        change_other_task = ines_client.patch(
            f"/api/tasks/{task_id}",
            json={"title": "Alteração não autorizada"},
            headers={"X-CSRF-Token": ines_csrf},
        )
        create_in_other_workspace = ines_client.post(
            "/api/projects/1/tasks",
            json={"title": "Criação não autorizada"},
            headers={"X-CSRF-Token": ines_csrf},
        )

        self.assertEqual(read_other_task.status_code, 404)
        self.assertEqual(change_other_task.status_code, 404)
        self.assertEqual(create_in_other_workspace.status_code, 404)
        self.assertEqual(self.ana_client.get(f"/api/tasks/{task_id}").get_json()["title"], "Privada da Equipa Produto")

    def test_authorized_workspace_member_can_create_task(self):
        bruno_client, bruno_csrf = self._authenticated_client(self.app, "bruno")
        response = bruno_client.post(
            "/api/projects/1/tasks",
            json={"title": "Tarefa criada por membro"},
            headers={"X-CSRF-Token": bruno_csrf},
        )

        self.assertEqual(response.status_code, 201, response.get_json())
        self.assertEqual(response.get_json()["title"], "Tarefa criada por membro")

    def test_nonexistent_project_is_not_disclosed(self):
        response = self.ana_client.post(
            "/api/projects/9999/tasks",
            json={"title": "Projeto inexistente"},
            headers={"X-CSRF-Token": self.ana_csrf},
        )

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.get_json()["error"]["code"], "not_found")


if __name__ == "__main__":
    unittest.main()