from __future__ import annotations

import json
import os
from contextlib import asynccontextmanager
from typing import Any, Literal

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response, StreamingResponse
from pydantic import BaseModel, Field

from lab.chat import ChatAnswer, answer_question
from lab.compare import (
    evaluations_csv,
    generate_pair,
    generations_by_id,
    list_questions,
    load_evaluations,
    result_for,
    save_evaluation,
    save_override,
)
from lab.config import Settings, load_settings
from lab.context import ContextPolicy, ContextStore
from lab.providers.base import ChatProvider
from lab.sweep_report import (
    MAX_UPLOAD_BYTES,
    list_runs,
    load_or_build_report,
    resolve_run_dir,
    save_uploaded_report,
)


class EvaluationRequest(BaseModel):
    case_id: str = Field(min_length=1)
    verdict: Literal["xai_better", "gemini_better", "tie", "both_weak"]
    notes: str = ""


class ChatRequest(BaseModel):
    message: str = Field(min_length=1)
    history: list[dict[str, str]] = Field(default_factory=list)
    provider: Literal["gemini", "xai"] | None = None


class ChatResponse(BaseModel):
    answer: str
    is_refusal: bool
    scratchpad_leaked: bool
    latency_ms: int
    provider: str
    model: str
    retrieval: str
    sources: list[dict[str, Any]]
    error: str | None = None


class AppState:
    settings: Settings
    store: ContextStore
    providers: dict[str, ChatProvider]
    models: dict[str, str]
    default_provider: str


state = AppState()


def _payload(answer: ChatAnswer) -> dict[str, Any]:
    return {
        "answer": answer.answer,
        "is_refusal": answer.is_refusal,
        "scratchpad_leaked": answer.scratchpad_leaked,
        "latency_ms": answer.latency_ms,
        "provider": answer.provider,
        "model": answer.model,
        "retrieval": answer.retrieval,
        "sources": answer.sources,
        "error": answer.error,
    }


def _resolve_provider(name: str | None) -> tuple[ChatProvider, str]:
    chosen = (name or state.default_provider).strip().lower()
    if chosen not in state.providers:
        raise HTTPException(status_code=400, detail=f"Fornecedor indisponível: {chosen}")
    return state.providers[chosen], state.models[chosen]


@asynccontextmanager
async def lifespan(_app: FastAPI):
    settings = load_settings(require_keys=False)
    state.settings = settings
    state.store = ContextStore.from_files(
        chunks_path=settings.chunks_path,
        retrieval_path=settings.retrieval_path,
        gold_path=settings.gold_path,
        policy=ContextPolicy(mode="top_n", top_n=6, max_chars=9000),
    )
    state.providers = {}
    state.models = {"gemini": settings.gemini_model, "xai": settings.xai_model}
    if settings.gemini_api_key:
        from lab.providers.gemini import GeminiProvider

        state.providers["gemini"] = GeminiProvider(settings)
    if settings.xai_api_key:
        from lab.providers.xai import XaiProvider

        state.providers["xai"] = XaiProvider(settings)
    preferred = (os.getenv("CHAT_PROVIDER") or "xai").strip().lower()
    state.default_provider = preferred if preferred in state.providers else (next(iter(state.providers), "xai"))
    yield


app = FastAPI(title="Goldilocks RAG", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173", "http://localhost:8000", "http://127.0.0.1:8000"],
    allow_methods=["*"],
    allow_headers=["*"],
)


def _snapshot() -> tuple[dict[str, Any], dict[str, str], dict[str, Any]]:
    generations, models = generations_by_id(state.settings.runs_dir)
    models = {**state.models, **models}
    return generations, models, load_evaluations()


@app.get("/health")
def health() -> dict[str, Any]:
    return {
        "ok": True,
        "default_provider": state.default_provider,
        "providers": list(state.providers),
        "models": {name: state.models[name] for name in state.providers},
    }


@app.get("/questions")
def questions() -> list[dict[str, Any]]:
    generations, _models, evaluations = _snapshot()
    return list_questions(state.store, generations=generations, evaluations=evaluations)


@app.get("/results/{case_id}")
def results(case_id: str) -> dict[str, Any]:
    generations, models, evaluations = _snapshot()
    try:
        return result_for(
            state.store,
            case_id,
            generations=generations,
            evaluations=evaluations,
            models=models,
        )
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=f"Pergunta desconhecida: {case_id}") from exc


@app.post("/run/{case_id}")
def rerun(case_id: str) -> dict[str, Any]:
    missing = [name for name in ("xai", "gemini") if name not in state.providers]
    if missing:
        raise HTTPException(status_code=503, detail=f"Faltam fornecedores: {', '.join(missing)}")
    try:
        case = generate_pair(
            store=state.store,
            providers=[state.providers["xai"], state.providers["gemini"]],
            case_id=case_id,
        )
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=f"Pergunta desconhecida: {case_id}") from exc
    save_override(case)
    generations, models, evaluations = _snapshot()
    generations[case_id] = case
    return result_for(
        state.store,
        case_id,
        generations=generations,
        evaluations=evaluations,
        models=models,
    )


@app.get("/metrics/runs")
def metrics_runs() -> list[dict[str, Any]]:
    return list_runs(state.settings.runs_dir)


@app.post("/metrics/runs/upload")
async def metrics_upload(file: UploadFile = File(...)) -> dict[str, Any]:
    raw = await file.read()
    if not raw:
        raise HTTPException(status_code=400, detail="Ficheiro vazio")
    if len(raw) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=400, detail="Ficheiro demasiado grande (máx. 20 MB)")
    try:
        payload = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise HTTPException(status_code=400, detail="JSON inválido") from exc
    try:
        return save_uploaded_report(state.settings.runs_dir, payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except FileExistsError as exc:
        raise HTTPException(status_code=409, detail="Corrida já existe; tente de novo") from exc


@app.get("/metrics/runs/{run_id}")
def metrics_run(run_id: str) -> dict[str, Any]:
    try:
        folder = resolve_run_dir(state.settings.runs_dir, run_id)
        return load_or_build_report(folder, run_id=run_id)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=f"Corrida desconhecida: {run_id}") from exc


@app.get("/evaluations")
def get_evaluations() -> dict[str, Any]:
    return load_evaluations()


@app.get("/evaluations.csv")
def get_evaluations_csv() -> Response:
    return Response(
        content=evaluations_csv(),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": "attachment; filename=evaluations.csv"},
    )


@app.post("/evaluations")
def post_evaluation(body: EvaluationRequest) -> dict[str, Any]:
    if state.store.gold_case(body.case_id) is None:
        raise HTTPException(status_code=404, detail=f"Pergunta desconhecida: {body.case_id}")
    try:
        return save_evaluation(body.case_id, verdict=body.verdict, notes=body.notes)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/chat", response_model=ChatResponse)
def chat(body: ChatRequest) -> ChatResponse:
    provider, model = _resolve_provider(body.provider)
    result = answer_question(
        question=body.message,
        history=body.history,
        store=state.store,
        provider=provider,
        model=model,
    )
    if result.error:
        raise HTTPException(status_code=502, detail=result.error)
    return ChatResponse(**_payload(result))


@app.post("/chat/stream")
def chat_stream(body: ChatRequest) -> StreamingResponse:
    provider, model = _resolve_provider(body.provider)

    def events():
        result = answer_question(
            question=body.message,
            history=body.history,
            store=state.store,
            provider=provider,
            model=model,
        )
        if result.error:
            yield f"event: error\ndata: {json.dumps({'error': result.error}, ensure_ascii=False)}\n\n"
            return
        payload = _payload(result)
        yield f"event: sources\ndata: {json.dumps({'sources': payload['sources'], 'retrieval': payload['retrieval']}, ensure_ascii=False)}\n\n"
        answer = payload["answer"] or ""
        step = 24
        for index in range(0, len(answer), step):
            chunk = answer[index : index + step]
            yield f"event: delta\ndata: {json.dumps({'text': chunk}, ensure_ascii=False)}\n\n"
        yield f"event: done\ndata: {json.dumps(payload, ensure_ascii=False)}\n\n"

    return StreamingResponse(events(), media_type="text/event-stream")


def main() -> None:
    import uvicorn

    uvicorn.run("lab.app:app", host="127.0.0.1", port=8000, reload=True)


if __name__ == "__main__":
    main()
