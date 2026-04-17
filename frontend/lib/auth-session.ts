import { buildApiUrl } from "./api-base";

const SESSION_ACTIVE_KEY = "socio_session_active";
const CSRF_TOKEN_KEY = "socio_csrf_token";

export function hasSessionState(): boolean {
  if (typeof window === "undefined") return false;
  return window.localStorage.getItem(SESSION_ACTIVE_KEY) === "1";
}

export function getStoredCsrfToken(): string {
  if (typeof window === "undefined") return "";
  return String(window.localStorage.getItem(CSRF_TOKEN_KEY) || "");
}

export function setSessionState(csrfToken: string): void {
  if (typeof window === "undefined") return;
  window.localStorage.setItem(SESSION_ACTIVE_KEY, "1");
  window.localStorage.setItem(CSRF_TOKEN_KEY, csrfToken || "");
  window.dispatchEvent(new Event("socio-auth-changed"));
}

export function clearSessionState(): void {
  if (typeof window === "undefined") return;
  window.localStorage.removeItem(SESSION_ACTIVE_KEY);
  window.localStorage.removeItem(CSRF_TOKEN_KEY);
  // Clear token from both storages
  window.localStorage.removeItem("socio_auth_token");
  if (window.sessionStorage) {
    window.sessionStorage.removeItem("socio_auth_token");
  }
  window.dispatchEvent(new Event("socio-auth-changed"));
}

export async function logoutSession(): Promise<void> {
  try {
    await fetch(buildApiUrl("/auth/logout"), {
      method: "POST",
      credentials: "include",
    });
  } catch {
    // ignore logout network failures and clear client state regardless
  } finally {
    clearSessionState();
  }
}
