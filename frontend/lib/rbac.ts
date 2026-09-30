/** Staff role helpers for control-plane UI. */

const STAFF_ROLES = new Set([
  "admin",
  "operations",
  "risk_analyst",
  "finance",
  "card_operations",
  "compliance",
  "auditor",
]);

export function isStaffRole(role: string | undefined | null): boolean {
  return !!role && STAFF_ROLES.has(role);
}

export function staffNavHrefs(role: string | undefined | null): string[] {
  if (!role || !isStaffRole(role)) return [];
  if (role === "admin") {
    return [
      "/admin",
      "/admin/users",
      "/admin/transactions",
      "/admin/flagged",
      "/admin/reconciliation",
      "/admin/card-requests",
    ];
  }
  const map: Record<string, string[]> = {
    operations: ["/admin", "/admin/users", "/admin/transactions", "/admin/flagged"],
    risk_analyst: ["/admin", "/admin/users", "/admin/transactions", "/admin/flagged"],
    finance: ["/admin", "/admin/transactions", "/admin/reconciliation"],
    card_operations: ["/admin", "/admin/users", "/admin/card-requests"],
    compliance: ["/admin", "/admin/users", "/admin/transactions"],
    auditor: ["/admin", "/admin/users", "/admin/transactions", "/admin/reconciliation"],
  };
  return map[role] ?? ["/admin"];
}
