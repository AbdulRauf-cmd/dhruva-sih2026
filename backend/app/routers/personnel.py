import json
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Event, PersonnelCreate, MovementCreate, SortieCreate, CheckInCreate, User
from app.auth import get_current_user
from app.event_store import append_event
from app.config import settings
from app.services import get_active_sorties, check_overdue_sorties

router = APIRouter(prefix="/api/personnel", tags=["personnel"])

def get_personnel_state(db):
    people = {}
    events = db.query(Event).filter(
        Event.type.like('personnel.%')
    ).order_by(Event.lamport_clock.asc()).all()
    for ev in events:
        p = json.loads(ev.payload) if isinstance(ev.payload, str) else ev.payload
        if ev.type == 'personnel.created':
            pid = p.get('person_id', ev.id)
            people[pid] = {
                'id': pid,
                'name': p.get('name'),
                'role': p.get('role'),
                'station_id': p.get('station_id'),
                'medical_clearance': p.get('medical_clearance'),
                'location': p.get('station_id') or 'transit',
                'movements': []
            }
        elif ev.type == 'personnel.movement':
            pid = p.get('person_id')
            if pid in people:
                people[pid]['location'] = p.get('to_location')
                people[pid]['movements'].append({
                    'from': p.get('from_location'),
                    'to': p.get('to_location'),
                    'type': p.get('movement_type'),
                    'time': ev.created_at
                })
    return people

@router.get("")
def list_personnel(db: Session = Depends(get_db)):
    return list(get_personnel_state(db).values())

@router.post("")
def create_personnel(person: PersonnelCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    ev = append_event(db, settings.NODE_ID, 'personnel.created', person.model_dump(), user.username)
    return {"id": ev.id}

@router.get("/{id}")
def get_person(id: str, db: Session = Depends(get_db)):
    state = get_personnel_state(db)
    if id not in state:
        raise HTTPException(status_code=404, detail="Person not found")
    return state[id]

@router.post("/movement")
def log_movement(mov: MovementCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    ev = append_event(db, settings.NODE_ID, 'personnel.movement', mov.model_dump(), user.username)
    return {"status": "ok"}

@router.get("/where-now")
def where_now(db: Session = Depends(get_db)):
    state = get_personnel_state(db)
    by_loc = {}
    for p in state.values():
        loc = p['location']
        if loc not in by_loc:
            by_loc[loc] = []
        by_loc[loc].append(p)
    return by_loc

@router.post("/sorties")
def create_sortie(sortie: SortieCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    ev = append_event(db, settings.NODE_ID, 'sortie.created', sortie.model_dump(), user.username)
    return {"id": ev.id}

@router.get("/sorties")
def list_sorties(db: Session = Depends(get_db)):
    return list(get_active_sorties(db).values())

@router.get("/sorties/{id}")
def get_sortie(id: str, db: Session = Depends(get_db)):
    sorties = get_active_sorties(db)
    if id not in sorties:
        raise HTTPException(status_code=404, detail="Sortie not found or not active")
    return sorties[id]

@router.post("/sorties/{id}/checkin")
def checkin_sortie(id: str, ci: CheckInCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    ev = append_event(db, settings.NODE_ID, 'sortie.checkin', ci.model_dump(), user.username)
    return {"status": "ok"}

@router.post("/sorties/{id}/complete")
def complete_sortie(id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    ev = append_event(db, settings.NODE_ID, 'sortie.completed', {'sortie_id': id}, user.username)
    return {"status": "ok"}

@router.get("/sorties/check-escalations")
def trigger_escalations(db: Session = Depends(get_db)):
    alerts = check_overdue_sorties(db, demo_mode=settings.DEMO_MODE)
    return {"alerts": alerts}
