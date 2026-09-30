"""
ModernBank control-plane permissions.

Roles are coarse; permissions gate endpoints.
ADMIN retains full power (backward compatible with existing admin users).
No permission allows direct Account.balance edits — money moves only via ledger ops.
"""
from __future__ import annotations

from enum import Enum
from fastapi import HTTPException, status

from app.models.user import User, UserRole


class Permission(str, Enum):
    STATS_READ = "stats:read"
    USERS_READ = "users:read"
    USERS_WRITE = "users:write"
    TRANSACTIONS_READ = "transactions:read"
    TRANSACTIONS_FLAGGED = "transactions:flagged"
    TRANSACTIONS_REVIEW = "transactions:review"
    RECONCILIATION_READ = "reconciliation:read"
    ACCOUNTS_FREEZE = "accounts:freeze"
    KYC_WRITE = "kyc:write"
    AUDIT_READ = "audit:read"
    CARDS_OPS = "cards:ops"


# Role → granted permissions (ADMIN = all)
_ROLE_PERMISSIONS: dict[UserRole, set[Permission]] = {
    UserRole.CUSTOMER: set(),
    UserRole.ADMIN: set(Permission),  # super-admin equivalent
    UserRole.OPERATIONS: {
        Permission.STATS_READ,
        Permission.USERS_READ,
        Permission.TRANSACTIONS_READ,
        Permission.TRANSACTIONS_FLAGGED,
        Permission.ACCOUNTS_FREEZE,
    },
    UserRole.RISK_ANALYST: {
        Permission.STATS_READ,
        Permission.USERS_READ,
        Permission.TRANSACTIONS_READ,
        Permission.TRANSACTIONS_FLAGGED,
        Permission.TRANSACTIONS_REVIEW,
        Permission.AUDIT_READ,
    },
    UserRole.FINANCE: {
        Permission.STATS_READ,
        Permission.TRANSACTIONS_READ,
        Permission.RECONCILIATION_READ,
        Permission.AUDIT_READ,
    },
    UserRole.CARD_OPERATIONS: {
        Permission.STATS_READ,
        Permission.USERS_READ,
        Permission.CARDS_OPS,
        Permission.TRANSACTIONS_READ,
    },
    UserRole.COMPLIANCE: {
        Permission.STATS_READ,
        Permission.USERS_READ,
        Permission.USERS_WRITE,  # KYC status only in practice
        Permission.KYC_WRITE,
        Permission.TRANSACTIONS_READ,
        Permission.AUDIT_READ,
    },
    UserRole.AUDITOR: {
        Permission.STATS_READ,
        Permission.USERS_READ,
        Permission.TRANSACTIONS_READ,
        Permission.RECONCILIATION_READ,
        Permission.AUDIT_READ,
    },
}


STAFF_ROLES: frozenset[UserRole] = frozenset(
    {
        UserRole.ADMIN,
        UserRole.OPERATIONS,
        UserRole.RISK_ANALYST,
        UserRole.FINANCE,
        UserRole.CARD_OPERATIONS,
        UserRole.COMPLIANCE,
        UserRole.AUDITOR,
    }
)


def is_staff(user: User) -> bool:
    return user.role in STAFF_ROLES


def permissions_for(role: UserRole) -> set[Permission]:
    return set(_ROLE_PERMISSIONS.get(role, set()))


def has_permission(user: User, permission: Permission) -> bool:
    if not user.is_active:
        return False
    return permission in permissions_for(user.role)


def require_permission(user: User, permission: Permission) -> None:
    if not has_permission(user, permission):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Missing permission: {permission.value}",
        )


def require_any_permission(user: User, *permissions: Permission) -> None:
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Inactive user")
    granted = permissions_for(user.role)
    if not any(p in granted for p in permissions):
        needed = ", ".join(p.value for p in permissions)
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Missing one of permissions: {needed}",
        )
