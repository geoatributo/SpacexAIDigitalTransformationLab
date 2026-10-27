import { useEffect, useState } from "react";
import BlindEval from "./BlindEval";
import Chat from "./Chat";
import Compare from "./Compare";
import Gate from "./Gate";
import Plots from "./Plots";
import Start from "./Start";
import { api } from "./api";
import { clearSession, loadSession, type Session } from "./session";

type View = "eval" | "compare" | "metrics" | "chat";

export default function App() {
  const [passedStart, setPassedStart] = useState(false);
  const [preferredRunId, setPreferredRunId] = useState("");
  const [session, setSession] = useState<Session | null>(() => loadSession());
  const [allowGeneration, setAllowGeneration] = useState(false);
  const [view, setView] = useState<View>("metrics");

  useEffect(() => {
    api<{ allow_generation?: boolean }>("/health")
      .then((payload) => setAllowGeneration(Boolean(payload.allow_generation)))
      .catch(() => setAllowGeneration(false));
  }, []);

  function enter(next: Session) {
    setSession(next);
    setView(next.mode === "rate" ? "eval" : "metrics");
  }

  if (!passedStart) {
    return (
      <div className="app-root">
        <header className="app-bar">
          <strong>Goldilocks RAG</strong>
        </header>
        <Start
          onUseExisting={() => {
            setPreferredRunId("");
            setPassedStart(true);
          }}
          onUploaded={(runId) => {
            setPreferredRunId(runId);
            setPassedStart(true);
            setView("metrics");
          }}
        />
      </div>
    );
  }

  if (!session) {
    return (
      <div className="app-root">
        <header className="app-bar">
          <strong>Goldilocks RAG</strong>
        </header>
        <Gate onEnter={enter} />
      </div>
    );
  }

  return (
    <div className="app-root">
      <header className="app-bar">
        <strong>Goldilocks RAG</strong>
        <nav>
          {session.mode === "rate" ? (
            <button type="button" className={view === "eval" ? "ghost active" : "ghost"} onClick={() => setView("eval")}>
              Avaliar
            </button>
          ) : null}
          <button type="button" className={view === "metrics" ? "ghost active" : "ghost"} onClick={() => setView("metrics")}>
            Métricas
          </button>
          <button type="button" className={view === "compare" ? "ghost active" : "ghost"} onClick={() => setView("compare")}>
            Comparar
          </button>
          {allowGeneration ? (
            <button type="button" className={view === "chat" ? "ghost active" : "ghost"} onClick={() => setView("chat")}>
              Chat
            </button>
          ) : null}
        </nav>
        <span className="muted">
          {session.mode === "rate" ? session.name : "consulta"}
          <button
            type="button"
            className="ghost"
            onClick={() => {
              clearSession();
              setSession(null);
              setPassedStart(false);
              setPreferredRunId("");
            }}
          >
            Sair
          </button>
        </span>
      </header>
      {view === "eval" && session.mode === "rate" ? <BlindEval session={session} /> : null}
      {view === "metrics" ? <Plots preferredRunId={preferredRunId} /> : null}
      {view === "compare" ? <Compare allowGeneration={allowGeneration} /> : null}
      {view === "chat" && allowGeneration ? <Chat /> : null}
    </div>
  );
}
