# Lab SpaceXAI — proposta de abordagem (RASCUNHO para revisão)

Regras oficiais do Evento (prazos, entregáveis, PI, pré-existente): [RULES.md](RULES.md).

Data: 26-10-2026 (data do sistema). Estado: rascunho, nada enviado a ninguém.

**Idioma / Language:** os documentos deste repositório passam a ser bilingues (português e inglês). A tradução faz-se **à medida que cada documento é atualizado**; ver a tabela na secção 11. / Documents in this repository are becoming bilingual (Portuguese and English), translated **as each document is updated**; see the table in section 11.

## 0. Regra de trabalho (obrigatória)

Este repositório (`SpacexAIDigitalTransformationLab`) é o único sítio onde se constrói o lab. O projeto **PC-IA** (`geoatributo/pc-ia-cognitive-assistant`) **não se altera**.

- **O que é:** referência e *baseline* de mecanismos (prompts, política de recusa, orçamento de contexto, métricas, fluxo pergunta → contexto → resposta).
- **O que não é:** código-base a editar, *fork* a evoluir, nem pasta para *patches*.
- **Como trabalhar:** ler o PC-IA, copiar o *comportamento* que interessa, e **implementar de raiz aqui**. Código, interface, adaptador xAI, executor comparado e avaliação vivem só neste repositório.
- **O que não fazer:** *commits*, *PRs* ou ficheiros novos no PC-IA; *symlink* ou *import* do código da aplicação original como dependência de runtime.

O PC-IA continua a ser o sistema em uso (Gemini) contra o qual se compara o Grok. A comparação usa o mesmo tipo de mecanismos; a implementação nova é independente.

## 1. Objetivo e critérios (decisão do Ricardo; texto da candidatura)

**Pergunta central** (decisão do Ricardo, 26-10-2026): usar o Grok como **modelo alternativo** ao Gemini (em uso) e **comparar os resultados** dos dois, sobre o **mesmo contexto já recuperado**: o Grok melhora de forma mensurável a fundamentação nas fontes, a exatidão das citações e as recusas corretas? E a que custo e latência? Não se trata de substituir o Gemini, mas de comparar.

O que se constrói no Lab é só o **módulo de geração e a avaliação** (a candidatura descreve o pipeline de ingestão, partição em excertos e pesquisa como já existente e inalterado).

> **EN.** Central question (Ricardo's decision, 26-10-2026): use Grok as an **alternative model** next to Gemini (in use) and **compare the results** on the **same retrieved context**: does Grok measurably improve grounding in sources, citation accuracy and correct refusals, and at what cost and latency? This is a comparison, not a replacement of Gemini. What we build at the Event is only the generation module and the evaluation; the ingestion, chunking and retrieval pipeline is described in our application as existing and unchanged. Measured quantitatively: grounding, citation accuracy, refusal correctness, latency and cost per question. A qualitative side-by-side review by users is a secondary addition.

**Pergunta do plano de trabalhos: parâmetro, não pergunta central** (decisão do Ricardo, 26-10-2026). Segundo a conversa da equipa de 23-10-2026 (o plano em si não foi lido por quem escreveu esta secção), o plano pergunta qual é o volume e a forma de contexto entregue ao modelo que maximiza respostas corretas e recusas corretas, sem aumentar as afirmações não suportadas, e a que custo. Fica como **parâmetro** da comparação (k, vizinhos, limite de caracteres, corte de relevância; ver D6), aplicado de forma igual aos dois modelos. Aplica-se a **regra da mesma configuração**: em cada comparação, os dois modelos correm com o mesmo prompt, o mesmo contexto, os mesmos parâmetros e a mesma temperatura. O que varia é o modelo; o contexto varia em séries separadas. A hipótese de partida da equipa (o modelo recusa em excesso por receber pouco contexto) pode ser testada com essas séries, se o tempo permitir. O código da Fase 1 só cobre o modelo com 6 excertos e 9000 caracteres fixos.

> **EN.** Work-plan question: a parameter, not the central question (Ricardo's decision, 26-10-2026). As quoted in the team chat of 23-10-2026 (the plan itself was not read here), the plan asks what volume and form of context given to the model maximises correct answers and correct refusals without more unsupported claims, and at what cost. It stays a **parameter** of the comparison (k, neighbours, character limit, relevance cut-off; see D6), applied identically to both models. The **same-configuration rule** holds: in every comparison both models run with the same prompt, context, parameters and temperature. The model is what varies; context varies in separate series. The team's starting hypothesis (the model over-refuses because it gets too little context) can be tested with those series if time allows. Phase 1 code only covers the model with fixed 6 chunks and 9000 characters.

- Usar o PC-IA só como referência: os mesmos mecanismos e critérios, reescritos neste repositório.
- Construir de raiz uma interface simples, com o serviço mínimo para interação com o utilizador.
- Avaliar em dois eixos, com o Gemini (em uso) como base:
  1. **Medições quantitativas automáticas**, reimplementadas aqui (sem invocar código do PC-IA): fundamentação nas fontes, exatidão das citações, recusa correta, **latência** e **custo** (tokens e preço por pergunta, a calcular com os preços oficiais dos modelos, por verificar).
  2. **Avaliação qualitativa pelo utilizador**, sobre respostas dos dois sistemas lado a lado. É um acrescento da equipa à candidatura e é secundária.

## 2. Confirmado (leitura de referência, sem alterar o original)

Fonte: `adapters/llm/service.py` em `geoatributo/pc-ia-cognitive-assistant`, 26-10-2026. Só leitura, para saber o *baseline* a recriar aqui.

- O fornecedor do modelo escolhe-se por configuração (`CHAT_PROVIDER` ou `LLM_PROVIDER`; valores aceites: `openai`, `ollama`, `gemini`).
- Já existe um cliente OpenAI com `base_url` configurável (é assim que o Ollama está ligado).
- O ficheiro tem 1287 linhas e mistura lógica de prompts, deteção de perguntas de seguimento, orçamento de contexto e política de recusa. Importa `core.config`, `core.language`, `core.text` e `modules.generation.policy`. Não é um adaptador fino.
- O limite de tamanho da resposta (`max_output_tokens`) só é enviado no caminho do Gemini. No caminho OpenAI/Ollama é calculado e registado, mas não enviado.
- O caminho com medição de tokens (`complete_with_usage`) usa só a API Responses da OpenAI.
- O código tem expressões para limpar variantes do bloco `<scratchpad>` (comentário "X.39"). Não li o corpo da função que as aplica.

## 2b. Avaliação já existente no PC-IA (referência; conteúdo NÃO lido)

Os nomes sugerem avaliação com RAGAS e conjuntos de referência ("gold"), mas isto é inferência a partir dos nomes. Servem para saber *o que* recriar neste repositório, não para ligar ou editar esses ficheiros:

- `modules/evaluation/` (`metrics.py`, `benchmarks.py`, `datasets.py`, `matcher.py`, `service.py`) e `modules/rag/evaluators.py`.
- Scripts: `scripts/evaluate_ragas.py`, `scripts/run_full_ragas_eval.py`, `scripts/compare_ragas_results.py`, `scripts/evaluate_geoatributo_answers.py`, `scripts/run_gold_eval_*.py`.
- Documentação: `docs/ragas_query_set_schema.md`, `docs/testing/gemini-answer-generation-eval-guide.md`, `tests/fixtures/RAGAS_EVAL.README.md`, `tests/fixtures/CHANGELOG_eval.md`.
- Resultados guardados em ficheiros `*_eval_results.json` na raiz do PC-IA.

## 3. Hipóteses (não verificadas)

- A API da xAI (console.x.ai) segue o formato da API da OpenAI, pelo que o ramo do Grok seria pequeno (conhecimento geral, não do material do projeto).
- A API da xAI suporta o mesmo formato da API Responses. Se não suportar, é preciso um caminho alternativo para medir tokens.
- O Grok segue a instrução de produzir o bloco `<scratchpad>`. Só o teste o mostra.
- As métricas do PC-IA podem ser *reproduzidas* neste repositório e aplicadas a um segundo fornecedor. Não se assume *import* do código original. Só se sabe pelos nomes dos ficheiros (secção 2b); o conteúdo não foi lido.

## 4. Desconhecido

- Que modelos Grok estão disponíveis com os créditos do Lab, e o limite de créditos.
- Preços oficiais dos modelos (necessários para o custo por pergunta).
- (Resolvido) Os excertos do SGQ já estão exportados: `data/chunk_data/chunks.json` (1037 excertos de 86 documentos), mais `retrieval.json` (50 perguntas, 50 candidatos cada, sem texto: só identificadores e pontuações, que se ligam a `chunks.json`).

Texto das Regras (§7, §8, §12) e prazos de submissão: ver [RULES.md](RULES.md). Em resumo: construir de raiz neste repositório durante o Evento; bibliotecas públicas com atribuição; PC-IA só como referência, não como código a entregar.

## 5. Arquitetura proposta (tudo neste repositório)

Nada disto se acrescenta ao PC-IA. O original fica intacto; aqui cria-se um serviço novo que *espelha* os mecanismos necessários.

1. **Interface mínima**: uma pergunta, as respostas lado a lado (Gemini em uso e Grok), e o espaço para o utilizador classificar.
2. **Adaptador novo e pequeno para a xAI**: cliente OpenAI com `base_url` da xAI, chave por variável de ambiente, limite de resposta definido. Escrito aqui, não um ramo novo em `adapters/llm/service.py` do PC-IA.
3. **Executor comparado**: a mesma pergunta e o mesmo contexto enviados ao Gemini (base) e ao Grok.
4. **Eixo 1, métricas automáticas**: implementar neste repositório métricas equivalentes às do PC-IA (nomes e intenção na secção 2b; detalhe por confirmar lendo `modules/evaluation/metrics.py` *só como referência*). Medições complementares propostas, a validar: fuga de raciocínio interno para a resposta final, recusa correta quando não há resposta no contexto, latência e tokens usados.
5. **Eixo 2, avaliação qualitativa**: o utilizador vê as respostas dos dois sistemas sem saber qual é qual (proposta, para reduzir enviesamento) e escolhe a melhor ou dá uma nota segundo critérios fixos. Critérios a definir pela equipa (por exemplo, correção, utilidade, linguagem). Os resultados guardam-se com os das métricas para comparar os dois eixos.

## 6. Enquadramento nas Regras

Ver [RULES.md](RULES.md). Leitura para este lab:

- O entregável é trabalho **deste** repositório, feito **durante** o Evento (TAIKAI §7–§8).
- Código pré-existente só se for **público** e **atribuído** (Termos SpaceXAI). O PC-IA não o é: fica como referência de comportamento, sem *fork*, *import* nem patches.
- Na submissão (inglês, até **27-10-2026 13:00** na TAIKAI) declarar: (1) OSS/APIs usadas; (2) o que se observou no PC-IA; (3) o que se construiu aqui (adaptador xAI, executor, avaliação, interface).
- Pitch de 5 minutos em inglês; não colocar na plataforma dados que a empresa não queira públicos.

Confirmar por escrito com o contacto da organização (`laurence.peghaire@x.ai`) antes de apresentar.

### Declaração de elementos pré-existentes (rascunho, em inglês para a submissão)

```markdown
## Pre-existing elements and declaration

**1. Pre-processed organisational data (input only).**
The files in `data/` come from our own organisation's documents. Before the Event they were transformed and adapted by an internal pipeline into chunks that a RAG-type system can use, and a retrieval snapshot was produced for a fixed set of questions. This preparation is not part of the Project, was described in our application as existing and unchanged, and is not part of what we describe as built during the Event. We hold the rights to use these data. They are used only as test input.

**2. Reference questions and answers (50).**
Prepared before the Event and described in our application as "a subset of our internal benchmark questions". Used only as input for evaluation.

**3. Public components** (source indicated) [to confirm which are actually used]:
- OpenAI Python SDK (used with the xAI API endpoint)
- xAI API
- Gemini API
- [any other public library, if used]

**4. Internal reference knowledge.**
We know from a previous internal system how a RAG assistant is evaluated and which behaviours matter. No code from that system is copied or imported here. [to confirm: prompts and the refusal sentence were written here and not copied]

**5. Built during the Event.**
The xAI and Gemini adapters, the comparison runner, the evaluation code (automatic and qualitative) and the interface.
```

Decisão do Ricardo (26-10-2026): assume o risco de o §8 das Regras TAIKAI ("apenas trabalho feito durante o Evento") ser lido contra o uso de `data/`, e clarifica-o por esta declaração. Não está confirmado pela organização.

## 7. Fases

- **Fase 1 (curta)**: 3 a 5 perguntas nos dois sistemas. Verificar formato da resposta, fuga de raciocínio interno e suporte da API Responses.

### Como correr a Fase 1

O código vive só neste repositório (`src/lab`). O PC-IA não se altera.

1. Copiar `.env.example` para `.env` e preencher `GEMINI_API_KEY`. A chave xAI é lida de `CHAVE-API.md` (decisão do Ricardo, ver `DECISAO-CHAVE-API.md`); `XAI_API_KEY` no ambiente ou no `.env` tem prioridade. Não partilhar a chave fora do repositório (chat, email).
2. Instalar dependências: `pip install -r requirements.txt`
3. Correr, com `src` no `PYTHONPATH`:

```text
python -m pip install -r requirements.txt
$env:PYTHONPATH="src"
python -m lab --limit 5
```

Isto envia as perguntas `gold-01` … `gold-05` (mesmo contexto congelado em `data/chunk_data/`) a Gemini e a Grok, mais um caso `refuse-empty` sem contexto. Os resultados vão para `data/runs/` (pasta ignorada pelo git). No fim da run (ou com `python -m lab --eval`) calculam-se métricas lexicais (`correctness`, `grounded_rate`, `completeness`, `pass_rate`, limiar 0.8) para `data/runs/*.eval.json`. Juiz opcional com um terceiro modelo: `python -m lab --eval --judge` (`JUDGE_PROVIDER=gemini`, `JUDGE_MODEL=gemini-3.5-flash` por omissão). Testes sem rede: `python -m pytest`.

#### Flags de contexto

O retrieval não volta a correr: só se escolhe **quanto** texto do ranking congelado vai no prompt. Sem `--max-chars` não há teto de caracteres (chunks nunca são cortados a meio).

| Flag | Default | O que faz |
|---|---|---|
| `--context-mode` | `top_n` | `top_n`, `top_n_adjacent` ou `full_top1` |
| `--top-n` | `6` | Quantos chunks de topo (1–50). Ignorado em `full_top1` |
| `--adjacent-m` | (obrigatório em `top_n_adjacent`) | Vizinhos ±M no mesmo documento, por `chunk_index` |
| `--max-chars` | nenhum | Teto opcional; o próximo chunk que não cabe fica de fora |
| `--dry-run` | off | Monta o contexto e grava JSON, **sem** chamar Gemini/xAI |

```text
# Top 8 chunks (ordem do ranking)
python -m lab --limit 5 --context-mode top_n --top-n 8

# Top 3 + o chunk imediatamente antes e depois de cada um
python -m lab --limit 5 --context-mode top_n_adjacent --top-n 3 --adjacent-m 1

# Os 2 vizinhos de cada lado (M=2)
python -m lab --limit 5 --context-mode top_n_adjacent --top-n 3 --adjacent-m 2

# Documento inteiro do chunk em 1.º lugar
python -m lab --limit 5 --context-mode full_top1

# Ver volume (nº de chunks, caracteres, ids) sem gastar créditos
python -m lab --dry-run --context-mode top_n_adjacent --top-n 5 --adjacent-m 2
```

O JSON da corrida inclui `context_policy`, e por caso `chunk_ids`, `chunk_count` e `char_count`.
- **Fase 2**: aumentar o volume de contexto e comparar o sistema atual (base) com o Grok em paralelo.
- **Fase 3**: interface e relatório de métricas.

## 8. Riscos e pendências

- A chave da API xAI está neste repositório privado, por decisão do Ricardo (`DECISAO-CHAVE-API.md`): quem tem acesso ao repositório ou a um clone pode gastar os créditos, e a chave fica no histórico do Git. Se o link do repositório for dado ao júri ou a terceiros, retirar ou revogar a chave antes.
- Créditos finitos: definir o limite de resposta antes da primeira chamada.
- Dados: confirmar que os dados usados podem ir para uma API externa. Copiar para este repositório só o mínimo necessário; o resto permanece no PC-IA, sem o modificar.
- Dados pessoais no corpus: **tratado em 26-10-2026** (commit `7b29ff7`): o número do cartão de cidadão e a morada pessoal de um gerente foram substituídos por marcadores em 9 ficheiros de `data/`. O texto original continua no histórico do Git (decisão: manter o histórico, não o reescrever). Ver secção 10. Pesquisa feita por padrões de texto, não por leitura de todos os excertos: não garante que não haja outros dados pessoais.
- O conjunto de 50 perguntas só tem casos em que a resposta existe. Passa a ser um **desafio** (secção 9, D1), não só um risco.
- Custo: a Fase 1 corre sem limite de tokens de saída. Definir um antes de escalar para as 50 perguntas.
- Dois eixos de avaliação podem discordar (a métrica favorece um sistema e o utilizador outro). Isso não é falha, mas o relatório deve mostrar ambos e não fundi-los numa nota única.
- Avaliação qualitativa com poucos avaliadores é frágil: indicar o número de avaliadores e de perguntas em qualquer conclusão.

## 9. Desafios para a equipa de programação / Challenges for the dev team

Pontos fracos encontrados na leitura de 26-10-2026, convertidos em requisitos a superar. / Weaknesses found on 26-10-2026, turned into requirements.

**D1. Recusas corretas / Correct refusals.**
- PT: o conjunto de referência tem 50 perguntas e **todas** esperam resposta. A candidatura promete avaliar recusas. Criar casos de recusa durante o Evento (pergunta sem resposta no contexto; pergunta fora do âmbito; contexto com excertos parecidos mas insuficientes), definir "recusa correta" e medir também as recusas indevidas (recusar quando a resposta existe). A Fase 1 já tem um caso sem contexto (`refuse-empty`); é o ponto de partida, não o desafio completo.
- EN: all 50 reference questions expect an answer, yet our application promises to evaluate refusals. Build refusal cases during the Event (answer absent from context; out of scope; near-miss context), define "correct refusal", and also measure wrongful refusals. The existing `refuse-empty` case is only a starting point.
- PT (atualização, 26-10-2026): a base de **30 perguntas** (P4; factual, lista ou tabela, recusa esperada, seguimento), construída a partir do Golden Set e dos relatórios de QA de 04-10 e 22-10, já está em [`data/P4-perguntas-avaliacao.md`](data/P4-perguntas-avaliacao.md). Falta: o *merge* com as 50 perguntas, gerar o `retrieval.json` para as perguntas novas e código para o formato P4 (sequências de seguimento, que o código atual não suporta). As 6 recusas esperadas foram verificadas só contra o conjunto de 162 ficheiros do SGQ; o repositório tem 86 documentos, ver a nota sobre o corpus abaixo.
- EN (update, 26-10-2026): the 30-question P4 base is now in [`data/P4-perguntas-avaliacao.md`](data/P4-perguntas-avaliacao.md). Still missing: the merge with the 50 questions, retrieval for the new questions, and code for the P4 format (follow-up sequences, unsupported by the current code). The 6 expected refusals were checked only against the 162-file SGQ set; this repository has 86 documents, so see the corpus note below.
- PT (corpus, medido a 26-10-2026): o repositório tem **86 documentos** (`manifest.jsonl`), todos em `RAG_pronto`, e 1037 excertos. Medido: (a) dois documentos aparecem duplicados em formatos diferentes: o Anexo VIII (`.docx` e `.md`, 5 excertos cada) e o Anexo II (`.xlsx`, 103 excertos, e `.docx`, 12); (b) `log_erros.txt` está no corpus (1 excerto); (c) 450 dos 1037 excertos (43%) têm `is_low_signal` nos metadados. **Declarado pelo Ricardo (26-10-2026), não verificado pelo assistente:** os ficheiros a mais do conjunto de 162 não têm impacto nas perguntas nem no retrieval. Consequência lógica: se os 86 documentos forem um subconjunto dos 162, as recusas R1 a R6 (sem resposta nos 162) também não têm resposta nos 86; isto só falha se os 86 incluírem ficheiros que não estão nos 162 (não comparado). **Não verificado:** se o código exclui os excertos de baixo sinal antes de montar o contexto. Decisão do Ricardo: só registar; a limpeza, se houver, fica ao Eduardo.
- EN (corpus, measured 26-10-2026): the repository has **86 documents** and 1037 chunks. Measured: (a) two documents are duplicated in different formats (Annex VIII: `.docx` and `.md`, 5 chunks each; Annex II: `.xlsx`, 103 chunks, and `.docx`, 12); (b) `log_erros.txt` is in the corpus (1 chunk); (c) 450 of 1037 chunks (43%) carry `is_low_signal`. **Stated by Ricardo (26-10-2026), not verified by the assistant:** the extra files in the 162-file set have no impact on the questions or on retrieval. Logical consequence: if the 86 documents are a subset of the 162, refusals R1 to R6 (no answer in the 162) also have none in the 86; this fails only if the 86 include files not in the 162 (not compared). **Not verified:** whether the code drops low-signal chunks before building the context. Ricardo decided to record only; any cleanup is up to Eduardo.

**D2. Fundamentação e citações / Grounding and citations.**
- PT: estes dois critérios da candidatura ainda não têm código (só latência, recusa e fuga do bloco de raciocínio). Definir e implementar de raiz: o que conta como afirmação suportada pelo contexto, e quando uma citação é exata (aponta para o excerto que contém a afirmação). Validar o método à mão em algumas respostas antes de o aplicar às 50.
- EN: these two criteria have no code yet. Define and build, from scratch, what counts as a claim supported by the context and when a citation is exact; check the method by hand on a few answers before running all 50.
- Cardápio / Menu: ver [`CRITERIOS-AVALIACAO.md`](CRITERIOS-AVALIACAO.md) (secção D, indicadores 1, 3 e 7, e secção E / section D, indicators 1, 3 and 7, and section E). Opções para seleção pela equipa, não imperativas; recusar um item é válido com justificação. / Options for the team to choose from, not mandatory; any item may be rejected with a reason.

**D3. Origem do texto dos prompts / Provenance of prompt text.**
- PT: confirmar que os prompts e a frase de recusa foram escritos neste repositório e não copiados do PC-IA (secção 6, declaração, ponto 4). Se houver cópia, declarar ou reescrever.
- EN: confirm the prompts and the refusal sentence were written here, not copied from the previous internal system; if copied, declare or rewrite.

**D4. Perguntas fáceis / Easy questions (proposta do assistente, por validar).**
- PT: em 43 das 50 perguntas o excerto certo está em 1.º lugar, pelo que as diferenças entre modelos podem ser pequenas. Acrescentar casos mais difíceis (excerto certo mais abaixo, respostas em lista) e indicar sempre o número de perguntas nas conclusões.
- EN: the right chunk is ranked first in 43 of 50 questions, so model differences may be small. Add harder cases and always state the sample size.

**D5. Propostas de clientes fora dos dados / Client proposals out of the dataset.**
- PT: a equipa decidiu em 23-10 que duas propostas comerciais para clientes (dados de terceiros) não entram no conjunto de dados. Em 26-10 ainda há 41 excertos delas em `data/chunk_data/chunks.json` (de 1037) e os respetivos documentos em texto. Desafio: retirá-las, regenerar `retrieval.json` (as posições mudam) e confirmar que nenhum contexto enviado às APIs as contém. Confirmar também se o repositório partiu do conjunto da opção B (manual de procedimentos, anexos e modelos).
- EN: the team decided on 23-10 that two client proposals (third-party data) stay out of the dataset. On 26-10 they are still in `data/` (41 of 1037 chunks plus the text documents). Challenge: remove them, regenerate `retrieval.json`, and verify no context sent to the APIs contains them. Also confirm the repository started from the option B corpus.

**D6. Parâmetros configuráveis / Configurable parameters.**
- PT: o código fixa 6 excertos e 9000 caracteres. A curva de k (3 a 20) e o limite de caracteres têm de ser parâmetros, aplicados da mesma forma aos dois modelos, com cache dos resultados intermédios para não repetir configurações. Dimensionar primeiro quantas configurações cabem nas cerca de 7 h 15 úteis do Evento (valor dito na conversa; não verificado) e quanto custam em tokens.
- EN: the code fixes 6 chunks and 9000 characters. The k curve (3 to 20) and the character limit must be parameters, applied identically to both models, with caching of intermediate results. First size how many configurations fit in the roughly 7h15 of working time (stated in the chat; unverified) and what they cost in tokens.
- Cardápio / Menu: ver [`CRITERIOS-AVALIACAO.md`](CRITERIOS-AVALIACAO.md) (secções A e B, parâmetros e valores a testar / sections A and B, parameters and values to test). Opções para seleção pela equipa, não imperativas; recusar um item é válido com justificação. / Options for the team to choose from, not mandatory; any item may be rejected with a reason.

**D7. Comparabilidade dos modelos / Model comparability (recomendação, por decidir).**
- Nota / Note: o texto vem da conta `coopera-web` (commit `3d653cd`); a renumeração de D5 para D7 foi feita a 26-10-2026 para não coincidir com o D5 das propostas de clientes. O alias `grok-latest` apontar para `grok-4.7` e os preços citados **não foram verificados** por quem reviu o repositório; confirmar na API antes de decidir. / Text by `coopera-web`; renumbered D5 to D7 to avoid clashing with the client-proposals D5. The `grok-latest` to `grok-4.7` mapping and the prices are **unverified** by the reviewer; check against the API before deciding.
- PT: a configuração atual compara `gemini-flash-lite-latest` (gama ligeira) com `grok-latest`, que em 26-10-2026 aponta para `grok-4.7` (gama de topo, com raciocínio). Assim, a diferença mistura fornecedor e categoria do modelo. Recomendação:
  - **Comparação principal (ligeiro vs ligeiro):** Gemini Flash-Lite vs `grok-4.20-non-reasoning` ou `grok-4.3` com `reasoning_effort: none`. Espelha o sistema em uso. Pelos preços devolvidos pela API da xAI, custam cerca de metade do `grok-4.7` na entrada e menos de metade na saída.
  - **Referência extra (topo vs topo), se os créditos chegarem:** `grok-4.7` vs Gemini Pro.
  - Fixar versões concretas em vez de aliases `latest`; usar o mesmo limite de tokens de resposta e a mesma temperatura; registar se o raciocínio está ligado (afeta latência e custo).
- EN: the current setup compares a lightweight Gemini model with Grok's flagship reasoning model, so differences mix provider and model tier. Recommended: main comparison Flash-Lite vs `grok-4.20-non-reasoning` (or `grok-4.3` with reasoning off); optional flagship-vs-flagship reference `grok-4.7` vs Gemini Pro. Pin versions, match output-token cap and temperature, and record whether reasoning is on.
- Cardápio / Menu: ver [`CRITERIOS-AVALIACAO.md`](CRITERIOS-AVALIACAO.md) (secção C / section C). Opções para seleção pela equipa, não imperativas; recusar um item é válido com justificação. / Options for the team to choose from, not mandatory; any item may be rejected with a reason.

## 9b. Termos / Glossary

Definições de trabalho para uso comum. As marcadas (proposta) são do assistente e precisam de validação; as restantes vêm do plano e da candidatura, como citados na conversa. / Working definitions. Those marked (proposal) are the assistant's and need validation.

| Termo / Term | Definição / Definition |
|---|---|
| Contexto / context | Excertos de documentos entregues ao modelo com a pergunta. / Chunks given to the model with the question. |
| Volume do contexto / context volume | Quantos excertos (k) e quantos caracteres. / Number of chunks (k) and characters. |
| Forma do contexto / context form | Como os excertos são escolhidos e montados: vizinhos, ordem, corte de relevância. / How chunks are selected and assembled: neighbours, order, relevance cutoff. |
| Configuração / configuration | Um conjunto fixo de parâmetros antes do modelo. Dois modelos só se comparam na mesma configuração. / A fixed parameter set applied before the model; models are compared only under the same one. |
| Resposta correta / correct answer | A resposta coincide com a de referência nos factos pedidos (proposta: verificada à mão numa amostra). / Matches the reference on the requested facts (proposal: hand-checked on a sample). |
| Recusa correta / correct refusal | O modelo recusa quando a resposta não está no contexto ou o tipo da pergunta é "recusa esperada". / The model refuses when the answer is not in the context or the type is "expected refusal". |
| Recusa indevida / wrongful refusal | O modelo recusa quando a resposta existe no contexto (proposta). / The model refuses although the answer is in the context (proposal). |
| Afirmação não suportada / unsupported claim | Afirmação na resposta que não consta de nenhum excerto entregue (proposta de definição; o método de medição está por desenhar, ver D2). / Statement in the answer found in none of the given chunks (proposed; measurement method not yet designed, see D2). |
| Fundamentação / grounding | Proporção de afirmações suportadas pelo contexto. / Share of claims supported by the context. |
| Citação exata / citation accuracy | A citação aponta para o excerto que contém a afirmação. / The citation points to the chunk that holds the claim. |
| Tipos de pergunta / question types | Factual, lista ou tabela, recusa esperada, seguimento (do plano). / Factual, list or table, expected refusal, follow-up. |
| Custo / cost | Tokens e latência por pergunta; o preço em euros só com os preços oficiais dos modelos (por verificar). / Tokens and latency per question; money only with official model prices (unverified). |

**Resposta aos desafios / Response to the challenges.**
- PT: o conjunto P4 ([`data/P4-perguntas-avaliacao.md`](data/P4-perguntas-avaliacao.md)) tem 30 perguntas (37 turnos) já tipificadas: 10 factuais, 9 de lista ou tabela, 6 recusas esperadas (R1–R6, três com armadilha de contexto próximo) e 5 sequências de seguimento, com resposta esperada e fonte. Inclui as recusas indevidas F9 e L9 e os casos difíceis das rondas de QA. Vai ser feito um *merge* deste ficheiro com o golden set global de 50 perguntas (não uma soma: as perguntas comuns ficam uma só vez) (`data/geoatributo_base2_gold_questions.json`), o que **contribui** para o D1 (recusas e seguimentos) e em parte para o D4 (casos mais difíceis). Os desafios D2, D3, D5, D6 e D7 não dependem deste conjunto e continuam em aberto (ver tabela de estado).
- EN: the P4 set ([`data/P4-perguntas-avaliacao.md`](data/P4-perguntas-avaliacao.md)) has 30 typed questions (37 turns): 10 factual, 9 list/table, 6 expected refusals and 5 follow-up sequences, each with expected answer and source. It will be merged (not simply added) with the global 50-question golden set, with overlapping questions kept once, which contributes to D1 (refusals, follow-ups) and partly to D4 (harder cases). D2, D3, D5, D6 and D7 do not depend on this set and remain open (see the status table).

**Estado dos desafios / Challenge status (26-10-2026).**

| Desafio / Challenge | Estado / Status | O que falta / What is missing |
|---|---|---|
| D1 Recusas / Refusals | parcial / partial | P4 no repositório; falta merge, retrieval novo, código para seguimentos, confirmar recusas contra os 86 documentos |
| D2 Fundamentação e citações / Grounding | parcial / partial | PR #2 fundido: métricas lexicais e juiz opcional (`evaluate.py`, `judge.py`, `metrics.py`). Falta validar o método à mão em algumas respostas. O juiz por defeito é `gemini-3.5-flash` (valor em `.env.example`, não verificado), do mesmo fornecedor que um dos modelos em teste: risco de enviesamento por avaliar |
| D3 Origem dos prompts / Provenance | aberto / open | confirmar que não foram copiados do PC-IA |
| D4 Perguntas fáceis / Easy questions | parcial / partial | P4 acrescenta casos difíceis; falta retrieval para eles |
| D5 Propostas de clientes / Client proposals | cumprido / done (excertos) | 41 excertos retirados (1037 para 996, 86 para 84 documentos) e retrieval regenerado (`a259f91`). Por confirmar: se o repositório partiu do corpus da opção B |
| D6 Parâmetros / Parameters | parcial / partial | PR #1 fundido: modos de contexto `top_n`, `top_n_adjacent` e `full_top1`, `--top-n`, `--adjacent-m`, `--max-chars`, `--dry-run`. PR #3 (varrimento paralelo de configurações) aberto. Não encontrei cache dos resultados nem dimensionamento das configurações face ao tempo do Evento |
| D7 Modelos / Models | por decidir / to decide | escolher a comparação principal; verificar versões e preços |


## 10. Histórico e evolução / History and evolution

O histórico do Git mantém-se: não se reescreve. Esta secção explica as mudanças. / Git history is kept, not rewritten; this section gives the context.

| Data / Date | O que mudou / What changed |
|---|---|
| 26-10-2026 | Primeira proposta: reutilizar código do PC-IA. **Superada**: não cumpre as Regras TAIKAI §7 e §8 (trabalho de raiz, durante o Evento). / First proposal: reuse PC-IA code. Superseded: it does not meet Rules §7 and §8. |
| 26-10-2026 | Regra de trabalho (secção 0): construir de raiz, PC-IA só como referência. Regras e Termos lidos e resumidos em `RULES.md`. / Build-from-scratch rule; rules read and summarised in `RULES.md`. |
| 26-10-2026 | Decisão sobre a chave da API: fica no repositório, risco assumido; ver `DECISAO-CHAVE-API.md`. / API key decision: kept in the repo, risk accepted. |
| 26-10-2026 | Objetivo realinhado com a candidatura (secção 1); declaração de elementos pré-existentes (secção 6). / Objective aligned with the application; pre-existing elements declaration. |
| 26-10-2026 | Conversa da equipa de 23-10 lida como contexto: em parte ultrapassada. Dela vêm a pergunta do plano, a base P4 de 30 perguntas, a decisão de excluir duas propostas de clientes e a regra da mesma configuração (secções 1, 9 e 9b). / Team chat of 23-10 read as context, partly outdated; it supplies the plan question, the P4 base, the exclusion of two client proposals and the same-configuration rule. |
| 26-10-2026 | Dados pessoais redigidos em `data/` (commit `7b29ff7`). Os commits anteriores `369374c` e `ba05d9b` (pasta `data/`) ainda contêm o texto original; mantidos por decisão. / Personal data redacted in `data/` (`7b29ff7`); earlier commits `369374c` and `ba05d9b` still contain the original text, kept by decision. |
| 26-10-2026 | Correção de coerência: o parágrafo «D1 a D4 respondidos» passa a «contribui»; D5 duplicado (modelos) renumerado para D7; texto do D1 atualizado; tabela de estado. / Coherence fix: «D1 to D4 answered» becomes «contributes»; duplicate D5 (models) renumbered D7; D1 text updated; status table added. |
| 26-10-2026 | Corpus do repositório (86 documentos) medido contra o do P4 (162 ficheiros): duplicados, ruído e baixo sinal registados no D1; sem alteração aos dados. / Repository corpus (86 documents) measured against the P4 one (162 files): duplicates, noise and low-signal chunks recorded in D1; no data change. |
| 26-10-2026 | Decisão do Ricardo: a pergunta central é usar o Grok como modelo alternativo e comparar resultados com o Gemini; volume e forma do contexto passam a parâmetro (D6). / Ricardo's decision: the central question is Grok as an alternative model compared with Gemini; context volume and form become a parameter (D6). |
| 26-10-2026 | Dados pessoais redigidos de novo em 4 excertos de `data/chunk_data/chunks.json` após a regeneração do corpus; criado `ALTERACOES-DO-ASSISTENTE.md` (registo das alterações diretas do assistente, um capítulo por ficheiro). / Personal data redacted again in 4 chunks after corpus regeneration; `ALTERACOES-DO-ASSISTENTE.md` created. |
| 26-10-2026 | Criado `CRITERIOS-AVALIACAO.md`: cardápio de parâmetros e indicadores para seleção pela equipa (não imperativo), referenciado em D2, D6 e D7. / `CRITERIOS-AVALIACAO.md` created: menu of parameters and indicators for the team to select (not mandatory), referenced in D2, D6 and D7. |
| 26-10-2026 | Tabela de estado atualizada (D2 parcial, D5 cumprido nos excertos, D6 parcial) após os PR #1 e #2 fundidos e o PR #3 aberto. / Status table updated (D2 partial, D5 done for chunks, D6 partial) after PR #1 and #2 merged and PR #3 open. |

## 11. Estado do bilinguismo / Bilingual status

| Documento / Document | PT | EN |
|---|---|---|
| `README.md` | sim | parcial: secção 1 e secções 9 a 11 (incluindo 9b); declaração da secção 6 já em inglês / partial |
| `ORIENTACAO.md` | sim | sim (26-10-2026) / done |
| `DECISAO-CHAVE-API.md` | sim | por fazer / to do |
| `ALTERACOES-DO-ASSISTENTE.md` | sim | sim (26-10-2026) / done |
| `RULES.md` | sim | por fazer (é da Kerolayne) / to do (owned by Kerolayne) |
