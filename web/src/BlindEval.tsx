import { KeyboardEvent, useEffect, useMemo, useRef, useState } from "react";
import Markdown from "react-markdown";
import { API_URL, api, sessionHeaders } from "./api";
import type { Session } from "./session";

type Question = {
  id: string;
  text: string;
  category: string | null;
  has_results: boolean;
  evaluated: boolean;
};

type BlindCase = {
  case_id: string;
  question: string;
  chunk_count: number | null;
  expected_behavior: string | null;
  answer_a: { text: string | null; available: boolean };
  answer_b: { text: string | null; available: boolean };
  rated: boolean;
};

type Props = { session: Session };

export default function BlindEval({ session }: Props) {
  const [questions, setQuestions] = useState<Question[]>([]);
  const [query, setQuery] = useState("");
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [current, setCurrent] = useState<BlindCase | null>(null);
  const [scoreA, setScoreA] = useState(5);
  const [scoreB, setScoreB] = useState(5);
  const [notes, setNotes] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const headers = sessionHeaders(session.id);
  const filtered = useMemo(() => {
    const needle = query.trim().toLowerCase();
    if (!needle) return questions;
    return questions.filter((item) => `${item.id} ${item.text}`.toLowerCase().includes(needle));
  }, [questions, query]);
  const selectedIndex = filtered.findIndex((item) => item.id === selectedId);

  async function loadList(prefer?: string) {
    const rows = await api<Question[]>("/blind/questions", { headers });
    setQuestions(rows);
    setSelectedId((currentId) => prefer || currentId || rows[0]?.id || null);
  }

  useEffect(() => {
    loadList().catch((err: Error) => setError(err.message));
  }, []);

  useEffect(() => {
    if (!selectedId) return;
    api<BlindCase>(`/blind/cases/${selectedId}`, { headers })
      .then((payload) => {
        setCurrent(payload);
        setNotes("");
        setScoreA(5);
        setScoreB(5);
      })
      .catch((err: Error) => setError(err.message));
  }, [selectedId]);

  function go(delta: number) {
    if (!filtered.length) return;
    const next = Math.min(filtered.length - 1, Math.max(0, selectedIndex + delta));
    setSelectedId(filtered[next].id);
  }

  const goRef = useRef(go);
  goRef.current = go;

  useEffect(() => {
    function onKey(event: globalThis.KeyboardEvent) {
      const target = event.target as HTMLElement | null;
      if (target && ["INPUT", "TEXTAREA", "SELECT"].includes(target.tagName)) return;
      if (event.key === "ArrowLeft") goRef.current(-1);
      if (event.key === "ArrowRight") goRef.current(1);
    }
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, []);

  async function submit() {
    if (!selectedId) return;
    setBusy(true);
    setError(null);
    try {
      await api("/human/ratings", {
        method: "POST",
        headers,
        body: JSON.stringify({ case_id: selectedId, score_a: scoreA, score_b: scoreB, notes }),
      });
      await loadList(selectedId);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Não foi possível gravar.");
    } finally {
      setBusy(false);
    }
  }

  function onNotesKey(event: KeyboardEvent<HTMLTextAreaElement>) {
    event.stopPropagation();
  }

  return (
    <div className="shell compare">
      <aside className="rail">
        <input className="search" value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Pesquisar…" />
        <p className="muted">
          {filtered.filter((item) => item.evaluated).length}/{filtered.length} avaliadas
        </p>
        <nav className="qlist">
          {filtered.map((item) => (
            <button
              type="button"
              key={item.id}
              className={`qitem ${item.id === selectedId ? "active" : ""}`}
              onClick={() => setSelectedId(item.id)}
            >
              <span>{item.id}</span>
              <small>{item.text}</small>
              <em>{item.evaluated ? "avaliada" : item.has_results ? "por avaliar" : "sem run"}</em>
            </button>
          ))}
        </nav>
      </aside>
      <main className="stage compare-stage">
        {error && <div className="banner">{error}</div>}
        {!current ? (
          <p className="muted">A carregar…</p>
        ) : (
          <>
            <header className="compare-head">
              <div>
                <p className="muted">
                  {current.case_id}
                  {current.expected_behavior ? ` · ${current.expected_behavior}` : ""}
                  {" · "}
                  Chunks recuperados: {current.chunk_count ?? "—"}
                </p>
                <h1>{current.question}</h1>
              </div>
              <div className="nav-row">
                <button type="button" className="ghost" onClick={() => go(-1)} disabled={selectedIndex <= 0}>
                  Anterior
                </button>
                <button
                  type="button"
                  className="ghost"
                  onClick={() => go(1)}
                  disabled={selectedIndex < 0 || selectedIndex >= filtered.length - 1}
                >
                  Seguinte
                </button>
                <a className="ghost" href={`${API_URL}/human/export.csv`}>
                  Exportar CSV
                </a>
                <a className="ghost" href={`${API_URL}/evaluations/report.txt`}>
                  Descarregar relatório
                </a>
              </div>
            </header>
            <p className="muted">Avalie só com base na leitura. 0 = muito mau, 10 = excelente. Os sistemas não são identificados.</p>
            <section className="columns">
              {(["a", "b"] as const).map((slot) => {
                const answer = slot === "a" ? current.answer_a : current.answer_b;
                const score = slot === "a" ? scoreA : scoreB;
                const setScore = slot === "a" ? setScoreA : setScoreB;
                return (
                  <article key={slot} className="column">
                    <header className="column-head">
                      <h2>Resposta {slot.toUpperCase()}</h2>
                      <label className="score">
                        Nota {score}
                        <input
                          type="range"
                          min={0}
                          max={10}
                          value={score}
                          onChange={(event) => setScore(Number(event.target.value))}
                        />
                      </label>
                    </header>
                    {answer.available && answer.text ? (
                      <div className="markdown">
                        <Markdown>{answer.text}</Markdown>
                      </div>
                    ) : (
                      <p className="muted">Resposta indisponível para este caso.</p>
                    )}
                  </article>
                );
              })}
            </section>
            <section className="panel judge">
              <textarea value={notes} onChange={(event) => setNotes(event.target.value)} onKeyDown={onNotesKey} placeholder="Notas (opcional)" rows={3} />
              <button type="button" className="ghost" disabled={busy} onClick={() => void submit()}>
                {busy ? "A gravar…" : current.rated ? "Atualizar avaliação" : "Submeter avaliação"}
              </button>
            </section>
          </>
        )}
      </main>
    </div>
  );
}
