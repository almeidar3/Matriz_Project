import os
import tempfile
import threading
import unittest

from werkzeug.serving import make_server

from app import create_app
from db import DEMO_USERS, seed_demo
from playwright.sync_api import expect, sync_playwright


class TaskCreationE2ETests(unittest.TestCase):
    def setUp(self):
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary_directory.cleanup)
        app = create_app({
            "TESTING": True,
            "DATABASE": os.path.join(self.temporary_directory.name, "e2e.sqlite3"),
            "SECRET_KEY": "e2e-test-only",
        })
        with app.app_context():
            seed_demo()

        self.server = make_server("127.0.0.1", 0, app)
        self.server_thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.server_thread.start()
        self.addCleanup(self.server_thread.join, 5)
        self.addCleanup(self.server.shutdown)
        self.base_url = f"http://127.0.0.1:{self.server.server_port}"

        self.playwright = sync_playwright().start()
        self.addCleanup(self.playwright.stop)
        self.browser = self.playwright.chromium.launch(headless=True)
        self.addCleanup(self.browser.close)
        self.context = self.browser.new_context()
        self.addCleanup(self.context.close)
        self.context.tracing.start(screenshots=True, snapshots=True, sources=True)
        self.page = self.context.new_page()

    def test_user_can_login_open_project_create_task_and_see_it_in_list(self):
        try:
            demo_user = next(user for user in DEMO_USERS if user["username"] == "ana")
            self.page.goto(self.base_url)
            self.page.locator("#username").fill(demo_user["username"])
            self.page.locator("#password").fill(demo_user["password"])
            self.page.locator('#login-form button[type="submit"]').click()
            expect(self.page.locator("#app-shell")).to_be_visible()

            self.page.locator('#project-nav [data-project-id="1"]').click()
            expect(self.page.get_by_role("heading", name="Website institucional")).to_be_visible()
            self.page.locator('#main-content [data-action="new-task"]').click()
            title = "Fluxo E2E da Ficha 04"
            self.page.locator("#task-title").fill(title)
            self.page.locator('#task-form button[type="submit"]').click()
            expect(self.page.locator("#task-list").get_by_role("heading", name=title)).to_be_visible()
        except Exception:
            artifact_directory = tempfile.mkdtemp(prefix="matriz-e2e-failure-")
            self.page.screenshot(path=os.path.join(artifact_directory, "failure.png"), full_page=True)
            self.context.tracing.stop(path=os.path.join(artifact_directory, "trace.zip"))
            self.fail(f"E2E falhou; screenshot e trace guardados em {artifact_directory}")
        else:
            self.context.tracing.stop()


if __name__ == "__main__":
    unittest.main()