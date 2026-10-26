export const API_URL = (import.meta.env.VITE_API_URL ?? "").replace(/\/$/, "");

export function sessionHeaders(sessionId?: string | null): HeadersInit {
  return sessionId ? { "X-Session-Id": sessionId } : {};
}

export async function api<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_URL}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(init?.headers || {}),
    },
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
  return (await response.json()) as T;
}
