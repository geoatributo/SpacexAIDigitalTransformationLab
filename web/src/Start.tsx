import { ChangeEvent, useRef, useState } from "react";
import { apiForm } from "./api";

type Props = {
  onUseExisting: () => void;
  onUploaded: (runId: string) => void;
};

export default function Start({ onUseExisting, onUploaded }: Props) {
  const fileRef = useRef<HTMLInputElement>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function onPick(event: ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0];
    event.target.value = "";
    if (!file) return;
    setBusy(true);
    setError(null);
    const body = new FormData();
    body.append("file", file);
    try {
      const saved = await apiForm<{ id: string }>("/metrics/runs/upload", body);
      onUploaded(saved.id);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Não foi possível carregar o JSON.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <main className="gate">
      <h1>Goldilocks RAG</h1>
      <p>
        Avaliar que modelos de linguagem servem melhor os processos internos de uma organização, com os seus
        documentos.
      </p>
      <p className="muted">Primeiro escolha a origem dos resultados. Sem isto o painel não mostra gráficos novos.</p>
      <section className="panel start-actions">
        <h2>Ficheiros de resultados</h2>
        <p className="muted">JSON de uma corrida (relatório de métricas) ou os ficheiros já no servidor.</p>
        <div className="nav-row">
          <button type="button" className="ghost" disabled={busy} onClick={onUseExisting}>
            Analisar os ficheiros já carregados
          </button>
          <button type="button" className="ghost" disabled={busy} onClick={() => fileRef.current?.click()}>
            {busy ? "A carregar…" : "Carregar documento JSON"}
          </button>
        </div>
        <input ref={fileRef} type="file" accept="application/json,.json" hidden onChange={(event) => void onPick(event)} />
        {error ? <p className="fail">{error}</p> : null}
      </section>
    </main>
  );
}
