const PUBLIC_API_BASE = process.env.NEXT_PUBLIC_API_BASE ?? process.env.NEXT_PUBLIC_API_URL ?? "";
const DEFAULT_API_BASE =
  process.env.NODE_ENV === "development"
    ? "http://localhost:8000"
    : "https://socio-inteligente-production.up.railway.app";

function stripTrailingSlash(value: string): string {
  return value.endsWith("/") ? value.slice(0, -1) : value;
}

function isRelativePath(value: string): boolean {
  return value.startsWith("/");
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
    // Absolute URL configured (e.g., http://localhost:8000)
    if (configured && !isRelativePath(configured)) {
      return stripTrailingSlash(configured);
    }
    // Relative base (/api) is preferred for production (Vercel)
    if (configured && isRelativePath(configured)) {
      return stripTrailingSlash(configured);
    }
    // Default to relative /api for production
    return "/api";
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
