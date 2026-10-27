import { useEffect, useState } from "react";
import BlindEval from "./BlindEval";
import Compare from "./Compare";
import Gate from "./Gate";
import { api } from "./api";
import { clearSession, loadSession, type Session } from "./session";

export default function App() {
  const [session, setSession] = useState<Session | null>(() => loadSession());
  const [allowGeneration, setAllowGeneration] = useState(false);

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

import Plots from "./Plots";

export default function App() {
  const [view, setView] = useState<"compare" | "chat" | "metrics">("compare");
  return (
    <div className="app-root">
      <header className="app-bar">
        <strong>Goldilocks RAG</strong>
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
      {session.mode === "rate" ? (
        <BlindEval session={session} />
      ) : (
        <Compare allowGeneration={allowGeneration} />
      )}
          <button type="button" className={view === "metrics" ? "ghost active" : "ghost"} onClick={() => setView("metrics")}>
            Métricas
          </button>
        </nav>
      </header>
      {view === "compare" ? <Compare /> : view === "chat" ? <Chat /> : <Plots />}
    </div>
  );
}
