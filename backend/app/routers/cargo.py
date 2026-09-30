import json
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Event, CrateCreate, CheckpointCreate, User, VesselPositionCreate
from app.auth import get_current_user
from app.event_store import append_event
from app.config import settings
from datetime import datetime, timezone

router = APIRouter(prefix="/api/cargo", tags=["cargo"])

def get_cargo_state(db):
    crates = {}
    events = db.query(Event).filter(
        Event.type.like('cargo.%')
    ).order_by(Event.lamport_clock.asc()).all()
    for ev in events:
        p = json.loads(ev.payload) if isinstance(ev.payload, str) else ev.payload
        if ev.type == 'cargo.created':
            crates[ev.id] = {
                'crate_id': ev.id,
                'contents': p.get('contents'),
                'criticality_class': p.get('criticality_class'),
                'hazmat_class': p.get('hazmat_class'),
                'weight_kg': p.get('weight_kg'),
                'destination': p.get('destination'),
                'leg_id': p.get('leg_id'),
                'status': 'CREATED',
                'checkpoints': []
            }
        elif ev.type == 'cargo.checkpoint':
            cid = p.get('crate_id')
            if cid in crates:
                crates[cid]['status'] = p.get('checkpoint_type')
                crates[cid]['checkpoints'].append({
                    'type': p.get('checkpoint_type'),
                    'location': p.get('location'),
                    'time': ev.created_at
                })
    return crates

@router.get("/crates")
def list_crates(db: Session = Depends(get_db)):
    return list(get_cargo_state(db).values())

@router.post("/crates")
def create_crate(crate: CrateCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    ev = append_event(db, settings.NODE_ID, 'cargo.created', crate.model_dump(), user.username)
    return {"id": ev.id}

@router.get("/crates/{id}")
def get_crate(id: str, db: Session = Depends(get_db)):
    state = get_cargo_state(db)
    if id not in state:
        raise HTTPException(status_code=404, detail="Crate not found")
    return state[id]

@router.post("/checkpoint")
def log_checkpoint(ckpt: CheckpointCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    ev = append_event(db, settings.NODE_ID, 'cargo.checkpoint', ckpt.model_dump(), user.username)
    return {"status": "ok"}

@router.get("/crates/{id}/qr")
def generate_qr_data(id: str, db: Session = Depends(get_db)):
    state = get_cargo_state(db)
    if id not in state:
        raise HTTPException(status_code=404, detail="Crate not found")
    return {"qr_data": json.dumps(state[id])}

@router.get("/overdue")
def list_overdue_crates(db: Session = Depends(get_db)):
    # Mock overdue logic for now
    return []

@router.post("/vessel-position")
def log_vessel_position(vp: VesselPositionCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    ev = append_event(db, settings.NODE_ID, 'vessel.position', vp.model_dump(), user.username)
    return {"status": "ok"}

@router.get("/vessel-positions")
def get_vessel_positions(db: Session = Depends(get_db)):
    events = db.query(Event).filter(Event.type == 'vessel.position').order_by(Event.lamport_clock.asc()).all()
    positions = {}
    for ev in events:
        p = json.loads(ev.payload) if isinstance(ev.payload, str) else ev.payload
        positions[p.get('vessel_name')] = p
    return list(positions.values())
