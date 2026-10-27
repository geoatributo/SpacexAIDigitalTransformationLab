from lab.rag_judge import (
    CONTEXT_JOIN,
    JUDGE_MAX_OUTPUT_TOKENS,
    JUDGE_SYSTEM_PROMPT,
    JUDGE_TEMPERATURE,
    JUDGE_TIMEOUT_S,
    JUDGE_TOP_P,
    aggregate_llm_cases,
    ask_score,
    classify_case,
    join_retrieved_context,
    media,
    parse_scores,
    pass_rate,
    score_generated_answer,
)
from lab.providers.base import CompletionResult


class SequentialJudge:
    name = "gemini"

    def __init__(self, replies: list[str]) -> None:
        self.replies = list(replies)
        self.calls: list[dict] = []

    def complete(self, **kwargs):
        self.calls.append(kwargs)
        return CompletionResult(text=self.replies.pop(0), latency_ms=1)


def test_ask_score_normalizes_0_100_and_0_1() -> None:
    assert ask_score("85") == 0.85
    assert ask_score("Score: 100") == 1.0
    assert ask_score("0.9") == 0.9
    assert ask_score("no number") is None


def test_parse_scores_reads_json_and_fences() -> None:
    assert parse_scores('{"correctness": 90, "grounded": 80, "completeness": 100}') == {
        "correctness": 0.9,
        "grounded": 0.8,
        "completeness": 1.0,
    }
    assert parse_scores('```json\n{"correctness": 0.5, "grounded": 1, "completeness": 70}\n```') == {
        "correctness": 0.5,
        "grounded": 1.0,
        "completeness": 0.7,
    }
    assert parse_scores("no json") == {"correctness": None, "grounded": None, "completeness": None}


def test_media_and_pass_rate_skip_none_and_use_correctness_only() -> None:
    casos = [
        {"correctness": 1.0, "grounded": 0.5, "passed": True},
        {"correctness": 0.5, "grounded": None, "passed": False},
        {"correctness": None, "grounded": 1.0, "passed": False},
    ]
    assert media("correctness", casos) == 0.75
    assert media("grounded", casos) == 0.75
    assert pass_rate(casos) == 0.3333


def test_classify_excludes_expected_refuse_false_refusal_and_empty_context() -> None:
    assert classify_case(expected_behavior="refuse", is_refusal=True, context_chunks=[], error=None) == "unanswerable_ok"
    assert classify_case(expected_behavior="refusal", is_refusal=True, context_chunks=[], error=None) == "unanswerable_ok"
    assert classify_case(expected_behavior="refusal", is_refusal=False, context_chunks=["ctx"], error=None) == "unanswerable_answered"
    assert classify_case(expected_behavior="answer", is_refusal=True, context_chunks=["ctx"], error=None) == "false_refusal"
    assert classify_case(expected_behavior="answer", is_refusal=False, context_chunks=[], error=None) == "no_context"
    assert classify_case(expected_behavior="answer", is_refusal=False, context_chunks=["ctx"], error=None) == "score"


def test_score_generated_answer_makes_one_call_with_all_scores() -> None:
    judge = SequentialJudge(['{"correctness": 90, "grounded": 80, "completeness": 100}'])
    scored = score_generated_answer(
        judge,
        model="grok-latest",
        question="Qual o limite?",
        reference="25 MB",
        generated="O limite é 25 MB.",
        context_chunks=["Limite 25 MB.", "Google Drive permitido."],
        expected_behavior="answer",
        is_refusal=False,
        error=None,
        pass_threshold=0.8,
    )
    assert scored["correctness"] == 0.9
    assert scored["grounded"] == 0.8
    assert scored["completeness"] == 1.0
    assert scored["passed"] is True
    assert scored["bucket"] == "score"
    assert len(judge.calls) == 1
    first = judge.calls[0]
    assert first["system"] == JUDGE_SYSTEM_PROMPT
    assert first["temperature"] == JUDGE_TEMPERATURE == 0.2
    assert first["top_p"] == JUDGE_TOP_P == 0.95
    assert first["max_output_tokens"] == JUDGE_MAX_OUTPUT_TOKENS == 8192
    assert first["timeout"] == JUDGE_TIMEOUT_S == 120.0
    assert "Score the generated answer on three metrics" in first["user"]
    assert "Retrieved context:" in first["user"]
    assert CONTEXT_JOIN.join(["Limite 25 MB.", "Google Drive permitido."]) in first["user"]
    assert '"correctness"' in first["user"]
    assert join_retrieved_context(["a", "b"]) == "a\n\n---\n\nb"


def test_score_retries_on_transport_error(monkeypatch) -> None:
    class FlakyJudge:
        name = "xai"

        def __init__(self) -> None:
            self.calls = 0

        def complete(self, **_kwargs):
            self.calls += 1
            if self.calls < 3:
                return CompletionResult(text="", latency_ms=1, error="APITimeoutError: Request timed out.")
            return CompletionResult(
                text='{"correctness": 80, "grounded": 90, "completeness": 70}',
                latency_ms=2,
            )

    monkeypatch.setattr("lab.rag_judge.JUDGE_RETRY_BACKOFF_S", 0)
    judge = FlakyJudge()
    scored = score_generated_answer(
        judge,
        model="m",
        question="q",
        reference="r",
        generated="a",
        context_chunks=["ctx"],
        expected_behavior="answer",
        is_refusal=False,
        error=None,
    )
    assert judge.calls == 3
    assert scored["correctness"] == 0.8
    assert scored["error"] is None
    assert scored["calls"][0]["attempts"] == 3


def test_score_skips_llm_for_expected_refusal() -> None:
    judge = SequentialJudge(["90"])
    scored = score_generated_answer(
        judge,
        model="m",
        question="q",
        reference=None,
        generated="recusa",
        context_chunks=[],
        expected_behavior="refuse",
        is_refusal=True,
        error=None,
    )
    assert scored["bucket"] == "unanswerable_ok"
    assert scored["correctness"] is None
    assert scored["passed"] is False
    assert judge.calls == []


def test_aggregate_llm_cases_excludes_refusals_from_averages() -> None:
    summary = aggregate_llm_cases(
        [
            {"bucket": "score", "correctness": 1.0, "grounded": 0.5, "completeness": 1.0, "passed": True},
            {"bucket": "unanswerable_ok", "correctness": None, "unanswerable_ok": True, "passed": False},
            {"bucket": "false_refusal", "correctness": None, "false_refusal": True, "passed": False},
        ]
    )
    assert summary["correctness"] == 1.0
    assert summary["grounded_rate"] == 0.5
    assert summary["n"] == 1
    assert summary["n_unanswerable_ok"] == 1
    assert summary["n_false_refusal"] == 1
    assert summary["pass_rate"] == 1.0
