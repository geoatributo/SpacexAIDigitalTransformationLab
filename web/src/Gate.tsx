import { FormEvent, useState } from "react";
import { api } from "./api";
import { saveSession, type Session } from "./session";

type Props = { onEnter: (session: Session) => void };

export default function Gate({ onEnter }: Props) {
  const [name, setName] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function enter(mode: Session["mode"]) {
    setBusy(true);
    setError(null);
    try {
      const session = await api<Session>("/session", {
        method: "POST",
        body: JSON.stringify({ name, mode }),
      });
      saveSession(session);
      onEnter(session);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Não foi possível iniciar a sessão.");
    } finally {
      setBusy(false);
    }
  }

  function onSubmit(event: FormEvent) {
    event.preventDefault();
    void enter("rate");
  }

  return (
    <main className="gate">
      <h1>Goldilocks RAG</h1>
      <p className="muted">Sistema de experimentação e teste — uso autorizado durante o Evento.</p>
      <section className="panel terms">
        <h2>Termo de utilização (rascunho)</h2>
        <ol>
          <li>Este site mostra resultados já gerados no Lab (JSON da run). Não faz perguntas novas nem chama Gemini ou Grok.</li>
          <li>Ao avaliar, declara o seu nome. O nome e as notas 0–10 ficam no Firestore do projeto Google Cloud, não no Git.</li>
          <li>Pode só ver as respostas já gravadas, sem avaliar e sem ser contado como respondente.</li>
          <li>Na avaliação humana as duas respostas aparecem às cegas (A e B), sem identificar o sistema.</li>
          <li>Os resultados são indicativos, de uma amostra pequena.</li>
        </ol>
      </section>
      <form className="panel" onSubmit={onSubmit}>
        <label>
          Nome declarado
          <input value={name} onChange={(event) => setName(event.target.value)} placeholder="O seu nome" />
        </label>
        {error && <p className="fail">{error}</p>}
        <div className="nav-row">
          <button type="submit" className="ghost" disabled={busy}>
            Aceitar e avaliar
          </button>
          <button type="button" className="ghost" disabled={busy} onClick={() => void enter("metrics_only")}>
            Só ver as respostas
          </button>
        </div>
      </form>
    </main>
  );
}
