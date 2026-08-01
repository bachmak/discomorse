// The reverse proxy serves the backend's HTTP API under /api (prefix stripped)
// and its WebSockets under /ws. The dev server proxies the same two prefixes.
const API_PREFIX = "/api";
const WS_PREFIX = "/ws";

export const UPLOAD_URL = `${API_PREFIX}/upload`;

export function micSocketUrl(): string {
  const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
  return `${protocol}//${window.location.host}${WS_PREFIX}/mic`;
}
