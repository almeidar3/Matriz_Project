# Plano de testes — Ficha Prática 04

## Âmbito e decisões

Validar criação de tarefas a partir dos critérios de US-02/RF-11 e do contrato em `openapi.yaml`. A suite usa `unittest`, Flask e SQLite; todos os testes de API e E2E criam uma base temporária e semeiam dados fictícios. Não se alterou código de produção para obter resultados verdes.

| ID | Cenário | Resultado esperado | Nível e teste | Resultado observado |
|---|---|---|---|---|
| UT-01 | Título nos limites de 3 e 150 caracteres; vazio, só espaços, abaixo/acima do limite e tipo inválido. | Aceitar os limites; rejeitar restantes entradas com erro de validação. | Unitário — `test_task_validation_unit.py` | Passou. |
| UT-02 | Descrição com 2000 e 2001 caracteres. | Aceitar 2000; rejeitar 2001. | Unitário — `test_task_validation_unit.py` | Passou. |
| UT-03 | Estados, prioridades, data ISO e payload malformado/desconhecido. | Aceitar valores definidos no contrato; rejeitar valores e formatos inválidos. | Unitário — `test_task_validation_unit.py` | Passou para os casos incluídos. |
| INT-01 | Criar tarefa válida e conferir resposta HTTP, campos, estado/prioridade por omissão e prazo. | HTTP 201; tarefa associada ao projeto; `TODO` e `MEDIUM` por omissão. | Integração — `test_task_creation_integration.py` | Passou. |
| INT-02 | Consultar tarefa através de uma nova instância Flask com a mesma base SQLite. | HTTP 200 e representação persistida igual à criação. | Integração — `test_task_creation_integration.py` | Passou. |
| INT-03 | Título composto apenas por espaços. | HTTP 422 `validation_error`; número de tarefas não aumenta. | Integração — `test_task_creation_integration.py` | Passou. |
| INT-04 | Membro autorizado cria tarefa no seu workspace. | HTTP 201. | Integração — `test_task_creation_integration.py` | Passou. |
| INT-05 | Utilizadora de outro workspace tenta consultar, alterar e criar no projeto protegido. | HTTP 404 sem revelar o recurso; tarefa original mantém os dados. | Integração — `test_task_creation_integration.py` | Passou com Ana e Inês. |
| INT-06 | Criar tarefa num projeto inexistente. | HTTP 404 `not_found`. | Integração — `test_task_creation_integration.py` | Passou. |
| E2E-01 | Login, abrir projeto de demonstração, criar tarefa e encontrá-la na lista. | A tarefa aparece na interface sem espera fixa. | Playwright — `tests/e2e/test_task_creation_e2e.py` | Passou em Chromium headless. |

## Execução

No diretório `Matriz_Project`, com o ambiente virtual ativado:

```sh
python -m pip install -r requirements-test.txt
python -m unittest discover -s tests -v
python -m playwright install chromium
python -m unittest discover -s tests/e2e -v
node --check static/app.js
```

Execução registada nesta ficha: suite unitária/de integração, 22 testes passaram; E2E, 1 teste passou; `node --check static/app.js` terminou sem erros. A instalação de Playwright/Chromium foi feita no ambiente virtual local. O teste E2E guarda screenshot e trace em `/tmp` apenas se falhar.

## Cobertura pendente

- Não foi executado um validador automático de schemas OpenAPI; a operação `createTask` e os campos da resposta foram comparados com o contrato. A discrepância de formato de `dueDate` está registada em `quality-security-review.md`.
- A revisão de segurança limita-se à criação/leitura/alteração de tarefas e ao controlo por workspace; não é uma auditoria completa da aplicação.
- A Ficha 04 não exigiu configurar CI/CD; nenhum workflow foi criado.