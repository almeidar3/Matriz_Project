from datetime import date

from flask import Blueprint, g, jsonify, request

from auth import api_error, require_auth, serialize_user
from db import get_db
from projects import accessible_project


tasks_bp = Blueprint("tasks", __name__)
TASK_STATES = {"TODO", "IN_PROGRESS", "DONE"}
TASK_PRIORITIES = {"LOW", "MEDIUM", "HIGH"}


def accessible_task(task_id):
    return get_db().execute(
        """SELECT t.* FROM task t
           JOIN workspace_member wm ON wm.workspace_id = t.workspace_id
           WHERE t.id = ? AND wm.user_id = ?""",
        (task_id, g.current_user["id"]),
    ).fetchone()


def task_assignees(task_id):
    rows = get_db().execute(
        """SELECT u.id, u.username, u.name, u.email FROM user_account u
           JOIN task_assignment ta ON ta.user_id = u.id
           WHERE ta.task_id = ? ORDER BY u.name""",
        (task_id,),
    ).fetchall()
    return [serialize_user(row) for row in rows]


def serialize_task(task):
    return {
        "id": task["id"],
        "workspaceId": task["workspace_id"],
        "projectId": task["project_id"],
        "title": task["title"],
        "description": task["description"],
        "status": task["status"],
        "priority": task["priority"],
        "dueDate": task["due_date"],
        "createdAt": task["created_at"],
        "updatedAt": task["updated_at"],
        "assignees": task_assignees(task["id"]),
    }


def validate_task_payload(payload, partial=False):
    if not isinstance(payload, dict):
        return None, ("invalid_json", "O corpo deve ser um objeto JSON.", 400)
    allowed = {"title", "description", "status", "priority", "dueDate"}
    if set(payload) - allowed:
        return None, ("validation_error", "O pedido contém campos desconhecidos.", 422)
    if not partial and "title" not in payload:
        return None, ("validation_error", "O título é obrigatório.", 422)
    result = {}
    if "title" in payload:
        title = payload["title"]
        if not isinstance(title, str) or not 3 <= len(title.strip()) <= 150:
            return None, ("validation_error", "O título deve ter entre 3 e 150 caracteres.", 422)
        result["title"] = title.strip()
    if "description" in payload:
        description = payload["description"]
        if not isinstance(description, str) or len(description) > 2000:
            return None, ("validation_error", "A descrição não pode exceder 2000 caracteres.", 422)
        result["description"] = description.strip()
    if "status" in payload:
        status = payload["status"]
        if not isinstance(status, str) or status not in TASK_STATES:
            return None, ("validation_error", "Estado de tarefa inválido.", 422)
        result["status"] = status
    if "priority" in payload:
        priority = payload["priority"]
        if not isinstance(priority, str) or priority not in TASK_PRIORITIES:
            return None, ("validation_error", "Prioridade inválida.", 422)
        result["priority"] = priority
    if "dueDate" in payload:
        due_date = payload["dueDate"]
        if due_date is not None:
            if not isinstance(due_date, str):
                return None, ("validation_error", "A data limite deve usar o formato YYYY-MM-DD.", 422)
            try:
                date.fromisoformat(due_date)
            except ValueError:
                return None, ("validation_error", "A data limite deve usar o formato YYYY-MM-DD.", 422)
        result["due_date"] = due_date
    if partial and not result:
        return None, ("validation_error", "Indica pelo menos um campo para atualizar.", 422)
    return result, None


@tasks_bp.get("/projects/<int:project_id>/members")
@require_auth
def list_project_members(project_id):
    project = accessible_project(project_id)
    if project is None:
        return api_error("not_found", "Recurso não encontrado.", 404)
    rows = get_db().execute(
        """SELECT u.id, u.username, u.name, u.email, wm.role
           FROM workspace_member wm JOIN user_account u ON u.id = wm.user_id
           WHERE wm.workspace_id = ? ORDER BY u.name""",
        (project["workspace_id"],),
    ).fetchall()
    return jsonify([{
        "id": row["id"],
        "username": row["username"],
        "name": row["name"],
        "email": row["email"],
        "role": row["role"],
    } for row in rows])


@tasks_bp.get("/projects/<int:project_id>/tasks/summary")
@require_auth
def project_task_summary(project_id):
    project = accessible_project(project_id)
    if project is None:
        return api_error("not_found", "Recurso não encontrado.", 404)
    row = get_db().execute(
        """SELECT COUNT(*) AS total,
                  SUM(CASE WHEN status = 'TODO' THEN 1 ELSE 0 END) AS todo,
                  SUM(CASE WHEN status = 'IN_PROGRESS' THEN 1 ELSE 0 END) AS in_progress,
                  SUM(CASE WHEN status = 'DONE' THEN 1 ELSE 0 END) AS done
           FROM task WHERE project_id = ?""",
        (project_id,),
    ).fetchone()
    return jsonify({
        "total": row["total"],
        "counts": {
            "TODO": row["todo"] or 0,
            "IN_PROGRESS": row["in_progress"] or 0,
            "DONE": row["done"] or 0,
        },
    })


@tasks_bp.get("/projects/<int:project_id>/tasks")
@require_auth
def list_project_tasks(project_id):
    project = accessible_project(project_id)
    if project is None:
        return api_error("not_found", "Recurso não encontrado.", 404)
    status = request.args.get("status")
    priority = request.args.get("priority")
    if status and status not in TASK_STATES:
        return api_error("validation_error", "Estado de tarefa inválido.", 422)
    if priority and priority not in TASK_PRIORITIES:
        return api_error("validation_error", "Prioridade inválida.", 422)
    try:
        page = max(1, int(request.args.get("page", "1")))
        page_size = min(100, max(1, int(request.args.get("pageSize", "50"))))
    except ValueError:
        return api_error("validation_error", "A paginação deve usar números inteiros.", 422)

    clauses = ["project_id = ?"]
    parameters = [project_id]
    if status:
        clauses.append("status = ?")
        parameters.append(status)
    if priority:
        clauses.append("priority = ?")
        parameters.append(priority)
    where_clause = " AND ".join(clauses)
    database = get_db()
    total = database.execute(f"SELECT COUNT(*) FROM task WHERE {where_clause}", parameters).fetchone()[0]
    rows = database.execute(
        f"SELECT * FROM task WHERE {where_clause} ORDER BY created_at DESC, id DESC LIMIT ? OFFSET ?",
        [*parameters, page_size, (page - 1) * page_size],
    ).fetchall()
    return jsonify({
        "items": [serialize_task(row) for row in rows],
        "page": page,
        "pageSize": page_size,
        "total": total,
    })


@tasks_bp.post("/projects/<int:project_id>/tasks")
@require_auth
def create_task(project_id):
    project = accessible_project(project_id)
    if project is None:
        return api_error("not_found", "Recurso não encontrado.", 404)
    payload, error = validate_task_payload(request.get_json(silent=True))
    if error:
        return api_error(*error)
    database = get_db()
    cursor = database.execute(
        """INSERT INTO task
           (workspace_id, project_id, title, description, status, priority, due_date)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (
            project["workspace_id"], project_id, payload["title"],
            payload.get("description", ""), payload.get("status", "TODO"),
            payload.get("priority", "MEDIUM"), payload.get("due_date"),
        ),
    )
    database.commit()
    task = database.execute("SELECT * FROM task WHERE id = ?", (cursor.lastrowid,)).fetchone()
    return jsonify(serialize_task(task)), 201


@tasks_bp.get("/tasks/<int:task_id>")
@require_auth
def get_task(task_id):
    task = accessible_task(task_id)
    if task is None:
        return api_error("not_found", "Recurso não encontrado.", 404)
    return jsonify(serialize_task(task))


@tasks_bp.patch("/tasks/<int:task_id>")
@require_auth
def update_task(task_id):
    task = accessible_task(task_id)
    if task is None:
        return api_error("not_found", "Recurso não encontrado.", 404)
    payload, error = validate_task_payload(request.get_json(silent=True), partial=True)
    if error:
        return api_error(*error)
    assignments = ", ".join(f"{field} = ?" for field in payload)
    database = get_db()
    database.execute(
        f"UPDATE task SET {assignments}, updated_at = strftime('%Y-%m-%dT%H:%M:%fZ', 'now') WHERE id = ?",
        [*payload.values(), task_id],
    )
    database.commit()
    updated = database.execute("SELECT * FROM task WHERE id = ?", (task_id,)).fetchone()
    return jsonify(serialize_task(updated))


@tasks_bp.delete("/tasks/<int:task_id>")
@require_auth
def delete_task(task_id):
    task = accessible_task(task_id)
    if task is None:
        return api_error("not_found", "Recurso não encontrado.", 404)
    database = get_db()
    database.execute("DELETE FROM task WHERE id = ?", (task_id,))
    database.commit()
    return "", 204


@tasks_bp.get("/tasks/<int:task_id>/assignments")
@require_auth
def list_assignments(task_id):
    task = accessible_task(task_id)
    if task is None:
        return api_error("not_found", "Recurso não encontrado.", 404)
    return jsonify(task_assignees(task_id))


@tasks_bp.put("/tasks/<int:task_id>/assignments/<int:user_id>")
@require_auth
def add_assignment(task_id, user_id):
    task = accessible_task(task_id)
    if task is None:
        return api_error("not_found", "Recurso não encontrado.", 404)
    database = get_db()
    member = database.execute(
        "SELECT 1 FROM workspace_member WHERE workspace_id = ? AND user_id = ?",
        (task["workspace_id"], user_id),
    ).fetchone()
    if member is None:
        return api_error("not_found", "Utilizador elegível não encontrado.", 404)
    existing = database.execute(
        "SELECT 1 FROM task_assignment WHERE task_id = ? AND user_id = ?",
        (task_id, user_id),
    ).fetchone()
    if existing is not None:
        return jsonify({"taskId": task_id, "userId": user_id, "created": False}), 200
    database.execute(
        "INSERT INTO task_assignment (workspace_id, task_id, user_id) VALUES (?, ?, ?)",
        (task["workspace_id"], task_id, user_id),
    )
    database.commit()
    return jsonify({"taskId": task_id, "userId": user_id, "created": True}), 201


@tasks_bp.delete("/tasks/<int:task_id>/assignments/<int:user_id>")
@require_auth
def remove_assignment(task_id, user_id):
    task = accessible_task(task_id)
    if task is None:
        return api_error("not_found", "Recurso não encontrado.", 404)
    database = get_db()
    database.execute(
        "DELETE FROM task_assignment WHERE task_id = ? AND user_id = ?",
        (task_id, user_id),
    )
    database.commit()
    return "", 204


@tasks_bp.get("/tasks/<int:task_id>/comments")
@require_auth
def list_comments(task_id):
    task = accessible_task(task_id)
    if task is None:
        return api_error("not_found", "Recurso não encontrado.", 404)
    rows = get_db().execute(
        """SELECT c.id, c.task_id, c.content, c.created_at,
                  u.id AS author_id, u.name AS author_name
           FROM comment c JOIN user_account u ON u.id = c.author_user_id
           WHERE c.task_id = ? ORDER BY c.created_at, c.id""",
        (task_id,),
    ).fetchall()
    return jsonify([{
        "id": row["id"],
        "taskId": row["task_id"],
        "content": row["content"],
        "createdAt": row["created_at"],
        "author": {"id": row["author_id"], "name": row["author_name"]},
    } for row in rows])


@tasks_bp.post("/tasks/<int:task_id>/comments")
@require_auth
def create_comment(task_id):
    task = accessible_task(task_id)
    if task is None:
        return api_error("not_found", "Recurso não encontrado.", 404)
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict) or set(payload) != {"content"}:
        return api_error("invalid_json", "Indica apenas o campo content em JSON.", 400)
    content = payload["content"]
    if not isinstance(content, str) or not 1 <= len(content.strip()) <= 2000:
        return api_error("validation_error", "O comentário deve ter entre 1 e 2000 caracteres.", 422)
    database = get_db()
    cursor = database.execute(
        """INSERT INTO comment (workspace_id, task_id, author_user_id, content)
           VALUES (?, ?, ?, ?)""",
        (task["workspace_id"], task_id, g.current_user["id"], content.strip()),
    )
    database.commit()
    row = database.execute(
        """SELECT c.id, c.task_id, c.content, c.created_at,
                  u.id AS author_id, u.name AS author_name
           FROM comment c JOIN user_account u ON u.id = c.author_user_id
           WHERE c.id = ?""",
        (cursor.lastrowid,),
    ).fetchone()
    return jsonify({
        "id": row["id"],
        "taskId": row["task_id"],
        "content": row["content"],
        "createdAt": row["created_at"],
        "author": {"id": row["author_id"], "name": row["author_name"]},
    }), 201