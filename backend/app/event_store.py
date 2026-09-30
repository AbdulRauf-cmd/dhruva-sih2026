import hashlib
import json
import uuid
from datetime import datetime, timezone
from app.models import Event

_lamport_clock = 0

def _canonical_json(data: dict) -> str:
    return json.dumps(data, sort_keys=True, default=str)

def compute_hash(prev_hash: str, event_data: dict) -> str:
    canonical = prev_hash + _canonical_json(event_data)
    return hashlib.sha256(canonical.encode('utf-8')).hexdigest()

def get_last_event(db):
    return db.query(Event).order_by(Event.lamport_clock.desc()).first()

def append_event(db, node_id, event_type, payload, actor) -> Event:
    global _lamport_clock
    last = get_last_event(db)
    if last:
        _lamport_clock = max(_lamport_clock, last.lamport_clock) + 1
        prev_hash = last.hash
    else:
        _lamport_clock += 1 
        prev_hash = '0' * 64
    
    now_iso = datetime.now(timezone.utc).isoformat()
    
    event_data = {
        'node_id': node_id,
        'type': event_type,
        'payload': payload,
        'actor': actor,
        'created_at': now_iso,
        'lamport_clock': _lamport_clock
    }
    
    event_hash = compute_hash(prev_hash, event_data)
    
    event = Event(
        id=str(uuid.uuid4()),
        node_id=node_id,
        type=event_type,
        payload=json.dumps(payload),
        actor=actor,
        created_at=now_iso,
        lamport_clock=_lamport_clock,
        prev_hash=prev_hash,
        hash=event_hash,
        synced=(node_id == 'hq')
    )
    db.add(event)
    db.commit()
    db.refresh(event)
    return event

def verify_chain(db) -> dict:
    events = db.query(Event).order_by(Event.lamport_clock.asc()).all()
    if not events:
        return {'valid': True, 'total_events': 0, 'broken_at': None, 'first_bad_event': None}
    
    for i, event in enumerate(events):
        expected_prev = events[i-1].hash if i > 0 else '0' * 64
        if event.prev_hash != expected_prev:
            return {'valid': False, 'total_events': len(events), 'broken_at': i, 'first_bad_event': event.id, 'expected_prev_hash': expected_prev, 'actual_prev_hash': event.prev_hash}
        
        event_data = {
            'node_id': event.node_id,
            'type': event.type,
            'payload': json.loads(event.payload) if isinstance(event.payload, str) else event.payload,
            'actor': event.actor,
            'created_at': event.created_at,
            'lamport_clock': event.lamport_clock
        }
        expected_hash = compute_hash(expected_prev, event_data)
        if event.hash != expected_hash:
            return {'valid': False, 'total_events': len(events), 'broken_at': i, 'first_bad_event': event.id, 'reason': 'hash_mismatch', 'expected_hash': expected_hash, 'actual_hash': event.hash}
    
    return {'valid': True, 'total_events': len(events), 'broken_at': None, 'first_bad_event': None}
