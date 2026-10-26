from lab.config import REFUSAL_SENTENCE
from lab.metrics import score_completion


CONTEXT = (
    "As cópias de download ou upload direto de ficheiros através da VPN só devem "
    "ser efetuadas para ficheiros de dimensão inferior a 25 MB. Para conjuntos "
    "superiores a 25 MB, usar WeTransfer ou Google Drive."
)
REFERENCE = (
    "As cópias de download ou upload direto de ficheiros através da VPN só devem "
    "ser efetuadas para ficheiros ou conjuntos de ficheiros de dimensão inferior "
    "a 25 MB. Para ficheiros superiores a 25 MB, o manual propõe WeTransfer ou Google Drive."
)


def test_matching_answer_passes() -> None:
    scores = score_completion(
        expected_behavior="answer",
        reference_answer=REFERENCE,
        visible_text="Download/upload direto via VPN só abaixo de 25 MB [1]. Acima disso, WeTransfer ou Google Drive [1].",
        is_refusal=False,
        context_text=CONTEXT,
        error=None,
    )
    assert scores.correctness >= 0.8
    assert scores.completeness >= 0.8
    assert scores.grounded_rate >= 0.8
    assert scores.passed is True


def test_wrongful_refusal_is_ungraded_but_grounded() -> None:
    scores = score_completion(
        expected_behavior="answer",
        reference_answer=REFERENCE,
        visible_text=REFUSAL_SENTENCE,
        is_refusal=True,
        context_text=CONTEXT,
        error=None,
    )
    assert scores.correctness == 0.0
    assert scores.completeness == 0.0
    assert scores.grounded_rate == 1.0
    assert scores.passed is False


def test_expected_refusal_scores_one() -> None:
    scores = score_completion(
        expected_behavior="refuse",
        reference_answer=None,
        visible_text=REFUSAL_SENTENCE,
        is_refusal=True,
        context_text="",
        error=None,
    )
    assert scores.correctness == 1.0
    assert scores.completeness == 1.0
    assert scores.grounded_rate == 1.0
    assert scores.passed is True


def test_invented_claim_lowers_grounding() -> None:
    scores = score_completion(
        expected_behavior="answer",
        reference_answer=REFERENCE,
        visible_text="O limite é 25 MB. O prazo máximo de transferência é 72 horas úteis.",
        is_refusal=False,
        context_text=CONTEXT,
        error=None,
    )
    assert scores.grounded_rate < 1.0


def test_parenthetical_example_is_optional_for_correctness() -> None:
    scores = score_completion(
        expected_behavior="answer",
        reference_answer="O formato obrigatório é decimal com duas casas (por exemplo, 8,50 em vez de 8h30).",
        visible_text="O formato obrigatório é decimal com duas casas.",
        is_refusal=False,
        context_text="O formato obrigatório é decimal com duas casas. Exemplo: 8,50.",
        error=None,
    )
    assert scores.completeness >= 0.8
    assert scores.correctness >= 0.8
    assert scores.passed is True


def test_missing_reference_number_drops_correctness() -> None:
    scores = score_completion(
        expected_behavior="answer",
        reference_answer=REFERENCE,
        visible_text="O upload pela VPN deve usar WeTransfer ou Google Drive.",
        is_refusal=False,
        context_text=CONTEXT,
        error=None,
    )
    assert scores.correctness < 0.8
    assert scores.passed is False


def test_api_error_is_zero() -> None:
    scores = score_completion(
        expected_behavior="answer",
        reference_answer=REFERENCE,
        visible_text="",
        is_refusal=False,
        context_text=CONTEXT,
        error="ClientError",
    )
    assert scores.correctness == 0.0
    assert scores.passed is False
