export const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api/v1";

export function csrfToken(): string {
  if (typeof document === "undefined") return "";
  const value = document.cookie
    .split("; ")
    .find((item) => item.startsWith("tributaria_csrf="));
  return value ? decodeURIComponent(value.split("=")[1] ?? "") : "";
}

export async function apiFetch(path: string, init: RequestInit = {}): Promise<Response> {
  const headers = new Headers(init.headers);
  // A FormData body (batch file upload, Etapa 23) must keep the browser's own
  // multipart Content-Type with its boundary - setting it manually would drop
  // the boundary and break parsing on the server.
  if (init.body && !(init.body instanceof FormData)) headers.set("Content-Type", "application/json");
  const csrf = csrfToken();
  if (csrf) headers.set("X-CSRF-Token", csrf);
  return fetch(`${API_URL}${path}`, { ...init, headers, credentials: "include" });
}

