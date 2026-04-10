const PUBLIC_API_BASE = process.env.NEXT_PUBLIC_API_BASE ?? process.env.NEXT_PUBLIC_API_URL ?? "";

function stripTrailingSlash(value: string): string {
  return value.endsWith("/") ? value.slice(0, -1) : value;
}

function isLoopbackHost(value: string): boolean {
  const lower = value.toLowerCase();
  return lower.includes("localhost") || lower.includes("127.0.0.1");
}

function isLocalBrowserHost(): boolean {
  if (typeof window === "undefined") return false;
  const host = String(window.location.hostname || "").toLowerCase();
  return host === "localhost" || host === "127.0.0.1";
}

export function getApiBase(): string {
  if (typeof window !== "undefined") {
    const configured = PUBLIC_API_BASE.trim();
    if (configured) {
      // Protect remote sessions from accidental localhost config.
      if (isLoopbackHost(configured) && !isLocalBrowserHost()) {
        return stripTrailingSlash(DEFAULT_API_BASE);
      }
      return stripTrailingSlash(configured);
    }
    // Local browser can keep proxy path; remote browser should use direct backend.
    return isLocalBrowserHost() ? "/api" : stripTrailingSlash(DEFAULT_API_BASE);
  }
  const configured = PUBLIC_API_BASE.trim();
  if (configured) {
    return stripTrailingSlash(configured);
  }
  // Server-side fallback.
  return "/api";
}

export function buildApiUrl(path: string): string {
  const normalizedPath = path.startsWith("/") ? path : `/${path}`;
  return `${getApiBase()}${normalizedPath}`;
}

export function getBrowserOrigin(): string {
  if (typeof window !== "undefined" && window.location?.origin) {
    return window.location.origin;
  }
  return "unknown-origin";
}
