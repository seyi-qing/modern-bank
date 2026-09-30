"""RBAC contract tests for the ModernBank control plane."""

import unittest

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
        Permission.STATS_READ, Permission.USERS_READ,
        Permission.TRANSACTIONS_READ, Permission.TRANSACTIONS_FLAGGED,
        Permission.ACCOUNTS_FREEZE,
    },
    UserRole.RISK_ANALYST: {
        Permission.STATS_READ, Permission.USERS_READ,
        Permission.TRANSACTIONS_READ, Permission.TRANSACTIONS_FLAGGED,
        Permission.TRANSACTIONS_REVIEW, Permission.AUDIT_READ,
    },
    UserRole.FINANCE: {
        Permission.STATS_READ, Permission.TRANSACTIONS_READ,
        Permission.RECONCILIATION_READ, Permission.AUDIT_READ,
    },
    UserRole.CARD_OPERATIONS: {
        Permission.STATS_READ, Permission.USERS_READ,
        Permission.CARDS_OPS, Permission.TRANSACTIONS_READ,
    },
    UserRole.COMPLIANCE: {
        Permission.STATS_READ, Permission.USERS_READ, Permission.USERS_WRITE,
        Permission.KYC_WRITE, Permission.TRANSACTIONS_READ,
        Permission.AUDIT_READ,
    },
    UserRole.AUDITOR: {
        Permission.STATS_READ, Permission.USERS_READ,
        Permission.TRANSACTIONS_READ, Permission.RECONCILIATION_READ,
        Permission.AUDIT_READ,
    },
}


class PermissionMatrixTests(unittest.TestCase):
    def test_permission_matrix_matches_policy(self):
        for role, expected in EXPECTED.items():
            with self.subTest(role=role):
                self.assertEqual(permissions_for(role), expected)

    def test_staff_classification(self):
        for role in UserRole:
            with self.subTest(role=role):
                self.assertEqual(is_staff(make_user(role)), role != UserRole.CUSTOMER)

    def test_admin_has_every_permission(self):
        user = make_user(UserRole.ADMIN)
        for permission in Permission:
            with self.subTest(permission=permission):
                self.assertTrue(has_permission(user, permission))

    def test_customer_has_no_staff_permission(self):
        user = make_user(UserRole.CUSTOMER)
        for permission in Permission:
            with self.subTest(permission=permission):
                self.assertFalse(has_permission(user, permission))

    def test_inactive_users_have_no_permissions(self):
        for role in UserRole:
            with self.subTest(role=role):
                user = make_user(role, active=False)
                self.assertEqual(permissions_for(role), EXPECTED[role])
                self.assertTrue(all(
                    not has_permission(user, permission) for permission in Permission
                ))


if __name__ == "__main__":
    unittest.main()
