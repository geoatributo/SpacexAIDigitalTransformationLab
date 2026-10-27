import { ChangeEvent, useRef, useState } from "react";
import { api, apiForm } from "./api";

type Props = {
  onUseExisting: () => void;
  onMetricsUploaded: (runId: string) => void;
  onQuestionsUploaded: (count: number) => void;
};

export default function Start({ onUseExisting, onMetricsUploaded, onQuestionsUploaded }: Props) {
  const metricsRef = useRef<HTMLInputElement>(null);
  const questionsRef = useRef<HTMLInputElement>(null);
  const [busy, setBusy] = useState<"metrics" | "questions" | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function onPickMetrics(event: ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0];
    event.target.value = "";
    if (!file) return;
    setBusy("metrics");
    setError(null);
    const body = new FormData();
    body.append("file", file);
    try {
      const saved = await apiForm<{ id: string }>("/metrics/runs/upload", body);
      onMetricsUploaded(saved.id);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Não foi possível carregar o relatório.");
    } finally {
      setBusy(null);
    }
  }

  async function onPickQuestions(event: ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0];
    event.target.value = "";
    if (!file) return;
    setBusy("questions");
    setError(null);
    const body = new FormData();
    body.append("file", file);
    try {
      const saved = await apiForm<{ n: number }>("/questions/upload", body);
      onQuestionsUploaded(saved.n);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Não foi possível carregar as perguntas.");
    } finally {
      setBusy(null);
    }
  }

  async function useExisting() {
    setBusy("metrics");
    setError(null);
    try {
      await api("/questions/reset", { method: "POST", body: "{}" });
    } catch {
      /* API antiga sem overlay de perguntas */
    }
    onUseExisting();
  }

  const blocked = busy !== null;

  return (
    <main className="gate">
      <h1>Goldilocks RAG</h1>
      <p>
        Avaliar que modelos de linguagem servem melhor os processos internos de uma organização, com os seus
        documentos.
      </p>
      <p className="muted">
        Escolha a origem dos ficheiros. Pode analisar o que já está no servidor, carregar métricas já avaliadas, ou
        carregar uma nova base de perguntas para o Comparar (sem gerar respostas).
      </p>
      <section className="panel start-actions">
        <h2>Resultados já avaliados</h2>
        <p className="muted">Relatório de métricas (report.json) ou os ficheiros já no servidor.</p>
        <div className="nav-row">
          <button type="button" className="ghost" disabled={blocked} onClick={() => void useExisting()}>
            Analisar os ficheiros já carregados
          </button>
          <button type="button" className="ghost" disabled={blocked} onClick={() => metricsRef.current?.click()}>
            {busy === "metrics" ? "A carregar…" : "Carregar relatório de métricas"}
          </button>
        </div>
        <input
          ref={metricsRef}
          type="file"
          accept="application/json,.json"
          hidden
          onChange={(event) => void onPickMetrics(event)}
        />
      </section>
      <section className="panel start-actions">
        <h2>Nova base de perguntas</h2>
        <p className="muted">
          JSON gold com <code>cases</code> e <code>question</code> em cada caso. Substitui a lista do Comparar nesta
          sessão; não chama os modelos. Serve para validar bases novas, não só métricas já avaliadas.
        </p>
        <div className="nav-row">
          <button type="button" className="ghost" disabled={blocked} onClick={() => questionsRef.current?.click()}>
            {busy === "questions" ? "A carregar…" : "Carregar ficheiro de perguntas"}
          </button>
        </div>
        <input
          ref={questionsRef}
          type="file"
          accept="application/json,.json"
          hidden
          onChange={(event) => void onPickQuestions(event)}
        />
        {error ? <p className="fail">{error}</p> : null}
      </section>
    </main>
  );
}
