export const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000"

// In the desktop build, the page loads and fires its first fetches before
// the bundled backend sidecar has finished starting up — those calls fail
// at the network level (not an HTTP error response), so retry a few times
// before giving up rather than leaving the UI stuck on a stale error.
async function fetchWithRetry(url: string, init: RequestInit, retries = 5): Promise<Response> {
  try {
    return await fetch(url, init)
  } catch (e) {
    if (retries <= 0) throw e
    await new Promise((r) => setTimeout(r, 400))
    return fetchWithRetry(url, init, retries - 1)
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  // Only set Content-Type when there's actually a body — sending it on
  // bodyless GET/DELETE requests forces a CORS preflight for no reason.
  const res = await fetchWithRetry(`${API_URL}${path}`, {
    ...init,
    headers: { ...(init?.body ? { "Content-Type": "application/json" } : {}), ...init?.headers },
  })
  if (!res.ok) {
    const error = await res.json().catch(() => ({ detail: res.statusText }))
    throw new Error(error.detail ?? "Request failed")
  }
  if (res.status === 204) return undefined as T
  return res.json()
}

export const api = {
  get: <T>(path: string) => request<T>(path),
  post: <T>(path: string, body: unknown) =>
    request<T>(path, { method: "POST", body: JSON.stringify(body) }),
  patch: <T>(path: string, body: unknown) =>
    request<T>(path, { method: "PATCH", body: JSON.stringify(body) }),
  delete: <T>(path: string) => request<T>(path, { method: "DELETE" }),
  upload: <T>(path: string, formData: FormData): Promise<T> =>
    fetch(`${API_URL}${path}`, { method: "POST", body: formData }).then(async (res) => {
      if (!res.ok) {
        const error = await res.json().catch(() => ({ detail: res.statusText }))
        throw new Error(error.detail ?? "Upload failed")
      }
      return res.json() as Promise<T>
    }),
}
