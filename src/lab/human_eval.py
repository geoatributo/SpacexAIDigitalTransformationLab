from __future__ import annotations

import csv
import hashlib
import io
import os
import random
import threading
import uuid
from datetime import datetime, timezone
from typing import Any, Literal, Protocol

Mode = Literal["rate", "metrics_only"]


def rater_id(name: str) -> str:
    return hashlib.sha256(name.strip().lower().encode("utf-8")).hexdigest()[:12]


class HumanEvalStore(Protocol):
    def put_session(self, session: dict[str, Any]) -> None: ...
    def get_session(self, session_id: str) -> dict[str, Any] | None: ...
    def get_assignment(self, session_id: str, case_id: str) -> tuple[str, str] | None: ...
    def put_assignment(self, session_id: str, case_id: str, slot_a: str, slot_b: str) -> None: ...
    def put_rating(self, row: dict[str, Any]) -> None: ...
    def rated_case_ids(self, session_id: str) -> set[str]: ...
    def all_ratings(self) -> list[dict[str, Any]]: ...


class MemoryStore:
    """Isolamento em testes. Não usar no Evento."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self.sessions: dict[str, dict[str, Any]] = {}
        self.assignments: dict[tuple[str, str], tuple[str, str]] = {}
        self.ratings: dict[tuple[str, str], dict[str, Any]] = {}

    def put_session(self, session: dict[str, Any]) -> None:
        with self._lock:
            self.sessions[session["id"]] = dict(session)

    def get_session(self, session_id: str) -> dict[str, Any] | None:
        with self._lock:
            row = self.sessions.get(session_id)
            return dict(row) if row else None

    def get_assignment(self, session_id: str, case_id: str) -> tuple[str, str] | None:
        with self._lock:
            return self.assignments.get((session_id, case_id))

    def put_assignment(self, session_id: str, case_id: str, slot_a: str, slot_b: str) -> None:
        with self._lock:
            self.assignments[(session_id, case_id)] = (slot_a, slot_b)

    def put_rating(self, row: dict[str, Any]) -> None:
        with self._lock:
            self.ratings[(row["session_id"], row["case_id"])] = dict(row)

    def rated_case_ids(self, session_id: str) -> set[str]:
        with self._lock:
            return {case_id for (sid, case_id) in self.ratings if sid == session_id}

    def all_ratings(self) -> list[dict[str, Any]]:
        with self._lock:
            return [dict(row) for row in self.ratings.values()]


class FirestoreStore:
    """Firebase / Google Cloud Firestore. O browser nunca escreve aqui; só a API."""

    def __init__(self, project: str | None = None, database: str | None = None) -> None:
        from google.cloud import firestore

        kwargs: dict[str, Any] = {}
        if project:
            kwargs["project"] = project
        if database:
            kwargs["database"] = database
        self._db = firestore.Client(**kwargs)
        self._sessions = self._db.collection("human_eval_sessions")
        self._assignments = self._db.collection("human_eval_assignments")
        self._ratings = self._db.collection("human_eval_ratings")

    @staticmethod
    def _pair_id(session_id: str, case_id: str) -> str:
        return f"{session_id}__{case_id}"

    def put_session(self, session: dict[str, Any]) -> None:
        self._sessions.document(session["id"]).set(session)

    def get_session(self, session_id: str) -> dict[str, Any] | None:
        snap = self._sessions.document(session_id).get()
        return snap.to_dict() if snap.exists else None

    def get_assignment(self, session_id: str, case_id: str) -> tuple[str, str] | None:
        snap = self._assignments.document(self._pair_id(session_id, case_id)).get()
        if not snap.exists:
            return None
        data = snap.to_dict() or {}
        return str(data["slot_a"]), str(data["slot_b"])

    def put_assignment(self, session_id: str, case_id: str, slot_a: str, slot_b: str) -> None:
        self._assignments.document(self._pair_id(session_id, case_id)).set(
            {"session_id": session_id, "case_id": case_id, "slot_a": slot_a, "slot_b": slot_b}
        )

    def put_rating(self, row: dict[str, Any]) -> None:
        self._ratings.document(self._pair_id(row["session_id"], row["case_id"])).set(row)

    def rated_case_ids(self, session_id: str) -> set[str]:
        return {
            str(doc.to_dict()["case_id"])
            for doc in self._ratings.where("session_id", "==", session_id).stream()
            if doc.to_dict()
        }

    def all_ratings(self) -> list[dict[str, Any]]:
        rows = [doc.to_dict() or {} for doc in self._ratings.stream()]
        rows.sort(key=lambda item: str(item.get("created_at") or ""))
        return rows


def firestore_project() -> str:
    return (os.getenv("FIREBASE_PROJECT_ID") or os.getenv("GOOGLE_CLOUD_PROJECT") or "").strip()


def default_store() -> HumanEvalStore:
    if (os.getenv("HUMAN_EVAL_STORE") or "").strip().lower() == "memory":
        return MemoryStore()
    project = firestore_project() or None
    database = (os.getenv("FIRESTORE_DATABASE") or "").strip() or None
    if project or os.getenv("K_SERVICE"):
        return FirestoreStore(project, database)
    return MemoryStore()


_store: HumanEvalStore | None = None


def get_store() -> HumanEvalStore:
    global _store
    if _store is None:
        _store = default_store()
    return _store


def reset_store(store: HumanEvalStore | None = None) -> None:
    global _store
    _store = store


def _use(store: HumanEvalStore | None) -> HumanEvalStore:
    return store if store is not None else get_store()


def create_session(name: str, mode: Mode, *, store: HumanEvalStore | None = None) -> dict[str, Any]:
    cleaned = name.strip()
    if mode == "rate" and len(cleaned) < 2:
        raise ValueError("Declare o nome para avaliar.")
    if mode not in {"rate", "metrics_only"}:
        raise ValueError("Modo inválido.")
    display = cleaned or "visita"
    session = {
        "id": str(uuid.uuid4()),
        "name": display,
        "rater_id": rater_id(display),
        "mode": mode,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    _use(store).put_session(session)
    return {"id": session["id"], "name": session["name"], "mode": session["mode"]}


def get_session(session_id: str, *, store: HumanEvalStore | None = None) -> dict[str, Any] | None:
    return _use(store).get_session(session_id)


def assignment_for(session_id: str, case_id: str, *, store: HumanEvalStore | None = None) -> tuple[str, str]:
    backend = _use(store)
    existing = backend.get_assignment(session_id, case_id)
    if existing:
        return existing
    order = ("xai", "gemini")
    if random.Random(f"{session_id}:{case_id}").random() < 0.5:
        order = ("gemini", "xai")
    backend.put_assignment(session_id, case_id, order[0], order[1])
    return order


def blind_answers(result: dict[str, Any], slot_a: str, slot_b: str) -> dict[str, Any]:
    def slot(name: str) -> dict[str, Any]:
        row = result.get(name) or {}
        text = row.get("visible_text")
        if row.get("error"):
            text = None
        return {"text": text, "available": bool(text)}

    return {
        "case_id": result["case_id"],
        "question": result["question"],
        "chunk_count": result.get("chunk_count"),
        "expected_behavior": result.get("expected_behavior"),
        "answer_a": slot(slot_a),
        "answer_b": slot(slot_b),
    }


def save_rating(
    *,
    session_id: str,
    case_id: str,
    score_a: int,
    score_b: int,
    notes: str = "",
    run_file: str | None,
    context: dict[str, Any] | None,
    store: HumanEvalStore | None = None,
) -> dict[str, Any]:
    if not (0 <= score_a <= 10 and 0 <= score_b <= 10):
        raise ValueError("As notas têm de estar entre 0 e 10.")
    backend = _use(store)
    session = backend.get_session(session_id)
    if session is None:
        raise KeyError("Sessão desconhecida.")
    if session["mode"] != "rate":
        raise ValueError("Esta sessão só consulta métricas.")
    slot_a, slot_b = assignment_for(session_id, case_id, store=backend)
    backend.put_rating(
        {
            "id": str(uuid.uuid4()),
            "session_id": session_id,
            "rater_id": session["rater_id"],
            "case_id": case_id,
            "score_a": score_a,
            "score_b": score_b,
            "notes": notes,
            "slot_a": slot_a,
            "slot_b": slot_b,
            "run_file": run_file,
            "context": context or {},
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
    )
    return {"ok": True, "case_id": case_id}


def rated_cases(session_id: str, *, store: HumanEvalStore | None = None) -> set[str]:
    return _use(store).rated_case_ids(session_id)


def summary(*, store: HumanEvalStore | None = None, case_ids: list[str] | None = None) -> dict[str, Any]:
    rows = _use(store).all_ratings()
    users = {str(row.get("rater_id")) for row in rows if row.get("rater_id")}
    by_case: dict[str, int] = {}
    for row in rows:
        case_id = str(row.get("case_id") or "")
        by_case[case_id] = by_case.get(case_id, 0) + 1
    total_cases = len(case_ids or [])
    covered = sum(1 for case_id in (case_ids or by_case) if by_case.get(case_id, 0) > 0)
    return {
        "distinct_raters": len(users),
        "n_ratings": len(rows),
        "cases_covered": covered,
        "cases_total": total_cases or len(by_case),
        "by_case": by_case,
    }


def export_rows(*, store: HumanEvalStore | None = None) -> list[dict[str, Any]]:
    out = []
    for row in _use(store).all_ratings():
        out.append(
            {
                "case_id": row.get("case_id"),
                "rater_id": row.get("rater_id"),
                "score_a": row.get("score_a"),
                "score_b": row.get("score_b"),
                "notes": row.get("notes"),
                "slot_a": row.get("slot_a"),
                "slot_b": row.get("slot_b"),
                "run_file": row.get("run_file"),
                "created_at": row.get("created_at"),
                "context": row.get("context") or {},
            }
        )
    return out


def export_csv_text(*, store: HumanEvalStore | None = None) -> str:
    rows = export_rows(store=store)
    buffer = io.StringIO()
    fields = ["case_id", "rater_id", "score_a", "score_b", "slot_a", "slot_b", "notes", "run_file", "created_at"]
    writer = csv.DictWriter(buffer, fieldnames=fields, extrasaction="ignore")
    writer.writeheader()
    for row in rows:
        writer.writerow(row)
    return buffer.getvalue()
