# Requisitos da Matriz

## Visão e objetivos

O cliente descreveu a necessidade de uma aplicação que permita às equipas organizar projetos, gerir tarefas e acompanhar o progresso do trabalho. A Matriz pretende responder a essa necessidade com uma área partilhada para projetos e tarefas.

**Facto confirmado pelo cliente:** pretende uma aplicação para as equipas organizarem projetos, gerirem tarefas e acompanharem o progresso.

**Proposta, ainda não validada:** os objetivos e requisitos deste documento traduzem essa descrição num MVP inicial. Não representam decisões já tomadas pelo cliente.

## Utilizadores propostos

- **Administrador do espaço de trabalho:** gere os membros e os projetos do espaço.
- **Membro da equipa:** consulta projetos e cria ou atualiza tarefas nos projetos a que tem acesso.

Os papéis e permissões são pressupostos para estruturar a proposta; devem ser confirmados. Não se assume, nesta fase, suporte a convidados, clientes externos ou múltiplos níveis de administração.

## Requisitos funcionais propostos

| ID | Prioridade | Requisito | Justificação |
|---|---|---|---|
| RF-01 | Must | Um administrador pode criar um projeto com nome e descrição opcional e consultar os projetos do espaço de trabalho. | Dá à equipa uma unidade explícita para organizar o trabalho. |
| RF-02 | Must | Um membro autorizado pode criar, consultar e editar tarefas dentro de um projeto. Cada tarefa tem título; descrição é opcional. | É o núcleo da gestão de tarefas. |
| RF-03 | Must | Uma tarefa tem um estado selecionado de uma lista inicial fixa: `A fazer`, `Em curso` ou `Concluída`. Um membro autorizado pode alterar o estado. | Permite acompanhar o fluxo e calcular progresso sem regras configuráveis no MVP. |
| RF-04 | Must | Uma tarefa pode ter um membro responsável e uma data limite, ambos opcionais. | Ajuda a clarificar responsabilidade e prazo sem impedir tarefas ainda não atribuídas. |
| RF-05 | Must | A equipa pode consultar tarefas de um projeto em lista e num quadro agrupado por estado. | Oferece duas formas simples de localizar e acompanhar o trabalho. |
| RF-06 | Must | O projeto apresenta um resumo com o total de tarefas e a quantidade e percentagem de tarefas concluídas. Com zero tarefas, a percentagem é apresentada como 0%. | Torna o progresso observável com uma regra objetiva. |
| RF-07 | Must | O sistema restringe a consulta e alteração de dados aos membros autenticados e autorizados do espaço de trabalho. | Os dados de trabalho da equipa não devem ser públicos. A solução de autenticação fica por decidir. |
| RF-08 | Should | Um administrador pode adicionar ou remover membros do espaço de trabalho. | Permite delimitar quem colabora, mas o convite e o ciclo de vida das contas precisam de validação. |

As prioridades são propostas para discussão. `Must` define o núcleo sugerido do MVP e `Should` uma capacidade desejável que pode ser adiada sem bloquear a validação do fluxo principal.

## Requisitos não funcionais propostos

Estes requisitos carecem de confirmação e de critérios técnicos na fase seguinte:

- **NFR-01 Segurança:** exigir identidade autenticada e autorização por espaço de trabalho antes de permitir acesso a dados privados. Não expor dados de um espaço a utilizadores de outro.
- **NFR-02 Privacidade:** recolher apenas os dados necessários à gestão do trabalho; definir retenção, eliminação e tratamento de dados pessoais antes de produção.
- **NFR-03 Usabilidade:** apresentar nomes de estados e ações de forma consistente nas vistas de lista, quadro e detalhe.
- **NFR-04 Acessibilidade:** os fluxos essenciais devem poder ser operados por teclado e os controlos devem ter nomes acessíveis. O nível de conformidade deve ser acordado.
- **NFR-05 Compatibilidade e desempenho:** navegadores suportados, limites de utilização, disponibilidade e metas de desempenho não foram definidos; devem ser acordados antes da implementação.

## Âmbito do MVP proposto

Inclui projetos, tarefas, estados fixos, atribuição opcional de responsável e prazo, vistas de lista e quadro, resumo de progresso e controlo de acesso a um espaço de trabalho. O fluxo principal é: um administrador cria um projeto; membros autorizados criam e atualizam tarefas; a equipa consulta o estado e o resumo do projeto.

O resumo é calculado como tarefas concluídas / total de tarefas. Se o total for zero, apresenta 0%. Não há nesta proposta outros estados, fluxos de aprovação ou fórmulas de progresso.

## Fora do âmbito inicial

- Planeamento de sprints, dependências, subtarefas, gráficos de Gantt e controlo de tempo.
- Automatizações, campos personalizados, estados configuráveis e relatórios avançados.
- Integrações com ferramentas externas, importação/exportação e aplicações móveis nativas.
- Funcionalidades de faturação, gestão de portefólio ou gestão de recursos.
- Qualquer arquitetura, linguagem, framework ou base de dados específica.

Estas exclusões delimitam a proposta inicial e não são uma decisão permanente do cliente.