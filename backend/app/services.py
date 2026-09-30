import json
from datetime import datetime, timezone, timedelta
from app.models import Event, MarginResult
from app.event_store import append_event

CRITICALITY_WEIGHTS = {'C1': 3.0, 'C2': 2.0, 'C3': 1.0}

IMDG_COMPATIBILITY = {
    ('flammable_liquid', 'oxidizer'): False,
    ('flammable_gas', 'oxidizer'): False,
    ('flammable_liquid', 'flammable_gas'): True,
}

# --- Inventory State Derivation ---
def get_item_state(db, station_id, item_id=None):
    items = {}
    events = db.query(Event).filter(
        Event.type.like('inventory.%'),
        Event.node_id == station_id
    ).order_by(Event.lamport_clock.asc()).all()
    
    for event in events:
        payload = json.loads(event.payload) if isinstance(event.payload, str) else event.payload
        eid = payload.get('item_id', '')
        
        if event.type == 'inventory.created':
            items[eid] = {
                'item_id': eid,
                'name': payload['name'],
                'category': payload['category'],
                'criticality_class': payload['criticality_class'],
                'location_bay': payload.get('location_bay', ''),
                'batch': payload.get('batch', ''),
                'expiry_date': payload.get('expiry_date'),
                'quantity': payload.get('quantity', 0),
                'unit': payload.get('unit', 'units'),
                'planned_daily_rate': payload.get('planned_daily_rate', 0),
                'last_count_date': event.created_at,
            }
        elif event.type == 'inventory.added':
            if eid in items:
                items[eid]['quantity'] += payload.get('quantity', 0)
        elif event.type == 'inventory.consumed':
            if eid in items:
                items[eid]['quantity'] -= payload.get('quantity', 0)
                items[eid]['quantity'] = max(0, items[eid]['quantity'])
        elif event.type == 'inventory.adjustment':
            if eid in items:
                items[eid]['quantity'] = payload.get('counted_quantity', items[eid]['quantity'])
                items[eid]['last_count_date'] = event.created_at
        elif event.type == 'inventory.cargo_received':
            if eid in items:
                items[eid]['quantity'] += payload.get('quantity', 0)
            else:
                items[eid] = {
                    'item_id': eid,
                    'name': payload.get('name', 'Unknown'),
                    'category': payload.get('category', 'general'),
                    'criticality_class': payload.get('criticality_class', 'C3'),
                    'quantity': payload.get('quantity', 0),
                    'unit': payload.get('unit', 'units'),
                    'planned_daily_rate': payload.get('planned_daily_rate', 0),
                    'last_count_date': event.created_at,
                }
    
    if item_id:
        return items.get(item_id)
    return items

def get_recent_consumption(db, station_id, item_id, days=14):
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    events = db.query(Event).filter(
        Event.type == 'inventory.consumed',
        Event.node_id == station_id
    ).order_by(Event.lamport_clock.asc()).all()
    
    total = 0
    for event in events:
        try:
            ev_date = datetime.fromisoformat(event.created_at)
        except:
            continue
        if ev_date.replace(tzinfo=timezone.utc) >= cutoff:
            payload = json.loads(event.payload) if isinstance(event.payload, str) else event.payload
            if payload.get('item_id') == item_id:
                total += payload.get('quantity', 0)
    return total / days if days > 0 else 0

def get_next_resupply_date(db, station_id):
    events = db.query(Event).filter(
        Event.type.like('leg.%')
    ).order_by(Event.lamport_clock.asc()).all()
    
    legs = {}
    for event in events:
        payload = json.loads(event.payload) if isinstance(event.payload, str) else event.payload
        if event.type == 'leg.created':
            lid = payload.get('leg_id', event.id)
            if payload.get('to_location') == station_id:
                legs[lid] = payload
        elif event.type == 'leg.delayed':
            lid = payload.get('leg_id')
            if lid in legs:
                delay = payload.get('delay_days', 0)
                end_date = datetime.fromisoformat(legs[lid]['end_date'])
                legs[lid]['end_date'] = (end_date + timedelta(days=delay)).isoformat()
                
    now = datetime.now(timezone.utc)
    future_legs = []
    for lid, leg in legs.items():
        ed = datetime.fromisoformat(leg['end_date'])
        if ed.tzinfo is None:
            ed = ed.replace(tzinfo=timezone.utc)
        if ed > now:
            future_legs.append(ed)
    
    if future_legs:
        return min(future_legs)
    return None

def compute_survival_margin(db, station_id: str, item_id: str) -> MarginResult:
    item = get_item_state(db, station_id, item_id)
    if not item:
        raise ValueError("Item not found")
        
    avg_daily_consumption = get_recent_consumption(db, station_id, item_id)
    if avg_daily_consumption <= 0:
        avg_daily_consumption = item.get('planned_daily_rate', 0)
        
    safety_factors = {'C1': 1.5, 'C2': 1.25, 'C3': 1.0}
    sf = safety_factors.get(item['criticality_class'], 1.0)
    
    if avg_daily_consumption > 0:
        days_of_stock = item['quantity'] / (avg_daily_consumption * sf)
    else:
        days_of_stock = float('inf')
        
    resupply_date = get_next_resupply_date(db, station_id)
    now = datetime.now(timezone.utc)
    days_to_resupply = None
    if resupply_date:
        days_to_resupply = (resupply_date - now).days
        survival_margin = days_of_stock - days_to_resupply
    else:
        survival_margin = days_of_stock
        
    tier = 'BLACK'
    if not resupply_date and days_of_stock < 30:
        tier = 'BLACK'
    elif survival_margin < 0:
        tier = 'BLACK'
    elif survival_margin < 10:
        tier = 'RED'
    elif survival_margin < 30:
        tier = 'AMBER'
    else:
        tier = 'GREEN'
        
    try:
        lcd = datetime.fromisoformat(item['last_count_date'])
        if lcd.tzinfo is None: lcd = lcd.replace(tzinfo=timezone.utc)
        data_age_days = (now - lcd).days
    except:
        data_age_days = 0

    alert_text = None
    if tier in ['RED', 'BLACK'] and resupply_date:
        out_days = int(abs(survival_margin))
        alert_text = f"{item['name']} at {station_id} runs out {out_days} days before next ship arrives."
    elif tier == 'BLACK' and not resupply_date:
        alert_text = f"{item['name']} at {station_id} is running critically low with no resupply scheduled."

    return MarginResult(
        item_id=item['item_id'],
        item_name=item['name'],
        station_id=station_id,
        quantity=item['quantity'],
        avg_daily_consumption=avg_daily_consumption,
        safety_factor=sf,
        days_of_stock=days_of_stock,
        days_to_resupply=days_to_resupply,
        survival_margin=survival_margin if resupply_date else None,
        tier=tier,
        resupply_date=resupply_date.isoformat() if resupply_date else None,
        data_age_days=data_age_days,
        criticality_class=item['criticality_class'],
        unit=item['unit'],
        alert_text=alert_text
    )

def check_hazmat_conflicts(crates: list) -> list:
    conflicts = []
    for i, c1 in enumerate(crates):
        for c2 in crates[i+1:]:
            if c1.get('hazmat_class') and c2.get('hazmat_class'):
                pair = tuple(sorted([c1['hazmat_class'], c2['hazmat_class']]))
                if pair in IMDG_COMPATIBILITY and not IMDG_COMPATIBILITY[pair]:
                    conflicts.append({
                        'crate1': c1.get('crate_id'),
                        'crate2': c2.get('crate_id'),
                        'hazmat1': c1['hazmat_class'],
                        'hazmat2': c2['hazmat_class'],
                        'reason': f"{c1['hazmat_class']} incompatible with {c2['hazmat_class']}"
                    })
    return conflicts

def rank_manifest(db, leg_id: str, station_id: str) -> list:
    # 1. Get all crates
    crates = {}
    events = db.query(Event).filter(Event.type.like('cargo.%')).order_by(Event.lamport_clock.asc()).all()
    for ev in events:
        p = json.loads(ev.payload) if isinstance(ev.payload, str) else ev.payload
        if ev.type == 'cargo.created':
            crates[ev.id] = {
                'crate_id': ev.id,
                'contents': p.get('contents'),
                'criticality_class': p.get('criticality_class', 'C3'),
                'hazmat_class': p.get('hazmat_class'),
                'weight_kg': p.get('weight_kg'),
                'destination': p.get('destination'),
                'leg_id': p.get('leg_id')
            }
        elif ev.type == 'cargo.leg_assigned':
            cid = p.get('crate_id')
            if cid in crates:
                crates[cid]['leg_id'] = p.get('leg_id')
                
    leg_crates = [c for c in crates.values() if c.get('leg_id') == leg_id]
    
    for c in leg_crates:
        w = CRITICALITY_WEIGHTS.get(c['criticality_class'], 1.0)
        c['score'] = w * 10
        
    leg_crates.sort(key=lambda x: x['score'], reverse=True)
    for i, c in enumerate(leg_crates):
        c['rank'] = i + 1
    return leg_crates

ESCALATION_LEVELS = [
    {'level': 'WARNING', 'delay_minutes': 15, 'notify': 'sortie_members'},
    {'level': 'ALERT', 'delay_minutes': 30, 'notify': 'station_lead'},
    {'level': 'EMERGENCY', 'delay_minutes': 60, 'notify': 'all'},
]

DEMO_ESCALATION_LEVELS = [
    {'level': 'WARNING', 'delay_minutes': 0.25, 'notify': 'sortie_members'},
    {'level': 'ALERT', 'delay_minutes': 0.5, 'notify': 'station_lead'},  
    {'level': 'EMERGENCY', 'delay_minutes': 1.0, 'notify': 'all'},
]

def get_active_sorties(db):
    sorties = {}
    events = db.query(Event).filter(
        Event.type.like('sortie.%')
    ).order_by(Event.lamport_clock.asc()).all()
    
    for event in events:
        payload = json.loads(event.payload) if isinstance(event.payload, str) else event.payload
        sid = payload.get('sortie_id', event.id if event.type == 'sortie.created' else '')
        
        if event.type == 'sortie.created':
            sorties[sid] = {
                'sortie_id': sid,
                'name': payload.get('name'),
                'members': payload.get('members', []),
                'route': payload.get('route', ''),
                'expected_return': payload.get('expected_return'),
                'checkin_interval_minutes': payload.get('checkin_interval_minutes', 30),
                'status': 'ACTIVE',
                'station_id': event.node_id,
                'created_at': event.created_at,
                'last_checkin': event.created_at,
                'checkins': [],
                'escalation_level': None,
            }
        elif event.type == 'sortie.checkin':
            if sid in sorties:
                sorties[sid]['last_checkin'] = event.created_at
                sorties[sid]['checkins'].append(event.created_at)
        elif event.type == 'sortie.completed':
            if sid in sorties:
                sorties[sid]['status'] = 'COMPLETED'
        elif event.type == 'sortie.escalation':
            if sid in sorties:
                sorties[sid]['escalation_level'] = payload.get('level')
    
    return {k: v for k, v in sorties.items() if v['status'] == 'ACTIVE'}

def check_overdue_sorties(db, demo_mode=False):
    levels = DEMO_ESCALATION_LEVELS if demo_mode else ESCALATION_LEVELS
    active = get_active_sorties(db)
    now = datetime.now(timezone.utc)
    alerts = []
    
    for sid, sortie in active.items():
        try:
            lc = datetime.fromisoformat(sortie['last_checkin'])
            if lc.tzinfo is None: lc = lc.replace(tzinfo=timezone.utc)
        except:
            continue
            
        interval_mins = sortie.get('checkin_interval_minutes', 30)
        minutes_since = (now - lc).total_seconds() / 60.0
        
        overdue_by = minutes_since - interval_mins
        if overdue_by > 0:
            target_level = None
            for lvl in reversed(levels):
                if overdue_by >= lvl['delay_minutes']:
                    target_level = lvl['level']
                    break
                    
            if target_level and target_level != sortie['escalation_level']:
                append_event(db, sortie['station_id'], 'sortie.escalation', {
                    'sortie_id': sid,
                    'level': target_level,
                    'overdue_minutes': overdue_by
                }, 'system')
                alerts.append({'sortie_id': sid, 'level': target_level})
                
    return alerts

def merge_events(db, incoming_events: list) -> dict:
    merged = 0
    skipped = 0
    for ev_data in incoming_events:
        existing = db.query(Event).filter(Event.id == ev_data['id']).first()
        if existing:
            skipped += 1
            continue
        event = Event(
            id=ev_data['id'],
            node_id=ev_data['node_id'],
            type=ev_data['type'],
            payload=ev_data['payload'] if isinstance(ev_data['payload'], str) else json.dumps(ev_data['payload']),
            actor=ev_data['actor'],
            created_at=ev_data['created_at'],
            lamport_clock=ev_data['lamport_clock'],
            prev_hash=ev_data['prev_hash'],
            hash=ev_data['hash'],
            synced=True
        )
        db.add(event)
        merged += 1
    db.commit()
    return {'merged': merged, 'skipped': skipped}

def get_unsynced_events(db) -> list:
    return db.query(Event).filter(Event.synced == False).order_by(Event.lamport_clock.asc()).all()

def mark_synced(db, event_ids: list):
    db.query(Event).filter(Event.id.in_(event_ids)).update({Event.synced: True}, synchronize_session=False)
    db.commit()
