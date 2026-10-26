from __future__ import annotations

from lab.config import REFUSAL_SENTENCE
from lab.context import ContextChunk

SYSTEM_PROMPT = f"""Responde na língua do utilizador. Se não for clara, usa português.

O histórico da conversa, se existir, serve apenas para resolver pronomes e referências. Nunca cites o histórico.

Antes de responder, pensa dentro de um bloco <scratchpad> e lista:
- as pessoas ou papéis envolvidos
- se a versão do documento pedida pelo utilizador coincide com os excertos
- restrições e prazos
- se a resposta está realmente no texto

Usa apenas o contexto recuperado. Cita cada facto com [1], [2], e assim por diante, correspondendo ao número do excerto.

Sinónimos contam: se o texto diz o mesmo por outras palavras, isso é uma resposta. Se a pergunta assenta numa premissa errada, corrige-a em vez de recusar.

Responde a partir do plano ou documento que se aplica à situação. Se usares um procedimento interno de outra entidade, diz-o.

Quando pedirem regras, passos ou requisitos, lista todos os itens que aparecem no texto, e nada que não apareça.

REGRA DE OURO: se a resposta não estiver no contexto, responde exactamente:
{REFUSAL_SENTENCE}
"""


def build_user_prompt(question: str, chunks: list[ContextChunk]) -> str:
    if not chunks:
        context_block = "(nenhum contexto recuperado)"
    else:
        parts: list[str] = []
        for chunk in chunks:
            page = chunk.page if chunk.page else "—"
            section = chunk.section if chunk.section else "—"
            version = chunk.version if chunk.version else "—"
            parts.append(
                f"[{chunk.index}] Titulo: {chunk.title}\n"
                f"Ficheiro: {chunk.filename} | Pagina: {page} | Secao: {section} | Versao do documento: {version}\n"
                f"Conteudo:\n{chunk.text}"
            )
        context_block = "\n\n".join(parts)

    return (
        f"Pergunta:\n{question.strip()}\n\n"
        f"Contexto recuperado:\n{context_block}"
    )
