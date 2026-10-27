import { useEffect, useState } from "react";
import { API_URL, api } from "./api";
import { compareMetric, formatPt } from "./metrics";

type Card = {
  id: string;
  label: string;
  n: number | { gemini?: number; xai?: number } | null;
  gemini: number | null;
  xai: number | null;
  delta: number | null;
  config: Record<string, unknown>;
  source_file: string | null;
  run_file: string | null;
  method: string | null;
  summary_kind: string;
  color_policy: string;
};

type Challenge = { id: string; label: string; text: string };

type DashboardData = {
  models: Record<string, string>;
  config: Record<string, unknown>;
  source_file: string | null;
  run_file: string | null;
  pass_threshold: number | null;
  cards: Card[];
  note: string;
  n_cases?: number;
  n_answer?: number;
  n_refuse?: number;
  challenges?: Challenge[];
};

type Summary = {
  distinct_raters: number;
  n_ratings: number;
  cases_covered: number;
  cases_total: number;
};

function fmt(value: number | null) {
  return value == null ? "—" : formatPt(value, value >= 1 ? 2 : 3);
}

function nLabel(n: Card["n"]) {
  if (n == null) return "n = —";
  if (typeof n === "number") return `n = ${n}`;
  return `n Gemini ${n.gemini ?? "—"} · n xAI ${n.xai ?? "—"}`;
}

export default function Dashboard() {
  const [data, setData] = useState<DashboardData | null>(null);
  const [summary, setSummary] = useState<Summary | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api<DashboardData>("/dashboard")
      .then(setData)
      .catch((err: Error) => setError(err.message));
    api<Summary>("/human/summary")
      .then(setSummary)
      .catch(() => setSummary(null));
  }, []);

  if (error) return <p className="fail">{error}</p>;
  if (!data) return <p className="muted">A carregar indicadores…</p>;

  return (
    <section className="dashboard">
      <header>
        <h1>Indicadores automáticos</h1>
        <p className="muted">
          Modelos: xAI {data.models.xai || "—"} · Gemini {data.models.gemini || "—"}
        </p>
        <p className="muted">
          Configuração: {JSON.stringify(data.config)} · limiar pass {data.pass_threshold ?? "—"} · n casos{" "}
          {data.n_cases ?? "—"} ({data.n_answer ?? "—"} resposta / {data.n_refuse ?? "—"} recusa)
        </p>
        <p className="muted">{data.note}</p>
      </header>
      <div className="cards">
        {data.cards.map((card) => {
          const cmp = compareMetric(card.xai, card.gemini);
          return (
            <article key={card.id} className="metric-card">
              <h2>{card.label}</h2>
              <p className="n-line">{nLabel(card.n)}</p>
              <p>
                <span className={`chip ${cmp.a}`}>xAI {fmt(card.xai)}</span>
                <span className="metric-sep">·</span>
                <span className={`chip ${cmp.b}`}>Gemini {fmt(card.gemini)}</span>
              </p>
              <p className="muted">Δ (xAI − Gemini): {card.delta == null ? "—" : formatPt(card.delta, 3)}</p>
              <details>
                <summary>Detalhe técnico</summary>
                <p>{card.method || "—"}</p>
                <p>Fonte: {card.source_file || "—"} ({card.summary_kind})</p>
                <p>Run: {card.run_file || "—"}</p>
                <p>Cor: {card.color_policy}</p>
              </details>
            </article>
          );
        })}
      </div>
      <section className="panel summary-panel">
        <h2>Quadro resumo da avaliação humana</h2>
        <p>
          {summary
            ? `${summary.distinct_raters} utilizadores distintos · ${summary.n_ratings} avaliações · cobertura ${summary.cases_covered}/${summary.cases_total} casos`
            : "Ainda sem avaliações humanas."}
        </p>
        <div className="nav-row">
          <a className="ghost" href={`${API_URL}/human/export.csv`}>
            Descarregar CSV
          </a>
          <a className="ghost" href={`${API_URL}/human/export.json`}>
            Descarregar JSON
          </a>
        </div>
        <p className="muted">A descarga pública usa um identificador, não o nome declarado. Os nomes ficam só no Firestore.</p>
      </section>
      {data.challenges?.length ? (
        <section className="panel">
          <h2>Notas dos desafios da equipa</h2>
          <ul>
            {data.challenges.map((item) => (
              <li key={item.id}>
                <strong>{item.id} {item.label}.</strong> {item.text}
              </li>
            ))}
          </ul>
        </section>
      ) : null}
    </section>
  );
}
