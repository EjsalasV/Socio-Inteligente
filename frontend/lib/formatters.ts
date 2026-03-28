export function formatMoney(value: number, currency: string = "USD"): string {
  const abs = Math.abs(value);
  const formatted = new Intl.NumberFormat("en-US", {
    style: "currency",
    currency,
    minimumFractionDigits: 0,
    maximumFractionDigits: 2,
  }).format(abs);

  if (value < 0) {
    return `(${formatted})`;
  }
  return formatted;
}

export function moneyClass(value: number | string): string {
  if (typeof value === "number") {
    return value < 0 ? "text-editorial-error" : "text-navy-900";
  }
  return value.startsWith("(") ? "text-editorial-error" : "text-navy-900";
}
