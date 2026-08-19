export function normalizeClienteId(value: string): string {
  return String(value || "").trim().replace(/;+$/, "");
}
