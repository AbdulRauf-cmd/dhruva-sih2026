from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Event, User
from app.auth import get_current_user, require_role
from app.config import settings, link_status

router = APIRouter(prefix="/api/admin", tags=["admin"])


class LinkStatusRequest(BaseModel):
    status: str


@router.post("/link/{station_id}")
def set_link(station_id: str, body: LinkStatusRequest, db: Session = Depends(get_db)):
    if station_id in link_status:
        link_status[station_id] = body.status.upper()
        if station_id == settings.NODE_ID:
            settings.LINK_STATUS = body.status.upper()
        return {"status": "ok", "station": station_id, "link": body.status.upper()}
    raise HTTPException(status_code=404, detail="Station not found")


@router.get("/link")
def get_link():
    return link_status


@router.post("/tamper/{event_id}")
def tamper_event(event_id: str, db: Session = Depends(get_db)):
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        # Pick the third event if no specific ID given
        event = db.query(Event).order_by(Event.lamport_clock.asc()).offset(2).first()
    if not event:
        raise HTTPException(status_code=404, detail="No events to tamper with")
    original_hash = event.hash
    event.hash = "TAMPERED_" + event.hash[:54]
    db.commit()
    return {"status": "tampered", "event_id": event.id, "original_hash": original_hash}


@router.get("/stats")
def system_stats(db: Session = Depends(get_db)):
    return {
        "events": db.query(Event).count(),
        "users": db.query(User).count(),
        "node_id": settings.NODE_ID,
        "role": settings.NODE_ROLE,
    }
