import secrets
from functools import wraps

from flask import Blueprint, g, jsonify, request, session

from db import get_db


auth_bp = Blueprint("auth", __name__)


def api_error(code, message, status):
    return jsonify({"error": {"code": code, "message": message}}), status


def require_auth(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        user_id = session.get("user_id")
        if user_id is None:
            return api_error("unauthorized", "Inicia sessão para continuar.", 401)
        user = get_db().execute(
            "SELECT id, username, email, name FROM user_account WHERE id = ?",
            (user_id,),
        ).fetchone()
        if user is None:
            session.clear()
            return api_error("unauthorized", "A sessão deixou de ser válida.", 401)
        g.current_user = user
        return view(*args, **kwargs)

    return wrapped


@auth_bp.get("/csrf")
def get_csrf_token():
    token = session.get("csrf_token")
    if token is None:
        token = secrets.token_urlsafe(32)
        session["csrf_token"] = token
    return jsonify({"csrfToken": token})


@auth_bp.post("/login")
def login():
    from werkzeug.security import check_password_hash

    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return api_error("invalid_json", "O corpo deve ser um objeto JSON.", 400)
    username = payload.get("username")
    password = payload.get("password")
    if not isinstance(username, str) or not isinstance(password, str):
        return api_error("validation_error", "Indica utilizador e palavra-passe.", 422)
    row = get_db().execute(
        "SELECT id, username, email, name, password_hash FROM user_account WHERE username = ?",
        (username.strip(),),
    ).fetchone()
    if row is None or not check_password_hash(row["password_hash"], password):
        return api_error("invalid_credentials", "Credenciais inválidas.", 401)
    session.clear()
    session["user_id"] = row["id"]
    session["csrf_token"] = secrets.token_urlsafe(32)
    session.permanent = True
    return jsonify({"user": serialize_user(row), "csrfToken": session["csrf_token"]})


@auth_bp.post("/logout")
@require_auth
def logout():
    session.clear()
    return "", 204


@auth_bp.get("/me")
@require_auth
def current_user():
    memberships = get_db().execute(
        """SELECT w.id, w.name, wm.role
           FROM workspace w JOIN workspace_member wm ON wm.workspace_id = w.id
           WHERE wm.user_id = ? ORDER BY w.name""",
        (g.current_user["id"],),
    ).fetchall()
    return jsonify({
        "user": serialize_user(g.current_user),
        "workspaces": [dict(row) for row in memberships],
    })


def serialize_user(user):
    return {
        "id": user["id"],
        "username": user["username"],
        "name": user["name"],
        "email": user["email"],
    }