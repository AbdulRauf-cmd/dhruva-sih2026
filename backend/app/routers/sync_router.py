import httpx
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import SyncPushRequest
from app.config import settings, link_status
from app.services import merge_events, get_unsynced_events, mark_synced

router = APIRouter(prefix="/api/sync", tags=["sync"])

@router.post("/push")
def push_events(req: SyncPushRequest, db: Session = Depends(get_db)):
    if settings.NODE_ROLE != 'hq':
        raise HTTPException(status_code=400, detail="Only HQ can receive push")
    
    # Check link status simulation
    if req.events and req.events[0].get('node_id') in link_status:
        st_id = req.events[0].get('node_id')
        if link_status[st_id] == 'DOWN':
            raise HTTPException(status_code=503, detail="Link is DOWN")

    res = merge_events(db, req.events)
    return res

@router.get("/pull")
def pull_events(after_lamport: int = 0, db: Session = Depends(get_db)):
    if settings.NODE_ROLE != 'hq':
        raise HTTPException(status_code=400, detail="Only HQ can serve pull")
    
    from app.models import Event
    events = db.query(Event).filter(Event.lamport_clock > after_lamport).order_by(Event.lamport_clock.asc()).all()
    out = []
    for ev in events:
        import json
        out.append({
            'id': ev.id,
            'node_id': ev.node_id,
            'type': ev.type,
            'payload': json.loads(ev.payload) if isinstance(ev.payload, str) else ev.payload,
            'actor': ev.actor,
            'created_at': ev.created_at,
            'lamport_clock': ev.lamport_clock,
            'prev_hash': ev.prev_hash,
            'hash': ev.hash
        })
    return {"events": out}

@router.post("/trigger")
def trigger_sync(db: Session = Depends(get_db)):
    if settings.NODE_ROLE == 'hq':
        raise HTTPException(status_code=400, detail="HQ does not trigger sync")
    
    unsynced = get_unsynced_events(db)
    if not unsynced:
        return {"status": "up_to_date"}
        
    out = []
    for ev in unsynced:
        import json
        out.append({
            'id': ev.id,
            'node_id': ev.node_id,
            'type': ev.type,
            'payload': json.loads(ev.payload) if isinstance(ev.payload, str) else ev.payload,
            'actor': ev.actor,
            'created_at': ev.created_at,
            'lamport_clock': ev.lamport_clock,
            'prev_hash': ev.prev_hash,
            'hash': ev.hash
        })

    try:
        resp = httpx.post(f"{settings.HQ_URL}/api/sync/push", json={"events": out})
        if resp.status_code != 200:
            raise HTTPException(status_code=resp.status_code, detail="Push failed")
            
        mark_synced(db, [e.id for e in unsynced])
        
        # Then pull (simplified)
        last_ev = db.query(Event).order_by(Event.lamport_clock.desc()).first()
        lam = last_ev.lamport_clock if last_ev else 0
        pull_resp = httpx.get(f"{settings.HQ_URL}/api/sync/pull?after_lamport={lam}")
        if pull_resp.status_code == 200:
            merge_events(db, pull_resp.json().get('events', []))
            
        return {"pushed": len(unsynced), "pulled": len(pull_resp.json().get('events', []))}
    except Exception as e:
        raise HTTPException(status_code=503, detail=str(e))

@router.get("/status")
def sync_status(db: Session = Depends(get_db)):
    unsynced = get_unsynced_events(db)
    return {
        "pending_count": len(unsynced),
        "link_state": settings.LINK_STATUS
    }

@router.get("/pending")
def pending_events(db: Session = Depends(get_db)):
    return get_unsynced_events(db)
