import { useState } from "react";
import Chat from "./Chat";
import Compare from "./Compare";
import Plots from "./Plots";

export default function App() {
  const [view, setView] = useState<"compare" | "chat" | "metrics">("compare");
  return (
    <div className="app-root">
      <header className="app-bar">
        <strong>Goldilocks RAG</strong>
        <nav>
          <button type="button" className={view === "compare" ? "ghost active" : "ghost"} onClick={() => setView("compare")}>
            Comparar
          </button>
          <button type="button" className={view === "chat" ? "ghost active" : "ghost"} onClick={() => setView("chat")}>
            Chat
          </button>
          <button type="button" className={view === "metrics" ? "ghost active" : "ghost"} onClick={() => setView("metrics")}>
            Métricas
          </button>
        </nav>
      </header>
      {view === "compare" ? <Compare /> : view === "chat" ? <Chat /> : <Plots />}
    </div>
  );
}
