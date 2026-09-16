"""Notifications REST + WebSocket live feed."""

from typing import List, Optional
from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect, Query
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.deps import get_current_user
from app.core.security import decode_token
from app.models.user import User
from app.models.schemas import NotificationOut
from app.services.banking_service import list_notifications, mark_notifications_read
from app.services.ws_manager import manager

router = APIRouter(prefix="/notifications", tags=["Notifications"])


@router.get("", response_model=List[NotificationOut])
def get_notifications(
    limit: int = Query(30, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return list_notifications(db, current_user.id, limit)


@router.post("/read")
def mark_read(
    ids: Optional[List[int]] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    mark_notifications_read(db, current_user.id, ids)
    return {"ok": True}


@router.websocket("/ws")
async def notifications_ws(websocket: WebSocket, token: str = Query(...)):
    payload = decode_token(token)
    if not payload or payload.get("type") != "access":
        await websocket.close(code=4001)
        return

    user_id = int(payload["sub"])
    await manager.connect(user_id, websocket)
    try:
        await websocket.send_json({"type": "connected", "user_id": user_id})
        while True:
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_json({"type": "pong"})
    except WebSocketDisconnect:
        await manager.disconnect(user_id, websocket)
    except Exception:
        await manager.disconnect(user_id, websocket)
