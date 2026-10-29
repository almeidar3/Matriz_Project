import os
import secrets
import hmac

import click
from flask import Flask, jsonify, render_template, request, session

from db import close_db, get_db, init_db, seed_demo
from auth import auth_bp
from projects import projects_bp
from tasks import tasks_bp


def create_app(test_config=None):
    app = Flask(
        __name__,
        instance_path=os.path.join(os.path.dirname(os.path.abspath(__file__)), "instance"),
        instance_relative_config=True,
    )
    app.config.from_mapping(
        SECRET_KEY=os.environ.get("MATRIX_SECRET_KEY") or secrets.token_urlsafe(32),
        DATABASE=os.path.join(app.instance_path, "matriz.sqlite3"),
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax",
        SESSION_COOKIE_SECURE=os.environ.get("MATRIX_COOKIE_SECURE", "0") == "1",
        PERMANENT_SESSION_LIFETIME=60 * 60 * 8,
        MAX_CONTENT_LENGTH=1024 * 1024,
    )
    if test_config:
        app.config.update(test_config)

    os.makedirs(app.instance_path, exist_ok=True)
    if app.config["DATABASE"] != ":memory:":
        os.makedirs(os.path.dirname(app.config["DATABASE"]), exist_ok=True)

    app.teardown_appcontext(close_db)
    app.register_blueprint(auth_bp, url_prefix="/api/auth")
    app.register_blueprint(projects_bp, url_prefix="/api")
    app.register_blueprint(tasks_bp, url_prefix="/api")

    @app.before_request
    def protect_mutating_api_requests():
        if request.path.startswith("/api/") and request.method in {"POST", "PUT", "PATCH", "DELETE"}:
            expected = session.get("csrf_token", "")
            supplied = request.headers.get("X-CSRF-Token", "")
            if not expected or not supplied or not hmac.compare_digest(expected, supplied):
                return jsonify({"error": {"code": "csrf_failed", "message": "Token CSRF inválido ou ausente."}}), 400

    @app.errorhandler(404)
    def handle_not_found(error):
        if request.path.startswith("/api/"):
            return jsonify({"error": {"code": "not_found", "message": "Recurso não encontrado."}}), 404
        return error

    with app.app_context():
        init_db()

    @app.get("/")
    def index():
        return render_template("index.html")

    @app.get("/api/health")
    def health():
        get_db().execute("SELECT 1")
        return jsonify({"status": "ok"})

    @app.cli.command("seed-demo")
    def seed_demo_command():
        """Insert fictitious demo data without deleting existing rows."""
        seed_demo()
        click.echo("Demo data is ready. Existing data was preserved.")

    return app


if __name__ == "__main__":
    create_app().run(host="127.0.0.1", port=int(os.environ.get("PORT", "5000")), debug=False)