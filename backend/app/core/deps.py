"""
FastAPI dependencies: JWT user, staff gate, permission checks.
"""

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import decode_token
from app.core.permissions import (
    Permission,
    has_permission,
    is_staff,
    require_permission,
)
from app.models.user import User
from app.core.config import settings

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_PREFIX}/auth/login")


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    payload = decode_token(token)
    if not payload or payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token payload")

    user = db.query(User).filter(User.id == int(user_id)).first()
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="User not found or inactive")
    return user


def get_current_staff(current_user: User = Depends(get_current_user)) -> User:
    """Any control-plane staff role (not customer)."""
    if not is_staff(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Staff privileges required",
        )
    return current_user


def get_current_admin(current_user: User = Depends(get_current_user)) -> User:
    """Backward-compatible: any staff member may enter admin API surface;
    individual routes still enforce Permission checks."""
    if not is_staff(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required",
        )
    return current_user


def require_perm(permission: Permission):
    """FastAPI dependency factory: require a single permission."""

    def _dep(current_user: User = Depends(get_current_user)) -> User:
        require_permission(current_user, permission)
        return current_user

    return _dep
