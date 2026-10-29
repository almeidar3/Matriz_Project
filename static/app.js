const state = {
  csrfToken: null,
  user: null,
  workspaces: [],
  workspaceId: null,
  projects: [],
  dashboard: [],
  selectedProject: null,
  tasks: [],
  taskSummary: { total: 0, counts: { TODO: 0, IN_PROGRESS: 0, DONE: 0 } },
  taskTotal: 0,
  taskPage: 1,
  taskPageSize: 20,
  members: [],
  filters: { status: "", priority: "" },
};

const labels = {
  TODO: "A fazer",
  IN_PROGRESS: "Em curso",
  DONE: "Concluída",
  LOW: "Baixa",
  MEDIUM: "Média",
  HIGH: "Alta",
};

const escapeHtml = (value) => String(value ?? "").replace(/[&<>"']/g, (character) => ({
  "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;",
}[character]));

const elements = {};

document.addEventListener("DOMContentLoaded", () => {
  for (const id of ["login-view", "login-form", "login-error", "app-shell", "workspace-select", "project-nav", "new-project-open", "home-open", "logout-button", "user-avatar", "user-name", "user-role", "breadcrumb", "topbar-date", "main-content", "toast", "dialog-root"]) {
    elements[id] = document.getElementById(id);
  }
  elements["topbar-date"].textContent = new Intl.DateTimeFormat("pt-PT", { dateStyle: "long" }).format(new Date());
  bindShellEvents();
  initialize();
});

async function initialize() {
  try {
    const csrf = await api("/api/auth/csrf");
    state.csrfToken = csrf.csrfToken;
    const profile = await api("/api/auth/me");
    state.user = profile.user;
    state.workspaces = profile.workspaces;
    showApplication();
    await loadHome();
  } catch (error) {
    showLogin();
  }
}

async function api(path, options = {}) {
  const headers = { Accept: "application/json", ...options.headers };
  if (options.body !== undefined) headers["Content-Type"] = "application/json";
  if (["POST", "PUT", "PATCH", "DELETE"].includes(options.method)) {
    headers["X-CSRF-Token"] = state.csrfToken || "";
  }
  const response = await fetch(path, { ...options, headers, credentials: "same-origin" });
  if (response.status === 204) return null;
  const result = await response.json().catch(() => ({}));
  if (!response.ok) {
    if (response.status === 401 && state.user) showLogin("A sessão terminou. Inicia sessão novamente.");
    throw new Error(result.error?.message || "Não foi possível concluir o pedido.");
  }
  if (result.csrfToken) state.csrfToken = result.csrfToken;
  return result;
}

function showLogin(message = "") {
  state.user = null;
  elements["app-shell"].hidden = true;
  elements["login-view"].hidden = false;
  elements["login-error"].textContent = message;
  elements["login-error"].hidden = !message;
  document.getElementById("username").focus();
}

function showApplication() {
  elements["login-view"].hidden = true;
  elements["app-shell"].hidden = false;
  elements["user-name"].textContent = state.user.name;
  elements["user-avatar"].textContent = state.user.name.slice(0, 1).toUpperCase();
  elements["workspace-select"].innerHTML = state.workspaces.map((workspace) => `<option value="${workspace.id}">${escapeHtml(workspace.name)}</option>`).join("");
  if (!state.workspaceId && state.workspaces.length) state.workspaceId = state.workspaces[0].id;
  elements["workspace-select"].value = state.workspaceId;
  updateRoleLabel();
}

function updateRoleLabel() {
  const current = state.workspaces.find((workspace) => workspace.id === Number(state.workspaceId));
  elements["user-role"].textContent = current?.role === "admin" ? "Administrador" : "Membro";
  elements["new-project-open"].hidden = current?.role !== "admin";
}

function bindShellEvents() {
  document.querySelector(".brand").addEventListener("click", (event) => {
    event.preventDefault();
    loadHome();
  });
  elements["login-form"].addEventListener("submit", submitLogin);
  elements["logout-button"].addEventListener("click", logout);
  elements["new-project-open"].addEventListener("click", () => openProjectForm());
  elements["home-open"].addEventListener("click", loadHome);
  elements["workspace-select"].addEventListener("change", async (event) => {
    state.workspaceId = Number(event.target.value);
    state.selectedProject = null;
    state.filters = { status: "", priority: "" };
    updateRoleLabel();
    await loadHome();
  });
  elements["project-nav"].addEventListener("click", (event) => {
    const button = event.target.closest("[data-project-id]");
    if (button) openProject(Number(button.dataset.projectId));
  });
  elements["main-content"].addEventListener("click", handleMainClick);
  elements["main-content"].addEventListener("change", handleMainChange);
  elements["main-content"].addEventListener("submit", handleMainSubmit);
  elements["dialog-root"].addEventListener("click", handleDialogClick);
  elements["dialog-root"].addEventListener("submit", handleDialogSubmit);
}

async function submitLogin(event) {
  event.preventDefault();
  const form = new FormData(event.currentTarget);
  const button = event.currentTarget.querySelector("button[type=submit]");
  button.disabled = true;
  elements["login-error"].hidden = true;
  try {
    const result = await api("/api/auth/login", {
      method: "POST",
      body: JSON.stringify({ username: form.get("username"), password: form.get("password") }),
    });
    state.user = result.user;
    const profile = await api("/api/auth/me");
    state.workspaces = profile.workspaces;
    showApplication();
    await loadHome();
  } catch (error) {
    elements["login-error"].textContent = error.message;
    elements["login-error"].hidden = false;
  } finally {
    button.disabled = false;
  }
}

async function logout() {
  try {
    await api("/api/auth/logout", { method: "POST" });
    state.user = null;
    state.csrfToken = null;
    const csrf = await api("/api/auth/csrf");
    state.csrfToken = csrf.csrfToken;
    showLogin("Terminaste a sessão.");
  } catch (error) {
    toast(error.message, "error");
  }
}

async function loadHome() {
  elements["breadcrumb"].textContent = "Painel inicial";
  state.selectedProject = null;
  await withLoading(async () => {
    const [dashboard, projects] = await Promise.all([
      api("/api/dashboard"),
      api(`/api/workspaces/${state.workspaceId}/projects`),
    ]);
    state.dashboard = dashboard.projects.filter((project) => project.workspaceId === Number(state.workspaceId));
    state.projects = projects.items;
    renderProjectNav();
    renderHome();
  });
}

async function openProject(projectId) {
  state.filters = { status: "", priority: "" };
  state.taskPage = 1;
  await withLoading(async () => {
    const [project, tasks, members, summary] = await Promise.all([
      api(`/api/projects/${projectId}`),
      fetchTasks(projectId),
      api(`/api/projects/${projectId}/members`),
      api(`/api/projects/${projectId}/tasks/summary`),
    ]);
    if (project.workspaceId !== Number(state.workspaceId)) throw new Error("O projeto não pertence ao espaço selecionado.");
    state.selectedProject = project;
    state.tasks = tasks.items;
    state.taskTotal = tasks.total;
    state.taskSummary = summary;
    state.members = members;
    renderProjectNav();
    renderProjectDetail();
  });
}

async function reloadProject() {
  if (!state.selectedProject) return loadHome();
  const projectId = state.selectedProject.id;
  await withLoading(async () => {
    const [project, tasks, members, summary] = await Promise.all([
      api(`/api/projects/${projectId}`),
      fetchTasks(projectId),
      api(`/api/projects/${projectId}/members`),
      api(`/api/projects/${projectId}/tasks/summary`),
    ]);
    state.selectedProject = project;
    state.tasks = tasks.items;
    state.taskTotal = tasks.total;
    state.taskSummary = summary;
    state.members = members;
    renderProjectNav();
    renderProjectDetail();
  });
}

async function fetchTasks(projectId) {
  const query = new URLSearchParams({ page: String(state.taskPage), pageSize: String(state.taskPageSize) });
  if (state.filters.status) query.set("status", state.filters.status);
  if (state.filters.priority) query.set("priority", state.filters.priority);
  return api(`/api/projects/${projectId}/tasks?${query}`);
}

async function withLoading(action) {
  elements["main-content"].innerHTML = '<div class="loading-line"><span></span>A carregar…</div>';
  try {
    await action();
  } catch (error) {
    if (state.user) elements["main-content"].innerHTML = `<div class="empty-state"><strong>Não foi possível carregar</strong><p>${escapeHtml(error.message)}</p><button class="button button-secondary" data-action="retry">Tentar novamente</button></div>`;
  }
}

function renderProjectNav() {
  const projects = state.dashboard.filter((project) => project.workspaceId === Number(state.workspaceId));
  elements["project-nav"].innerHTML = projects.length
    ? projects.map((project) => `<button class="project-nav-item ${state.selectedProject?.id === project.id ? "active" : ""}" data-project-id="${project.id}" type="button"><span class="project-dot"></span><span>${escapeHtml(project.name)}</span><small>${project.taskCount}</small></button>`).join("")
    : '<p class="sidebar-empty">Sem projetos</p>';
}

function renderHome() {
  const projects = state.dashboard.filter((project) => project.workspaceId === Number(state.workspaceId));
  const counts = projects.reduce((total, project) => ({
    tasks: total.tasks + project.taskCount,
    TODO: total.TODO + project.counts.TODO,
    IN_PROGRESS: total.IN_PROGRESS + project.counts.IN_PROGRESS,
    DONE: total.DONE + project.counts.DONE,
  }), { tasks: 0, TODO: 0, IN_PROGRESS: 0, DONE: 0 });
  elements["breadcrumb"].textContent = "Painel inicial";
  elements["main-content"].innerHTML = `
    <div class="page-heading"><div><p class="eyebrow">VISÃO GERAL</p><h1>Bom dia, ${escapeHtml(state.user.name.split(" ")[0])}</h1><p class="muted">Acompanhe o trabalho deste espaço.</p></div><button class="button button-primary" data-action="new-project" ${currentRole() !== "admin" ? "hidden" : ""}>+ Novo projeto</button></div>
    <section class="metric-grid" aria-label="Resumo das tarefas">
      ${metric("Tarefas", counts.tasks, "no total")}${metric("A fazer", counts.TODO, "por iniciar")}${metric("Em curso", counts.IN_PROGRESS, "em andamento")}${metric("Concluídas", counts.DONE, "finalizadas")}
    </section>
    <div class="section-heading"><div><h2>Projetos</h2><p class="muted">${projects.length} ${projects.length === 1 ? "projeto" : "projetos"} neste espaço</p></div><label class="search-field"><span class="search-symbol">⌕</span><input id="project-search" type="search" placeholder="Pesquisar projetos" aria-label="Pesquisar projetos"></label></div>
    <section id="project-grid" class="project-grid">${projectCards(projects)}</section>`;
  document.getElementById("project-search").addEventListener("input", (event) => {
    const query = event.target.value.trim().toLocaleLowerCase("pt-PT");
    const visible = projects.filter((project) => project.name.toLocaleLowerCase("pt-PT").includes(query));
    document.getElementById("project-grid").innerHTML = projectCards(visible);
  });
}

function metric(title, value, note) {
  return `<article class="metric"><span class="metric-label">${title}</span><strong>${value}</strong><span class="metric-note">${note}</span></article>`;
}

function projectCards(projects) {
  if (!projects.length) return '<div class="empty-state"><strong>Ainda sem projetos</strong><p>Cria um projeto para começar a organizar o trabalho.</p></div>';
  return projects.map((project, index) => `<button class="project-card" data-project-id="${project.id}" type="button" style="--card-index:${index}"><span class="card-kicker">PROJETO</span><strong>${escapeHtml(project.name)}</strong><span class="project-description">${escapeHtml(project.description || "Sem descrição")}</span><span class="project-card-foot"><span>${project.taskCount} tarefas</span><span class="card-arrow">↗</span></span><span class="mini-progress"><span style="width:${project.taskCount ? Math.round(project.counts.DONE / project.taskCount * 100) : 0}%"></span></span></button>`).join("");
}

function renderProjectDetail() {
  const project = state.selectedProject;
  const isAdmin = currentRole() === "admin";
  const filteredTasks = state.tasks;
  const done = state.taskSummary.counts.DONE;
  const percent = state.taskSummary.total ? Math.round(done / state.taskSummary.total * 100) : 0;
  const pageCount = Math.max(1, Math.ceil(state.taskTotal / state.taskPageSize));
  elements["breadcrumb"].textContent = `Projetos / ${project.name}`;
  elements["main-content"].innerHTML = `
    <div class="page-heading project-page-heading"><div><p class="eyebrow">PROJETO</p><h1>${escapeHtml(project.name)}</h1><p class="muted">${escapeHtml(project.description || "Sem descrição")}</p></div><div class="heading-actions">${isAdmin ? `<button class="button button-secondary" data-action="edit-project">Editar</button><button class="button button-danger-quiet" data-action="delete-project">Eliminar</button>` : ""}<button class="button button-primary" data-action="new-task">+ Nova tarefa</button></div></div>
    <section class="project-summary"><div><span class="eyebrow">PROGRESSO</span><strong>${percent}%</strong></div><div class="summary-bar"><span style="width:${percent}%"></span></div><div class="summary-counts"><span><b>${state.taskSummary.total}</b> tarefas</span><span><b>${done}</b> concluídas</span></div></section>
    <div class="section-heading task-section-heading"><div><h2>Tarefas</h2><p class="muted">${state.taskTotal} resultado(s) · página ${state.taskPage} de ${pageCount}</p></div><div class="filter-row"><label><span class="sr-only">Filtrar por estado</span><select id="status-filter"><option value="">Todos os estados</option>${option("TODO", state.filters.status, "A fazer")}${option("IN_PROGRESS", state.filters.status, "Em curso")}${option("DONE", state.filters.status, "Concluída")}</select></label><label><span class="sr-only">Filtrar por prioridade</span><select id="priority-filter"><option value="">Todas as prioridades</option>${option("LOW", state.filters.priority, "Baixa")}${option("MEDIUM", state.filters.priority, "Média")}${option("HIGH", state.filters.priority, "Alta")}</select></label></div></div>
    <section id="task-list" class="task-list">${taskCards(filteredTasks)}</section>
    ${pageCount > 1 ? `<nav class="pagination" aria-label="Paginação de tarefas"><button class="button button-secondary button-small" data-action="task-page" data-page="${state.taskPage - 1}" ${state.taskPage === 1 ? "disabled" : ""}>Anterior</button><span>${state.taskPage} / ${pageCount}</span><button class="button button-secondary button-small" data-action="task-page" data-page="${state.taskPage + 1}" ${state.taskPage >= pageCount ? "disabled" : ""}>Seguinte</button></nav>` : ""}`;
}

function option(value, selected, text) {
  return `<option value="${value}" ${selected === value ? "selected" : ""}>${text}</option>`;
}

function taskCards(tasks) {
  if (!tasks.length) return '<div class="empty-state"><strong>Sem tarefas para mostrar</strong><p>Cria uma tarefa ou ajusta os filtros.</p></div>';
  return tasks.map((task) => `<article class="task-card" data-task-id="${task.id}">
    <div class="task-main"><div class="task-title-line"><span class="status-marker status-${task.status.toLowerCase()}"></span><h3>${escapeHtml(task.title)}</h3><span class="priority-label priority-${task.priority.toLowerCase()}">${labels[task.priority]}</span></div>
    <p class="task-description">${escapeHtml(task.description || "Sem descrição")}</p>
    <div class="task-controls"><label><span class="sr-only">Estado de ${escapeHtml(task.title)}</span><select data-task-field="status">${option("TODO", task.status, "A fazer")}${option("IN_PROGRESS", task.status, "Em curso")}${option("DONE", task.status, "Concluída")}</select></label><label><span class="sr-only">Prioridade de ${escapeHtml(task.title)}</span><select data-task-field="priority">${option("LOW", task.priority, "Baixa")}${option("MEDIUM", task.priority, "Média")}${option("HIGH", task.priority, "Alta")}</select></label>${task.dueDate ? `<span class="due-date">Prazo ${escapeHtml(task.dueDate)}</span>` : ""}</div></div>
    <div class="task-actions"><button class="icon-button task-more" data-action="edit-task" title="Editar tarefa" aria-label="Editar tarefa">•••</button></div>
    <details class="task-details"><summary>Responsáveis e comentários <span>${task.assignees.length} responsáveis</span></summary><div class="task-detail-content"><section><h4>Responsáveis</h4><div class="assignee-list">${state.members.map((member) => `<label class="assignee-option"><input type="checkbox" data-assignee-id="${member.id}" ${task.assignees.some((assignee) => assignee.id === member.id) ? "checked" : ""}><span>${escapeHtml(member.name)}</span></label>`).join("")}</div></section><section class="comments-section"><div class="comments-heading"><h4>Comentários</h4><button class="text-button" data-action="load-comments" type="button">Ver comentários</button></div><div class="comment-list" data-comment-list hidden></div><form class="comment-form" data-task-id="${task.id}"><label class="sr-only" for="comment-${task.id}">Novo comentário</label><textarea id="comment-${task.id}" name="content" maxlength="2000" placeholder="Escreve um comentário…" required></textarea><button class="button button-secondary button-small" type="submit">Comentar</button></form></section></div></details>
  </article>`).join("");
}

async function handleMainClick(event) {
  const actionButton = event.target.closest("[data-action]");
  const projectButton = event.target.closest(".project-card[data-project-id]");
  if (projectButton) return openProject(Number(projectButton.dataset.projectId));
  if (!actionButton) return;
  const action = actionButton.dataset.action;
  if (action === "new-project") return openProjectForm();
  if (action === "new-task") return openTaskForm();
  if (action === "edit-project") return openProjectForm(state.selectedProject);
  if (action === "delete-project") return deleteProject();
  if (action === "edit-task") return openTaskForm(state.tasks.find((task) => task.id === Number(actionButton.closest("[data-task-id]").dataset.taskId)));
  if (action === "load-comments") return loadComments(actionButton.closest(".task-card"));
  if (action === "task-page") {
    state.taskPage = Number(actionButton.dataset.page);
    return reloadProject();
  }
  if (action === "retry") return state.selectedProject ? openProject(state.selectedProject.id) : loadHome();
}

async function handleMainChange(event) {
  if (event.target.id === "status-filter" || event.target.id === "priority-filter") {
    state.taskPage = 1;
    state.filters = {
      status: document.getElementById("status-filter").value,
      priority: document.getElementById("priority-filter").value,
    };
    await reloadProject();
    return;
  }
  const taskCard = event.target.closest(".task-card");
  if (!taskCard) return;
  const taskId = Number(taskCard.dataset.taskId);
  if (event.target.matches("[data-task-field]")) {
    const field = event.target.dataset.taskField;
    const previous = state.tasks.find((task) => task.id === taskId)?.[field];
    event.target.disabled = true;
    try {
      await api(`/api/tasks/${taskId}`, { method: "PATCH", body: JSON.stringify({ [field]: event.target.value }) });
      toast("Tarefa atualizada.");
      await reloadProject();
      await refreshDashboard();
    } catch (error) {
      event.target.value = previous;
      toast(error.message, "error");
    } finally {
      event.target.disabled = false;
    }
  } else if (event.target.matches("[data-assignee-id]")) {
    const userId = event.target.dataset.assigneeId;
    event.target.disabled = true;
    try {
      await api(`/api/tasks/${taskId}/assignments/${userId}`, { method: event.target.checked ? "PUT" : "DELETE" });
      await reloadProject();
      toast("Responsáveis atualizados.");
    } catch (error) {
      event.target.checked = !event.target.checked;
      toast(error.message, "error");
    } finally {
      event.target.disabled = false;
    }
  }
}

async function handleMainSubmit(event) {
  if (!event.target.matches(".comment-form")) return;
  event.preventDefault();
  const form = event.target;
  const taskId = form.dataset.taskId;
  const button = form.querySelector("button[type=submit]");
  const content = new FormData(form).get("content");
  button.disabled = true;
  try {
    await api(`/api/tasks/${taskId}/comments`, { method: "POST", body: JSON.stringify({ content }) });
    form.reset();
    await loadComments(form.closest(".task-card"));
    toast("Comentário adicionado.");
  } catch (error) {
    toast(error.message, "error");
  } finally {
    button.disabled = false;
  }
}

function openProjectForm(project = null) {
  const editing = Boolean(project);
  showDialog(editing ? "Editar projeto" : "Novo projeto", `
    <form id="project-form" class="form-stack" data-project-id="${project?.id || ""}">
      <label for="project-name">Nome</label><input id="project-name" name="name" minlength="3" maxlength="100" value="${escapeHtml(project?.name || "")}" required>
      <label for="project-description">Descrição <span class="optional">Opcional</span></label><textarea id="project-description" name="description" maxlength="1000">${escapeHtml(project?.description || "")}</textarea>
      <div class="dialog-actions"><button type="button" class="button button-secondary" data-action="close-dialog">Cancelar</button><button type="submit" class="button button-primary">${editing ? "Guardar" : "Criar projeto"}</button></div>
    </form>`);
  document.getElementById("project-name").focus();
}

function openTaskForm(task = null) {
  const editing = Boolean(task);
  showDialog(editing ? "Editar tarefa" : "Nova tarefa", `
    <form id="task-form" class="form-stack" data-task-id="${task?.id || ""}">
      <label for="task-title">Título</label><input id="task-title" name="title" minlength="3" maxlength="150" value="${escapeHtml(task?.title || "")}" required>
      <label for="task-description">Descrição <span class="optional">Opcional</span></label><textarea id="task-description" name="description" maxlength="2000">${escapeHtml(task?.description || "")}</textarea>
      <div class="form-pair"><div><label for="task-priority">Prioridade</label><select id="task-priority" name="priority">${option("LOW", task?.priority || "MEDIUM", "Baixa")}${option("MEDIUM", task?.priority || "MEDIUM", "Média")}${option("HIGH", task?.priority || "MEDIUM", "Alta")}</select></div><div><label for="task-status">Estado</label><select id="task-status" name="status">${option("TODO", task?.status || "TODO", "A fazer")}${option("IN_PROGRESS", task?.status || "TODO", "Em curso")}${option("DONE", task?.status || "TODO", "Concluída")}</select></div></div>
      <label for="task-due-date">Prazo <span class="optional">Opcional</span></label><input id="task-due-date" name="dueDate" type="date" value="${escapeHtml(task?.dueDate || "")}">
      <div class="dialog-actions"><button type="button" class="button button-secondary" data-action="close-dialog">Cancelar</button>${editing ? `<button type="button" class="button button-danger-quiet" data-action="delete-task" data-task-id="${task.id}">Eliminar</button>` : ""}<button type="submit" class="button button-primary">${editing ? "Guardar" : "Criar tarefa"}</button></div>
    </form>`);
  document.getElementById("task-title").focus();
}

function showDialog(title, body) {
  elements["dialog-root"].innerHTML = `<div class="dialog-backdrop" data-action="backdrop-close"><section class="dialog" role="dialog" aria-modal="true" aria-labelledby="dialog-title"><header class="dialog-header"><h2 id="dialog-title">${title}</h2><button class="icon-button" data-action="close-dialog" type="button" aria-label="Fechar">×</button></header>${body}</section></div>`;
  elements["dialog-root"].querySelector("input")?.focus();
}

function handleDialogClick(event) {
  const actionButton = event.target.closest("[data-action]");
  if (!actionButton) return;
  if (actionButton.dataset.action === "close-dialog" || (actionButton.dataset.action === "backdrop-close" && event.target === actionButton)) {
    elements["dialog-root"].innerHTML = "";
  }
  if (actionButton.dataset.action === "delete-task") deleteTask(Number(actionButton.dataset.taskId));
}

async function handleDialogSubmit(event) {
  if (!event.target.matches("#project-form, #task-form")) return;
  event.preventDefault();
  const form = event.target;
  const button = form.querySelector("button[type=submit]");
  button.disabled = true;
  const data = Object.fromEntries(new FormData(form).entries());
  if (data.dueDate === "") data.dueDate = null;
  try {
    if (form.id === "project-form") {
      const projectId = form.dataset.projectId;
      const path = projectId ? `/api/projects/${projectId}` : `/api/workspaces/${state.workspaceId}/projects`;
      await api(path, { method: projectId ? "PATCH" : "POST", body: JSON.stringify(data) });
      elements["dialog-root"].innerHTML = "";
      await loadHome();
      toast(projectId ? "Projeto atualizado." : "Projeto criado.");
    } else {
      const taskId = form.dataset.taskId;
      const path = taskId ? `/api/tasks/${taskId}` : `/api/projects/${state.selectedProject.id}/tasks`;
      await api(path, { method: taskId ? "PATCH" : "POST", body: JSON.stringify(data) });
      elements["dialog-root"].innerHTML = "";
      await reloadProject();
      await refreshDashboard();
      toast(taskId ? "Tarefa atualizada." : "Tarefa criada.");
    }
  } catch (error) {
    toast(error.message, "error");
    button.disabled = false;
  }
}

async function deleteProject() {
  if (!window.confirm(`Eliminar o projeto “${state.selectedProject.name}” e todos os seus dados?`)) return;
  try {
    await api(`/api/projects/${state.selectedProject.id}`, { method: "DELETE" });
    state.selectedProject = null;
    await loadHome();
    toast("Projeto eliminado.");
  } catch (error) { toast(error.message, "error"); }
}

async function deleteTask(taskId) {
  if (!window.confirm("Eliminar esta tarefa e os respetivos comentários e responsáveis?")) return;
  try {
    await api(`/api/tasks/${taskId}`, { method: "DELETE" });
    elements["dialog-root"].innerHTML = "";
    await reloadProject();
    await refreshDashboard();
    toast("Tarefa eliminada.");
  } catch (error) { toast(error.message, "error"); }
}

async function loadComments(taskCard) {
  const list = taskCard.querySelector("[data-comment-list]");
  try {
    const comments = await api(`/api/tasks/${taskCard.dataset.taskId}/comments`);
    list.innerHTML = comments.length ? comments.map((comment) => `<article class="comment"><div><strong>${escapeHtml(comment.author.name)}</strong><time>${new Date(comment.createdAt).toLocaleString("pt-PT")}</time></div><p>${escapeHtml(comment.content)}</p></article>`).join("") : '<p class="muted">Ainda não há comentários.</p>';
    list.hidden = false;
  } catch (error) { toast(error.message, "error"); }
}

async function refreshDashboard() {
  const result = await api("/api/dashboard");
  state.dashboard = result.projects;
  renderProjectNav();
}

function currentRole() {
  return state.workspaces.find((workspace) => workspace.id === Number(state.workspaceId))?.role;
}

let toastTimeout;
function toast(message, type = "success") {
  const element = elements["toast"];
  element.textContent = message;
  element.className = `toast toast-${type}`;
  element.hidden = false;
  clearTimeout(toastTimeout);
  toastTimeout = setTimeout(() => { element.hidden = true; }, 3600);
}