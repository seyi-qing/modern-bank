"""Card management endpoints."""

from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.user import User, CardStatus
from app.models.schemas import CardCreate, CardOut, CardUpdate
from app.services.banking_service import create_card, list_cards, update_card

router = APIRouter(prefix="/cards", tags=["Cards"])


@router.get("", response_model=List[CardOut])
def get_cards(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return list_cards(db, current_user.id)


@router.post("", response_model=CardOut, status_code=201)
def issue_card(
    data: CardCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return create_card(db, current_user, data)


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
