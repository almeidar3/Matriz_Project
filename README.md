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
- [`docs/test-plan.md`](docs/test-plan.md): plano e resultados de testes da Ficha 04.
- [`docs/quality-security-review.md`](docs/quality-security-review.md): revisão de qualidade e segurança da Ficha 04.
- [`CHANGELOG.md`](CHANGELOG.md): histórico de alterações e versão candidata.
- [`docs/releases/v0.1.0-rc.1.md`](docs/releases/v0.1.0-rc.1.md): notas da versão candidata.
- [`.github/workflows/ci.yml`](.github/workflows/ci.yml): verificações automatizadas em push e pull request.
- [`openapi.yaml`](openapi.yaml): contrato REST simplificado com duas operações.
- [`docs/ui/wireframe.svg`](docs/ui/wireframe.svg): wireframe de baixa fidelidade do projeto.
- [`AGENTS.md`](AGENTS.md): instruções persistentes para agentes de desenvolvimento.

## Executar localmente

Requisitos: Python 3.11 ou superior para a aplicação e testes; Node.js para a verificação de JavaScript; Docker Desktop com o plugin Compose para a execução containerizada.

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

## Docker Compose (local)

Requisitos: Docker Desktop com o plugin Docker Compose. O container é para o exercício local e não representa uma configuração de produção.

```sh
cp .env.example .env
python -c 'import secrets; print(secrets.token_urlsafe(32))'
```

Substitui o valor de exemplo de `MATRIX_SECRET_KEY` no `.env` local pelo valor gerado. O `.env` está ignorado pelo Git. Depois, constrói e inicia a aplicação:

```sh
docker compose config -q
docker compose build
docker compose up -d
docker compose ps
docker compose logs --tail=50
docker compose exec web flask --app app seed-demo
```

Abre `http://127.0.0.1:5000`. Os dados SQLite ficam no volume Docker `matriz_data`; `docker compose down` remove o container sem apagar esse volume. `docker compose down -v` apaga também os dados persistentes.

## Verificação

```sh
python -m pip install -r requirements-test.txt
python -m unittest discover -s tests -v
python -m playwright install chromium
python -m unittest discover -s tests/e2e -v
node --check static/app.js
```

O contrato REST está em [`openapi.yaml`](openapi.yaml); os resultados da Ficha 04 estão em [`docs/test-plan.md`](docs/test-plan.md) e [`docs/quality-security-review.md`](docs/quality-security-review.md). Para regras de negócio, consultar [`docs/requirements.md`](docs/requirements.md) e [`docs/user-stories.md`](docs/user-stories.md). A stack e as funcionalidades são escolhas académicas, não uma decisão validada para produção.
