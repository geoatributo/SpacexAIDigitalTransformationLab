import { PointerEvent as ReactPointerEvent, useEffect, useMemo, useRef, useState } from "react";
import { api } from "./api";
import { formatPt } from "./metrics";

type RunSummary = {
  id: string;
  created_at: string;
  config_count: number;
};

type MetricRow = {
  correctness: number | null;
  grounded_rate: number | null;
  completeness: number | null;
  n?: number;
};

type ConfigReport = {
  name: string;
  label: string;
  title: string;
  n: number;
  metrics: Record<string, MetricRow>;
  delta: Record<string, number | null>;
  cost: Record<string, { median_s: number; mean_tokens: number }>;
};

type Report = {
  id: string;
  created_at: string;
  sampling_note: string;
  models: Record<string, string>;
  configs: ConfigReport[];
  cases: string[];
  disagreement: {
    pass: (number | null)[][];
    refusal: (number | null)[][];
  };
};

const METRICS = ["correctness", "grounded_rate", "completeness"] as const;
const PROVIDER_ORDER = ["gemini", "xai"];
const SERIES_COLORS = ["#3b6ea5", "#c47b2b", "#2f6f4e", "#6b4c9a"];
const HEAT_COLORS = ["#d9d9d9", "#3b6ea5", "#c47b2b", "#7a2e2e"];
const PASS_LABELS = ["ambos passam", "só Gemini passa", "só Grok passa", "ambos falham"];
const REFUSAL_LABELS = ["ambos respondem", "só Gemini recusa", "só Grok recusa", "ambos recusam"];

type Series = {
  id: string;
  label: string;
  color: string;
  values: (number | null)[];
};

function providersOf(report: Report): string[] {
  const names = new Set<string>();
  for (const config of report.configs) {
    for (const name of Object.keys(config.metrics)) names.add(name);
  }
  const ordered = PROVIDER_ORDER.filter((name) => names.has(name));
  for (const name of names) {
    if (!ordered.includes(name)) ordered.push(name);
  }
  return ordered;
}

function modelName(report: Report, provider: string): string {
  return report.models[provider] || provider;
}

function meanAcrossModels(config: ConfigReport, metric: (typeof METRICS)[number]): number | null {
  const values = Object.values(config.metrics)
    .map((row) => row?.[metric])
    .filter((value): value is number => value != null && !Number.isNaN(value));
  if (!values.length) return null;
  return values.reduce((sum, value) => sum + value, 0) / values.length;
}

function meanMetric(configs: ConfigReport[], provider: string, metric: (typeof METRICS)[number]): number | null {
  let weight = 0;
  let total = 0;
  for (const config of configs) {
    const row = config.metrics[provider];
    const value = row?.[metric];
    if (value == null || Number.isNaN(value)) continue;
    const n = row?.n || config.n || 1;
    total += value * n;
    weight += n;
  }
  return weight ? total / weight : null;
}

function meanCostAcrossModels(config: ConfigReport, field: "median_s" | "mean_tokens"): number | null {
  const values = Object.values(config.cost)
    .map((row) => row?.[field])
    .filter((value): value is number => value != null && !Number.isNaN(value));
  if (!values.length) return null;
  return values.reduce((sum, value) => sum + value, 0) / values.length;
}

function meanCost(configs: ConfigReport[], provider: string, field: "median_s" | "mean_tokens"): number | null {
  let weight = 0;
  let total = 0;
  for (const config of configs) {
    const value = config.cost[provider]?.[field];
    if (value == null || Number.isNaN(value)) continue;
    const n = config.metrics[provider]?.n || config.n || 1;
    total += value * n;
    weight += n;
  }
  return weight ? total / weight : null;
}

function bestOf(values: (number | null)[]): number | null {
  const finite = values.filter((value): value is number => value != null && !Number.isNaN(value));
  return finite.length ? Math.max(...finite) : null;
}

function isBest(value: number | null, best: number | null): boolean {
  return value != null && best != null && Math.abs(value - best) < 1e-9;
}

function score(value: number | null | undefined, digits = 2): string {
  if (value == null || Number.isNaN(value)) return "—";
  return formatPt(value, digits);
}

function signed(value: number | null | undefined): string {
  if (value == null || Number.isNaN(value)) return "—";
  const text = formatPt(Math.abs(value), 2);
  if (value > 0) return `+${text}`;
  if (value < 0) return `−${text}`;
  return text;
}

function placeTip(tip: HTMLDivElement, clientX: number, clientY: number, text: string) {
  tip.hidden = false;
  if (tip.textContent !== text) tip.textContent = text;
  const nearRight = clientX > window.innerWidth * 0.72;
  const nearTop = clientY < 48;
  tip.style.transform = `${nearRight ? "translateX(-100%)" : "translateX(12px)"} ${nearTop ? "translateY(14px)" : "translateY(-130%)"}`;
  tip.style.left = `${clientX}px`;
  tip.style.top = `${clientY}px`;
}

function localPoint(svg: SVGSVGElement, event: { clientX: number; clientY: number }) {
  const matrix = svg.getScreenCTM();
  if (!matrix) return null;
  return new DOMPoint(event.clientX, event.clientY).matrixTransform(matrix.inverse());
}

function useBoxWidth() {
  const ref = useRef<HTMLDivElement>(null);
  const [width, setWidth] = useState(0);
  useEffect(() => {
    const node = ref.current;
    if (!node) return;
    const update = () => setWidth(Math.floor(node.clientWidth));
    update();
    const observer = new ResizeObserver(update);
    observer.observe(node);
    return () => observer.disconnect();
  }, []);
  return [ref, width] as const;
}

function GroupedBars({
  categories,
  series,
  yMin,
  yMax,
  signedAxis = false,
  compact = false,
  fill = false,
  showLegend = true,
  seriesLabels = false,
}: {
  categories: string[];
  series: Series[];
  yMin: number;
  yMax: number;
  signedAxis?: boolean;
  compact?: boolean;
  fill?: boolean;
  showLegend?: boolean;
  seriesLabels?: boolean;
}) {
  const [hostRef, boxWidth] = useBoxWidth();
  const tipRef = useRef<HTMLDivElement>(null);
  const hotRef = useRef("");
  const natural = Math.max(compact ? 220 : 480, categories.length * (compact ? 48 : 72));
  const width = fill && boxWidth > 40 ? boxWidth : natural;
  const height = seriesLabels ? 334 : compact ? 196 : 340;
  const pad = seriesLabels
    ? { l: 92, r: 16, t: 16, b: 112 }
    : compact
      ? { l: 36, r: 6, t: 8, b: 72 }
      : { l: 52, r: 16, t: 16, b: 118 };
  const innerW = width - pad.l - pad.r;
  const innerH = height - pad.t - pad.b;
  const span = yMax - yMin || 1;
  const yOf = (value: number) => pad.t + ((yMax - value) / span) * innerH;
  const groupW = categories.length ? innerW / categories.length : innerW;
  const barW = (groupW * 0.72) / Math.max(series.length, 1);
  const unit = !signedAxis && yMax <= 1 && yMin >= 0;
  const ticks = unit
    ? [0, 0.25, 0.5, 0.75, 1]
    : [0, 1, 2, 3, 4].map((step) => yMin + ((yMax - yMin) * step) / 4);

  const hitAt = (x: number) => {
    if (!categories.length || !series.length || x < pad.l || x > width - pad.r) return null;
    const index = Math.min(categories.length - 1, Math.max(0, Math.floor((x - pad.l) / groupW)));
    const groupX = pad.l + index * groupW;
    const cluster = series.length * barW;
    const start = groupX + (groupW - cluster) / 2;
    const seriesIndex = Math.min(series.length - 1, Math.max(0, Math.floor((x - start) / barW)));
    return { index, seriesIndex };
  };

  const clearHot = (svg: SVGSVGElement | null) => {
    hotRef.current = "";
    svg?.querySelectorAll(".chart-label.hot").forEach((node) => node.classList.remove("hot"));
  };

  const follow = (event: ReactPointerEvent<SVGSVGElement>) => {
    const tip = tipRef.current;
    const point = localPoint(event.currentTarget, event);
    if (!tip || !point) return;
    const hit = hitAt(point.x);
    if (!hit) {
      tip.hidden = true;
      clearHot(event.currentTarget);
      return;
    }
    const labelKey = seriesLabels ? `${hit.index}-${hit.seriesIndex}` : String(hit.index);
    if (hotRef.current !== labelKey) {
      hotRef.current = labelKey;
      event.currentTarget.querySelectorAll(".chart-label.hot").forEach((node) => node.classList.remove("hot"));
      event.currentTarget.querySelector(`[data-label="${hit.index}"]`)?.classList.add("hot");
      if (seriesLabels) event.currentTarget.querySelector(`[data-series="${labelKey}"]`)?.classList.add("hot");
    }
    const item = series[hit.seriesIndex];
    const valueText = signedAxis ? signed(item.values[hit.index]) : score(item.values[hit.index]);
    const text = series.length > 1 ? `${item.label}: ${valueText}` : valueText;
    placeTip(tip, event.clientX, event.clientY, text);
  };

  return (
    <div className="chart-scroll" ref={hostRef}>
      <svg
        viewBox={`0 0 ${width} ${height}`}
        width={fill ? "100%" : width}
        height={height}
        className={compact ? "chart-svg compact" : "chart-svg"}
        role="img"
        onPointerMove={follow}
        onPointerLeave={(event) => {
          if (tipRef.current) tipRef.current.hidden = true;
          clearHot(event.currentTarget);
        }}
      >
        {ticks.map((tick) => (
          <g key={tick} className="chart-ink">
            <line x1={pad.l} x2={width - pad.r} y1={yOf(tick)} y2={yOf(tick)} className="chart-grid" />
            <text x={pad.l - 8} y={yOf(tick) + 4} className="chart-tick" textAnchor="end">
              {Math.abs(yMax) >= 20 ? formatPt(tick, 0) : score(tick, Math.abs(tick) >= 10 ? 1 : 2)}
            </text>
          </g>
        ))}
        {signedAxis && yMin <= 0 && yMax >= 0 ? (
          <line x1={pad.l} x2={width - pad.r} y1={yOf(0)} y2={yOf(0)} className="chart-zero" />
        ) : null}
        {categories.map((category, index) => {
          const groupX = pad.l + index * groupW;
          const base = yOf(Math.min(Math.max(0, yMin), yMax));
          const clusterX = groupX + (groupW - series.length * barW) / 2;
          const axisY = pad.t + innerH;
          const labelY = axisY + (seriesLabels ? 98 : compact ? 14 : 18);
          return (
            <g key={category}>
              {series.map((item, seriesIndex) => {
                const value = item.values[index];
                if (value == null) return null;
                const y = yOf(value);
                const top = Math.min(y, base);
                const barH = Math.max(Math.abs(y - base), 1);
                const x = clusterX + seriesIndex * barW;
                return (
                  <rect
                    key={item.id}
                    x={x}
                    y={top}
                    width={Math.max(barW - 3, 2)}
                    height={barH}
                    fill={item.color}
                    rx={3}
                    className="chart-bar"
                  />
                );
              })}
              {seriesLabels
                ? series.map((item, seriesIndex) => {
                    const x = clusterX + seriesIndex * barW + Math.max(barW - 3, 2) / 2;
                    const y = axisY + 12;
                    return (
                      <text
                        key={item.id}
                        data-series={`${index}-${seriesIndex}`}
                        x={x}
                        y={y}
                        className="chart-label chart-series-label"
                        textAnchor="end"
                        fill={item.color}
                        transform={`rotate(-45 ${x} ${y})`}
                      >
                        {item.label}
                      </text>
                    );
                  })
                : null}
              {seriesLabels && series.length > 1 ? (
                <line
                  x1={clusterX + barW / 2}
                  x2={clusterX + (series.length - 0.5) * barW}
                  y1={axisY + 82}
                  y2={axisY + 82}
                  className="chart-grid"
                />
              ) : null}
              <text
                data-label={index}
                x={groupX + groupW / 2}
                y={labelY}
                className="chart-label"
                textAnchor={seriesLabels ? "middle" : "end"}
                transform={seriesLabels ? undefined : `rotate(-32 ${groupX + groupW / 2} ${labelY})`}
              >
                {category}
              </text>
            </g>
          );
        })}
      </svg>
      <div className="chart-tip" ref={tipRef} hidden />
      {showLegend && !seriesLabels ? (
        <div className="chart-legend">
          {series.map((item) => (
            <span key={item.id}>
              <i style={{ background: item.color }} />
              {item.label}
            </span>
          ))}
        </div>
      ) : null}
    </div>
  );
}

function Heatmap({
  title,
  labels,
  configs,
  cases,
  rows,
}: {
  title: string;
  labels: string[];
  configs: ConfigReport[];
  cases: string[];
  rows: (number | null)[][];
}) {
  const [hostRef, boxWidth] = useBoxWidth();
  const tipRef = useRef<HTMLDivElement>(null);
  const hotRef = useRef("");
  const labelW = 148;
  const tail = 4;
  const count = Math.max(cases.length, 1);
  const width = boxWidth > labelW + tail ? boxWidth : labelW + count * 12 + tail;
  const pitch = (width - labelW - tail) / count;
  const gap = Math.min(3, pitch * 0.2);
  const cellW = Math.max(1, pitch - gap);
  const cellH = Math.max(cellW, 12);
  const slotX = cellW + gap;
  const slotY = cellH + gap;
  const axis = 4 + configs.length * slotY;
  const height = axis + 54;

  const hitAt = (x: number, y: number) => {
    const row = Math.floor((y - 4) / slotY);
    const column = Math.floor((x - labelW) / slotX);
    if (row < 0 || column < 0 || row >= configs.length || column >= cases.length) return null;
    return { row, column };
  };

  const follow = (event: ReactPointerEvent<SVGSVGElement>) => {
    const tip = tipRef.current;
    const point = localPoint(event.currentTarget, event);
    if (!tip || !point) return;
    const hit = hitAt(point.x, point.y);
    if (!hit) {
      tip.hidden = true;
      hotRef.current = "";
      event.currentTarget.querySelector(".chart-label.hot")?.classList.remove("hot");
      return;
    }
    const labelKey = String(hit.column);
    if (hotRef.current !== labelKey) {
      hotRef.current = labelKey;
      event.currentTarget.querySelector(".chart-label.hot")?.classList.remove("hot");
      event.currentTarget.querySelector(`[data-xlabel="${labelKey}"]`)?.classList.add("hot");
    }
    const code = rows[hit.row]?.[hit.column];
    placeTip(tip, event.clientX, event.clientY, code == null ? "sem dados" : labels[code] || "sem dados");
  };

  return (
    <section className="panel metrics-wide">
      <h2>{title}</h2>
      <div className="chart-scroll chart-fit" ref={hostRef}>
        <svg
          viewBox={`0 0 ${width} ${height}`}
          width="100%"
          height={height}
          className="chart-svg"
          role="img"
          onPointerMove={follow}
          onPointerLeave={(event) => {
            if (tipRef.current) tipRef.current.hidden = true;
            hotRef.current = "";
            event.currentTarget.querySelector(".chart-label.hot")?.classList.remove("hot");
          }}
        >
          {configs.map((config, rowIndex) => {
            const y = 4 + rowIndex * slotY;
            return (
              <g key={config.name}>
                <text
                  x={labelW - 8}
                  y={y + cellH * 0.72}
                  className="chart-label"
                  textAnchor="end"
                >
                  {config.label}
                </text>
                {(rows[rowIndex] || []).map((code, column) => (
                  <rect
                    key={cases[column] || column}
                    data-cell={`${rowIndex}:${column}`}
                    x={labelW + column * slotX}
                    y={y}
                    width={cellW}
                    height={cellH}
                    rx={Math.min(3, cellW / 2)}
                    fill={code == null ? "#2a2a2a" : HEAT_COLORS[code] || "#2a2a2a"}
                    className="chart-cell"
                  />
                ))}
              </g>
            );
          })}
          {cases.map((caseId, column) => {
            const x = labelW + column * slotX + cellW / 2;
            const y = axis + 12;
            return (
              <text
                key={caseId}
                data-xlabel={column}
                x={x}
                y={y}
                className="chart-label"
                textAnchor="end"
                transform={`rotate(-55 ${x} ${y})`}
              >
                {caseId}
              </text>
            );
          })}
        </svg>
        <div className="chart-tip" ref={tipRef} hidden />
      </div>
      <div className="chart-legend">
        {labels.map((label, index) => (
          <span key={label}>
            <i style={{ background: HEAT_COLORS[index] }} />
            {label}
          </span>
        ))}
      </div>
    </section>
  );
}

export default function Plots() {
  const [runs, setRuns] = useState<RunSummary[]>([]);
  const [runId, setRunId] = useState("");
  const [report, setReport] = useState<Report | null>(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  const [showInfo, setShowInfo] = useState(false);

  useEffect(() => {
    let active = true;
    api<RunSummary[]>("/metrics/runs")
      .then((rows) => {
        if (!active) return;
        setRuns(rows);
        setRunId("");
        setLoading(false);
      })
      .catch((exc: Error) => {
        if (!active) return;
        setError(exc.message);
        setLoading(false);
      });
    return () => {
      active = false;
    };
  }, []);

  useEffect(() => {
    if (!runId) return;
    let active = true;
    setError("");
    api<Report>(`/metrics/runs/${encodeURIComponent(runId)}`)
      .then((payload) => {
        if (!active) return;
        setReport(payload);
      })
      .catch((exc: Error) => {
        if (!active) return;
        setReport(null);
        setError(exc.message);
      });
    return () => {
      active = false;
    };
  }, [runId]);

  const providers = useMemo(() => (report ? providersOf(report) : []), [report]);
  const deltaValues = report
    ? report.configs.flatMap((item) =>
        METRICS.map((metric) => item.delta[metric]).filter((value): value is number => value != null && !Number.isNaN(value)),
      )
    : [];
  const deltaMin = deltaValues.length ? Math.min(...deltaValues) : 0;
  const deltaMax = deltaValues.length ? Math.max(...deltaValues) : 0;
  const deltaExtent = Math.max(Math.abs(deltaMin), Math.abs(deltaMax), 0.01) * 1.12;
  const modelScores = report
    ? providers.map((provider) => METRICS.map((metric) => meanMetric(report.configs, provider, metric)))
    : [];
  const configScores = report
    ? report.configs.map((config) => METRICS.map((metric) => meanAcrossModels(config, metric)))
    : [];
  const modelBest = METRICS.map((_, index) => bestOf(modelScores.map((row) => row[index])));
  const configBest = METRICS.map((_, index) => bestOf(configScores.map((row) => row[index])));

  const providerSeries = (pick: (row: ConfigReport, provider: string) => number | null): Series[] =>
    providers.map((provider, index) => ({
      id: provider,
      label: report ? modelName(report, provider) : provider,
      color: SERIES_COLORS[index % SERIES_COLORS.length],
      values: report ? report.configs.map((row) => pick(row, provider)) : [],
    }));

  return (
    <div className="metrics-page">
      <div className="metrics-toolbar">
        <label className="provider">
          Corrida
          <select value={runId} onChange={(event) => setRunId(event.target.value)} disabled={!runs.length}>
            <option value="">{runs.length ? "Escolher uma corrida…" : "Nenhuma corrida"}</option>
            {runs.map((run) => (
              <option key={run.id} value={run.id}>
                {run.id} · {run.config_count} configs
              </option>
            ))}
          </select>
        </label>
        {report?.sampling_note ? <span className="muted">{report.sampling_note}</span> : null}
        <button
          type="button"
          className={showInfo ? "ghost active" : "ghost"}
          aria-expanded={showInfo}
          onClick={() => setShowInfo((open) => !open)}
        >
          Informação
        </button>
      </div>
      {showInfo ? (
        <section className="panel metrics-wide metrics-info">
          <h2>O que medem</h2>
          <p className="muted">
            Cada pergunta recebe uma nota de 0 a 1 por comparação lexical com a resposta de referência e com os chunks dados. As tabelas e os gráficos mostram a média dessas notas.
          </p>
          <dl>
            <div>
              <dt>correctness</dt>
              <dd>
                Proximidade à referência: 60% é a fração dos números da referência que aparecem na resposta, 40% é a completeness. Afirmações a mais não baixam esta nota.
              </dd>
            </div>
            <div>
              <dt>completeness</dt>
              <dd>
                Fração das frases da referência cobertas pela resposta. Uma frase conta se os seus números estão na resposta e pelo menos metade das palavras de conteúdo também. Exemplos entre parênteses na referência são opcionais.
              </dd>
            </div>
            <div>
              <dt>grounded_rate</dt>
              <dd>
                Fração das frases da resposta sustentadas pelos chunks. Uma frase conta se os seus números e palavras de conteúdo aparecem nesse contexto.
              </dd>
            </div>
          </dl>
          <p className="muted">
            Se a pergunta pede recusa e o modelo recusa, as três notas ficam a 1. Se recusa quando devia responder, correctness e completeness ficam a 0 e grounded_rate fica a 1.
          </p>
        </section>
      ) : null}

      {loading ? <p className="muted">A carregar…</p> : null}
      {error ? <p className="muted">{error}</p> : null}
      {!loading && !error && !runs.length ? <p className="muted">Nenhuma corrida com métricas.</p> : null}
      {!loading && !error && runs.length && !runId ? (
        <p className="muted">Escolha uma corrida no seletor para carregar o JSON das métricas.</p>
      ) : null}

      {report ? (
        <>
          <section className="panel metrics-wide metrics-summary">
            <div>
              <h2>Média por modelo</h2>
              <table className="metrics-table">
                <thead>
                  <tr>
                    <th>Modelo</th>
                    {METRICS.map((metric) => (
                      <th key={metric}>{metric}</th>
                    ))}
                    <th>latência (s)</th>
                    <th>tokens</th>
                  </tr>
                </thead>
                <tbody>
                  {providers.map((provider, index) => (
                    <tr key={provider}>
                      <td>
                        <span className="metrics-model">
                          <i style={{ background: SERIES_COLORS[index % SERIES_COLORS.length] }} />
                          {modelName(report, provider)}
                        </span>
                      </td>
                      {METRICS.map((metric, metricIndex) => {
                        const value = modelScores[index][metricIndex];
                        const top = isBest(value, modelBest[metricIndex]);
                        return (
                          <td key={metric} className={top ? "metrics-best" : undefined}>
                            {score(value)}
                            {top ? <span className="metrics-mark">▲</span> : null}
                          </td>
                        );
                      })}
                      <td>{score(meanCost(report.configs, provider, "median_s"))}</td>
                      <td>{score(meanCost(report.configs, provider, "mean_tokens"), 0)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <div>
              <h2>Média por config</h2>
              <table className="metrics-table">
                <thead>
                  <tr>
                    <th>Config</th>
                    {METRICS.map((metric) => (
                      <th key={metric}>{metric}</th>
                    ))}
                    <th>latência (s)</th>
                    <th>tokens</th>
                  </tr>
                </thead>
                <tbody>
                  {report.configs.map((config, index) => (
                    <tr key={config.name}>
                      <td title={config.title}>{config.label}</td>
                      {METRICS.map((metric, metricIndex) => {
                        const value = configScores[index][metricIndex];
                        const top = isBest(value, configBest[metricIndex]);
                        return (
                          <td key={metric} className={top ? "metrics-best" : undefined}>
                            {score(value)}
                            {top ? <span className="metrics-mark">▲</span> : null}
                          </td>
                        );
                      })}
                      <td>{score(meanCostAcrossModels(config, "median_s"))}</td>
                      <td>{score(meanCostAcrossModels(config, "mean_tokens"), 0)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>

          <section className="panel metrics-wide metrics-scores">
            <div className="metrics-trio">
              {METRICS.map((metric) => (
                <div key={metric}>
                  <h2>{metric}</h2>
                  <GroupedBars
                    fill
                    compact
                    showLegend={false}
                    categories={report.configs.map((item) => item.label)}
                    series={providerSeries((row, provider) => row.metrics[provider]?.[metric] ?? null)}
                    yMin={0}
                    yMax={1}
                  />
                </div>
              ))}
            </div>
            <div className="chart-legend">
              {providers.map((provider, index) => (
                <span key={provider}>
                  <i style={{ background: SERIES_COLORS[index % SERIES_COLORS.length] }} />
                  {modelName(report, provider)}
                </span>
              ))}
            </div>
          </section>

          <section className="panel metrics-wide">
            <h2>
              Diferença · {modelName(report, "xai")} − {modelName(report, "gemini")}
            </h2>
            <GroupedBars
              fill
              categories={report.configs.map((item) => item.label)}
              series={METRICS.map((metric, index) => ({
                id: metric,
                label: metric,
                color: SERIES_COLORS[index % SERIES_COLORS.length],
                values: report.configs.map((item) => item.delta[metric] ?? null),
              }))}
              yMin={-deltaExtent}
              yMax={deltaExtent}
              signedAxis
              seriesLabels
            />
          </section>

          <div className="metrics-pair">
            <section className="panel">
              <h2>Latência mediana (s)</h2>
              <GroupedBars
                fill
                categories={report.configs.map((item) => item.label)}
                series={providerSeries((row, provider) => row.cost[provider]?.median_s ?? null)}
                yMin={0}
                yMax={Math.max(1, ...report.configs.flatMap((row) => providers.map((provider) => row.cost[provider]?.median_s || 0))) * 1.15}
              />
            </section>
            <section className="panel">
              <h2>Tokens médios</h2>
              <GroupedBars
                fill
                categories={report.configs.map((item) => item.label)}
                series={providerSeries((row, provider) => row.cost[provider]?.mean_tokens ?? null)}
                yMin={0}
                yMax={Math.max(1, ...report.configs.flatMap((row) => providers.map((provider) => row.cost[provider]?.mean_tokens || 0))) * 1.15}
              />
            </section>
          </div>

          <Heatmap
            title="Pass / fail por pergunta"
            labels={PASS_LABELS}
            configs={report.configs}
            cases={report.cases}
            rows={report.disagreement.pass}
          />
          <Heatmap
            title="Recusas por pergunta"
            labels={REFUSAL_LABELS}
            configs={report.configs}
            cases={report.cases}
            rows={report.disagreement.refusal}
          />
        </>
      ) : null}
    </div>
  );
}
