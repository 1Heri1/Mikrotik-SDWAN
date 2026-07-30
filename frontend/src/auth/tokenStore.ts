// Access token is kept in memory only (never localStorage) to limit the blast
// radius of XSS. It lives here, outside React state, because the axios
// interceptors in api/client.ts run outside the React render tree and need
// synchronous read access. AuthProvider is the only place that calls
// setAccessToken - it mirrors the value into React state for components.

let accessToken: string | null = null;
let onAuthFailure: (() => void) | null = null;

export function getAccessToken(): string | null {
  return accessToken;
}

export function setAccessToken(token: string | null): void {
  accessToken = token;
}

/** Registered by AuthProvider so the axios interceptor can force a logout
 * (redirect to /login) when a refresh ultimately fails. */
export function registerAuthFailureHandler(handler: () => void): void {
  onAuthFailure = handler;
}

export function notifyAuthFailure(): void {
  onAuthFailure?.();
}
