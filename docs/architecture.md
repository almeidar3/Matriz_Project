# Proposta de arquitetura

## Estado e âmbito

Esta é uma proposta produzida para a Ficha Prática Laboratorial 02, baseada no MVP de [`requirements.md`](requirements.md) e nas histórias de [`user-stories.md`](user-stories.md). A arquitetura ainda não foi aprovada pelo cliente. Não escolhe linguagem, framework, fornecedor de base de dados, alojamento nem mecanismo de autenticação, e não descreve uma implementação funcional.
Esta proposta começou na Ficha Prática Laboratorial 02 e foi consolidada para a Ficha 03. A necessidade geral do cliente continua a ser o único facto confirmado; as funcionalidades detalhadas permanecem propostas académicas. Para tornar a implementação reproduzível, esta atividade seleciona Flask, SQLite e páginas HTML/CSS/JavaScript servidas pela mesma aplicação. Esta escolha vale para o exercício local, não é uma decisão de produção.

## Comparação de alternativas

| Alternativa | Vantagens para a Matriz | Custos e riscos | Adequação ao MVP |
|---|---|---|---|
| Monólito | Uma aplicação e um fluxo de entrega simples. | Os módulos podem ficar acoplados se não houver limites explícitos. | Adequado; simples, mas menos explícito quanto à organização interna. |
| Monólito modular | Uma aplicação implantável, com responsabilidades separadas por módulos e fronteiras internas claras. | Exige disciplina para manter as dependências entre módulos controladas. | **Recomendado:** suporta o âmbito pequeno do MVP sem introduzir operação distribuída. |
| Microserviços | Permite implantação e escala independentes por serviço. | Acrescenta comunicação de rede, observabilidade, segurança e operação distribuída. | Desproporcionado para as necessidades e escala ainda desconhecidas. |

## Recomendação

Usar um **monólito modular** como ponto de partida. Projetos, tarefas e pertença ao espaço de trabalho partilham regras de autorização e operações relacionadas; mantê-los numa aplicação reduz a complexidade operacional, enquanto módulos com responsabilidades claras deixam espaço para evolução. Não há evidência de escala, equipas autónomas ou requisitos de implantação independente que justifiquem microserviços.

Para a Ficha 03, a implementação usa Flask para HTTP, sessões e templates, SQLite para persistência e JavaScript nativo para atualizar dados pela API. Isto evita um segundo runtime e um serviço de base de dados para o exercício. A configuração é local e não deve ser interpretada como arquitetura de produção.

## Componentes e responsabilidades

- **Interface web:** apresenta autenticação, painel, projetos, tarefas, responsáveis e comentários; recolhe ações do utilizador. Não é fronteira de autorização.
- **API da aplicação:** expõe os contratos REST documentados em [`../openapi.yaml`](../openapi.yaml), valida entradas e traduz erros em respostas HTTP.
- **Módulo de identidade e acesso:** resolve a identidade autenticada e verifica pertença ao espaço e papel de administrador em cada operação. O fornecedor e o fluxo de autenticação estão por decidir.
- **Módulo de projetos:** cria e consulta projetos, sempre no contexto do espaço de trabalho.
- **Módulo de tarefas e colaboração:** cria, consulta, atualiza e elimina tarefas; valida estado, prioridade e pertença de cada responsável ao mesmo espaço; regista comentários com autor derivado da sessão.
- **Módulo de progresso:** calcula o total de tarefas e a percentagem concluída conforme RF-06; com zero tarefas apresenta 0%.
- **Persistência:** SQLite guarda espaços, membros, projetos, tarefas, atribuições e comentários. O esquema é inicializado de forma idempotente; a base de dados e a autenticação local servem apenas para demonstração.
## Decisões de implementação para a Ficha 03

- Manter `Workspace` e `WorkspaceMember` da Ficha 02 como fronteira de acesso, em vez de trocar silenciosamente para propriedade individual por `owner_id`.
- Administradores criam, editam e eliminam projetos; membros do espaço consultam projetos e gerem tarefas, responsáveis e comentários.
- Responsáveis elegíveis são membros do mesmo espaço. A relação tarefa-utilizador é muitos-para-muitos, sem atribuições duplicadas.
- Valores técnicos de estado: `TODO`, `IN_PROGRESS` e `DONE`; a interface apresenta `A fazer`, `Em curso` e `Concluída`. Prioridades: `LOW`, `MEDIUM` e `HIGH`.
- A aplicação local usa contas fictícias sem registo público. Pesquisa, filtros e contagens são limitados aos dados autorizados do espaço.

## Decisões ainda pendentes para produção

Os módulos de projetos, tarefas e progresso podem partilhar a mesma aplicação e fronteira transacional. O armazenamento e a implantação concretos ficam para a fase técnica.

## Fluxos principais

1. Um administrador autenticado pede a criação de um projeto. A aplicação valida o papel no espaço, guarda o projeto e devolve a representação criada.
2. Um membro autenticado pede a criação de uma tarefa num projeto. A aplicação verifica o acesso ao projeto e, se indicado, que o responsável pertence ao mesmo espaço; a tarefa começa em `A fazer`.
3. Ao consultar o resumo, a aplicação conta as tarefas do projeto e calcula concluídas / total. Para total igual a zero, devolve 0%.

## Decisões pendentes

- Validar a recomendação de monólito modular, a stack e os limites entre módulos para uso real.
- Escolher alojamento, estratégia de implantação, gestão de segredos e base de dados para produção.
- Definir o ciclo de vida de contas, recuperação de acesso e gestão de sessões.
- Confirmar os papéis, permissões e fronteiras entre espaços e projetos com o cliente.
- Definir requisitos de escala, disponibilidade, desempenho, auditoria e recuperação.

## Revisão de consistência

- O modelo de [`database.md`](database.md) representa projetos e tarefas dentro de um espaço e restringe o responsável a um membro desse espaço.
- [`../openapi.yaml`](../openapi.yaml) documenta criação de projeto e de tarefa, incluindo autenticação e autorização propostas.
- O wireframe em [`ui/wireframe.svg`](ui/wireframe.svg) mostra uma vista de projeto com resumo e tarefas, sem acrescentar fluxos fora do MVP.
- Papeis, permissões, autenticação e tecnologia continuam identificados como propostas ou decisões pendentes, em linha com [`constraints.md`](constraints.md).