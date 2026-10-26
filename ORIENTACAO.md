# Orientação do Lab / Lab guidance — 26-10-2026

Resumo de uma página para a equipa. O texto de referência é o [README](README.md); em caso de diferença, vale o README.
One-page summary for the team. The [README](README.md) is the reference text; if they differ, the README wins.

## Objetivo / Objective

**PT.** Medir, de forma simples e com números, o que muda ao usar o Grok como modelo alternativo ao Gemini (em uso): fundamentação nas fontes, exatidão das citações e recusas corretas, e a que custo em tokens e latência. É uma comparação, não uma substituição. Esta é a pergunta central (decisão do Ricardo, 26-10-2026). O volume e a forma do contexto (pergunta do plano de trabalhos) são um parâmetro da comparação; ver README, secções 1 e 9 (D6). Os dois modelos correm sempre com a mesma configuração.

**EN.** Measure, simply and with numbers, what changes when Grok is used as an alternative model next to Gemini (in use): grounding in sources, citation accuracy and correct refusals, and at what token and latency cost. It is a comparison, not a replacement. This is the central question (Ricardo's decision, 26-10-2026). Context volume and form (the work-plan question) are a parameter of the comparison; see README, sections 1 and 9 (D6). Both models always run with the same configuration.

## O que fazemos / What we do

1. **PT.** Construímos tudo de raiz neste repositório, durante o Evento. O PC-IA é só referência de comportamento: não se copia, não se importa, não se altera (README, secção 0; Regras TAIKAI §7 e §8).
   **EN.** We build everything from scratch in this repository, during the Event. The previous internal system (PC-IA) is a behaviour reference only: not copied, not imported, not changed.
2. **PT.** Corremos os dois modelos sobre o mesmo contexto já recuperado, com o mesmo prompt, os mesmos parâmetros e a mesma temperatura.
   **EN.** Both models run on the same pre-retrieved context, with the same prompt, parameters and temperature.
3. **PT.** Medimos de forma automática: fundamentação, exatidão das citações, recusa correta e indevida, latência e tokens (README, secção 9b). A avaliação qualitativa, por pessoas, é secundária.
   **EN.** Automatic measures: grounding, citation accuracy, correct and wrongful refusals, latency and tokens. Human qualitative review is secondary.
4. **PT.** As perguntas são o conjunto de 50 de referência mais as 30 do P4 (factual, lista ou tabela, recusa esperada, seguimento), em *merge* e sem duplicados.
   **EN.** Questions are the 50 reference questions plus the 30 of P4, merged without duplicates.

## Fases / Phases

- **Fase 1 (curta / short):** Gemini e Grok em 3 a 5 perguntas, mais um caso de recusa sem contexto. / Both models on 3 to 5 questions plus one refusal case with empty context.
- **Fase 2:** variar o volume e a forma do contexto, igual nos dois modelos. / Vary context volume and form, identically for both models.
- **Fase 3:** relatório com os resultados e, se houver tempo, interface. / Report with results and, if time allows, an interface.

## Regras da equipa / Team rules

- **PT.** A chave da API foi criada pela Liliana e, por decisão do Ricardo (ver [DECISAO-CHAVE-API.md](DECISAO-CHAVE-API.md)), fica neste repositório privado. Não a partilhar fora dele (chat, email, outros repositórios).
  **EN.** The API key was created by Liliana and, by Ricardo's decision (see the decision note), is kept in this private repository. Do not share it outside it.
- **PT.** Não colocar no que enviamos às APIs dados de clientes nem dados pessoais. Os desafios D5 e D6 do README tratam do que ainda lá está.
  **EN.** Send no client data or personal data to the APIs. Challenges D5 and D6 in the README cover what is still there.
- **PT.** Os desafios em aberto estão na secção 9 do README. / **EN.** Open challenges are in README section 9.
- **PT.** A decisão final é do Ricardo. / **EN.** Ricardo makes the final decision.

Responsáveis por cada parte / Owners of each part: a definir / to be defined.
