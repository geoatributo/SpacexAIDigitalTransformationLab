import { ChangeEvent, FormEvent, useRef, useState } from "react";
import { api } from "./api";
import { saveSession, type Session } from "./session";

type Props = { onEnter: (session: Session) => void };
type Step = "start" | "session";

export default function Gate({ onEnter }: Props) {
  const [step, setStep] = useState<Step>("start");
  const [name, setName] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [demoNote, setDemoNote] = useState<string | null>(null);
  const fileRef = useRef<HTMLInputElement>(null);

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

  function onPickFiles(event: ChangeEvent<HTMLInputElement>) {
    const count = event.target.files?.length ?? 0;
    event.target.value = "";
    setDemoNote(
      count
        ? `Demonstração: carregamento não ativo. ${count} ficheiro(s) escolhido(s); nada foi enviado nem analisado.`
        : "Demonstração: carregamento não ativo.",
    );
  }

  if (step === "start") {
    return (
      <main className="gate">
        <h1>Goldilocks RAG</h1>
        <p>
          Avaliar que modelos de linguagem servem melhor os processos internos de uma organização, com os seus
          documentos.
        </p>
        <p className="muted">Sistema de experimentação e teste — uso autorizado durante o Evento.</p>
        <section className="panel">
          <h2>Como começar</h2>
          <p className="muted">Os resultados no servidor já estão gerados. Carregar JSON novos neste ecrã é só visual.</p>
          <div className="nav-row">
            <button type="button" className="ghost" onClick={() => setStep("session")}>
              Analisar os ficheiros já carregados
            </button>
            <button type="button" className="ghost" onClick={() => fileRef.current?.click()}>
              Carregar ficheiros novos
            </button>
          </div>
          <input
            ref={fileRef}
            type="file"
            accept=".json,application/json"
            multiple
            hidden
            onChange={onPickFiles}
          />
          {demoNote ? <p className="fail">{demoNote}</p> : null}
        </section>
      </main>
    );
  }

  return (
    <main className="gate">
      <h1>Goldilocks RAG</h1>
      <p className="muted">Vai usar os JSON já no servidor (data/runs), não um ficheiro que tenha escolhido agora.</p>
      <section className="panel terms">
        <h2>Termo de utilização (rascunho)</h2>
        <ol>
          <li>Este site mostra resultados já gerados no Lab. Não faz perguntas novas nem chama Gemini ou Grok.</li>
          <li>Ao avaliar, declara o seu nome. O nome e as notas 0–10 ficam no Firestore, não no Git.</li>
          <li>Pode só ver métricas e gráficos, sem avaliar e sem ser contado como respondente.</li>
          <li>Na avaliação humana as duas respostas aparecem às cegas (A e B).</li>
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
          <button type="button" className="ghost" onClick={() => setStep("start")}>
            Voltar
          </button>
          <button type="submit" className="ghost" disabled={busy}>
            Aceitar e avaliar
          </button>
          <button type="button" className="ghost" disabled={busy} onClick={() => void enter("metrics_only")}>
            Ver métricas e gráficos
          </button>
        </div>
      </form>
    </main>
  );
}
