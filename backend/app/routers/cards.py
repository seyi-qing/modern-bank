"""Card management + card request workflow."""

from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.user import User, CardStatus
from app.models.schemas import CardOut, CardUpdate
from app.models.schemas_ops import CardRequestCreate, CardRequestOut
from app.services.banking_service import list_cards, update_card
from app.services.card_request_service import create_card_request, list_user_card_requests

router = APIRouter(prefix="/cards", tags=["Cards"])


@router.get("", response_model=List[CardOut])
def get_cards(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return list_cards(db, current_user.id)


@router.post("", status_code=201)
def issue_card_legacy_blocked():
    """Instant issue disabled — use POST /cards/requests."""
    raise HTTPException(
        status_code=410,
        detail="Instant card issue is disabled. Use POST /api/v1/cards/requests; staff approve via /admin/card-requests.",
    )


@router.post("/requests", response_model=CardRequestOut, status_code=201)
def request_card(
    data: CardRequestCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return create_card_request(db, current_user, data)


@router.get("/requests", response_model=List[CardRequestOut])
def my_card_requests(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return list_user_card_requests(db, current_user.id)


@router.patch("/{card_id}", response_model=CardOut)
def patch_card(
    card_id: int,
    data: CardUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return update_card(
        db,
        current_user,
        card_id,
        status=data.status,
        spending_limit=data.spending_limit,
        label=data.label,
    )


@router.post("/{card_id}/freeze", response_model=CardOut)
def freeze_card(card_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return update_card(db, current_user, card_id, status=CardStatus.FROZEN)


@router.post("/{card_id}/unfreeze", response_model=CardOut)
def unfreeze_card(card_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return update_card(db, current_user, card_id, status=CardStatus.ACTIVE)
