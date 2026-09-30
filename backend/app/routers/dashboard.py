import json
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Event
from app.services import get_item_state, compute_survival_margin, get_active_sorties
from app.event_store import verify_chain
from app.config import settings, link_status

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


@router.get("/summary")
def get_dashboard_summary(db: Session = Depends(get_db)):
    stations = ['maitri', 'bharati']
    all_margins = {}
    alerts = []
    total_items = 0
    alert_count = 0

    for sid in stations:
        items = get_item_state(db, sid)
        total_items += len(items)
        margins = []
        for it in items.values():
            try:
                m = compute_survival_margin(db, sid, it['item_id'])
                md = m.model_dump()
                md['days_of_stock'] = round(md['days_of_stock'], 1)
                if md['survival_margin'] is not None:
                    md['survival_margin'] = round(md['survival_margin'], 1)
                margins.append(md)
                if md['tier'] in ('RED', 'BLACK'):
                    alert_count += 1
                    if md.get('alert_text'):
                        alerts.append({'tier': md['tier'], 'text': md['alert_text'], 'station': sid})
            except Exception:
                pass
        all_margins[sid] = margins

    # Count expeditions
    exp_events = db.query(Event).filter(Event.type == 'expedition.created').count()

    # Count cargo crates
    crate_count = db.query(Event).filter(Event.type == 'cargo.created').count()

    # Count personnel
    personnel_count = db.query(Event).filter(Event.type == 'personnel.created').count()

    # Count active incidents
    incident_events = db.query(Event).filter(Event.type.like('incident.%')).order_by(Event.lamport_clock.asc()).all()
    incidents = {}
    for ev in incident_events:
        payload = json.loads(ev.payload) if isinstance(ev.payload, str) else ev.payload
        if ev.type == 'incident.created':
            iid = payload.get('incident_id', ev.id)
            incidents[iid] = {'status': 'OPEN', 'type': payload.get('type'), 'severity': payload.get('severity')}
        elif ev.type == 'incident.action':
            iid = payload.get('incident_id')
            if iid in incidents:
                action = payload.get('action_type', '')
                if action == 'RESOLVED':
                    incidents[iid]['status'] = 'RESOLVED'
                else:
                    incidents[iid]['status'] = action
    active_incidents = sum(1 for inc in incidents.values() if inc['status'] != 'RESOLVED')

    # Get active sorties
    sorties = get_active_sorties(db)
    sortie_list = []
    for sid, s in sorties.items():
        sortie_list.append({
            'id': sid,
            'name': s.get('name', 'Unknown'),
            'expected_return': s.get('expected_return', ''),
            'escalation_level': s.get('escalation_level', 'NORMAL'),
            'station_id': s.get('station_id', ''),
            'members': len(s.get('members', [])),
        })

    # Audit chain
    chain = verify_chain(db)

    # Sync status
    sync_status = {}
    for st in stations:
        unsynced = db.query(Event).filter(Event.synced == False, Event.node_id == st).count()
        sync_status[st] = {
            'link': link_status.get(st, 'UP'),
            'pending': unsynced,
            'last_sync': 'Never' if unsynced > 0 else 'Up to date',
        }

    # Get next leg date
    leg_events = db.query(Event).filter(Event.type == 'leg.created').all()
    next_leg = 'N/A'
    for ev in leg_events:
        payload = json.loads(ev.payload) if isinstance(ev.payload, str) else ev.payload
        sd = payload.get('start_date', '')
        if sd:
            next_leg = sd[:10]
            break

    return {
        'margins': all_margins,
        'active_alerts': alerts,
        'overdue_cargo_count': 0,
        'active_sorties': len(sorties),
        'sorties': sortie_list,
        'audit_chain': chain,
        'sync_status': sync_status,
        'stats': {
            'expeditions': exp_events,
            'next_leg_date': next_leg,
            'crates_total': crate_count,
            'crates_overdue': 0,
            'inventory_items': total_items,
            'inventory_alerts': alert_count,
            'personnel_total': personnel_count,
            'personnel_on_station': personnel_count,
            'active_incidents': active_incidents,
        }
    }
