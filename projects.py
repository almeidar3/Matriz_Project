from functools import wraps

from flask import Blueprint, g, jsonify, request

from auth import api_error, require_auth
from db import get_db


projects_bp = Blueprint("projects", __name__)


def workspace_role(workspace_id):
    return get_db().execute(
        "SELECT role FROM workspace_member WHERE workspace_id = ? AND user_id = ?",
        (workspace_id, g.current_user["id"]),
    ).fetchone()


def accessible_project(project_id):
    return get_db().execute(
        """SELECT p.* FROM project p
           JOIN workspace_member wm ON wm.workspace_id = p.workspace_id
           WHERE p.id = ? AND wm.user_id = ?""",
        (project_id, g.current_user["id"]),
    ).fetchone()


def admin_required(view):
    @wraps(view)
    def wrapped(workspace_id, *args, **kwargs):
        membership = workspace_role(workspace_id)
        if membership is None:
            return api_error("not_found", "Recurso não encontrado.", 404)
        if membership["role"] != "admin":
            return api_error("forbidden", "É necessária a função de administrador.", 403)
        return view(workspace_id, *args, **kwargs)

    return wrapped


def serialize_project(project):
    return {
        "id": project["id"],
        "workspaceId": project["workspace_id"],
        "name": project["name"],
        "description": project["description"],
        "createdAt": project["created_at"],
        "updatedAt": project["updated_at"],
    }


def validate_project_payload(payload, partial=False):
    if not isinstance(payload, dict):
        return None, ("invalid_json", "O corpo deve ser um objeto JSON.", 400)
    allowed = {"name", "description"}
    if set(payload) - allowed:
        return None, ("validation_error", "O pedido contém campos desconhecidos.", 422)
    if not partial and "name" not in payload:
        return None, ("validation_error", "O nome é obrigatório.", 422)
    result = {}
    if "name" in payload:
        name = payload["name"]
        if not isinstance(name, str) or not 3 <= len(name.strip()) <= 100:
            return None, ("validation_error", "O nome deve ter entre 3 e 100 caracteres.", 422)
        result["name"] = name.strip()
    if "description" in payload:
        description = payload["description"]
        if not isinstance(description, str) or len(description) > 1000:
            return None, ("validation_error", "A descrição não pode exceder 1000 caracteres.", 422)
        result["description"] = description.strip()
    if partial and not result:
        return None, ("validation_error", "Indica pelo menos um campo para atualizar.", 422)
    return result, None


@projects_bp.get("/workspaces")
@require_auth
def list_workspaces():
    rows = get_db().execute(
        """SELECT w.id, w.name, wm.role FROM workspace w
           JOIN workspace_member wm ON wm.workspace_id = w.id
           WHERE wm.user_id = ? ORDER BY w.name""",
        (g.current_user["id"],),
    ).fetchall()
    return jsonify([dict(row) for row in rows])


@projects_bp.get("/workspaces/<int:workspace_id>/projects")
@require_auth
def list_projects(workspace_id):
    if workspace_role(workspace_id) is None:
        return api_error("not_found", "Recurso não encontrado.", 404)
    search = request.args.get("search", "").strip()
    try:
        page = max(1, int(request.args.get("page", "1")))
        page_size = min(100, max(1, int(request.args.get("pageSize", "50"))))
    except ValueError:
        return api_error("validation_error", "A paginação deve usar números inteiros.", 422)
    database = get_db()
    pattern = f"%{search}%"
    total = database.execute(
        "SELECT COUNT(*) FROM project WHERE workspace_id = ? AND name LIKE ?",
        (workspace_id, pattern),
    ).fetchone()[0]
    rows = database.execute(
        """SELECT * FROM project WHERE workspace_id = ? AND name LIKE ?
           ORDER BY name LIMIT ? OFFSET ?""",
        (workspace_id, pattern, page_size, (page - 1) * page_size),
    ).fetchall()
    return jsonify({
        "items": [serialize_project(row) for row in rows],
        "page": page,
        "pageSize": page_size,
        "total": total,
    })


@projects_bp.post("/workspaces/<int:workspace_id>/projects")
@require_auth
@admin_required
def create_project(workspace_id):
    payload, error = validate_project_payload(request.get_json(silent=True))
    if error:
        return api_error(*error)
    database = get_db()
    cursor = database.execute(
        """INSERT INTO project (workspace_id, created_by_user_id, name, description)
           VALUES (?, ?, ?, ?)""",
        (workspace_id, g.current_user["id"], payload["name"], payload.get("description", "")),
    )
    database.commit()
    project = database.execute("SELECT * FROM project WHERE id = ?", (cursor.lastrowid,)).fetchone()
    return jsonify(serialize_project(project)), 201


@projects_bp.get("/projects/<int:project_id>")
@require_auth
def get_project(project_id):
    project = accessible_project(project_id)
    if project is None:
        return api_error("not_found", "Recurso não encontrado.", 404)
    return jsonify(serialize_project(project))


@projects_bp.patch("/projects/<int:project_id>")
@require_auth
def update_project(project_id):
    project = accessible_project(project_id)
    if project is None:
        return api_error("not_found", "Recurso não encontrado.", 404)
    if workspace_role(project["workspace_id"])["role"] != "admin":
        return api_error("forbidden", "É necessária a função de administrador.", 403)
    payload, error = validate_project_payload(request.get_json(silent=True), partial=True)
    if error:
        return api_error(*error)
    updates = ", ".join(f"{field} = ?" for field in payload)
    values = list(payload.values()) + [project_id]
    database = get_db()
    database.execute(
        f"UPDATE project SET {updates}, updated_at = strftime('%Y-%m-%dT%H:%M:%fZ', 'now') WHERE id = ?",
        values,
    )
    database.commit()
    updated = get_db().execute("SELECT * FROM project WHERE id = ?", (project_id,)).fetchone()
    return jsonify(serialize_project(updated))


@projects_bp.delete("/projects/<int:project_id>")
@require_auth
def delete_project(project_id):
    project = accessible_project(project_id)
    if project is None:
        return api_error("not_found", "Recurso não encontrado.", 404)
    if workspace_role(project["workspace_id"])["role"] != "admin":
        return api_error("forbidden", "É necessária a função de administrador.", 403)
    database = get_db()
    database.execute("DELETE FROM project WHERE id = ?", (project_id,))
    database.commit()
    return "", 204


@projects_bp.get("/dashboard")
@require_auth
def dashboard():
    rows = get_db().execute(
        """SELECT p.id, p.workspace_id, p.name, p.description,
                  COUNT(t.id) AS task_count,
                  SUM(CASE WHEN t.status = 'TODO' THEN 1 ELSE 0 END) AS todo_count,
                  SUM(CASE WHEN t.status = 'IN_PROGRESS' THEN 1 ELSE 0 END) AS in_progress_count,
                  SUM(CASE WHEN t.status = 'DONE' THEN 1 ELSE 0 END) AS done_count
           FROM project p
           JOIN workspace_member wm ON wm.workspace_id = p.workspace_id AND wm.user_id = ?
           LEFT JOIN task t ON t.project_id = p.id
           GROUP BY p.id ORDER BY p.name""",
        (g.current_user["id"],),
    ).fetchall()
    return jsonify({
        "projects": [
            {
                "id": row["id"],
                "workspaceId": row["workspace_id"],
                "name": row["name"],
                "description": row["description"],
                "taskCount": row["task_count"],
                "counts": {
                    "TODO": row["todo_count"] or 0,
                    "IN_PROGRESS": row["in_progress_count"] or 0,
                    "DONE": row["done_count"] or 0,
                },
            }
            for row in rows
        ]
    })