# Lab SpaceXAI — proposta de abordagem (RASCUNHO para revisão)

Data: 26-10-2026 (data do sistema). Estado: rascunho, nada enviado a ninguém.

## 1. Ideia (decisão do Ricardo)

- Reutilizar o máximo possível do conhecimento e do código da aplicação existente (PC-IA).
- Construir uma interface simples, com o serviço mínimo para interação com o utilizador.
- Avaliar as respostas em dois eixos, comparadas com o sistema que já está em desenvolvimento (Gemini, em uso):
  1. **Métricas automáticas** que já estão em uso no projeto original.
  2. **Avaliação qualitativa pelo utilizador**, sobre respostas dos vários sistemas lado a lado.

## 2. Confirmado (fonte: leitura de `adapters/llm/service.py` em `geoatributo/pc-ia-cognitive-assistant`, 26-10-2026)

- O fornecedor do modelo escolhe-se por configuração (`CHAT_PROVIDER` ou `LLM_PROVIDER`; valores aceites: `openai`, `ollama`, `gemini`).
- Já existe um cliente OpenAI com `base_url` configurável (é assim que o Ollama está ligado).
- O ficheiro tem 1287 linhas e mistura lógica de prompts, deteção de perguntas de seguimento, orçamento de contexto e política de recusa. Importa `core.config`, `core.language`, `core.text` e `modules.generation.policy`. Não é um adaptador fino.
- O limite de tamanho da resposta (`max_output_tokens`) só é enviado no caminho do Gemini. No caminho OpenAI/Ollama é calculado e registado, mas não enviado.
- O caminho com medição de tokens (`complete_with_usage`) usa só a API Responses da OpenAI.
- O código tem expressões para limpar variantes do bloco `<scratchpad>` (comentário "X.39"). Não li o corpo da função que as aplica.

## 2b. Avaliação já existente no repositório (só nomes de ficheiros; conteúdo NÃO lido)

Os nomes sugerem avaliação com RAGAS e conjuntos de referência ("gold"), mas isto é inferência a partir dos nomes:

- `modules/evaluation/` (`metrics.py`, `benchmarks.py`, `datasets.py`, `matcher.py`, `service.py`) e `modules/rag/evaluators.py`.
- Scripts: `scripts/evaluate_ragas.py`, `scripts/run_full_ragas_eval.py`, `scripts/compare_ragas_results.py`, `scripts/evaluate_geoatributo_answers.py`, `scripts/run_gold_eval_*.py`.
- Documentação: `docs/ragas_query_set_schema.md`, `docs/testing/gemini-answer-generation-eval-guide.md`, `tests/fixtures/RAGAS_EVAL.README.md`, `tests/fixtures/CHANGELOG_eval.md`.
- Resultados guardados em ficheiros `*_eval_results.json` na raiz.

## 3. Hipóteses (não verificadas)

- A API da xAI (console.x.ai) segue o formato da API da OpenAI, pelo que o ramo do Grok seria pequeno (conhecimento geral, não do material do projeto).
- A API da xAI suporta o mesmo formato da API Responses. Se não suportar, é preciso um caminho alternativo para medir tokens.
- O Grok segue a instrução de produzir o bloco `<scratchpad>`. Só o teste o mostra.
- As métricas existentes são reutilizáveis tal como estão com um segundo fornecedor. Só se sabe pelos nomes dos ficheiros (secção 2b); o conteúdo não foi lido.

## 4. Desconhecido

- Texto das Regras do Lab (§7, §8, §12): quando é permitido usar código pré-existente e como declará-lo.
- O enunciado do desafio na página da TAIKAI.
- Que modelos Grok estão disponíveis com os créditos do Lab, e o limite de créditos.
- Se os blocos de texto da qualidade (SGQ) já estão exportados em JSON.

## 5. Arquitetura proposta

1. **Interface mínima**: uma pergunta, as respostas lado a lado (Gemini em uso e Grok), e o espaço para o utilizador classificar.
2. **Adaptador novo e pequeno para a xAI**: cliente OpenAI com `base_url` da xAI, chave por variável de ambiente, limite de resposta definido.
3. **Executor comparado**: a mesma pergunta e o mesmo contexto enviados ao Gemini (base) e ao Grok.
4. **Eixo 1, métricas automáticas**: reutilizar as que já estão em uso no projeto original, aplicadas às respostas dos dois sistemas. Quais são e como se executam: por confirmar lendo `modules/evaluation/metrics.py` e a documentação (secção 2b). Medições complementares propostas, a validar: fuga de raciocínio interno para a resposta final, recusa correta quando não há resposta no contexto, latência e tokens usados.
5. **Eixo 2, avaliação qualitativa**: o utilizador vê as respostas dos dois sistemas sem saber qual é qual (proposta, para reduzir enviesamento) e escolhe a melhor ou dá uma nota segundo critérios fixos. Critérios a definir pela equipa (por exemplo, correção, utilidade, linguagem). Os resultados guardam-se com os das métricas para comparar os dois eixos.

## 6. Enquadramento nas Regras

Pendente. A declaração do que é pré-existente (pipeline e troca entre fornecedores) e do que se constrói no evento (adaptador xAI, executor, avaliação, interface) depende do texto das Regras. Recomenda-se confirmar por escrito com o contacto da organização antes de apresentar.

## 7. Fases

- **Fase 1 (curta)**: 3 a 5 perguntas nos dois sistemas. Verificar formato da resposta, fuga de raciocínio interno e suporte da API Responses.
- **Fase 2**: aumentar o volume de contexto e comparar o sistema atual (base) com o Grok em paralelo.
- **Fase 3**: interface e relatório de métricas.

## 8. Riscos e pendências

- A chave da API é um segredo partilhado: variável de ambiente, nunca no repositório nem no chat.
- Créditos finitos: definir o limite de resposta antes da primeira chamada.
- Dados: confirmar que os dados usados podem ir para uma API externa. Levar para o repositório novo só o mínimo necessário.
- Dois eixos de avaliação podem discordar (a métrica favorece um sistema e o utilizador outro). Isso não é falha, mas o relatório deve mostrar ambos e não fundi-los numa nota única.
- Avaliação qualitativa com poucos avaliadores é frágil: indicar o número de avaliadores e de perguntas em qualquer conclusão.
