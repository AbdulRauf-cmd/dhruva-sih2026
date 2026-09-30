import uuid
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Event, InventoryItemCreate, ConsumptionCreate, StockCountCreate, User
from app.auth import get_current_user
from app.event_store import append_event
from app.config import settings
from app.services import get_item_state, compute_survival_margin
from datetime import datetime, timezone, timedelta

router = APIRouter(prefix="/api/inventory", tags=["inventory"])


@router.get("")
def list_inventory(station_id: str = Query(default=None), db: Session = Depends(get_db)):
    sid = station_id or (settings.NODE_ID if settings.NODE_ID != 'hq' else 'maitri')
    items = get_item_state(db, sid)
    return list(items.values())


@router.get("/{station_id}")
def list_inventory_station(station_id: str, db: Session = Depends(get_db)):
    items = get_item_state(db, station_id)
    return list(items.values())


@router.post("/items")
def create_item(item: InventoryItemCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    data = item.model_dump()
    data['item_id'] = str(uuid.uuid4())
    node = settings.NODE_ID if settings.NODE_ID != 'hq' else 'maitri'
    ev = append_event(db, node, 'inventory.created', data, user.username)
    return {"status": "ok", "item_id": data['item_id'], "event_id": ev.id}


@router.post("/consume")
def log_consumption(cons: ConsumptionCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    node = settings.NODE_ID if settings.NODE_ID != 'hq' else 'maitri'
    ev = append_event(db, node, 'inventory.consumed', cons.model_dump(), user.username)
    return {"status": "ok", "event_id": ev.id}


@router.post("/count")
def log_count(count: StockCountCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    node = settings.NODE_ID if settings.NODE_ID != 'hq' else 'maitri'
    ev = append_event(db, node, 'inventory.adjustment', count.model_dump(), user.username)
    return {"status": "ok", "event_id": ev.id}


@router.get("/expiring")
def get_expiring(station_id: str = Query(default=None), db: Session = Depends(get_db)):
    sid = station_id or (settings.NODE_ID if settings.NODE_ID != 'hq' else 'maitri')
    items = get_item_state(db, sid)
    expiring = []
    now = datetime.now(timezone.utc)
    for it in items.values():
        if it.get('expiry_date'):
            try:
                ed = datetime.fromisoformat(it['expiry_date'])
                if ed.tzinfo is None:
                    ed = ed.replace(tzinfo=timezone.utc)
                days_left = (ed - now).days
                if days_left <= 30:
                    it['days_until_expiry'] = days_left
                    expiring.append(it)
            except Exception:
                pass
    return expiring


@router.get("/margins")
def get_all_margins(station_id: str = Query(default=None), db: Session = Depends(get_db)):
    sid = station_id or (settings.NODE_ID if settings.NODE_ID != 'hq' else 'maitri')
    items = get_item_state(db, sid)
    margins = []
    for it in items.values():
        try:
            m = compute_survival_margin(db, sid, it['item_id'])
            margins.append(m.model_dump())
        except Exception:
            pass
    return margins


@router.get("/margins/{item_id}")
def get_item_margin(item_id: str, station_id: str = Query(default=None), db: Session = Depends(get_db)):
    sid = station_id or (settings.NODE_ID if settings.NODE_ID != 'hq' else 'maitri')
    m = compute_survival_margin(db, sid, item_id)
    return m.model_dump()
