# Verificação da Ficha 03

## Testes automatizados

Comando: `python -m unittest discover -s tests -v`

| Cenário | Resultado esperado | Resultado observado |
|---|---|---|
| Migração de esquema legado | Remover restrições não aprovadas sem perder relações ou dados. | Passou: projeto/tarefa duplicados aceites; atribuição, comentário e integridade referencial preservados. |
| Seed repetível e migração de conta demo | Atualizar a identidade fictícia antiga sem remover projetos preexistentes. | Passou: utilizador preserva o ID, recebe nome fictício e projeto antigo mantém-se. |
| Credenciais inválidas e logout | Rejeitar palavra-passe incorreta; invalidar sessão ao terminar. | Passou: login inválido 401; logout 204; perfil seguinte 401. |
| Validação de tarefa | Rejeitar título vazio e estado com tipo inválido. | Passou: ambos devolvem 422 sem erro interno. |
| Utilizador de outro workspace | Recurso não revelado. | Passou: HTTP 404 para projeto de outro espaço. |
| Criação e persistência de tarefa | Criar e consultar depois de criar nova instância Flask. | Passou: HTTP 201 e tarefa continua consultável. |
| CRUD e papel de projeto | Membro não pode criar; administrador cria, atualiza e elimina. | Passou: membro 403; operações admin 201/200/204. |
| Atribuição repetida e utilizador externo | PUT idempotente; não permitir membro de outro espaço. | Passou: primeira atribuição 201, segunda 200, utilizador externo 404. |
| Autoria de comentário | Autor derivado da sessão; rejeitar `authorId` enviado pelo cliente. | Passou: corpo forjado HTTP 400; resposta válida mostra Ana Silva. |
| Autenticação e CSRF | Proteger API e rejeitar mutação sem token CSRF. | Passou: dashboard anónimo 401; login sem token 400. |

Resultado: 10 testes automatizados passaram. `node --check static/app.js` não reportou erros. O contrato passou validação YAML: 15 caminhos, 23 operações e referências internas resolvidas.

## Verificações no navegador

- Login e painel verificados com a conta fictícia `ana`; um projeto e contagens de tarefas apareceram após autenticação.
- Criada uma tarefa sem recarregar; atribuída a `bruno`; comentário adicionado; estado atualizado; filtro `Concluída` mostrou uma tarefa enquanto o resumo global continuou em 3 tarefas e 33% concluídas.
- Detalhe verificado em 1440px e 390px. `body.scrollWidth` correspondeu à largura da viewport em ambos; o layout móvel manteve acesso ao painel e ao logout.
- A aplicação não foi endurecida para produção. TLS, gestão de segredos, rate limiting, recuperação de conta e teste de expiração de sessão durante uma interação não fazem parte da validação deste exercício.

## Exemplos de utilização da IA

| Objetivo | Decisão do programador | Verificação |
|---|---|---|
| Comparar o MVP da Ficha 2 com a Ficha 3. | Preservar acesso por workspace, em vez de trocar silenciosamente para `owner_id`. | ERD, API e teste de isolamento entre espaços alinhados. |
| Propor uma stack local para o exercício. | Usar Flask + SQLite + HTML/CSS/JavaScript nativo, mantendo a escolha identificada como académica. | Ambiente virtual, arranque da app e testes automatizados. |
| Rever a implementação de autoria/atribuições. | Rejeitar identidade enviada pelo cliente; autor vem da sessão; atribuição é idempotente. | Teste de payload forjado, membro de outro espaço e pedido duplicado. |

Um primeiro teste esperava `username` no objeto `author`; o contrato expõe `id` e `name`. A expectativa foi corrigida para validar a resposta definida pela API, sem alterar a regra de autoria.

## Ficha 05 — Docker, CI e release candidate

### Análise e preparação

- Componentes: `app.py` cria a aplicação Flask; `auth.py`, `projects.py` e `tasks.py` implementam identidade e API; `templates/` e `static/` servem a interface; `db.py` inicializa e acede à base SQLite; `openapi.yaml` documenta a API.
- Dependência de execução: Flask, declarado em `requirements.txt`. Testes usam `unittest`; o E2E usa Playwright, separado em `requirements-test.txt`.
- Serviços externos em runtime: nenhum. O build Docker descarrega a imagem base Python; a pipeline usa GitHub Actions quando executada no GitHub.
- Configuração: `MATRIX_SECRET_KEY` e `MATRIX_COOKIE_SECURE` para a aplicação; Compose acrescenta `MATRIX_PORT`. A chave local é fornecida pelo utilizador, enquanto o workflow gera uma chave efémera.
- Persistência: SQLite em `instance/`; o Compose monta essa pasta num volume nomeado. Os testes automatizados usam bases temporárias isoladas.
- O seed contém contas fictícias para demonstração; não são credenciais de produção. Não foi encontrado ficheiro `.env` real nem chave privada versionada.

### Verificações locais

- `docker compose config -q`: passou com uma chave temporária gerada localmente.
- `docker compose -p matriz-ficha5 build`: imagem `matriz-ficha5-web` construída com sucesso.
- `docker compose -p matriz-ficha5 up -d --wait`: serviço `web` ficou `healthy`; `/api/health` devolveu `{"status":"ok"}`.
- Seed fictício executado no container; a base tinha 2 projetos antes e depois de `down`/`up`, confirmando persistência do volume `matriz-ficha5_matriz_data`.
- Após a configuração para Render, a imagem foi reconstruída com Gunicorn; Compose ficou saudável na porta local 5056 e o seed terminou com sucesso.
- Simulação isolada do comando Render com `PORT=10000` e `MATRIX_SEED_DEMO=1`: Gunicorn iniciou, `/api/health` respondeu `ok`, e login/criação/leitura/remoção passaram. O container de teste foi removido após o smoke test.
- Smoke test HTTP contra o container: login 200, criar tarefa 201, consultar 200 e remover 204.
- Logs sem erros críticos; Gunicorn iniciou com um worker.
- Inspeção das variáveis da imagem confirmou que `MATRIX_SECRET_KEY` não está embutida. A varredura de caminhos versionados não encontrou `.env` real nem chaves privadas.
- Workflow `.github/workflows/ci.yml` parseado como YAML. `actionlint` não está instalado; a pipeline não foi executada no GitHub porque não foi feito push nem criada uma pull request.
- `render.yaml` foi preparado conforme o schema/documentação oficial do Render; não foi validado pela API/CLI Render nem criado na conta. Configura serviço público free em Frankfurt, com `PORT=10000`, segredo gerado e seed demo.

### Versão candidata

Foi preparada a documentação `0.1.0-rc.1` em `CHANGELOG.md` e `docs/releases/v0.1.0-rc.1.md`. Não foi criada tag nem publicada release ou imagem.

### Limitações

- A pipeline remota continua por verificar no GitHub Actions; a validação local do YAML não substitui essa execução.
- O serviço Render ainda não foi criado; é necessário ligar o repositório no dashboard e aguardar o deploy/checks. O free service tem filesystem efémero; a demo usa dados fictícios públicos e não deve receber dados reais.
- A stack foi iniciada para os testes e parada com `docker compose down`, preservando intencionalmente o volume de validação. Não executar `docker compose down -v` sem intenção explícita de apagar os dados.
- O container usa Gunicorn, mas a aplicação e a configuração continuam académicas e não certificadas para produção.

## Extensão de dashboard e equipas de demonstração

- Suite completa após a extensão: 23 testes unitários/de integração passaram; 2 testes E2E passaram.
- Seed repetido confirmou memberships idempotentes. Ana seleciona Produto, Recursos Humanos e Marketing; Bruno continua limitado a Produto e Inês a Design.
- A dashboard filtrou métricas pelo workspace selecionado. No Produto, concluir uma tarefa atualizou o progresso de 0% para 50%; RH e Marketing mostraram 0 tarefas e 0%.
- E2E confirmou a navegação entre workspaces em desktop e viewport de 390 px, sem overflow horizontal.
- A criação dinâmica de workspaces e gestão de membros não foram implementadas; RH/Marketing são espaços fictícios sem projetos iniciais.