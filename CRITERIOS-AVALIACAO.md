# Critérios de avaliação: cardápio de parâmetros e indicadores

**Estatuto deste documento.** É um **cardápio completo de opções**, não uma lista imperativa. A equipa escolhe os parâmetros e indicadores que vai usar e pode **recusar qualquer um, desde que justifique a opção** (ver secção I). A decisão final é do Ricardo. Proposta da Liliana, 26-10-2026. Liga-se aos desafios D2, D6 e D7 do [README](README.md).

Os "objetivos de referência" são propostas para discussão, não valores medidos (a única exceção é o 0,80 de `answer_correctness` do PC-IA no golden set).

---

## A. Parâmetros de geração (iguais nos dois modelos)

| Parâmetro | Linha de base | Valores a testar (Fase 2) | Origem | Notas |
|---|---|---|---|---|
| Temperatura | 0,1 | 0; 0,3 | PC-IA (modo *governed*) | 0 = reprodutibilidade; 0,3 = sensibilidade |
| top_p | 0,9 | 1,0 | PC-IA | Mudar um parâmetro de cada vez |
| Limite de saída | 4.096 tokens | 8.192 | PC-IA usa 8.192 | Registar respostas cortadas (`finish_reason`) |
| Raciocínio | Desligado | Grok 4.7 ou 4.3 com raciocínio `low` / `high` | D7 | Tokens de raciocínio contados à parte |
| Prompt de sistema | O do PC-IA, igual nos dois | Variante sem scratchpad (D3) | PC-IA | Versão do prompt registada em cada corrida |
| Bloco `<scratchpad>` e frase de recusa | Instrução mantida | Sem instrução | X.39 | Bloco retirado antes de avaliar e contado |
| Formato de citação | `[n]` | Nenhum | PC-IA | Necessário para os indicadores 3 e 7 |
| Repetições | 1 | 2 nos 10 casos de calibração | Proposta | Mede estabilidade |
| Timeout e novas tentativas | 60 s, 2 novas tentativas | Nenhum | Proposta | Erros não contam como recusas |

## B. Parâmetros de contexto (congelados na Fase 1)

| Parâmetro | Linha de base (Baseline_Definition) | Valores a testar (Fase 2) | Notas |
|---|---|---|---|
| Top-k | 6 | 4; 10 | Mais contexto pode ajudar ou trazer ruído |
| Corte de relevância | 0,45 (fica sempre o melhor) | 0,35; 0,55 | Afeta diretamente as recusas |
| Vizinhos | ±2 nos 3 primeiros excertos | 0; ±1 | |
| Limite de contexto | 9.000 caracteres (16.000 com vizinhos) | 6.000; 24.000 | Robustez a contextos longos |
| Histórico (seguimentos) | Últimos 6 turnos | 2; 10 | Só nas sequências S1 a S5 |
| Ordem dos excertos | Por relevância | Inversa | Efeito "perdido no meio" |

## C. Modelos (D7)

| Papel | Gemini | Grok | Estado |
|---|---|---|---|
| Par principal | `gemini-2.5-flash-lite` (produção) | `grok-4.20-non-reasoning` ou `grok-4.3` sem raciocínio | Por decidir |
| Referência máxima (opcional) | Gemini Pro | `grok-4.7` | Se houver créditos |
| Juízes | Gemini | Grok | Cruzados e às cegas |

Os aliases `-latest` saem do `config.py` (versões fixadas). Nomes e preços confirmados na consola de cada fornecedor antes de correr.

## D. Indicadores

| # | Indicador | Fórmula | Universo | Tipo | Objetivo de referência | Prioridade |
|---|---|---|---|---|---|---|
| 1 | Fundamentação | Afirmações suportadas ÷ total de afirmações | 56 | Juiz | ≥ 90% | Crítica |
| 1b | Taxa de alucinação | Respostas com ≥ 1 afirmação não suportada ÷ total | 56 | Juiz | ≤ 10% | Crítica |
| 2 | Exatidão | Média de `answer_correctness` (0 a 1) | 56 | Juiz | ≥ 0,80 (PC-IA) | Crítica |
| 3 | Fonte certa | Respostas que citam o excerto com o extrato de referência ÷ total | 56 | Automático | ≥ 80% | Alta |
| 4 | Recusa correta | Recusas sem valor inventado ÷ 6 (R1, R5 e R6 são as mais exigentes) | 6 | Automático | 6/6 | Alta |
| 5 | Recusa indevida | Recusas ÷ 56 (F9 e L9 são casos conhecidos) | 56 | Automático | ≤ 5% | Alta |
| 6 | Premissas falsas | Média 0 a 2 | Casos com `premise_check` | Juiz | ≥ 1,5 | Alta |
| 7 | Citações válidas | `[n]` existentes ÷ `[n]` citados | 62 | Automático | 100% | Média |
| 8a | Fuga do scratchpad | Respostas com o bloco na resposta final ÷ total | 62 | Automático | 0% | Média |
| 8b | Idioma PT | Respostas em PT ÷ total | 62 | Automático | 100% | Média |
| 8c | Listas completas | Itens esperados presentes ÷ itens esperados | Itens L | Automático | 100% | Média |
| 9a | Custo | Custo por pergunta e por resposta correta | 62 | Automático | Comparativo | Média (forte no pitch) |
| 9b | Latência | p50 e p95 (s) | 62 | Automático | Comparativo | Média |
| 9c | Fiabilidade | Erros, timeouts, loops e cortes ÷ total | 62 | Automático | ≤ 2% | Média |
| 10 | Seguimentos | Média 0 a 2 por turno | 12 turnos (S1 a S5) | Juiz | ≥ 1,5 | Opcional |
| 11 | Avaliação qualitativa às cegas | Média 1 a 5 (utilidade, clareza, confiança) e % de preferência direta | ~20 casos, ≥ 2 avaliadores | Humano | Comparativo | Alta (credibilidade perante o júri) |
| 12 | Concordância entre juízes | % de acordo ou kappa | 62 | Automático | ≥ 0,6 | Controlo |
| 13 | Viés de autofavorecimento | Nota às respostas da própria família menos nota às da outra | 62 | Automático | ≈ 0 | Controlo |

As recusas corretas (4) e indevidas (5) reportam-se sempre lado a lado: um modelo que recusa tudo acerta nas 6 e falha nas 56.

## E. Escalas do juiz (a escrever no prompt do juiz)

- **Exatidão:** 1 = completa e correta; 0,5 = parcial; 0 = errada ou inventada.
- **Fundamentação (por afirmação):** suportada / não suportada / contraditória.
- **Premissas falsas:** 2 = deteta e corrige; 1 = hesita ou ambígua; 0 = aceita a premissa.
- **Seguimentos (por turno):** 2 = coerente; 1 = perde parte do contexto; 0 = contradiz-se ou perde o fio.

**Juiz cruzado.** Se o juiz for o Gemini ou o Grok, avalia respostas da própria família. Proposta: usar os dois como juízes, sem saber qual resposta é de quem, e reportar a concordância (12) e o viés (13). Antes dos 62 casos, calibrar à mão com 10 casos, como o D2 já prevê.

## F. Leitura e apresentação

- Tudo dividido por **tipo de pergunta** (F, L, R, S) e por modelo.
- **Intervalos de confiança:** bootstrap, 1.000 reamostragens, 95%.
- **Regra de decisão:** não declarar vencedor se a diferença for < 5 pontos ou os intervalos se sobrepuserem.
- **Índice global (opcional):** fundamentação 30%, exatidão 30%, recusas 20%, premissas 10%, qualitativa 10%. Alternativa: mostrar só o perfil de cada modelo.
- **Para o pitch:** gráfico exatidão × custo; tabela de perfil com os indicadores 1 a 6; 2 ou 3 exemplos lado a lado (alucinação, recusa, premissa falsa).

## G. Registo obrigatório por corrida

ID da corrida, data e hora; modelo e versão exata; todos os parâmetros das tabelas A e B; versão do prompt; resposta bruta e resposta sem scratchpad; tokens de entrada, saída e raciocínio; latência e `finish_reason`; erros.

## H. Ordem de execução sugerida

1. **Configuração:** versões, parâmetros e preços.
2. **Teste rápido:** 5 casos nos dois modelos (pipeline, citações, corte do scratchpad). Estimar o custo antes de correr tudo.
3. **Calibração do juiz:** 10 casos à mão.
4. **Fase 1, indicadores automáticos:** 62 casos (3, 4, 5, 7, 8, 9). **Mínimo garantido para o pitch.**
5. **Indicadores com juiz:** 1, 2, 6, 12, 13.
6. **Avaliação qualitativa às cegas:** ~20 casos.
7. **Fase 2 (se houver tempo):** valores a testar das tabelas A e B, um de cada vez; referência máxima; seguimentos S1 a S5.

## I. Seleção pela equipa

Preencher à medida que a equipa decide. Recusar um item é válido, desde que fique a justificação.

| Item (parâmetro ou indicador) | Decisão (usar / recusar / adiar) | Justificação | Quem decidiu |
|---|---|---|---|
| | | | |

## J. Relação com o código existente

O commit `299149f` (Kerolayne) já acrescentou `src/lab/metrics.py`, `judge.py` e `evaluate.py`, com métricas lexicais (`correctness`, `grounded_rate`, `completeness`) e um juiz LLM opcional (`JUDGE_PROVIDER` e `JUDGE_MODEL`, por defeito Gemini). Esses indicadores correspondem, em versão lexical, aos indicadores 1 e 2 deste cardápio. Os restantes estão por implementar, conforme a seleção da equipa.

## Decisões para o Ricardo

1. O Grok do par principal.
2. Limite de saída: 4.096 ou 8.192 tokens.
3. Objetivos de referência da tabela D.
4. Índice global ou só perfil de cada modelo.
5. Seguimentos já na Fase 1 ou na Fase 2.

## Notas para a equipa

- Não enviar dados de clientes ao Grok.
- O PC-IA só se lê; não se altera.
- A chave da API está no repositório privado e deve ser revogada no fim do Lab.
- Submissão na TAIKAI até 27-10-2026, 13:00 (Lisboa), em inglês, com pitch de 5 minutos.
