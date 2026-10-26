# Alterações diretas do assistente / Direct changes by the assistant

**PT.** Este ficheiro regista todas as alterações que o assistente (Elon, a trabalhar para o Ricardo Almendra) fez diretamente a documentos e código deste repositório, com um capítulo por ficheiro original alterado. Regra do Ricardo (26-10-2026): cada alteração direta fica aqui documentada. Os commits são feitos com a conta `ricardoalmendra-bit`, por ordem expressa do Ricardo. Ficheiros que o assistente só leu não aparecem. Para o detalhe linha a linha, ver `git log -- <ficheiro>`.

**EN.** This file records every change the assistant (Elon, working for Ricardo Almendra) made directly to documents and code in this repository, with one chapter per changed original file. Ricardo's rule (26-10-2026): every direct change is documented here. Commits are made with the `ricardoalmendra-bit` account, on Ricardo's express order. Files the assistant only read are not listed. For line-level detail, see `git log -- <file>`.

Manter este ficheiro atualizado em cada alteração futura. / Keep this file updated with every future change.

---

## `README.md`

Criado pelo assistente (commit `b13c17c`, 26-10-2026 11:16) e alterado várias vezes. Parte do conteúdo das secções 9 e 9b veio de outras contas (`coopera-web`) e foi depois corrigida pelo assistente. / Created by the assistant and edited several times; part of sections 9 and 9b came from `coopera-web` and was later corrected by the assistant.

| Commit | Alteração / Change |
|---|---|
| `b13c17c` | Proposta de abordagem inicial (superada). / Initial approach proposal (superseded). |
| `d263215` | Objetivo e critérios da candidatura; declaração de elementos pré-existentes (em inglês); riscos de dados. / Application objective and criteria; pre-existing elements declaration (English); data risks. |
| `6e96725` | Desafios D1 a D4, secção de histórico, estado do bilinguismo. / Challenges D1 to D4, history section, bilingual status. |
| `76997b2` | Pergunta do plano, regra da mesma configuração, D5 (propostas de clientes), D6 (parâmetros), glossário, base P4. / Plan question, same-configuration rule, D5, D6, glossary, P4 base. |
| `45f400c` | Marca `ORIENTACAO.md` como bilingue. / Marks `ORIENTACAO.md` as bilingual. |
| `5ba240d` | Texto da chave da API alinhado com a decisão do Ricardo (o código lê `CHAVE-API.md`). / API key text aligned with Ricardo's decision. |
| `09beca4` | «D1 a D4 respondidos» passa a «contribui»; D5 duplicado (modelos) renumerado para D7; D1 atualizado; tabela de estado dos desafios. / "D1 to D4 answered" becomes "contributes"; duplicate D5 renumbered D7; D1 updated; status table. |
| `915f7c5`, `f67cf88` | D1: medição do corpus (86 documentos, duplicados, ruído, baixo sinal) e declaração do Ricardo sobre os ficheiros a mais. / D1: corpus measurement and Ricardo's statement on the extra files. |
| `3bbacd4` | Secção 1: pergunta central passa a ser o modelo alternativo e a comparação; volume e forma do contexto passam a parâmetro (D6). / Section 1: central question is the alternative model and comparison; context volume and form become a parameter (D6). |

## `ORIENTACAO.md`

Criado pelo assistente (commit `f7b76c0`, baseado na proposta inicial, entretanto superada). / Created by the assistant, based on the initial proposal, since superseded.

| Commit | Alteração / Change |
|---|---|
| `57f607b` | Reescrito em PT e EN, alinhado com o README: construir de raiz, mesma configuração, P4, regras da equipa. / Rewritten in PT and EN, aligned with the README. |
| `3bbacd4` | Objetivo: comparação com modelo alternativo como pergunta central. / Objective: alternative-model comparison as the central question. |

## `DECISAO-CHAVE-API.md`

Criado pelo assistente (commit `abbabc5`) para registar a decisão do Ricardo sobre a chave da API e os riscos. Atualizado em `5ba240d`: o estado passa a dizer que a chave foi acrescentada em `CHAVE-API.md` (26-10-2026 12:09) e que o código a lê daí, com `XAI_API_KEY` no ambiente ou em `.env` com prioridade. Os riscos e a recomendação de revogar a chave depois do Lab não mudaram. / Created by the assistant to record Ricardo's decision on the API key and its risks; updated in `5ba240d` to say the code reads the key from `CHAVE-API.md`. Risks and the advice to revoke the key after the Lab are unchanged.

## `src/lab/config.py`

Código do Eduardo, alterado pelo assistente por ordem expressa do Ricardo (commit `5ba240d`): acrescentado `KEY_FILE` (`CHAVE-API.md`), a função `_read_key_file` (primeira linha não vazia do primeiro bloco de código) e a leitura da chave a partir desse ficheiro quando `XAI_API_KEY` está vazia ou é um valor de exemplo; mensagem de erro atualizada. / Eduardo's code, changed by the assistant on Ricardo's express order: added `KEY_FILE`, `_read_key_file` and the fallback to the key file; error message updated.

## `tests/test_config.py`

Criado pelo assistente (commit `5ba240d`): 2 testes (leitura da chave com uma chave de teste falsa; ficheiro em falta). / Created by the assistant: 2 tests (key read with a fake test key; missing file).

## `data/chunk_data/chunks.json`

Dados pessoais redigidos, por ordem expressa do Ricardo. / Personal data redacted, on Ricardo's express order.

| Quando / When | Alteração / Change |
|---|---|
| `7b29ff7` (26-10-2026 12:26) | N.º do cartão de cidadão e morada pessoal substituídos por `[REDIGIDO]` e `[MORADA REDIGIDA]` em 5 excertos (um deles da proposta Euroespuma, entretanto retirada do corpus) e nos 8 ficheiros de texto correspondentes (ver abaixo). / ID-card number and home address replaced by `[REDIGIDO]` and `[MORADA REDIGIDA]` in 5 chunks and in the 8 matching text files. |
| 26-10-2026, após `e34edb4` | Os `chunks.json` foram regenerados pelo Eduardo (`a259f91`) a partir dos originais e os 4 excertos voltaram a ter os dados. Redigidos de novo, mesmo padrão, 4 excertos (3 modelos de documento). Alterado só o campo `text`; ids, metadados e `retrieval.json` não mudam. / `chunks.json` was regenerated from the originals, so the 4 chunks had the data again; redacted again with the same pattern. Only the `text` field changed. |

Limitações / Limits: as pontuações do retrieval foram calculadas com o texto original; o histórico do Git mantém o texto original (decisão do Ricardo); se o corpus for regenerado a partir dos documentos de origem sem limpeza, os dados voltam. / Retrieval scores were computed on the original text; Git history keeps the original (Ricardo's decision); regenerating the corpus from uncleaned sources brings the data back.

## `data/geoatributo_base2_teste/documents/**` e `documents_md_only/**` (já não existem / no longer exist)

Em `7b29ff7` o assistente redigiu os mesmos dados em 8 ficheiros de texto (4 documentos, em duas pastas): `10417_modelo_base_de_proposta`, `11203_modelo_resposta_consulta_preliminar`, `PROP-261766I2320093_PEE_Euroespuma` e `10406_modelo_base_de_proposta_consulta_preliminar`. Estas pastas foram entretanto substituídas e depois apagadas pela equipa (`a259f91`, `becdc64`), por isso esta alteração já não está no estado atual do repositório. / In `7b29ff7` the assistant redacted the same data in 8 text files; these folders were later replaced and deleted by the team, so the change is no longer in the current state.
