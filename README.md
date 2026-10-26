# Lab SpaceXAI — proposta de abordagem (RASCUNHO para revisão)

Regras oficiais do Evento (prazos, entregáveis, PI, pré-existente): [RULES.md](RULES.md).

Data: 26-10-2026 (data do sistema). Estado: rascunho, nada enviado a ninguém.

## 0. Regra de trabalho (obrigatória)

Este repositório (`xAiData`) é o único sítio onde se constrói o lab. O projeto **PC-IA** (`geoatributo/pc-ia-cognitive-assistant`) **não se altera**.

- **O que é:** referência e *baseline* de mecanismos (prompts, política de recusa, orçamento de contexto, métricas, fluxo pergunta → contexto → resposta).
- **O que não é:** código-base a editar, *fork* a evoluir, nem pasta para *patches*.
- **Como trabalhar:** ler o PC-IA, copiar o *comportamento* que interessa, e **implementar de raiz aqui**. Código, interface, adaptador xAI, executor comparado e avaliação vivem só neste repositório.
- **O que não fazer:** *commits*, *PRs* ou ficheiros novos no PC-IA; *symlink* ou *import* do código da aplicação original como dependência de runtime.

O PC-IA continua a ser o sistema em uso (Gemini) contra o qual se compara o Grok. A comparação usa o mesmo tipo de mecanismos; a implementação nova é independente.

## 1. Ideia (decisão do Ricardo)

- Usar o PC-IA só como referência: os mesmos mecanismos e critérios, reescritos neste repositório.
- Construir de raiz uma interface simples, com o serviço mínimo para interação com o utilizador.
- Avaliar as respostas em dois eixos, comparadas com o sistema que já está em desenvolvimento (Gemini, em uso):
  1. **Métricas automáticas** equivalentes às do projeto original (reimplementadas aqui, não invocando o código do PC-IA).
  2. **Avaliação qualitativa pelo utilizador**, sobre respostas dos vários sistemas lado a lado.

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
- Se os blocos de texto da qualidade (SGQ) já estão exportados em JSON.

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

## 7. Fases

- **Fase 1 (curta)**: 3 a 5 perguntas nos dois sistemas. Verificar formato da resposta, fuga de raciocínio interno e suporte da API Responses.

### Como correr a Fase 1

O código vive só neste repositório (`src/lab`). O PC-IA não se altera.

1. Copiar `.env.example` para `.env` e preencher `GEMINI_API_KEY` e `XAI_API_KEY` (a chave xAI pede-se à Liliana; nunca vai para o git nem para o chat).
2. Instalar dependências: `pip install -r requirements.txt`
3. Correr, com `src` no `PYTHONPATH`:

```text
python -m pip install -r requirements.txt
$env:PYTHONPATH="src"
python -m lab --limit 5
```

Isto envia as perguntas `gold-01` … `gold-05` (mesmo contexto congelado em `data/chunk_data/`) a Gemini e a Grok, mais um caso `refuse-empty` sem contexto. Os resultados vão para `data/runs/` (pasta ignorada pelo git). Testes sem rede: `python -m pytest`.
- **Fase 2**: aumentar o volume de contexto e comparar o sistema atual (base) com o Grok em paralelo.
- **Fase 3**: interface e relatório de métricas.

## 8. Riscos e pendências

- A chave da API é um segredo partilhado: variável de ambiente, nunca no repositório nem no chat.
- Créditos finitos: definir o limite de resposta antes da primeira chamada.
- Dados: confirmar que os dados usados podem ir para uma API externa. Copiar para este repositório só o mínimo necessário; o resto permanece no PC-IA, sem o modificar.
- Dois eixos de avaliação podem discordar (a métrica favorece um sistema e o utilizador outro). Isso não é falha, mas o relatório deve mostrar ambos e não fundi-los numa nota única.
- Avaliação qualitativa com poucos avaliadores é frágil: indicar o número de avaliadores e de perguntas em qualquer conclusão.
