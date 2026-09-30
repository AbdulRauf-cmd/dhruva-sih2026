import json
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Event
from app.event_store import verify_chain

router = APIRouter(prefix="/api/audit", tags=["audit"])

@router.get("/verify")
def verify_audit_chain(db: Session = Depends(get_db)):
    return verify_chain(db)

@router.get("/events")
def list_events(limit: int = 50, offset: int = 0, db: Session = Depends(get_db)):
    events = db.query(Event).order_by(Event.lamport_clock.desc()).offset(offset).limit(limit).all()
    out = []
    for ev in events:
        out.append({
            'id': ev.id,
            'node_id': ev.node_id,
            'type': ev.type,
            'payload': json.loads(ev.payload) if isinstance(ev.payload, str) else ev.payload,
            'actor': ev.actor,
            'created_at': ev.created_at,
            'lamport_clock': ev.lamport_clock,
            'prev_hash': ev.prev_hash,
            'hash': ev.hash,
            'synced': ev.synced
        })
    return out

@router.get("/events/{id}")
def get_event(id: str, db: Session = Depends(get_db)):
    ev = db.query(Event).filter(Event.id == id).first()
    if not ev:
        raise HTTPException(status_code=404, detail="Event not found")
    return {
        'id': ev.id,
        'node_id': ev.node_id,
        'type': ev.type,
        'payload': json.loads(ev.payload) if isinstance(ev.payload, str) else ev.payload,
        'actor': ev.actor,
        'created_at': ev.created_at,
        'lamport_clock': ev.lamport_clock,
        'prev_hash': ev.prev_hash,
        'hash': ev.hash,
        'synced': ev.synced
    }
