"""
ModernBank control-plane permissions.
ADMIN retains full power (backward compatible with existing admin users).
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


_ROLE_PERMISSIONS: dict[UserRole, set[Permission]] = {
    UserRole.CUSTOMER: set(),
    UserRole.ADMIN: set(Permission),
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
        Permission.USERS_WRITE,
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


def _role_key(user: User) -> UserRole | None:
    """Normalize role whether ORM returned enum or raw string."""
    r = user.role
    if isinstance(r, UserRole):
        return r
    if isinstance(r, str):
        try:
            return UserRole(r)
        except ValueError:
            try:
                return UserRole[r.upper()]
            except KeyError:
                return None
    return None


def is_staff(user: User) -> bool:
    role = _role_key(user)
    return role in STAFF_ROLES if role else False


def permissions_for(role: UserRole | str | None) -> set[Permission]:
    if role is None:
        return set()
    if isinstance(role, str):
        try:
            role = UserRole(role)
        except ValueError:
            return set()
    # Admin always full set
    if role == UserRole.ADMIN:
        return set(Permission)
    return set(_ROLE_PERMISSIONS.get(role, set()))


def has_permission(user: User, permission: Permission) -> bool:
    if not user.is_active:
        return False
    role = _role_key(user)
    if role == UserRole.ADMIN:
        return True
    return permission in permissions_for(role)


def require_permission(user: User, permission: Permission) -> None:
    if not has_permission(user, permission):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Missing permission: {permission.value}",
        )


def require_any_permission(user: User, *permissions: Permission) -> None:
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Inactive user")
    if any(has_permission(user, p) for p in permissions):
        return
    needed = ", ".join(p.value for p in permissions)
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail=f"Missing one of permissions: {needed}",
    )
