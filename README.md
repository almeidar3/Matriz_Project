# Matriz

Matriz é uma proposta de aplicação para ajudar equipas de trabalho a organizar projetos, gerir tarefas e acompanhar o progresso.

## Problema

O cliente identificou a necessidade de as equipas organizarem projetos, gerirem tarefas e acompanharem o trabalho. As regras, prioridades e necessidades detalhadas ainda não foram confirmadas.

## Objetivos

- Reunir projetos e tarefas num espaço partilhado pela equipa.
- Tornar visíveis os responsáveis, estados e prazos das tarefas.
- Permitir acompanhar o progresso dos projetos através dos respetivos estados.

Estes objetivos e as funcionalidades abaixo são uma proposta inicial, não requisitos aprovados pelo cliente.

## MVP proposto

- Criar e consultar projetos.
- Criar, editar e consultar tarefas associadas a projetos.
- Registar estado, responsável e prazo de uma tarefa.
- Consultar tarefas numa vista de lista ou quadro por estado.
- Consultar um resumo do progresso de cada projeto.
- Distinguir administradores do espaço de trabalho de membros da equipa.

Os detalhes, pressupostos, prioridades e critérios de aceitação estão em [`docs/requirements.md`](docs/requirements.md) e [`docs/user-stories.md`](docs/user-stories.md).

## Documentação

- [`docs/requirements.md`](docs/requirements.md): visão, utilizadores, requisitos e âmbito.
- [`docs/user-stories.md`](docs/user-stories.md): backlog inicial e critérios verificáveis.
- [`docs/constraints.md`](docs/constraints.md): pressupostos, restrições, segurança e decisões pendentes.
- [`docs/architecture.md`](docs/architecture.md): comparação e proposta de arquitetura para o MVP.
- [`docs/database.md`](docs/database.md): modelo de dados e diagrama ER em Mermaid.
- [`docs/implementation-plan.md`](docs/implementation-plan.md): incrementos e critérios da Ficha 03.
- [`docs/verification.md`](docs/verification.md): evidência dos testes e verificações.
- [`openapi.yaml`](openapi.yaml): contrato REST simplificado com duas operações.
- [`docs/ui/wireframe.svg`](docs/ui/wireframe.svg): wireframe de baixa fidelidade do projeto.
- [`AGENTS.md`](AGENTS.md): instruções persistentes para agentes de desenvolvimento.

## Executar localmente

Requisitos: Python 3.11 ou superior.

```sh
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
cp .env.example .env
```

Define `MATRIX_SECRET_KEY` no ambiente antes de iniciar. Gera uma chave local com `python -c 'import secrets; print(secrets.token_urlsafe(32))'` e exporta-a; não uses a chave de exemplo em ambientes partilhados. A base SQLite é criada em `instance/matriz.sqlite3` na primeira execução.

```sh
set -a
source .env
set +a
flask --app app seed-demo
python app.py
```

Abre `http://127.0.0.1:5000`. O seed é idempotente e nunca limpa a base de dados. As contas e palavras-passe são fictícias e destinam-se apenas a demonstração:

| Utilizador | Palavra-passe | Espaço | Papel |
|---|---|---|---|
| `ana` | `Matriz-demo-ana-2026` | Equipa Produto | Administrador |
| `bruno` | `Matriz-demo-bruno-2026` | Equipa Produto | Membro |
| `ines` | `Matriz-demo-ines-2026` | Equipa Design | Administrador |

## Verificação

```sh
python -m unittest discover -s tests -v
node --check static/app.js
```

O contrato REST está em [`openapi.yaml`](openapi.yaml); os resultados e limitações conhecidos estão em [`docs/verification.md`](docs/verification.md). Para regras de negócio, consultar [`docs/requirements.md`](docs/requirements.md) e [`docs/user-stories.md`](docs/user-stories.md). A stack e as funcionalidades são escolhas académicas da Ficha 03, não uma decisão validada para produção.
