const PUBLIC_API_BASE = process.env.NEXT_PUBLIC_API_BASE ?? process.env.NEXT_PUBLIC_API_URL ?? "";

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

function shouldUseLocalProxy(configured: string): boolean {
  if (!configured || isRelativePath(configured)) return false;
  if (!isLocalBrowserHost()) return false;
  return isLoopbackHost(configured);
}

export function getApiBase(): string {
  if (typeof window !== "undefined") {
    const configured = PUBLIC_API_BASE.trim();
    // In local browser sessions, route loopback URLs through the Next.js proxy
    // so the browser does not depend on reaching a separate localhost origin.
    if (shouldUseLocalProxy(configured)) {
      return "/api";
    }
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
  let normalizedPath = path.startsWith("/") ? path : `/${path}`;
  const base = getApiBase();
  // La mayoría de rutas nuevas ya incluyen /api. Cuando el navegador local
  // usa el proxy /api, evita construir /api/api/... y conserva compatibilidad
  // con rutas históricas como /dashboard o /auth.
  if ((base === "/api" || base.endsWith("/api")) && normalizedPath.startsWith("/api/")) {
    normalizedPath = normalizedPath.slice(4);
  }
  return `${base}${normalizedPath}`;
}

export function getBrowserOrigin(): string {
  if (typeof window !== "undefined" && window.location?.origin) {
    return window.location.origin;
  }
  return "unknown-origin";
}
