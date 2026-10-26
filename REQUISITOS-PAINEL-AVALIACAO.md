# Painel de resultados e avaliação humana — requisitos e termo de utilização
# Results dashboard and human evaluation — requirements and terms of use

Estado / Status: **RASCUNHO para decisão do Ricardo / DRAFT for Ricardo's decision**. Não revisto juridicamente / Not legally reviewed.
Destinatária dos requisitos / Requirements addressee: Kerolayne Bianeck. Origem / Source: decisões do Ricardo, 2026-10-26.

---

# PARTE PT

## 1. Âmbito
Painel de resultados da avaliação comparada (dois sistemas, Gemini e Grok) com cartões de métricas e um componente de avaliação qualitativa humana, às cegas, por par de respostas.

## 2. Decisões do Ricardo (confirmadas)
- D-H1. Cartões visuais por métrica, com cor indicativa de maior ou menor desempenho e dados técnicos da aplicação da métrica, para leitura rápida ou atenta.
- D-H2. O utilizador pode formar a sua própria leitura dos resultados.
- D-H3. Para cada pergunta, o utilizador vê as respostas dos dois sistemas **sem identificação do sistema** e avalia apenas com base na leitura.
- D-H4. Identificação do utilizador por **declaração simples** no início. Existe a opção de **só ver as métricas**, sem avaliar.
- D-H5. As perguntas aparecem, quando aplicável, **a seguir** aos cartões de indicadores.
- D-H6. As respostas são guardadas numa **base de dados** com o nome do utilizador e as suas respostas.
- D-H7. Quadro resumo com o número de utilizadores que responderam e acesso à descarga das respostas.
- D-H8. A questão de dados pessoais dos avaliadores é **desconsiderada**: sistema de experimentação e teste, uso autorizado (decisão do Ricardo).

## 3. Requisitos
### 3.1 Cartões de métricas
- R1. Cada cartão mostra o valor da métrica, o **n** (número de casos), a diferença entre os dois sistemas e a configuração de contexto usada.
- R2. A cor indica desempenho **só se houver limiar acordado**. Os limiares do `CRITERIOS-AVALIACAO.md` são propostas, não valores medidos. Sem limiar acordado, o cartão mostra o valor sem cor de bom/mau, ou a cor é marcada como "provisória".
- R3. Só se comparam execuções com configuração igual, e a configuração está visível.
- R4. Cada cartão tem uma vista de detalhe técnico: como a métrica foi aplicada, a fonte dos dados (ficheiro de execução) e a versão do avaliador/juiz.
- R5. Os excertos e respostas mostrados vêm do corpus já redigido (sem dados pessoais do Ricardo).

### 3.2 Avaliação humana às cegas
- R6. Os dois sistemas aparecem como "Resposta A" e "Resposta B". O nome do sistema não aparece no ecrã, no código visível ao utilizador nem nos pedidos de rede enviados ao navegador antes de a avaliação ser submetida.
- R7. A ordem A/B é **sorteada por avaliação** e a atribuição é gravada, para correção posterior do efeito de posição.
- R8. As duas respostas têm a mesma formatação (sem elementos que revelem o sistema, como estilo de citação ou estrutura).
- R9. Cada avaliação grava: identificador do caso, identificadores das duas execuções, configuração de contexto, atribuição A/B, nome declarado, data e hora, e a avaliação.
- R10. Escala de avaliação qualitativa de **0 a 10** (0 = muito mau, 10 = excelente), visível no ecrã. Cada resposta (A e B) recebe a sua nota. Critérios de leitura por definir pela equipa.
- R11. O nome do avaliador é declarado no início. Dois registos com o mesmo nome contam como o mesmo utilizador, salvo decisão contrária.
- R12. Quem escolhe "só ver as métricas" não é contado como respondente.
- R13. As perguntas surgem a seguir ao cartão relevante, quando aplicável.

### 3.3 Quadro resumo e descarga
- R14. Mostra o número de utilizadores que avaliaram (distintos), o número de avaliações e a cobertura por caso.
- R15. Descarga das respostas em formato aberto (CSV ou JSON), incluindo a atribuição A/B.
- R16. Descarga **aberta a qualquer pessoa com o link público** do site (decisão do Ricardo). O site só fica disponível durante o Evento. Ver pontos em aberto sobre o conteúdo da descarga.

### 3.4 Armazenamento
- R17. Base de dados fora do repositório Git (o histórico do Git é permanente). Local e acesso por definir.
- R18. Cópia de segurança antes do Evento.

## 4. Pontos em aberto
- Critérios de leitura da escala 0-10 (R10).
- Conteúdo da descarga pública (R16): com ou sem o nome dos avaliadores. Como o link é público, o nome de cada avaliador fica acessível a qualquer visitante. Alternativa de custo baixo: a descarga traz um identificador em vez do nome, e o nome só fica na base de dados. Decisão por tomar.
- Site público sem autenticação: qualquer pessoa pode submeter avaliações, incluindo repetidas ou falsas. Definir limite por utilizador ou aceitar o risco e ler os resultados como indicativos.
- Prazo de desativação do site e da base de dados após o Evento.
- Limiares das cores (R2).
- Onde fica a base de dados (R17).

## 5. Termo de utilização (rascunho)
**Sistema de experimentação e teste — uso autorizado**

1. **Natureza.** Este sistema é um ambiente de experimentação e teste do SpaceXAI Digital Transformation Lab. Não é um produto em produção.
2. **Uso autorizado.** O sistema está acessível por link público apenas durante o Evento. A utilização destina-se exclusivamente a avaliar as respostas dos sistemas em teste, pelas pessoas a quem a equipa do Lab deu o link.
3. **Finalidade.** As avaliações servem para comparar o desempenho dos dois sistemas no âmbito do Lab.
4. **Dados recolhidos.** Ao participar, o utilizador declara o seu nome. O nome e as suas avaliações ficam guardados numa base de dados.
5. **Utilização dos dados.** Os dados são usados para a análise e apresentação dos resultados do Lab. As respostas podem ser descarregadas por qualquer pessoa com acesso ao link público durante o Evento.
6. **Ver sem avaliar.** O utilizador pode consultar só as métricas, sem avaliar e sem dados registados na avaliação.
7. **Às cegas.** O sistema que produziu cada resposta não é revelado durante a avaliação.
8. **Resultados indicativos.** Os resultados são de um teste com amostra pequena e não constituem conclusões definitivas.
9. **Sem garantias.** O sistema é fornecido como está, para teste.

*Nota: este texto não foi revisto juridicamente. A decisão do Ricardo é que a questão de dados pessoais dos avaliadores não se aplica por ser um sistema de teste de uso autorizado. O termo informa o utilizador do que é guardado.*

---

# PART EN

## 1. Scope
Results dashboard for the comparative evaluation (two systems, Gemini and Grok) with metric cards and a blind qualitative human evaluation component, per pair of answers.

## 2. Ricardo's decisions (confirmed)
- D-H1. Visual cards per metric, with a colour indicating higher or lower performance and technical data on how the metric was applied, for a quick or a close reading.
- D-H2. The user can form their own reading of the results.
- D-H3. For each question the user sees both systems' answers **without the system identified** and rates based on reading alone.
- D-H4. User identified by **simple declaration** at the start. An option to **only view metrics** exists, without rating.
- D-H5. Questions appear, where applicable, **right after** the indicator cards.
- D-H6. Answers are stored in a **database** with the user's name and their ratings.
- D-H7. Summary panel with the number of users who responded and access to download the responses.
- D-H8. The evaluators' personal-data concern is **disregarded**: experimental and test system, authorised use (Ricardo's decision).

## 3. Requirements
### 3.1 Metric cards
- R1. Each card shows the metric value, **n** (number of cases), the difference between the two systems and the context configuration used.
- R2. Colour indicates performance **only where a threshold is agreed**. Thresholds in `CRITERIOS-AVALIACAO.md` are proposals, not measured values. Without an agreed threshold the card shows the value with no good/bad colour, or the colour is labelled "provisional".
- R3. Only runs with identical configuration are compared, and the configuration is visible.
- R4. Each card has a technical detail view: how the metric was applied, the data source (run file) and the judge/evaluator version.
- R5. Excerpts and answers shown come from the already redacted corpus (no personal data of Ricardo).

### 3.2 Blind human evaluation
- R6. The two systems appear as "Answer A" and "Answer B". The system name does not appear on screen, in user-visible code, or in network requests sent to the browser before the rating is submitted.
- R7. A/B order is **randomised per evaluation** and the assignment is stored, to correct for position effects later.
- R8. Both answers have identical formatting (no elements revealing the system, such as citation style or structure).
- R9. Each rating stores: case identifier, both run identifiers, context configuration, A/B assignment, declared name, timestamp, and the rating.
- R10. Qualitative rating scale of **0 to 10** (0 = very bad, 10 = excellent), visible on screen. Each answer (A and B) gets its own score. Reading criteria to be defined by the team.
- R11. The rater's name is declared at the start. Two records with the same name count as the same user unless decided otherwise.
- R12. Users who choose "view metrics only" are not counted as respondents.
- R13. Questions appear after the relevant card, where applicable.

### 3.3 Summary panel and download
- R14. Shows the number of distinct users who rated, the number of ratings and coverage per case.
- R15. Download of responses in an open format (CSV or JSON), including the A/B assignment.
- R16. Download **open to anyone with the site's public link** (Ricardo's decision). The site is available only during the Event. See open points on download content.

### 3.4 Storage
- R17. Database outside the Git repository (Git history is permanent). Location and access to be defined.
- R18. Backup before the Event.

## 4. Open points
- Reading criteria for the 0-10 scale (R10).
- Content of the public download (R16): with or without evaluators' names. Since the link is public, each evaluator's name is accessible to any visitor. Low-cost alternative: the download carries an identifier instead of the name, and the name stays only in the database. Decision pending.
- Public site without authentication: anyone can submit ratings, including repeated or fake ones. Define a per-user limit or accept the risk and read results as indicative.
- Deadline to shut down the site and database after the Event.
- Colour thresholds (R2).
- Where the database lives (R17).

## 5. Terms of use (draft)
**Experimentation and test system — authorised use**

1. **Nature.** This system is an experimentation and test environment of the SpaceXAI Digital Transformation Lab. It is not a production product.
2. **Authorised use.** The system is reachable by public link only during the Event. Use is exclusively to evaluate the answers of the systems under test, by people the Lab team gave the link to.
3. **Purpose.** Ratings are used to compare the performance of the two systems within the Lab.
4. **Data collected.** By taking part, the user declares their name. The name and ratings are stored in a database.
5. **Use of data.** Data is used to analyse and present the Lab's results. Responses may be downloaded by anyone with access to the public link during the Event.
6. **View without rating.** The user may view the metrics only, without rating and without rating data being recorded.
7. **Blind.** The system that produced each answer is not revealed during the evaluation.
8. **Indicative results.** Results come from a small-sample test and are not definitive conclusions.
9. **No warranty.** The system is provided as is, for testing.

*Note: this text has not been legally reviewed. Ricardo's decision is that the evaluators' personal-data issue does not apply because this is an authorised-use test system. The terms inform the user of what is stored.*
