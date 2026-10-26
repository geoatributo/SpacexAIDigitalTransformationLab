from lab.config import REFUSAL_SENTENCE
from lab.scratchpad import strip_scratchpad


def test_strip_scratchpad_exact_tag() -> None:
    answer = "Some text. <scratchpad>internal reasoning</scratchpad> Final answer."
    result = strip_scratchpad(answer)
    assert result.visible_text == "Some text. Final answer."
    assert result.scratchpad_leaked is False


def test_strip_scratchpad_case_insensitive() -> None:
    answer = "Text. <SCRATCHPAD>hidden</SCRATCHPAD> Answer."
    result = strip_scratchpad(answer)
    assert result.visible_text == "Text. Answer."


def test_strip_scratchpad_whitespace_inside_tag() -> None:
    answer = "Text. < scratchpad >reasoning</ scratchpad > Answer."
    result = strip_scratchpad(answer)
    assert result.visible_text == "Text. Answer."


def test_strip_scratchpad_malformed_close_tag() -> None:
    for closer in ("</scratchpad]", "</scratchpad)", "</scratchpad}"):
        answer = f"Text. <scratchpad>reasoning{closer} Answer."
        result = strip_scratchpad(answer)
        assert result.visible_text == "Text. Answer.", closer


def test_strip_scratchpad_missing_closer() -> None:
    result = strip_scratchpad("Text. <scratchpad>reasoning that goes to the end")
    assert result.visible_text == "Text."


def test_strip_scratchpad_missing_opener() -> None:
    result = strip_scratchpad("Some reasoning</scratchpad> Final answer.")
    assert result.visible_text == "Final answer."


def test_strip_scratchpad_multiple_blocks() -> None:
    answer = "A. <scratchpad>reason 1</scratchpad> B. <scratchpad>reason 2</scratchpad> C."
    result = strip_scratchpad(answer)
    assert result.visible_text == "A. B. C."


def test_refusal_sentence() -> None:
    result = strip_scratchpad(REFUSAL_SENTENCE)
    assert result.is_refusal is True
    assert result.scratchpad_leaked is False


def test_leaked_when_visible_still_has_tag() -> None:
    result = strip_scratchpad("Answer <scratchpad")
    assert "scratchpad" in result.visible_text.lower() or result.scratchpad_leaked
