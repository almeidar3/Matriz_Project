# Revisão de qualidade e segurança — Ficha Prática 04

## Âmbito e referência

Revisão limitada ao fluxo de criação de tarefas, ao controlo de acesso por workspace, à resposta OpenAPI e ao diff dos testes/documentação desta ficha. A implementação observada está em `tasks.py`, `projects.py`, `auth.py`, `app.py` e `static/app.js`.

Referência do repositório no início da validação: branch `main`, commit `3490d80`. Não foi criado commit; os novos testes e documentos permanecem alterações locais. A alteração preexistente em `AGENTS.md` foi preservada.

## Achado

### Baixo — A API aceita datas fora do formato documentado

- **Evidência:** `openapi.yaml` define `dueDate` como `format: date`; `validate_task_payload` usa `date.fromisoformat`. O pedido de integração com `dueDate: "20261111"` foi aceite com HTTP 201 e o valor compacto foi devolvido sem normalização.
- **Impacto:** clientes que esperem o formato `YYYY-MM-DD` podem receber ou persistir uma data que não corresponde ao contrato documentado.
- **Recomendação:** validar estritamente o formato completo `YYYY-MM-DD` e acrescentar um teste unitário e um teste da API que rejeitem a forma compacta.
- **Decisão:** não alterado nesta entrega; é uma alteração de produção que deve ser revista/aprovada separadamente.

## Autorização e controlos observados

- Os testes com duas contas confirmaram que Inês, membro de outro workspace, recebe HTTP 404 ao consultar ou alterar uma tarefa da Equipa Produto e ao tentar criar tarefa nesse projeto. A tarefa original permaneceu inalterada.
- Ana e Bruno, ambos com acesso ao workspace do projeto, criaram tarefas com HTTP 201.
- A criação consulta o projeto acessível antes de inserir a tarefa. O fluxo de identidade depende da sessão; pedidos mutáveis também passam pelo controlo CSRF global. Os testes existentes cobrem rejeição de mutação sem CSRF.
- Nos caminhos revistos, consultas SQL usam parâmetros; a atualização limita os campos à lista validada. A interface escapa o título da tarefa antes de o inserir em HTML.
- Não foi confirmado IDOR/Broken Access Control no fluxo testado.

## Ferramentas e limitações

- `unittest`: 22 testes unitários/de integração passaram.
- Playwright Chromium headless: 1 teste E2E passou.
- `node --check static/app.js`: sem erros de sintaxe.
- Não há configuração de Bandit, Semgrep, SonarQube ou ferramenta equivalente no projeto; análise estática de segurança não executada.
- Não foi feita análise completa de dependências, produção, sessões expiradas ou todos os endpoints. Os resultados não certificam prontidão para produção.

## Decisões

Não foram alteradas rotas ou regras de produção. O achado de formato de data foi confirmado e documentado para revisão humana; o restante do fluxo de autorização observado passou nos cenários definidos em `test-plan.md`.