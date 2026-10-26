import { FormEvent, KeyboardEvent, useEffect, useMemo, useRef, useState } from "react";
import Markdown from "react-markdown";
import { API_URL } from "./api";

type Role = "user" | "assistant";

type Source = {
  index: number;
  chunk_id: string;
  document: string;
  filename: string;
  page: string | null;
  section: string | null;
  score: number;
  excerpt: string;
};

type ChatMessage = {
  id: string;
  role: Role;
  content: string;
  sources?: Source[];
  retrieval?: string;
  error?: string;
};

type StreamEvent = { event: string; data: string };

const STORAGE_KEY = "pc-rag-chat";

function uid() {
  return crypto.randomUUID();
}

function loadMessages(): ChatMessage[] {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    return raw ? (JSON.parse(raw) as ChatMessage[]) : [];
  } catch {
    return [];
  }
}

async function* readSse(response: Response): AsyncGenerator<StreamEvent> {
  const reader = response.body?.getReader();
  if (!reader) throw new Error("A resposta da API não tem corpo.");
  const decoder = new TextDecoder();
  let buffer = "";
  while (true) {
    const { done, value } = await reader.read();
    buffer += decoder.decode(value || new Uint8Array(), { stream: !done });
    const parts = buffer.split("\n\n");
    buffer = parts.pop() ?? "";
    for (const part of parts) {
      let event = "message";
      const dataLines: string[] = [];
      for (const line of part.split("\n")) {
        if (line.startsWith("event:")) event = line.slice(6).trim();
        if (line.startsWith("data:")) dataLines.push(line.slice(5).trim());
      }
      if (dataLines.length) yield { event, data: dataLines.join("\n") };
    }
    if (done) break;
  }
}

export default function Chat() {
  const [messages, setMessages] = useState<ChatMessage[]>(() => loadMessages());
  const [draft, setDraft] = useState("");
  const [provider, setProvider] = useState<"xai" | "gemini">("xai");
  const [pending, setPending] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const listRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(messages));
  }, [messages]);

  useEffect(() => {
    listRef.current?.scrollTo({ top: listRef.current.scrollHeight, behavior: "smooth" });
  }, [messages, pending]);

  const history = useMemo(
    () => messages.filter((item) => !item.error).map((item) => ({ role: item.role, content: item.content })),
    [messages],
  );

  async function send(text: string) {
    const trimmed = text.trim();
    if (!trimmed || pending) return;
    setError(null);
    setDraft("");
    const assistantId = uid();
    setMessages((current) => [
      ...current,
      { id: uid(), role: "user", content: trimmed },
      { id: assistantId, role: "assistant", content: "" },
    ]);
    setPending(true);
    try {
      const response = await fetch(`${API_URL}/chat/stream`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: trimmed, history, provider }),
      });
      if (!response.ok) {
        let detail = `A API devolveu ${response.status}.`;
        try {
          const payload = (await response.json()) as { detail?: string };
          if (payload.detail) detail = payload.detail;
        } catch {
          /* ignore */
        }
        throw new Error(detail);
      }
      for await (const event of readSse(response)) {
        const payload = JSON.parse(event.data) as {
          text?: string;
          sources?: Source[];
          retrieval?: string;
          answer?: string;
          error?: string;
        };
        if (event.event === "error") throw new Error(payload.error || "A geração falhou.");
        setMessages((current) =>
          current.map((item) => {
            if (item.id !== assistantId) return item;
            if (event.event === "sources") return { ...item, sources: payload.sources, retrieval: payload.retrieval };
            if (event.event === "delta") return { ...item, content: item.content + (payload.text || "") };
            if (event.event === "done" && payload.answer) {
              return { ...item, content: payload.answer, sources: payload.sources, retrieval: payload.retrieval };
            }
            return item;
          }),
        );
      }
    } catch (err) {
      const message = err instanceof Error ? err.message : "Não foi possível contactar a API.";
      setError(message);
      setMessages((current) =>
        current.map((item) => (item.id === assistantId ? { ...item, error: message, content: item.content } : item)),
      );
    } finally {
      setPending(false);
      inputRef.current?.focus();
    }
  }

  function onSubmit(event: FormEvent) {
    event.preventDefault();
    void send(draft);
  }

  function onKeyDown(event: KeyboardEvent<HTMLTextAreaElement>) {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      void send(draft);
    }
  }

  return (
    <div className="shell">
      <aside className="rail">
        <p className="muted">Pergunta livre ao RAG, um modelo de cada vez.</p>
        <button
          type="button"
          className="ghost"
          onClick={() => {
            setMessages([]);
            setError(null);
            localStorage.removeItem(STORAGE_KEY);
            inputRef.current?.focus();
          }}
        >
          Nova conversa
        </button>
        <label className="provider">
          Modelo
          <select value={provider} onChange={(event) => setProvider(event.target.value as "xai" | "gemini")}>
            <option value="xai">Grok (xAI)</option>
            <option value="gemini">Gemini</option>
          </select>
        </label>
      </aside>
      <main className="stage">
        <div className="thread" ref={listRef}>
          {messages.length === 0 && (
            <section className="welcome">
              <p>Olá. Sou o assistente de teste do RAG. Posso responder com base nos manuais já carregados.</p>
              <p className="muted">Escreva uma pergunta. Nada é enviado sem o seu pedido.</p>
            </section>
          )}
          {messages.map((item) => (
            <article key={item.id} className={`bubble ${item.role}`}>
              {item.role === "assistant" && !item.content && pending ? (
                <p className="thinking">A pensar…</p>
              ) : item.role === "assistant" ? (
                <div className="markdown">
                  <Markdown>{item.content || " "}</Markdown>
                </div>
              ) : (
                <p>{item.content}</p>
              )}
              {item.error && <p className="fail">{item.error}</p>}
              {item.role === "assistant" && item.content && (
                <div className="actions">
                  <button type="button" onClick={() => void navigator.clipboard.writeText(item.content)}>
                    Copiar
                  </button>
                </div>
              )}
              {item.sources && item.sources.length > 0 && (
                <details className="sources">
                  <summary>Fontes ({item.sources.length})</summary>
                  <ul>
                    {item.sources.map((source) => (
                      <li key={source.chunk_id}>
                        <strong>
                          [{source.index}] {source.document}
                        </strong>
                        <span>
                          {source.filename}
                          {source.page ? ` · p. ${source.page}` : ""}
                          {source.section ? ` · ${source.section}` : ""} · score {source.score}
                        </span>
                        <em>{source.excerpt}</em>
                      </li>
                    ))}
                  </ul>
                </details>
              )}
            </article>
          ))}
        </div>
        {error && <div className="banner">{error}</div>}
        <form className="composer" onSubmit={onSubmit}>
          <textarea
            ref={inputRef}
            rows={1}
            value={draft}
            onChange={(event) => setDraft(event.target.value)}
            onKeyDown={onKeyDown}
            placeholder="Escreva uma pergunta…"
            disabled={pending}
          />
          <button type="submit" disabled={pending || !draft.trim()}>
            Enviar
          </button>
        </form>
        <p className="hint">Enter envia · Shift+Enter muda de linha</p>
      </main>
    </div>
  );
}
