export const API_URL = (import.meta.env.VITE_API_URL ?? (import.meta.env.DEV ? "" : "http://localhost:8000")).replace(
  /\/$/,
  "",
);

async function readError(response: Response): Promise<string> {
  let detail = `A API devolveu ${response.status}.`;
  try {
    const payload = (await response.json()) as { detail?: string };
    if (payload.detail) detail = payload.detail;
  } catch {
    /* ignore */
  }
  return detail;
}

export async function api<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_URL}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(init?.headers || {}),
    },
  });
  if (!response.ok) throw new Error(await readError(response));
  return (await response.json()) as T;
}

export async function apiForm<T>(path: string, formData: FormData): Promise<T> {
  const response = await fetch(`${API_URL}${path}`, {
    method: "POST",
    body: formData,
  });
  if (!response.ok) throw new Error(await readError(response));
  return (await response.json()) as T;
}
