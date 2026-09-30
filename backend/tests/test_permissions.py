"""RBAC contract tests for the ModernBank control plane.

These tests are deliberately database-free: they verify the authorization
matrix without touching production/staging data.
"""

import pytest

from app.core.permissions import Permission, has_permission, is_staff, permissions_for
from app.models.user import User, UserRole


def make_user(role: UserRole, active: bool = True) -> User:
    return User(
        id=1,
        email="rbac-test@example.com",
        hashed_password="test-only",
        full_name="RBAC Test",
        role=role,
        is_active=active,
    )


EXPECTED = {
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


@pytest.mark.parametrize("role,expected", EXPECTED.items())
def test_permission_matrix_matches_policy(role, expected):
    assert permissions_for(role) == expected


@pytest.mark.parametrize("role", list(UserRole))
def test_customer_is_not_staff_and_staff_roles_are_staff(role):
    user = make_user(role)
    assert is_staff(user) is (role != UserRole.CUSTOMER)


@pytest.mark.parametrize("permission", list(Permission))
def test_admin_has_every_permission(permission):
    assert has_permission(make_user(UserRole.ADMIN), permission) is True


@pytest.mark.parametrize("permission", list(Permission))
def test_customer_has_no_staff_permission(permission):
    assert has_permission(make_user(UserRole.CUSTOMER), permission) is False


@pytest.mark.parametrize("role", list(UserRole))
def test_inactive_users_have_no_permissions(role):
    user = make_user(role, active=False)
    assert permissions_for(role) == EXPECTED[role]
    assert all(has_permission(user, permission) is False for permission in Permission)
