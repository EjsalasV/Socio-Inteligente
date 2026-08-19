export function answerStillNeedsConfirmation(value: string): boolean {
  const normalized = String(value || "").trim().toLowerCase();
  return [
    "falta confirmar",
    "falta por confirmar",
    "me falta confirmar",
    "debo confirmar",
    "debemos confirmar",
    "aún no se conoce",
    "aun no se conoce",
    "aún no tengo",
    "aun no tengo",
    "por confirmar",
    "por definir",
  ].some((marker) => normalized.includes(marker));
}
