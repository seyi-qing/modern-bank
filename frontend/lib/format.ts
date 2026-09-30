/** Display helpers — currency, dates, account masks. */

export function formatMoney(amount: number | string, currency = "USD") {
  const n = typeof amount === "string" ? Number(amount) : amount;
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency,
    minimumFractionDigits: 2,
  }).format(n ?? 0);
}

/** Compact for tight tiles: $1.00B, $16.8K, etc. Full amount on title hover. */
export function formatMoneyCompact(amount: number | string, currency = "USD") {
  const n = typeof amount === "string" ? Number(amount) : Number(amount ?? 0);
  const abs = Math.abs(n);
  if (abs >= 1_000_000_000) {
    return `${n < 0 ? "-" : ""}$${(abs / 1_000_000_000).toFixed(2)}B`;
  }
  if (abs >= 1_000_000) {
    return `${n < 0 ? "-" : ""}$${(abs / 1_000_000).toFixed(2)}M`;
  }
  if (abs >= 100_000) {
    return `${n < 0 ? "-" : ""}$${(abs / 1_000).toFixed(1)}K`;
  }
  return formatMoney(n, currency);
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
