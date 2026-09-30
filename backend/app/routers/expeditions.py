import json
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Event, ExpeditionCreate, LegCreate, User
from app.auth import get_current_user
from app.event_store import append_event
from app.config import settings

router = APIRouter(prefix="/api", tags=["expeditions"])

def get_expeditions_state(db):
    expeditions = {}
    events = db.query(Event).filter(
        Event.type.like('expedition.%') | Event.type.like('leg.%')
    ).order_by(Event.lamport_clock.asc()).all()
    for event in events:
        payload = json.loads(event.payload) if isinstance(event.payload, str) else event.payload
        if event.type == 'expedition.created':
            eid = payload.get('expedition_id', event.id)
            expeditions[eid] = {
                'id': eid,
                'name': payload['name'],
                'year': payload.get('year'),
                'description': payload.get('description', ''),
                'legs': [],
            }
        elif event.type == 'leg.created':
            eid = payload.get('expedition_id')
            if eid in expeditions:
                leg = {
                    'id': payload.get('leg_id', event.id),
                    'expedition_id': eid,
                    'from_location': payload['from_location'],
                    'to_location': payload['to_location'],
                    'vessel': payload.get('vessel', ''),
                    'start_date': payload['start_date'],
                    'end_date': payload['end_date'],
                    'capacity_tonnes': payload.get('capacity_tonnes', 0),
                    'capacity_m3': payload.get('capacity_m3', 0),
                    'assigned_cargo': [],
                    'assigned_personnel': [],
                }
                expeditions[eid]['legs'].append(leg)
        elif event.type == 'leg.delayed':
            leg_id = payload.get('leg_id')
            delay_days = payload.get('delay_days', 0)
            for exp in expeditions.values():
                for leg in exp['legs']:
                    if leg['id'] == leg_id:
                        from datetime import datetime, timedelta
                        start = datetime.fromisoformat(leg['start_date'])
                        end = datetime.fromisoformat(leg['end_date'])
                        leg['start_date'] = (start + timedelta(days=delay_days)).isoformat()
                        leg['end_date'] = (end + timedelta(days=delay_days)).isoformat()
    return expeditions

@router.get("/expeditions")
def list_expeditions(db: Session = Depends(get_db)):
    return list(get_expeditions_state(db).values())

@router.post("/expeditions")
def create_expedition(exp: ExpeditionCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    ev = append_event(db, settings.NODE_ID, 'expedition.created', exp.model_dump(), user.username)
    return {"id": ev.id}

@router.get("/expeditions/{id}")
def get_expedition(id: str, db: Session = Depends(get_db)):
    state = get_expeditions_state(db)
    if id not in state:
        raise HTTPException(status_code=404, detail="Expedition not found")
    return state[id]

@router.post("/expeditions/{id}/legs")
def create_leg(id: str, leg: LegCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    data = leg.model_dump()
    data['expedition_id'] = id
    ev = append_event(db, settings.NODE_ID, 'leg.created', data, user.username)
    return {"id": ev.id}

@router.get("/expeditions/{id}/legs")
def list_legs(id: str, db: Session = Depends(get_db)):
    state = get_expeditions_state(db)
    if id not in state:
        raise HTTPException(status_code=404, detail="Expedition not found")
    return state[id]['legs']

@router.post("/legs/{id}/delay")
def delay_leg(id: str, delay_days: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    ev = append_event(db, settings.NODE_ID, 'leg.delayed', {'leg_id': id, 'delay_days': delay_days}, user.username)
    return {"status": "ok"}

from app.services import rank_manifest, check_hazmat_conflicts

@router.get("/legs/{id}/manifest")
def get_manifest(id: str, station_id: str, db: Session = Depends(get_db)):
    return rank_manifest(db, id, station_id)

@router.post("/legs/{id}/assign-cargo")
def assign_cargo(id: str, crate_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    ev = append_event(db, settings.NODE_ID, 'cargo.leg_assigned', {'crate_id': crate_id, 'leg_id': id}, user.username)
    return {"status": "ok"}

@router.post("/legs/{id}/assign-personnel")
def assign_personnel(id: str, person_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    ev = append_event(db, settings.NODE_ID, 'personnel.leg_assigned', {'person_id': person_id, 'leg_id': id}, user.username)
    return {"status": "ok"}

@router.get("/legs/{id}/validate")
def validate_leg(id: str, db: Session = Depends(get_db)):
    # Simple validation using check_hazmat_conflicts
    # We would fetch assigned crates here
    # For now returning mock
    return {"valid": True, "conflicts": []}
