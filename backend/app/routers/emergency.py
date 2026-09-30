import json
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Event, IncidentCreate, IncidentActionCreate, User
from app.auth import get_current_user
from app.event_store import append_event
from app.config import settings

router = APIRouter(prefix="/api/incidents", tags=["emergency"])

def get_incident_state(db):
    incidents = {}
    events = db.query(Event).filter(
        Event.type.like('incident.%')
    ).order_by(Event.lamport_clock.asc()).all()
    for ev in events:
        p = json.loads(ev.payload) if isinstance(ev.payload, str) else ev.payload
        if ev.type == 'incident.created':
            iid = p.get('incident_id', ev.id)
            incidents[iid] = {
                'id': iid,
                'type': p.get('type'),
                'severity': p.get('severity'),
                'station_id': p.get('station_id'),
                'description': p.get('description'),
                'related_sortie_id': p.get('related_sortie_id'),
                'related_item_id': p.get('related_item_id'),
                'status': 'OPEN',
                'actions': []
            }
        elif ev.type == 'incident.action':
            iid = p.get('incident_id')
            if iid in incidents:
                act = p.get('action_type')
                if act == 'RESOLVED':
                    incidents[iid]['status'] = 'RESOLVED'
                incidents[iid]['actions'].append({
                    'action': act,
                    'notes': p.get('notes'),
                    'time': ev.created_at,
                    'actor': ev.actor
                })
    return incidents

@router.get("")
def list_incidents(db: Session = Depends(get_db)):
    return list(get_incident_state(db).values())

@router.post("")
def create_incident(inc: IncidentCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    ev = append_event(db, settings.NODE_ID, 'incident.created', inc.model_dump(), user.username)
    return {"id": ev.id}

@router.get("/active")
def list_active(db: Session = Depends(get_db)):
    state = get_incident_state(db)
    return [i for i in state.values() if i['status'] != 'RESOLVED']

@router.get("/{id}")
def get_incident(id: str, db: Session = Depends(get_db)):
    state = get_incident_state(db)
    if id not in state:
        raise HTTPException(status_code=404, detail="Incident not found")
    return state[id]

@router.post("/{id}/action")
def log_action(id: str, act: IncidentActionCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    ev = append_event(db, settings.NODE_ID, 'incident.action', act.model_dump(), user.username)
    return {"status": "ok"}

@router.post("/medevac-request")
def request_medevac(inc: IncidentCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    ev = append_event(db, settings.NODE_ID, 'incident.created', inc.model_dump(), user.username)
    ev_act = append_event(db, settings.NODE_ID, 'incident.action', {'incident_id': ev.id, 'action_type': 'MEDEVAC_REQUESTED', 'notes': 'Auto-generated medevac request'}, user.username)
    return {"id": ev.id}
