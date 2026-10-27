import { useEffect, useState } from "react";
import BlindEval from "./BlindEval";
import Chat from "./Chat";
import Compare from "./Compare";
import Gate from "./Gate";
import Plots from "./Plots";
import { api } from "./api";
import { clearSession, loadSession, type Session } from "./session";

type View = "compare" | "chat" | "metrics";

export default function App() {
  const [session, setSession] = useState<Session | null>(() => loadSession());
  const [allowGeneration, setAllowGeneration] = useState(false);
  const [view, setView] = useState<View>("compare");

  useEffect(() => {
    api<{ allow_generation?: boolean }>("/health")
      .then((payload) => setAllowGeneration(Boolean(payload.allow_generation)))
      .catch(() => setAllowGeneration(false));
  }, []);

  if (!session) {
    return (
      <div className="app-root">
        <header className="app-bar">
          <strong>Goldilocks RAG</strong>
        </header>
        <Gate onEnter={setSession} />
      </div>
    );
  }

  return (
    <div className="app-root">
      <header className="app-bar">
        <strong>Goldilocks RAG</strong>
        {session.mode === "metrics_only" ? (
          <nav>
            <button type="button" className={view === "compare" ? "ghost active" : "ghost"} onClick={() => setView("compare")}>
              Comparar
            </button>
            <button type="button" className={view === "metrics" ? "ghost active" : "ghost"} onClick={() => setView("metrics")}>
              Métricas
            </button>
            {allowGeneration ? (
              <button type="button" className={view === "chat" ? "ghost active" : "ghost"} onClick={() => setView("chat")}>
                Chat
              </button>
            ) : null}
          </nav>
        ) : null}
        <span className="muted">
          {session.mode === "rate" ? session.name : "consulta"}
          <button
            type="button"
            className="ghost"
            onClick={() => {
              clearSession();
              setSession(null);
            }}
          >
            Sair
          </button>
        </span>
      </header>
      {session.mode === "rate" ? <BlindEval session={session} /> : null}
      {session.mode === "metrics_only" && view === "compare" ? <Compare allowGeneration={allowGeneration} /> : null}
      {session.mode === "metrics_only" && view === "metrics" ? <Plots /> : null}
      {session.mode === "metrics_only" && view === "chat" && allowGeneration ? <Chat /> : null}
    </div>
  );
}
