from lab.config import REFUSAL_SENTENCE
from lab.prompts import SYSTEM_PROMPT, build_user_prompt


def test_golden_rule_is_last_instruction() -> None:
    assert SYSTEM_PROMPT.rstrip().endswith(REFUSAL_SENTENCE)
    assert SYSTEM_PROMPT.index("<scratchpad>") < SYSTEM_PROMPT.index("REGRA DE OURO")


def test_user_prompt_numbers_chunks() -> None:
    from lab.context import ContextChunk

    chunk = ContextChunk(
        index=1,
        chunk_id="c1",
        title="Normas",
        filename="normas.docx",
        page="1",
        section="VPN",
        version="V52",
        text="limite 25 MB",
        score=0.9,
    )
    prompt = build_user_prompt("Qual o limite?", [chunk])
    assert prompt.startswith("Pergunta:\nQual o limite?")
    assert "[1] Titulo: Normas" in prompt
    assert "limite 25 MB" in prompt
