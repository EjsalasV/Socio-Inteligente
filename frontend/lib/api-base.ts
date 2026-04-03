const PUBLIC_API_BASE = process.env.NEXT_PUBLIC_API_BASE ?? process.env.NEXT_PUBLIC_API_URL ?? "";

function stripTrailingSlash(value: string): string {
  return value.endsWith("/") ? value.slice(0, -1) : value;
}

export function getApiBase(): string {
  // In browser always use Next.js proxy to avoid direct CORS/network edge cases.
  if (typeof window !== "undefined") {
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
