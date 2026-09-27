/** Display helpers — currency, dates, account masks. */

export function formatMoney(amount: number, currency = "USD") {
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency,
    minimumFractionDigits: 2,
  }).format(amount ?? 0);
}

export function formatDate(iso: string | Date) {
  const d = typeof iso === "string" ? new Date(iso) : iso;
  return d.toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
  });
}

export function formatDateTime(iso: string | Date) {
  const d = typeof iso === "string" ? new Date(iso) : iso;
  return d.toLocaleString("en-US", {
    month: "short",
    day: "numeric",
    hour: "numeric",
    minute: "2-digit",
  });
}

export function maskAccount(num: string) {
  if (!num || num.length < 4) return num || "—";
  return `•••• ${num.slice(-4)}`;
}

export function cn(...parts: (string | false | null | undefined)[]) {
  return parts.filter(Boolean).join(" ");
}
