"""Card request lifecycle: request → review → issue."""
from datetime import datetime, timezone
from decimal import Decimal

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.card_request import CardRequest, CardRequestStatus
from app.models.schemas import CardCreate
from app.models.schemas_ops import CardRequestCreate
from app.models.user import User, Account, Notification
from app.services.banking_service import create_card


def create_card_request(db: Session, user: User, data: CardRequestCreate) -> CardRequest:
    acc = (
        db.query(Account)
        .filter(
            Account.id == data.account_id,
            Account.user_id == user.id,
            Account.is_active == True,
        )
        .first()
    )
    if not acc:
        raise HTTPException(status_code=404, detail="Account not found or inactive")

    pending = (
        db.query(CardRequest)
        .filter(
            CardRequest.user_id == user.id,
            CardRequest.status == CardRequestStatus.PENDING,
        )
        .count()
    )
    if pending >= 3:
        raise HTTPException(status_code=400, detail="Too many pending card requests (max 3)")

    req = CardRequest(
        user_id=user.id,
        account_id=data.account_id,
        card_type=data.card_type,
        label=data.label,
        spending_limit=data.spending_limit,
        status=CardRequestStatus.PENDING,
    )
    db.add(req)
    db.add(
        Notification(
            user_id=user.id,
            title="Card request submitted",
            message=f"Your {data.card_type.value} card request is pending bank review.",
            type="card",
        )
    )
    db.commit()
    db.refresh(req)
    return req


def list_user_card_requests(db: Session, user_id: int) -> list[CardRequest]:
    return (
        db.query(CardRequest)
        .filter(CardRequest.user_id == user_id)
        .order_by(CardRequest.created_at.desc())
        .all()
    )


def list_pending_card_requests(db: Session, limit: int = 100) -> list[CardRequest]:
    return (
        db.query(CardRequest)
        .filter(CardRequest.status == CardRequestStatus.PENDING)
        .order_by(CardRequest.created_at.asc())
        .limit(limit)
        .all()
    )


def review_card_request(
    db: Session,
    request_id: int,
    action: str,
    reason: str,
    reviewer: User,
) -> CardRequest:
    req = db.query(CardRequest).filter(CardRequest.id == request_id).with_for_update().first()
    if not req:
        raise HTTPException(status_code=404, detail="Card request not found")
    if req.status != CardRequestStatus.PENDING:
        raise HTTPException(status_code=409, detail="Request already reviewed")

    req.reviewed_by_user_id = reviewer.id
    req.reviewed_at = datetime.now(timezone.utc)
    req.review_reason = reason

    if action == "reject":
        req.status = CardRequestStatus.REJECTED
        db.add(
            Notification(
                user_id=req.user_id,
                title="Card request rejected",
                message=f"Request #{req.id} was rejected: {reason}",
                type="card",
            )
        )
        db.commit()
        db.refresh(req)
        return req

    # approve → issue card via existing issuer
    owner = db.query(User).filter(User.id == req.user_id).first()
    if not owner:
        raise HTTPException(status_code=404, detail="Customer not found")

    card = create_card(
        db,
        owner,
        CardCreate(
            account_id=req.account_id,
            card_type=req.card_type,
            label=req.label,
            spending_limit=Decimal(str(req.spending_limit)) if req.spending_limit is not None else None,
        ),
    )
    req.status = CardRequestStatus.APPROVED
    req.issued_card_id = card.id
    db.add(
        Notification(
            user_id=req.user_id,
            title="Card issued",
            message=f"Your card request #{req.id} was approved. Card ending {card.last_four} is active.",
            type="card",
        )
    )
    db.commit()
    db.refresh(req)
    return req
