const KEY = "goldilocks-session";

export type Session = {
  id: string;
  name: string;
  mode: "rate" | "metrics_only";
};

export function loadSession(): Session | null {
  try {
    const raw = sessionStorage.getItem(KEY);
    return raw ? (JSON.parse(raw) as Session) : null;
  } catch {
    return null;
  }
}

export function saveSession(session: Session) {
  sessionStorage.setItem(KEY, JSON.stringify(session));
}

export function clearSession() {
  sessionStorage.removeItem(KEY);
}
