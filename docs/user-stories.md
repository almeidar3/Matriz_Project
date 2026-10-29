# User Stories e critérios de aceitação

Este backlog é uma proposta baseada nos pressupostos de [`requirements.md`](requirements.md). As prioridades indicam a ordem sugerida para o MVP e carecem de validação do cliente.

## US-01 — Criar projeto

**Prioridade:** Must

Como administrador do espaço de trabalho, quero criar um projeto com nome e descrição opcional, para organizar o trabalho da equipa.

**Critérios de aceitação:**

- **Given** que sou administrador autenticado, **when** submeto um nome não vazio, **then** o projeto é criado no meu espaço de trabalho e aparece na lista de projetos.
- **Given** que o nome contém apenas espaços ou está vazio, **when** tento criar o projeto, **then** o projeto não é criado e recebo uma indicação para preencher o nome.
- **Given** que sou membro sem permissão de administração, **when** tento criar um projeto, **then** a operação é recusada e nenhum projeto é criado.

## US-02 — Criar tarefa

**Prioridade:** Must

Como membro da equipa, quero criar uma tarefa num projeto a que tenho acesso, para registar trabalho a realizar.

**Critérios de aceitação:**

- **Given** que tenho acesso ao projeto, **when** crio uma tarefa com título não vazio, **then** a tarefa fica associada ao projeto e começa no estado `A fazer`.
- **Given** que o título está vazio ou contém apenas espaços, **when** submeto a tarefa, **then** ela não é criada e recebo uma indicação para preencher o título.
- **Given** que não tenho acesso ao projeto, **when** tento criar-lhe uma tarefa, **then** a operação é recusada e os dados do projeto não são revelados.

## US-03 — Atualizar estado

**Prioridade:** Must

Como membro da equipa, quero alterar o estado de uma tarefa, para manter atualizado o progresso do trabalho.

**Critérios de aceitação:**

- **Given** uma tarefa a que tenho acesso, **when** seleciono `A fazer`, `Em curso` ou `Concluída`, **then** o novo estado fica guardado e visível na lista e no quadro.
- **Given** um valor de estado que não pertence à lista permitida, **when** tento guardá-lo, **then** a alteração é recusada e o estado anterior mantém-se.

## US-04 — Consultar tarefas por estado

**Prioridade:** Must

Como membro da equipa, quero consultar tarefas numa lista ou num quadro agrupado por estado, para localizar o trabalho e perceber em que fase está.

**Critério de aceitação:**

- **Given** tarefas existentes num projeto, **when** consulto a lista ou o quadro, **then** cada tarefa aparece uma vez, no projeto correto e com o estado guardado.

## US-05 — Atribuir responsável e prazo

**Prioridade:** Must

Como membro da equipa, quero associar um responsável e uma data limite opcionais a uma tarefa, para clarificar quem a acompanha e quando deve estar concluída.

**Critério de aceitação:**

- **Given** uma tarefa editável, **when** guardo um membro do mesmo espaço e uma data válida, **then** ambos aparecem associados à tarefa; se não forem indicados, a tarefa continua válida.

## US-06 — Acompanhar resumo do projeto

**Prioridade:** Must

Como membro da equipa, quero consultar o total e a percentagem de tarefas concluídas, para acompanhar o progresso do projeto.

**Critérios de aceitação:**

- **Given** um projeto com tarefas, **when** consulto o resumo, **then** o total corresponde ao número de tarefas do projeto e a percentagem corresponde a tarefas `Concluída` / total * 100.
- **Given** um projeto sem tarefas, **when** consulto o resumo, **then** o total é 0 e a percentagem apresentada é 0%, sem erro de divisão.
- **Given** que uma tarefa muda de estado, **when** volto a consultar o resumo, **then** os valores refletem o estado guardado.

## US-07 — Gerir membros

**Prioridade:** Should

Como administrador do espaço de trabalho, quero adicionar ou remover membros, para controlar quem pode colaborar nos projetos.

Esta história depende da definição do processo de convite, identidade e tratamento de tarefas de um membro removido; esses detalhes não ficam especificados nesta proposta.

## Extensões da Ficha 03 (propostas académicas)

Estas histórias alargam o MVP para cumprir a atividade; não são requisitos confirmados pelo cliente.

Na Ficha 03, US-11 amplia US-05: a proposta inicial permitia um responsável opcional; a implementação académica permite vários responsáveis do mesmo espaço.

### US-08 — Autenticar utilizador

Como membro registado, quero iniciar e terminar sessão e consultar o meu perfil, para aceder apenas aos dados permitidos.

- Credenciais demonstrativas válidas iniciam uma sessão; credenciais inválidas e pedidos sem sessão são recusados.
- O perfil devolvido corresponde à identidade da sessão; a API nunca aceita identidade enviada no corpo como prova de autorização.
- Terminar sessão invalida a sessão existente.

### US-09 — Gerir projetos

Como administrador do espaço, quero listar, consultar, editar, pesquisar e eliminar projetos, para manter o portefólio do espaço atualizado.

- Só administradores do espaço criam, editam ou eliminam projetos.
- Membros autenticados consultam projetos do seu espaço; recursos de outros espaços não são revelados.
- A pesquisa por nome e a paginação respeitam os parâmetros documentados na API.
- Eliminar um projeto elimina as respetivas tarefas, atribuições e comentários em cascata.

### US-10 — Gerir tarefas com prioridade

Como membro autorizado, quero consultar, editar e eliminar tarefas e definir estado e prioridade, para manter o trabalho atualizado.

- Título tem 3 a 150 caracteres; descrição tem no máximo 2000.
- Estados API: `TODO`, `IN_PROGRESS`, `DONE`; prioridade: `LOW`, `MEDIUM`, `HIGH`; prioridade inicial `MEDIUM`.
- Filtros e contagens refletem todas as tarefas correspondentes, mesmo com paginação.

### US-11 — Gerir responsáveis

Como membro autorizado, quero associar e remover vários responsáveis elegíveis numa tarefa.

- Cada responsável pertence ao mesmo espaço do projeto.
- A mesma atribuição não pode ser criada duas vezes.
- Um utilizador de outro espaço não pode ser atribuído nem consultar a tarefa.

### US-12 — Comentar tarefa

Como membro autorizado, quero adicionar e consultar comentários de uma tarefa, para partilhar contexto do trabalho.

- O conteúdo tem 1 a 2000 caracteres e não pode ser apenas espaços.
- Autor e data são determinados pelo servidor; o cliente não pode falsificá-los.
- Só membros autorizados do espaço consultam ou acrescentam comentários.

### US-13 — Consultar painel e filtrar tarefas

Como membro, quero ver os projetos acessíveis e as contagens por estado e filtrar tarefas por estado e prioridade.

- O painel só agrega projetos do espaço ao qual o utilizador tem acesso.
- Contagens são calculadas sobre o conjunto total, e não apenas sobre resultados da página atual.
- Criar, editar ou eliminar uma tarefa atualiza a lista e as contagens sem recarregar a página.

## Casos excecionais e limites

- Nome de projeto ou título de tarefa vazio ou composto apenas por espaços: rejeitar a criação e indicar o campo inválido.
- Tentativa de consultar ou alterar projeto ou tarefa por alguém sem acesso: recusar sem revelar se o recurso existe.
- Projeto sem tarefas: apresentar total 0 e progresso 0%, sem divisão por zero.
- Responsável que não pertence ao espaço de trabalho: rejeitar a atribuição; a tarefa pode permanecer sem responsável.
- Valor de estado desconhecido: rejeitar a atualização e preservar o estado existente.
- Data limite inválida: rejeitar a atualização; a política para datas passadas ainda precisa de confirmação.