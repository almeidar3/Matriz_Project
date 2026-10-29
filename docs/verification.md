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