import { KeyboardEvent, useEffect, useMemo, useRef, useState } from "react";
import Markdown from "react-markdown";
import { API_URL, api } from "./api";
import {
  buildSummary,
  citationLabel,
  compareMetric,
  formatPt,
  parseCitations,
  reasoningTokens,
  secondsFromMs,
  wordCount,
  type CompareSide,
} from "./metrics";

type Question = {
  id: string;
  text: string;
  category: string | null;
  expected_behavior: string | null;
  has_results: boolean;
  evaluated: boolean;
  verdict: string | null;
};

type Source = {
  index: number;
  chunk_id: string;
  document: string;
  filename: string;
  page: string | null;
  section: string | null;
  score: number;
  excerpt: string;
};

type ProviderRow = {
  provider: "xai" | "gemini";
  visible_text: string | null;
  latency_ms: number | null;
  usage: {
    prompt_tokens: number | null;
    completion_tokens: number | null;
    total_tokens: number | null;
  };
  is_refusal: boolean | null;
  scratchpad_leaked: boolean | null;
  error: string | null;
};

type Result = {
  case_id: string;
  question: string;
  chunk_ids: string[];
  chunk_count: number | null;
  empty_context: boolean | null;
  expected_behavior: string | null;
  reference_answer: string | null;
  models: { xai: string | null; gemini: string | null };
  sources: Source[];
  xai: ProviderRow | null;
  gemini: ProviderRow | null;
  evaluation: { verdict: string; notes: string } | null;
};

const VERDICTS = [
  { id: "xai_better", label: "xAI melhor" },
  { id: "gemini_better", label: "Gemini melhor" },
  { id: "tie", label: "Empate" },
  { id: "both_weak", label: "Ambas fracas" },
] as const;

function dash(value: string | number | null | undefined): string {
  if (value == null || value === "") return "—";
  return String(value);
}

type ChipItem = {
  key: string;
  label?: string;
  value: string;
  side: CompareSide;
  title?: string;
};

function MetricLine({ items }: { items: ChipItem[] }) {
  return (
    <p className="metric-line">
      {items.map((item, index) => (
        <span key={item.key}>
          {index > 0 ? <span className="metric-sep">·</span> : null}
          <span className="metric-item">
            {item.label ? <span className="metric-label">{item.label}</span> : null}
            {item.label ? (
              <span className={`chip ${item.side}`} title={item.title}>
                {item.value}
              </span>
            ) : (
              <span className="metric-model">{item.value}</span>
            )}
          </span>
        </span>
      ))}
    </p>
  );
}

function deltaTitle(side: CompareSide, delta: string | null | undefined, extra?: string): string | undefined {
  const parts: string[] = [];
  if (side === "high" && delta) parts.push(delta);
  if (extra) parts.push(extra);
  return parts.length ? parts.join(" · ") : undefined;
}

function citedBy(index: number, xai: number[], gemini: number[]): string {
  const inXai = xai.includes(index);
  const inGemini = gemini.includes(index);
  if (inXai && inGemini) return "citado por xAI e Gemini";
  if (inXai) return "citado por xAI";
  if (inGemini) return "citado por Gemini";
  return "não citado";
}

type Props = { allowGeneration?: boolean };

export default function Compare({ allowGeneration = false }: Props) {
  const [questions, setQuestions] = useState<Question[]>([]);
  const [query, setQuery] = useState("");
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [result, setResult] = useState<Result | null>(null);
  const [notes, setNotes] = useState("");
  const [verdict, setVerdict] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const drawerRef = useRef<HTMLDetailsElement>(null);

  const filtered = useMemo(() => {
    const needle = query.trim().toLowerCase();
    if (!needle) return questions;
    return questions.filter((item) => `${item.id} ${item.text}`.toLowerCase().includes(needle));
  }, [questions, query]);

  const selectedIndex = filtered.findIndex((item) => item.id === selectedId);

  const xai = result?.xai ?? null;
  const gemini = result?.gemini ?? null;
  const xaiSeconds = secondsFromMs(xai?.latency_ms);
  const geminiSeconds = secondsFromMs(gemini?.latency_ms);
  const xaiReasoning = reasoningTokens(xai?.usage);
  const geminiReasoning = reasoningTokens(gemini?.usage);
  const xaiCitations = parseCitations(xai?.visible_text);
  const geminiCitations = parseCitations(gemini?.visible_text);
  const xaiWords = wordCount(xai?.visible_text);
  const geminiWords = wordCount(gemini?.visible_text);

  const latencyCmp = compareMetric(xaiSeconds, geminiSeconds);
  const promptCmp = compareMetric(xai?.usage?.prompt_tokens, gemini?.usage?.prompt_tokens);
  const completionCmp = compareMetric(xai?.usage?.completion_tokens, gemini?.usage?.completion_tokens);
  const reasoningCmp = compareMetric(xaiReasoning, geminiReasoning);
  const totalCmp = compareMetric(xai?.usage?.total_tokens, gemini?.usage?.total_tokens);
  const citeCmp = compareMetric(
    xai?.visible_text == null ? null : xaiCitations.length,
    gemini?.visible_text == null ? null : geminiCitations.length,
  );
  const wordsCmp = compareMetric(xaiWords, geminiWords);

  function metricItems(name: "xai" | "gemini"): ChipItem[] {
    const row = name === "xai" ? xai : gemini;
    const side = name === "xai" ? "a" : "b";
    const seconds = name === "xai" ? xaiSeconds : geminiSeconds;
    const reasoning = name === "xai" ? xaiReasoning : geminiReasoning;
    const cites = name === "xai" ? xaiCitations : geminiCitations;
    const words = name === "xai" ? xaiWords : geminiWords;
    const items: ChipItem[] = [
      { key: "model", value: dash(result?.models[name]), side: "neutral" },
      {
        key: "tempo",
        label: "Tempo:",
        value: seconds == null ? "—" : `${formatPt(seconds, 1)}s`,
        side: latencyCmp[side],
        title: deltaTitle(latencyCmp[side], latencyCmp.delta != null ? `+${formatPt(latencyCmp.delta, 1)}s` : null),
      },
      {
        key: "entrada",
        label: "Entrada:",
        value: dash(row?.usage?.prompt_tokens ?? null),
        side: promptCmp[side],
        title: deltaTitle(promptCmp[side], promptCmp.delta != null ? `+${formatPt(promptCmp.delta)}` : null),
      },
      {
        key: "saida",
        label: "Saída:",
        value: dash(row?.usage?.completion_tokens ?? null),
        side: completionCmp[side],
        title: deltaTitle(completionCmp[side], completionCmp.delta != null ? `+${formatPt(completionCmp.delta)}` : null),
      },
    ];
    if (reasoning != null) {
      items.push({
        key: "raciocinio",
        label: "Raciocínio:",
        value: formatPt(reasoning),
        side: reasoningCmp[side],
        title: deltaTitle(reasoningCmp[side], reasoningCmp.delta != null ? `+${formatPt(reasoningCmp.delta)}` : null),
      });
    }
    items.push(
      {
        key: "total",
        label: "Total:",
        value: dash(row?.usage?.total_tokens ?? null),
        side: totalCmp[side],
        title: deltaTitle(totalCmp[side], totalCmp.delta != null ? `+${formatPt(totalCmp.delta)}` : null),
      },
      {
        key: "citas",
        label: "Citações:",
        value: row?.visible_text == null ? "—" : String(cites.length),
        side: citeCmp[side],
        title: deltaTitle(
          citeCmp[side],
          citeCmp.delta != null ? `+${formatPt(citeCmp.delta)}` : null,
          row?.visible_text == null ? undefined : citationLabel(cites),
        ),
      },
      {
        key: "palavras",
        label: "Palavras:",
        value: dash(words),
        side: wordsCmp[side],
        title: deltaTitle(wordsCmp[side], wordsCmp.delta != null ? `+${formatPt(wordsCmp.delta)}` : null),
      },
    );
    return items;
  }

  async function loadQuestions(preferId?: string) {
    const rows = await api<Question[]>("/questions");
    setQuestions(rows);
    setSelectedId((current) => preferId || current || rows[0]?.id || null);
  }

  async function loadResult(id: string) {
    setError(null);
    const payload = await api<Result>(`/results/${id}`);
    setResult(payload);
    setNotes(payload.evaluation?.notes || "");
    setVerdict(payload.evaluation?.verdict || null);
  }

  useEffect(() => {
    loadQuestions().catch((err: Error) => setError(err.message));
  }, []);

  useEffect(() => {
    const media = window.matchMedia("(min-width: 901px)");
    const sync = () => {
      if (drawerRef.current && media.matches) drawerRef.current.open = true;
    };
    sync();
    media.addEventListener("change", sync);
    return () => media.removeEventListener("change", sync);
  }, []);

  useEffect(() => {
    if (!selectedId) return;
    loadResult(selectedId).catch((err: Error) => setError(err.message));
  }, [selectedId]);

  useEffect(() => {
    function onKey(event: globalThis.KeyboardEvent) {
      const target = event.target as HTMLElement | null;
      if (target && ["INPUT", "TEXTAREA", "SELECT"].includes(target.tagName)) return;
      if (event.key === "ArrowLeft") {
        event.preventDefault();
        go(-1);
      }
      if (event.key === "ArrowRight") {
        event.preventDefault();
        go(1);
      }
    }
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  });

  function go(delta: number) {
    if (!filtered.length) return;
    const next = Math.min(filtered.length - 1, Math.max(0, selectedIndex + delta));
    setSelectedId(filtered[next].id);
  }

  async function save(nextVerdict?: string) {
    if (!selectedId) return;
    setBusy(true);
    setError(null);
    try {
      const payload: { case_id: string; notes: string; verdict?: string } = {
        case_id: selectedId,
        notes,
      };
      if (nextVerdict) payload.verdict = nextVerdict;
      const saved = await api<{ verdict: string | null }>("/evaluations", {
        method: "POST",
        body: JSON.stringify(payload),
      });
      setVerdict(saved.verdict || nextVerdict || verdict);
      await loadQuestions(selectedId);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Não foi possível guardar a avaliação.");
    } finally {
      setBusy(false);
    }
  }

  async function rerun() {
    if (!selectedId) return;
    setBusy(true);
    setError(null);
    try {
      const payload = await api<Result>(`/run/${selectedId}`, { method: "POST" });
      setResult(payload);
      await loadQuestions(selectedId);
    } catch (err) {
      setError(err instanceof Error ? err.message : "A geração falhou.");
    } finally {
      setBusy(false);
    }
  }

  function onNotesKey(event: KeyboardEvent<HTMLTextAreaElement>) {
    event.stopPropagation();
  }

  const sourceById = new Map((result?.sources || []).map((source) => [source.chunk_id, source]));

  return (
    <div className="shell compare">
      <aside className="rail">
        <input
          className="search"
          value={query}
          onChange={(event) => setQuery(event.target.value)}
          placeholder="Pesquisar perguntas…"
        />
        <p className="muted">
          {filtered.filter((item) => item.evaluated).length}/{filtered.length} avaliadas
        </p>
        <details ref={drawerRef} className="question-drawer" open>
          <summary>
            Perguntas
            {selectedId ? ` · ${selectedId}` : ""}
          </summary>
          <nav className="qlist">
            {filtered.map((item) => (
              <button
                type="button"
                key={item.id}
                className={`qitem ${item.id === selectedId ? "active" : ""}`}
                onClick={() => {
                  setSelectedId(item.id);
                  if (drawerRef.current && window.matchMedia("(max-width: 900px)").matches) {
                    drawerRef.current.open = false;
                  }
                }}
              >
                <span>{item.id}</span>
                <small>{item.text}</small>
                <em>{item.evaluated ? "avaliada" : item.has_results ? "com respostas" : "sem run"}</em>
              </button>
            ))}
          </nav>
        </details>
      </aside>

      <main className="stage compare-stage">
        {error && <div className="banner">{error}</div>}
        {!result ? (
          <p className="muted">A carregar…</p>
        ) : (
          <>
            <header className="compare-head">
              <div>
                <p className="muted">
                  {result.case_id}
                  {result.expected_behavior ? ` · ${result.expected_behavior}` : ""}
                  {" · "}
                  Chunks recuperados: {dash(result.chunk_count)}
                </p>
                <h1>{result.question}</h1>
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
                {allowGeneration ? (
                  <button type="button" className="ghost" onClick={() => void rerun()} disabled={busy}>
                    {busy ? "A gerar…" : "Gerar os dois modelos"}
                  </button>
                ) : null}
                <a className="ghost" href={`${API_URL}/evaluations/report.txt`}>
                  Descarregar relatório
                </a>
              </div>
            </header>

            {result.reference_answer ? (
              <details className="panel">
                <summary>Resposta de referência</summary>
                <div className="markdown">
                  <Markdown>{result.reference_answer}</Markdown>
                </div>
              </details>
            ) : (
              <p className="muted">Resposta de referência: —</p>
            )}

            <p className="summary-line">
              {buildSummary({
                xaiLatencyS: xaiSeconds,
                geminiLatencyS: geminiSeconds,
                xaiTokens: xai?.usage?.total_tokens ?? null,
                geminiTokens: gemini?.usage?.total_tokens ?? null,
                xaiCitations: xaiCitations.length,
                geminiCitations: geminiCitations.length,
              })}
            </p>

            <section className="columns">
              {(["xai", "gemini"] as const).map((name) => {
                const row = name === "xai" ? xai : gemini;
                return (
                  <article key={name} className="column">
                    <header className="column-head">
                      <h2>{name === "xai" ? "xAI" : "Gemini"}</h2>
                      <MetricLine items={metricItems(name)} />
                      <div className="tags">
                        {row?.is_refusal ? <span className="tag warn">recusa</span> : null}
                        {row?.scratchpad_leaked ? <span className="tag warn">scratchpad visível</span> : null}
                        {row?.error ? <span className="tag fail">erro</span> : null}
                      </div>
                    </header>
                    {row?.error ? (
                      <p className="fail">{row.error}</p>
                    ) : row?.visible_text ? (
                      <div className="markdown">
                        <Markdown>{row.visible_text}</Markdown>
                      </div>
                    ) : (
                      <p className="muted">Não há resposta neste JSON de execução.</p>
                    )}
                  </article>
                );
              })}
            </section>

            <details className="sources panel">
              <summary>Contexto recuperado ({dash(result.chunk_count)})</summary>
              <ul>
                {result.chunk_ids.map((chunkId, offset) => {
                  const index = offset + 1;
                  const source = sourceById.get(chunkId);
                  return (
                    <li key={`${chunkId}-${index}`}>
                      <strong>
                        [{index}] {chunkId}
                      </strong>
                      <span className="cite-flag">{citedBy(index, xaiCitations, geminiCitations)}</span>
                      {source ? (
                        <>
                          <span>
                            {source.document}
                            {source.page ? ` · p. ${source.page}` : ""}
                          </span>
                          <em>{source.excerpt}</em>
                        </>
                      ) : null}
                    </li>
                  );
                })}
              </ul>
            </details>

            <section className="panel judge">
              <h2>A sua avaliação</h2>
              <p className="muted">Escreva o que observa nesta pergunta. As notas entram no relatório de texto.</p>
              <div className="verdicts">
                {VERDICTS.map((item) => (
                  <button
                    type="button"
                    key={item.id}
                    className={verdict === item.id ? "ghost active" : "ghost"}
                    disabled={busy}
                    onClick={() => void save(item.id)}
                  >
                    {item.label}
                  </button>
                ))}
              </div>
              <textarea
                value={notes}
                onChange={(event) => setNotes(event.target.value)}
                onKeyDown={onNotesKey}
                placeholder="Notas da avaliação (obrigatório se não escolher veredicto)"
                rows={4}
              />
              <div className="nav-row">
                <button type="button" className="ghost" disabled={busy || !notes.trim()} onClick={() => void save()}>
                  {busy ? "A gravar…" : "Guardar notas"}
                </button>
                <a className="ghost" href={`${API_URL}/evaluations/report.txt`}>
                  Descarregar relatório .txt
                </a>
              </div>
              <p className="hint">Setas esquerda/direita mudam de pergunta. O veredicto grava já as notas escritas.</p>
            </section>
          </>
        )}
      </main>
    </div>
  );
}
