from __future__ import annotations

import re
from dataclasses import asdict, dataclass

from lab.config import REFUSAL_SENTENCE

PASS_THRESHOLD = 0.8

_STOPWORDS = frozenset(
    """
    a ao aos as à às aquele aquela aqueles aquelas aquilo
    com como da das de do dos e em entre esse essa esses essas isto
    mais mas na nas no nos num numa o os ou para pela pelas pelo pelos
    por que se ser seu sua seus suas um uma já não sim
    deve devem dever ficar ficando através caso via abaixo acima disso
    seguinte seguintes acordo normas manual só so ser serem feito feita
    efetuadas efetuados usar utilizar propõe propoe conforme
    """.split()
)

_CITATION = re.compile(r"\[\d+\]")
_PAREN = re.compile(r"\([^)]*\)")
_SENTENCE_SPLIT = re.compile(r"(?<=[\.\!\?;:])\s+|\n+")
_TOKEN = re.compile(r"[0-9]+(?:[.,][0-9]+)?|[a-z0-9áàâãéêíóôõúç]+", re.IGNORECASE)


@dataclass(frozen=True)
class CaseScores:
    correctness: float
    grounded_rate: float
    completeness: float
    passed: bool
    notes: str


def _normalize(text: str) -> str:
    cleaned = _CITATION.sub(" ", text or "")
    cleaned = cleaned.lower().replace("\u00a0", " ")
    cleaned = cleaned.replace(",", ".")
    return re.sub(r"\s+", " ", cleaned).strip()


def _tokens(text: str) -> list[str]:
    return [match.group(0).lower().replace(",", ".") for match in _TOKEN.finditer(_normalize(text))]


def _content_tokens(text: str) -> list[str]:
    return [token for token in _tokens(text) if token not in _STOPWORDS and (len(token) > 2 or token.isdigit() or "." in token)]


def _numbers(text: str) -> list[str]:
    return [token for token in _tokens(text) if token[:1].isdigit()]


def _required_numbers(text: str) -> list[str]:
    return _numbers(_PAREN.sub(" ", text or ""))


def _units(text: str) -> list[str]:
    parts = [part.strip(" -*") for part in _SENTENCE_SPLIT.split(text or "") if part.strip()]
    units = [part for part in parts if _content_tokens(part) or _numbers(part)]
    if units:
        return units
    return [text] if (text or "").strip() else []


def _coverage(unit: str, haystack: str, *, examples_optional: bool = False) -> bool:
    unit_numbers = _required_numbers(unit) if examples_optional else _numbers(unit)
    hay_numbers = set(_numbers(haystack))
    if unit_numbers and not set(unit_numbers).issubset(hay_numbers):
        return False
    unit_content = [token for token in _content_tokens(unit) if not token[:1].isdigit()]
    if not unit_content:
        return bool(unit_numbers) or (examples_optional and not unit_numbers)
    hay_content = set(_content_tokens(haystack))
    hits = sum(1 for token in unit_content if token in hay_content)
    if unit_numbers:
        return hits >= min(2, len(unit_content))
    return hits / len(unit_content) >= 0.5


def _number_recall(reference: str, answer: str) -> float:
    ref_numbers = set(_required_numbers(reference))
    if not ref_numbers:
        return 1.0
    return len(ref_numbers & set(_numbers(answer))) / len(ref_numbers)


def _correctness(reference: str, answer: str, completeness: float) -> float:
    # Bate com a referência se os números-chave estão lá e as unidades da gold estão cobertas.
    # Factos a mais na resposta não entram aqui (medem-se em grounded_rate).
    number_recall = _number_recall(reference, answer)
    return 0.6 * number_recall + 0.4 * completeness


def score_completion(
    *,
    expected_behavior: str,
    reference_answer: str | None,
    visible_text: str,
    is_refusal: bool,
    context_text: str,
    error: str | None,
) -> CaseScores:
    if error:
        return CaseScores(0.0, 0.0, 0.0, False, f"erro de chamada: {error}")

    expected = (expected_behavior or "answer").strip().lower()
    answer = (visible_text or "").strip()

    if expected in {"refuse", "refusal"}:
        ok = 1.0 if is_refusal or answer == REFUSAL_SENTENCE else 0.0
        grounded = 1.0 if ok == 1.0 else (0.0 if answer else 0.0)
        return CaseScores(ok, grounded, ok, ok >= PASS_THRESHOLD, "caso de recusa")

    if is_refusal or answer == REFUSAL_SENTENCE:
        return CaseScores(0.0, 1.0, 0.0, False, "recusa indevida")

    if not answer:
        return CaseScores(0.0, 0.0, 0.0, False, "resposta vazia")

    ref = reference_answer or ""
    completeness = _unit_recall(ref, answer)
    correctness = _correctness(ref, answer, completeness)
    grounded_rate = _grounded_rate(answer, context_text)
    return CaseScores(
        round(correctness, 4),
        round(grounded_rate, 4),
        round(completeness, 4),
        correctness >= PASS_THRESHOLD,
        "resposta vs referência + contexto",
    )


def _unit_recall(reference: str, answer: str) -> float:
    units = _units(reference)
    if not units:
        return 1.0 if not answer else 0.0
    hits = sum(1 for unit in units if _coverage(unit, answer, examples_optional=True))
    return hits / len(units)


def _grounded_rate(answer: str, context_text: str) -> float:
    units = _units(answer)
    if not units:
        return 0.0
    if not (context_text or "").strip():
        return 0.0
    hits = sum(1 for unit in units if _coverage(unit, context_text))
    return hits / len(units)


def aggregate(scores: list[CaseScores]) -> dict[str, float]:
    if not scores:
        return {
            "correctness": 0.0,
            "grounded_rate": 0.0,
            "completeness": 0.0,
            "pass_rate": 0.0,
            "n": 0,
        }
    n = len(scores)
    return {
        "correctness": round(sum(item.correctness for item in scores) / n, 4),
        "grounded_rate": round(sum(item.grounded_rate for item in scores) / n, 4),
        "completeness": round(sum(item.completeness for item in scores) / n, 4),
        "pass_rate": round(sum(1 for item in scores if item.passed) / n, 4),
        "n": n,
    }


def as_payload(scores: CaseScores) -> dict:
    return asdict(scores)
