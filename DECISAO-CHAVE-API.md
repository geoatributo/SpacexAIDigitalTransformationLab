# Decisão: chave da API no repositório

**Data:** 26-10-2026
**Decisão de:** Ricardo Almendra

## Decisão
Neste Lab, a chave da API da xAI vai ser guardada neste repositório privado, em vez de ficar só em variáveis de ambiente de cada pessoa. É uma escolha consciente de **ignorar a boa prática** de nunca pôr segredos num repositório.

## Motivo
Garantir eficácia durante o Lab: toda a equipa tem a chave logo ao clonar o repositório.

## Estado
A chave foi acrescentada em 26-10-2026 às 12:09 (commit `fdd22d2`), no ficheiro `CHAVE-API.md`. O código lê-a de lá (`src/lab/config.py`), com `XAI_API_KEY` no ambiente ou no `.env` a ter prioridade.

## Riscos conhecidos e aceites
- Quem tem acesso ao repositório (membros da organização `geoatributo` e colaboradores) ou a um clone pode usar os créditos do evento.
- Depois de um commit, a chave fica no histórico do Git. Apagar o ficheiro não a remove; só revogá-la e criar outra resolve.
- Não confirmado: se o GitHub ou a xAI revogam automaticamente chaves encontradas em repositórios, o que deixaria a chave de funcionar.
- Não confirmado: se as condições da xAI ou do evento permitem partilhar a chave.
- O PC-IA não limita o tamanho da resposta no caminho OpenAI, o que pode gastar créditos mais depressa.

## Atualização de 26-10-2026 (decisão do Ricardo, 18:41, hora de Lisboa)
- A solução do ficheiro `CHAVE-API.md` era **temporária**. O ficheiro foi **removido** do repositório. Cada pessoa passa a pôr `XAI_API_KEY` no seu `.env`.
- **A chave continua no histórico do Git** (commit `fdd22d2`) e ninguém a revogou até agora, pelo que o que está acima sobre o histórico continua a valer. Só o Ricardo pode revogá-la na xAI.
- O código (`src/lab/config.py`) ainda tenta ler `CHAVE-API.md` se o ficheiro existir, e a mensagem de erro ainda o menciona. Não foi alterado: sem o ficheiro, falta apenas definir `XAI_API_KEY`.

## Recomendação (não decidida)
Revogar a chave, e criar outra para o `.env`, quando o Lab terminar, ou já, dado que está no histórico.
