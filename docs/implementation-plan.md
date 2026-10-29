# Plano de implementação — Ficha 03

## Decisões e pressupostos

- **Facto confirmado:** a Matriz deve ajudar equipas a organizar projetos e tarefas e acompanhar progresso.
- **Âmbito académico:** a Ficha 03 pede autenticação, CRUD, prioridades, múltiplos responsáveis, comentários, pesquisa/filtros, painel, persistência e testes.
- **Fronteira de acesso:** manter `Workspace` e `WorkspaceMember` da Ficha 02. Não adotar o `owner_id` dos ficheiros de resultados, pois mudaria a regra de acesso sem aprovação.
- **Stack escolhida para o exercício:** Flask + SQLite + templates HTML/CSS/JavaScript nativo, servido num processo local.
- **Sessão:** cookie Flask HttpOnly, SameSite=Lax, CSRF token em pedidos mutáveis e hashes de palavras-passe com Werkzeug. Sem registo público.
- **Valores API:** estados `TODO`, `IN_PROGRESS`, `DONE`; prioridades `LOW`, `MEDIUM`, `HIGH`. A interface traduz os rótulos.
- **Seed:** utilizadores e dados fictícios idempotentes, sem apagar conteúdo existente.

## Incrementos e critérios

| Estado | Incremento | Critérios e verificação |
|---|---|---|
| Concluído | 1. Alinhar requisitos, dados, OpenAPI e documentação | Um modelo workspace; CRUD/auth/colaboração representados; decisões e lacunas registadas. |
| Concluído | 2. Aplicação, configuração, esquema e seed | Flask/SQLite inicializados; seed idempotente; contas para dois espaços distintos. |
| Concluído | 3. Autenticação e fronteira de autorização | Login/logout/perfil; sessão e CSRF; testes sem sessão e entre espaços. |
| Concluído | 4. Projetos | CRUD, pesquisa, autorização por papel/espaço e eliminação em cascata implementados. |
| Concluído | 5. Tarefas e painel (API) | CRUD, prioridade/estado, filtros e contagens completas implementados. |
| Concluído | 6. Atribuições e comentários (API) | Muitos-para-muitos sem duplicados; elegibilidade no mesmo espaço; autor/data definidos no servidor. |
| Concluído | 7. Interface integrada | Login, painel e detalhe ligados à API; percursos principais verificados em desktop e mobile. |
| Concluído | 8. Revisão e entrega | Suite e validações passam; OpenAPI, README, AGENTS e `docs/verification.md` atualizados. |

## Mapa inicial de componentes

- `app.py`: criação da aplicação, configuração e registo de rotas.
- `db.py`: ligação SQLite, esquema, transações e seed idempotente.
- `auth.py`: login, logout, perfil, sessão e validação CSRF.
- `projects.py`: endpoints e regras de acesso a projetos.
- `tasks.py`: endpoints de tarefas, filtros, atribuições e comentários.
- `templates/` e `static/`: interface servida pelo Flask e atualizações via API.
- `tests/`: testes de validação, autorização e round-trip de persistência.

Este plano autoriza a implementação incremental da atividade. Não autoriza remover a separação por workspace nem introduzir credenciais reais.