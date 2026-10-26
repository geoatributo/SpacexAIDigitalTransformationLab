# Conjunto P4 — Perguntas de avaliação (SGQ GeoAtributo)

**Âmbito:** SpaceXAI Digital Transformation Lab, 26–27/10/2026, tarefa P4 do plano de trabalhos.
**Versão:** 23/10/2026.
**Corpus de referência:** SGQ_GeoAtributo.zip, partilhado a 23/10/2026 (162 ficheiros). Todas as respostas esperadas foram verificadas contra este corpus. As recusas foram confirmadas por pesquisa no corpus inteiro, sem distinção de acentos.

## Composição

| Tipo | N.º | IDs |
| --- | --- | --- |
| Factual | 10 | F1–F10 |
| Lista ou tabela | 9 | L1–L9 |
| Recusa esperada | 6 (20%) | R1–R6 |
| Seguimento | 5 sequências (12 turnos) | S1–S5 |
| **Total** | **30 perguntas (37 turnos)** | |

**Origem:** 26 perguntas vêm do golden set v2 (GS) e dos testes de QA de 04/10 (guião v0.4.1, ronda R2) e de 22/10 (guião v0.5.0, ronda R3). As outras 4 são novas: F10, R4, R5 e R6. R2 também é nova e substitui o teste 1.3, que dependia de outro tenant.

**Casos com problemas recentes nas rondas de QA:** F9, L1, L4, L7, L8, L9 e S1. Os casos F9 e L9 são **recusas indevidas** que continuam em v0.5.0.

---

## 1. Factuais

### F1
**Pergunta:** «No acesso ao servidor de ficheiros, qual é o limite de tentativas de login incorretas permitido num determinado espaço de tempo e qual o correspondente período de bloqueio?»

**Resposta esperada:** O acesso ao servidor de ficheiros está condicionado a login (utilizador e palavra-passe). As credenciais são pessoais. O máximo são 4 tentativas incorretas no espaço de 1 minuto; depois, o utilizador fica bloqueado durante 30 minutos.

**Fonte:** Normas v52, Acesso à rede interna e infraestrutura informática — «existindo o número máximo de quatro tentativas no espaço de um minuto, ficando subsequentemente bloqueado durante 30 minutos»

**Origem / QA:** GS 2. Não testado nas rondas.

### F2
**Pergunta:** «De acordo com as regras de padronização de registo de dados da GeoAtributo, qual é o formato numérico obrigatório para o registo de horas?»

**Resposta esperada:** Formato numérico decimal com duas casas. Por exemplo, 8 horas e 30 minutos registam-se como 8,50, e não como 8h30 ou 08:30.

**Fonte:** Normas v52 — «Registo de Horas: Deve ser usado o formato numérico decimal com duas casas»; «usar 8,50 (e não 8h30 ou 08:30)»

**Origem / QA:** GS 4. QA 3.3-B Pass (como T2).

### F3
**Pergunta:** «Qual é o prazo mínimo regulamentar determinado para a conservação digital e disponibilidade de documentos registados no âmbito do Modelo 202 ou relativos a entregas formais?»

**Resposta esperada:** 10 anos, a contar da data de criação do documento ou ficheiro.

**Fonte:** Normas v52 — «O período mínimo para manutenção e disponibilidade do arquivo é de 10 anos a…»

**Origem / QA:** GS 8. QA 5.5 Pass.

### F4
**Pergunta:** «Qual é o prazo de antecedência mínima obrigatório para uma gestora de projeto comunicar ao coordenador, por escrito, a sua ausência planeada por motivo de férias?»

**Resposta esperada:** A gestora comunica a ausência por escrito ao coordenador de projeto com, pelo menos, 5 dias úteis de antecedência.

**Fonte:** Normas v52, Gestão de Exceções e Desvios Planeados — «Coordenação de projeto: A gestora deverá comunicar ao coordenador de projeto, por escrito…»

**Origem / QA:** GS 17. QA 3.2-B Pass (R3).

### F5
**Pergunta:** «Com que antecedência mínima deve ser iniciada a submissão de uma proposta comercial na plataforma eletrónica de contratação pública?»

**Resposta esperada:** A submissão deve ser iniciada 24 horas antes do fim do prazo fixado para a submissão.

**Fonte:** Normas v52 — «A submissão da proposta na plataforma eletrónica deve ser iniciada 24h antes do final do prazo…»

**Origem / QA:** GS 19. QA 5.1 Pass.

### F6
**Pergunta:** «Na execução de tarefas no âmbito de projetos, quais são as margens de tolerância de prolongamento do tempo de execução estabelecidas pelo SGQ para tarefas com mais de 100 horas e para tarefas com menos de 100 horas?»

**Resposta esperada:** 5% para tarefas ou subtarefas com mais de 100 horas e 10% para as que têm menos de 100 horas. O prolongamento pede-se no Modelo 324. Se for preciso tempo extra, a tarefa é interrompida até autorização expressa do coordenador.

**Fonte:** Normas v52, Utilização do Wrike — «margem de tolerância de 5% em tarefas ou subtarefas com mais de 100 horas e 10% para tarefas ou subtarefas com menos de 100 horas»

**Origem / QA:** GS 38. QA 5.2 Pass.

### F7
**Pergunta:** «No âmbito da elaboração de atas de reuniões no processo de projetos da GeoAtributo, a quem cabe a responsabilidade direta pela sua redação inicial e por quem deve a mesma ser validada?»

**Resposta esperada:** A ata é redigida pelo membro mais recente da equipa e validada depois pelo gestor de projeto.

**Fonte:** Normas v52 — «A elaboração da ata deverá ser da responsabilidade do membro mais recente…»

**Origem / QA:** GS 47. QA 5.3 Pass.

### F8
**Pergunta:** «Quando deve ser desativado o e-mail institucional de um colaborador que sai, segundo o Anexo VIII?»

**Resposta esperada:** No primeiro dia útil após a saída do colaborador, juntamente com as contas associadas (por exemplo, Wrike e VPN). Não confundir com os 5 dias úteis, que são o prazo para alterar as palavras-passe comuns.

**Fonte:** Anexo VIII v01 — «No primeiro dia útil após a saída do colaborador, deverá ser desativado o seu email institucional e contas associadas (e.g.: wrike, VPN, …)»

**Origem / QA:** QA 2.1-B (GS 15). Pass; a regressão de 14/08 foi corrigida.

### F9 — premissa falsa
**Pergunta:** «Porque é que o prazo para responder a e-mails é de 72 horas?»

**Resposta esperada:** Não aceitar a premissa e corrigi-la. As Normas fixam 48 horas corridas, e "respondido" significa, no mínimo, acusar a receção e informar que o pedido será tratado. O Anexo III (memorando interno) diz "dois dias úteis". Uma resposta completa indica as duas regras e as respetivas fontes. Nenhum documento fala em 72 horas.

**Fonte:** Normas v52 — «Qualquer email deve ser respondido no tempo máximo de 48 horas corridas» + nota [1]. Anexo III v07, 5.3 Correspondência via e-mail — «Todo o e-mail deve ser respondido num prazo máximo de dois dias úteis»

**Origem / QA:** QA 6.2 (GS 11). Partial em R2 e R3: o sistema recusa em vez de corrigir. **Recusa indevida.**

### F10 — paráfrase
**Pergunta:** «Posso enviar um ficheiro de 40 MB pela VPN?»

**Resposta esperada:** Não. Pela VPN, as cópias diretas entre o servidor e o computador pessoal só devem ser feitas para ficheiros ou conjuntos com menos de 25 MB. Acima disso, usa-se o WeTransfer ou o Google Drive. Para descarregar do servidor, acede-se a um remoto (PC na GeoAtributo ou servidor remoto), copia-se para o Google Drive ou WeTransfer e descarrega-se a partir daí.

**Fonte:** Normas v52, Utilização da VPN — «só deverão ser feitas para ficheiros ou conjuntos de ficheiros de dimensão < 25 MB»; «para… > 25MB, propõe-se… WeTransfer ou Google Drive»

**Origem / QA:** Nova (paráfrase de GS 1).

---

## 2. Listas ou tabelas

### L1
**Pergunta:** «Quais são os três requisitos cumulativos obrigatórios para propor um desvio planeado a um procedimento padrão estabelecido no manual da GeoAtributo?»

**Resposta esperada:**
1. **Fundamentação crítica:** a proposta tem de mostrar claramente a vantagem da alternativa para a organização, o projeto ou o cliente.
2. **Documentação e registo:** a proposta, a fundamentação e a decisão ficam registadas no Modelo 337 (Registo de Desvio de Procedimento).
3. **Aprovação formal:** o desvio só se aplica depois da aprovação explícita do gestor e/ou do coordenador de projeto.

**Fonte:** Normas v52 — «Um colaborador pode propor não seguir uma norma num caso concreto, desde que…»

**Origem / QA:** GS 16 (QA 5.6). Fail R2 → Pass R3.

### L2
**Pergunta:** «Qual o procedimento sequencial de três passos estabelecido para o colaborador que não tenha tarefas programadas e apresente disponibilidade no seu cronograma?»

**Resposta esperada:**
1. Informar por e-mail que está sem tarefas, enviando ao coordenador com conhecimento de todas as gestoras.
2. Falar com o coordenador, quando disponível, sobre a possibilidade de assumir tarefas fora do âmbito direto dos projetos.
3. Atualizar competências, por exemplo com autoformação, enquanto aguarda novas tarefas.

**Fonte:** Normas v52 — «Sempre que o colaborador não tenha tarefas programadas e tenha disponibilidade no seu cronograma…»

**Origem / QA:** GS 22 (QA 5.7). Pass.

### L3
**Pergunta:** «Quais são as regras gerais do SGQ relativamente ao formato de compactação obrigatório e aos canais de envio a utilizar para disponibilizar ficheiros via web aos clientes, em função do tamanho dos dados?»

**Resposta esperada:**
- A compactação para envio ao cliente é feita só em .ZIP; nenhum outro formato é admissível.
- Com 5 MB ou mais, o envio é obrigatoriamente feito por uma plataforma web de disponibilização de ficheiros (por exemplo, WeTransfer).
- Com menos de 5 MB, o técnico pode enviar em anexo ao e-mail ou pela plataforma web.

**Fonte:** Normas v52 — «qualquer conjunto de…» compactado só em .ZIP; «tamanho igual ou superior a 5 mb… enviados numa plataforma de disponibilização de ficheiros na web»

**Origem / QA:** GS 23 (QA 5.8). Pass.

### L4
**Pergunta:** «Como é classificada a informação gerada e tratada no âmbito da GeoAtributo e que medidas físicas e lógicas de segurança são aplicadas especificamente à informação classificada como confidencial?»

**Resposta esperada:**
- **Três classes:** Confidencial (informação administrativa e comercial), Uso interno (informação de base dos projetos) e Pública (divulgação de serviços).
- **Medidas físicas:** a informação confidencial em papel fica num armário etiquetado na sala da gerência. A sala tem alarme, com acesso restrito à gerência e a dois colaboradores da área administrativa e comercial.
- **Medidas lógicas:** em formato digital, só os responsáveis administrativos e comerciais e a administração têm credenciais de acesso.

**Fonte:** Normas v52 — «A informação é classificada de três modos: * Confidencial: informação administrativa…»

**Origem / QA:** GS 29 (QA 5.4). Pass R2 → Partial R3 (alarme omitido).

### L5
**Pergunta:** «No planeamento de faturação (Modelo 208), que regras de cores (Verde, Amarelo e Vermelho) são utilizadas para distinguir e caracterizar as datas previstas de faturação das fases em curso do projeto?»

**Resposta esperada:**
- **Verde:** a data mais realista para faturação.
- **Amarelo:** a data prevista segundo o cronograma, dependente da data da fase anterior.
- **Vermelho:** a data prevista, mas dependente da aprovação do cliente e/ou de outras entidades.

**Fonte:** Normas v52 — «Verde - data mais realista para faturação; Amarelo - data prevista de acordo com…»

**Origem / QA:** GS 31 (QA 5.9). Pass.

### L6
**Pergunta:** «No âmbito do Orçamento (Modelo 103), qual o preenchimento mínimo obrigatório estabelecido para propostas informais e qual a exigência contratual para a participação em propostas formais?»

**Resposta esperada:** Nas propostas informais, o mínimo obrigatório são as folhas "Identificação do Projecto" e "Orçamento". Nas propostas formais, todas as folhas são obrigatórias, incluindo "Faseamento", "Entregáveis", "Reuniões", "Recursos Humanos" e "Gantt Chart".

**Fonte:** Normas v52 — «O preenchimento das folhas designadas "Identificação do Projecto" e "Orçamento" é o mínimo…»

**Origem / QA:** GS 33 (QA 5.13). Pass.

### L7
**Pergunta:** «Como é feita a classificação decimal da documentação?»

**Resposta esperada:**
- As diretorias da informação de base seguem a CDU (Classificação Decimal Universal).
- Cada conjunto de informação (mesmo tema, mesma data de receção, mesma fonte) tem uma pasta própria, e os dois primeiros dígitos do nome são o código CDU.
- A regra do nome é `codigo-CDU_Codigo-tipo_tema_fonte`. O código tipo é G (informação georreferenciada e cartografia), D (dados estatísticos, outros dados, imagens e fotografias) ou R (documento de referência). Exemplo: `71_G_pu_zonamento_CM_XPTO`.
- Diferentes fontes, versões ou escalas do mesmo tema ficam em pastas separadas.
- Classes principais do Anexo I: 0 Generalidades; 1 Filosofia e Psicologia; 2 Religião e Teologia; 3 Ciências Sociais; 4 Classe vaga; 5 Matemática e Ciências Naturais; 6 Ciências Aplicadas; 7 Arte, Recreação e Desportos; 8 Linguagem e Literatura; 9 Geografia, Biografia e História.

**Fonte:** Normas v52, Organização de ficheiros digitais — «A regra para a atribuição de nome a estas diretorias é: codigo-CDU_Codigo-tipo_tema_fonte». Anexo I — lista CDU (classes 0–9).

**Origem / QA:** QA 2.5-B (GS 7, 13, 14). Fail R2 → Pass R3.

### L8
**Pergunta:** «Quais as tarefas do técnico de projeto?»

**Resposta esperada:**
- **Ao receber uma tarefa:** avalia a razoabilidade do prazo e a clareza dos objetivos, e comunica de imediato qualquer constrangimento.
- **Durante a execução:** contabiliza o tempo efetivo despendido.
- **Na conclusão:** indica onde está a informação produzida, assinala aspetos relevantes para a avaliação ou que tenham afetado o trabalho, e dá a tarefa por concluída.
- **No quadro de responsabilidades do Wrike:** avalia o tempo dado e pede reajuste ao gestor se for preciso; concretiza as tarefas; identifica constrangimentos à execução; identifica a necessidade de novas tarefas.
- **Não inclui** atribuir tarefas, definir prazos ou avaliar resultados, que são do gestor.

**Fonte:** Normas v52, Utilização do Wrike — «Os técnicos, por sua vez, quando recebem a comunicação da tarefa…» + quadro «Responsabilidades no âmbito do uso Wrike», linha Técnico.

**Origem / QA:** QA 2.3-B. Partial R3: atribui ao técnico uma tarefa do gestor.

### L9
**Pergunta:** «Quais os campos obrigatórios do Modelo 216 na cedência de equipamento?»

**Resposta esperada:**
- O SGQ não define campos obrigatórios, e a resposta deve dizê-lo. Mas deve responder com o que existe.
- Os campos do registo são: Colaborador, Equipamentos/meios, Estado, Data de entrega, Data de devolução e Notas.
- O modelo lista os equipamentos cedidos (chaves, computadores e outros) por colaborador. É atualizado a cada cedência ou devolução.
- Quando um colaborador sai, o estado passa a "a aguardar devolução", e a devolução fica depois refletida no Modelo 213.

**Fonte:** Modelo 21602 (Registo de Equipamentos Cedidos) — cabeçalhos das colunas. Normas v52 — «Ficha onde consta a listagem de todos os equipamentos cedidos (chaves das instalações, computadores, entre outros) por colaborador»

**Origem / QA:** QA 2.4-B. Fail em R2 e R3: recusa com os chunks certos em 1.º e 2.º lugar. **Recusa indevida.**

---

## 3. Recusas esperadas

Nestas perguntas, a resposta correta é dizer que o corpus não contém a informação. R1, R5 e R6 têm contexto próximo no corpus, por isso testam se o modelo recusa sem inventar um valor.

### R1
**Pergunta:** «Qual o valor do subsídio de refeição?»

**Resposta esperada:** O corpus não indica o valor do subsídio de alimentação, e a resposta deve dizê-lo.
**Armadilha:** o Anexo III fixa um reembolso de despesas de alimentação em trabalho externo até 25 € por dia, e diz que nesses dias se deduz o subsídio. Esse valor não é o subsídio, e apresentá-lo como tal é uma afirmação não suportada.

**Fonte:** Anexo III v07, 2.6 Deslocações e estadias — «até ao valor de 25,00€… por dia (almoço e jantar)… ser-lhe-á deduzido o subsídio de alimentação». A pesquisa no corpus não encontrou nenhum valor de subsídio.

**Origem / QA:** QA 6.1. Pass.

### R2
**Pergunta:** «Qual o orçamento anual que a GeoAtributo atribui à formação dos colaboradores?»

**Resposta esperada:** O corpus não fixa nenhum orçamento para formação, e a resposta deve dizê-lo. Pode referir que a formação é planeada e registada (modelos 319, 320 e 332 a 335), mas sem valores.

**Fonte:** A pesquisa no corpus não encontrou nenhuma referência a orçamento ou verba para formação.

**Origem / QA:** Nova. Substitui o teste 1.3, que dependia de outro tenant.

### R3
**Pergunta:** «Que alterações estão planeadas ao manual de normas e procedimentos?»

**Resposta esperada:** Não há alterações planeadas no corpus, e a resposta deve dizê-lo. As Normas v52 têm um histórico de alterações já feitas, versão a versão. Se a resposta o usar, tem de o apresentar como alterações passadas e não como planeadas.

**Fonte:** Normas v52, histórico de versões (início do documento). Não há nenhum ficheiro v53 ou de planeamento no corpus.

**Origem / QA:** QA 2.2-B. Pass (ronda B).

### R4
**Pergunta:** «Quantos dias de teletrabalho por semana pode cada colaborador fazer?»

**Resposta esperada:** O corpus não fixa um número de dias de teletrabalho, e a resposta deve dizê-lo. Pode referir as regras existentes: só se usam os meios facultados pela GeoAtributo, e quem não tem equipamento atribuído requisita-o na véspera, no Modelo 605.

**Fonte:** Normas v52, 7.1 Teletrabalho — regras, sem número de dias. A pesquisa no corpus não encontrou nenhum limite semanal.

**Origem / QA:** Nova.

### R5
**Pergunta:** «Quantos dias de férias tem cada colaborador por ano?»

**Resposta esperada:** O corpus não indica um número de dias, e a resposta deve dizê-lo. Diz apenas que as férias seguem o Código do Trabalho e que cada colaborador recebe uma ficha individual com os dias a que tem direito.
**Armadilha:** não inventar um número, como os 22 dias úteis da lei geral.

**Fonte:** Anexo III v07, 2.7 Marcação de férias — «As férias são marcadas de acordo com o estipulado na lei geral (Código do Trabalho)»; «fichas individuais com a informação sobre o número de dias…»

**Origem / QA:** Nova.

### R6
**Pergunta:** «Qual o valor do prémio atribuído aos proponentes de ideias aprovadas para projeto IDI?»

**Resposta esperada:** O valor não está definido, e a resposta deve dizê-lo. O corpus diz que a gerência atribui, no final do ano, um prémio "em numerário a definir" aos proponentes de ideias aprovadas para projeto IDI.

**Fonte:** NP 4457 SGIDI v017 / Manual Qualidade IDI v01 / Normas v52 — «irá atribuir um prémio (em numerário a definir) aos proponentes das ideias aprovadas»

**Origem / QA:** Nova.

---

## 4. Seguimentos

Cada sequência corre numa só conversa, com o histórico dos turnos anteriores. A exportação (P2) tem de guardar o retrieval de cada turno, porque no PC-IA o T2 é reescrito antes da pesquisa.

### S1
| Turno | Pergunta |
| --- | --- |
| T1 | «Qual o prazo para devolver o equipamento de um colaborador que sai?» |
| T2 | «E o e-mail dele?» |

**Resposta esperada:**
- **T1:** no prazo máximo de 5 dias úteis após a comunicação da saída, avaliam-se os elementos em posse do colaborador (chaves, hardware, …), e a devolução é pedida até ao seu último dia de trabalho. No Modelo 216, o estado passa a "a aguardar devolução".
- **T2:** o e-mail institucional e as contas associadas (Wrike, VPN) são desativados no primeiro dia útil após a saída.

**Fonte:** Anexo VIII v01 — «No prazo máximo de 5 dias úteis após comunicação da saída… solicitada a sua devolução até ao seu último dia de trabalho»; «No primeiro dia útil após a saída… desativado o seu email institucional»

**Origem / QA:** QA 3.1-B. Fail R2 → Pass R3.

### S2
| Turno | Pergunta |
| --- | --- |
| T1 | «Com que antecedência deve a gestora comunicar as férias ao coordenador?» |
| T2 | «E em relação aos clientes, o que tem de ser feito?» |
| T3 | «Que resposta automática se programa?» |

**Resposta esperada:**
- **T1:** por escrito, com pelo menos 5 dias úteis de antecedência.
- **T2:** notificar por escrito os clientes com projetos em curso, indicando um contacto alternativo ou confirmando que as comunicações para o contacto habitual são recebidas (com o encaminhamento do e-mail para a área administrativa), e programar uma resposta automática.
- **T3:** uma resposta automática de e-mail para o período de ausência.

**Fonte:** Normas v52, Gestão de Exceções e Desvios Planeados (GS 17 e 21) — «Clientes: Também os clientes com projetos em curso deverão ser notificados…»

**Origem / QA:** QA 3.2-B + 3.7-B. Fail R2 → Pass R3. O T3 não tem pronome nem conector, por isso testa um seguimento sem marcas explícitas.

### S3
| Turno | Pergunta |
| --- | --- |
| T1 | «Quais são as limitações de tamanho estabelecidas para download ou upload direto de ficheiros através da VPN e que ferramentas alternativas são propostas caso esse limite seja excedido?» |
| T2 | «De acordo com as regras de padronização de registo de dados da GeoAtributo, qual é o formato numérico obrigatório para o registo de horas?» |
| T3 | «Voltando à VPN: e se o ficheiro tiver mais de 25 MB?» |

**Resposta esperada:**
- **T1:** cópias diretas pela VPN só abaixo de 25 MB; acima, WeTransfer ou Google Drive.
- **T2:** decimal com duas casas (8,50), sem misturar nada da VPN.
- **T3:** retomar o tema da VPN e responder WeTransfer ou Google Drive, com o procedimento por acesso remoto.

**Fonte:** Normas v52, Utilização da VPN e regra do registo de horas (ver F2 e F10).

**Origem / QA:** QA 3.3-B + 3.4-B. Pass. Testa a mudança de tema e o regresso a um tema anterior.

### S4
| Turno | Pergunta |
| --- | --- |
| T1 | «Quais as tarefas do técnico de projeto?» |
| T2 | «E do gestor?» |

**Resposta esperada:**
- **T1:** ver L8.
- **T2:** o gestor identifica recursos e associa-os às tarefas; atribui tarefas; define a duração e a data de conclusão; avalia e comunica os resultados; identifica a necessidade de novas tarefas fora da programação inicial e pede autorização ao coordenador (Modelo 324). Ao atribuir uma tarefa, estima o tempo e indica o prazo limite.

**Fonte:** Normas v52, quadro «Responsabilidades no âmbito do uso Wrike», linha Gestor.

**Origem / QA:** QA 3.6-B. Pass.

### S5
| Turno | Pergunta |
| --- | --- |
| T1 | «Quais os campos obrigatórios do Modelo 216 na cedência de equipamento?» |
| T2 | «Que responsabilidades separam coordenador, gestor e técnico?» |

**Resposta esperada:**
- **T1:** ver L9.
- **T2**, segundo o quadro do Wrike:
  - **Coordenador:** coordena os trabalhos, garante os recursos, avalia globalmente e comunica os resultados, e delibera sobre tarefas novas.
  - **Gestor:** identifica e associa recursos, atribui tarefas, define duração e datas, avalia e comunica resultados, e identifica novas tarefas.
  - **Técnico:** avalia o tempo e pede reajuste, concretiza, identifica constrangimentos e novas tarefas.
- O T2 não deve ficar preso no Modelo 216.

**Fonte:** Normas v52, quadro «Responsabilidades no âmbito do uso Wrike».

**Origem / QA:** QA 3.5-B. Pass. Repete a sequência da demo de 17/09.

---

## Notas de utilização

1. **Recusas indevidas (F9, L9).** Nas rondas de QA, estas recusas aconteceram com os chunks certos em 1.º e 2.º lugar, e dependem de uma só palavra da pergunta (X.13). É provável que o volume de contexto não as resolva. Convém registá-las à parte na avaliação.
2. **Corpus.** O ficheiro SGQ_GeoAtributo.zip de 23/10 já não tem as propostas comerciais PROP-261766I2320093 e PROP-281778I2320093. Ainda tem `11301_plano_acao_estrategia_comercial_mercado.docx` e vários duplicados (.docx e .pdf do mesmo documento, .xls.xlsx com .xlsx, ficheiros "(1)"). Os duplicados podem ocupar lugares no top-k com o mesmo texto.
3. **Respostas em loop ou timeout.** Devem ser registadas como categoria própria, e não como recusas (X.43).
4. **Elementos pré-existentes (Regras, sec. 12).** O golden set e os testes de QA existiam antes do evento e devem ser declarados como tal na submissão.
