"""Customer 360 aggregation for control plane."""
from sqlalchemy import or_
from sqlalchemy.orm import Session
from fastapi import HTTPException

from app.models.user import User, Account, Card, Transaction
from app.models.card_request import CardRequest, CardRequestStatus


def search_users(db: Session, q: str | None, skip: int = 0, limit: int = 50) -> list[User]:
    query = db.query(User)
    if q and q.strip():
        term = f"%{q.strip()}%"
        query = query.filter(
            or_(
                User.email.ilike(term),
                User.full_name.ilike(term),
                User.phone.ilike(term),
            )
        )
    return query.order_by(User.id.desc()).offset(skip).limit(limit).all()


def get_customer_360(db: Session, user_id: int) -> dict:
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    accounts = db.query(Account).filter(Account.user_id == user_id).all()
    cards = db.query(Card).filter(Card.user_id == user_id).all()
    txs = (
        db.query(Transaction)
        .filter(Transaction.user_id == user_id)
        .order_by(Transaction.created_at.desc())
        .limit(20)
        .all()
    )
    open_reqs = (
        db.query(CardRequest)
        .filter(
            CardRequest.user_id == user_id,
            CardRequest.status == CardRequestStatus.PENDING,
        )
        .count()
    )

    return {
        "id": user.id,
        "email": user.email,
        "full_name": user.full_name,
        "phone": user.phone,
        "role": user.role,
        "is_active": user.is_active,
        "kyc_status": user.kyc_status,
        "created_at": user.created_at,
        "last_login": user.last_login,
        "accounts": accounts,
        "cards": [
            {
                "id": c.id,
                "last_four": c.last_four,
                "card_type": c.card_type.value if hasattr(c.card_type, "value") else c.card_type,
                "status": c.status.value if hasattr(c.status, "value") else c.status,
                "label": c.label,
            }
            for c in cards
        ],
        "recent_transactions": [
            {
                "id": t.id,
                "amount": str(t.amount),
                "type": t.type.value if hasattr(t.type, "value") else t.type,
                "status": t.status.value if hasattr(t.status, "value") else t.status,
                "reference": t.reference,
                "is_flagged": t.is_flagged,
                "created_at": t.created_at.isoformat() if t.created_at else None,
            }
            for t in txs
        ],
        "open_card_requests": open_reqs,
    }
