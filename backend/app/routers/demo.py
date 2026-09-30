import uuid
import json
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.config import settings, link_status
from app.event_store import append_event, verify_chain
from app.models import Event
from app.services import (
    get_item_state, compute_survival_margin, get_active_sorties,
    check_overdue_sorties, check_hazmat_conflicts, merge_events, get_unsynced_events
)

router = APIRouter(prefix="/api/demo", tags=["demo"])

demo_state = {
    'current_step': 0,
    'completed_steps': [],
    'results': {}
}


@router.post("/step/{step_number}")
def run_demo_step(step_number: int, db: Session = Depends(get_db)):
    result = {}

    if step_number == 1:
        # ── Step 1: View Command Console ──
        stations = ['maitri', 'bharati']
        all_margins = {}
        alerts = []
        for sid in stations:
            items = get_item_state(db, sid)
            margins = []
            for it in items.values():
                try:
                    m = compute_survival_margin(db, sid, it['item_id'])
                    md = m.model_dump()
                    md['days_of_stock'] = round(md['days_of_stock'], 1)
                    margins.append(md)
                    if md['tier'] in ('RED', 'BLACK') and md.get('alert_text'):
                        alerts.append({'tier': md['tier'], 'text': md['alert_text'], 'station': sid})
                except Exception:
                    pass
            all_margins[sid] = margins

        total_events = db.query(Event).count()
        chain = verify_chain(db)
        sorties = get_active_sorties(db)

        result = {
            'margins': all_margins,
            'alerts': alerts,
            'total_events': total_events,
            'chain_status': chain,
            'active_sorties': len(sorties),
            'description': 'Dashboard loaded. See survival margin heatmap and alerts below.'
        }

    elif step_number == 2:
        # ── Step 2: Delay ship leg by 7 days ──
        # Find leg 2 (Cape Town → Maitri)
        events = db.query(Event).filter(Event.type == 'leg.created').order_by(Event.lamport_clock.asc()).all()
        target_leg = None
        for ev in events:
            payload = json.loads(ev.payload) if isinstance(ev.payload, str) else ev.payload
            if payload.get('to_location') in ('Maitri', 'maitri'):
                target_leg = payload
                break

        if not target_leg:
            return {"error": "Leg to Maitri not found. Run seed data first."}

        # Compute BEFORE margins
        before_margins = []
        items = get_item_state(db, 'maitri')
        for it in items.values():
            try:
                m = compute_survival_margin(db, 'maitri', it['item_id'])
                before_margins.append(m.model_dump())
            except Exception:
                pass

        # Apply delay
        leg_id = target_leg['leg_id']
        append_event(db, settings.NODE_ID, 'leg.delayed', {
            'leg_id': leg_id,
            'delay_days': 7,
            'reason': 'Weather delay at Cape Town port'
        }, 'admin')

        # Compute AFTER margins
        after_margins = []
        for it in items.values():
            try:
                m = compute_survival_margin(db, 'maitri', it['item_id'])
                after_margins.append(m.model_dump())
            except Exception:
                pass

        # Find items that changed tier
        tier_changes = []
        before_map = {m['item_id']: m for m in before_margins}
        for am in after_margins:
            bm = before_map.get(am['item_id'])
            if bm and bm['tier'] != am['tier']:
                tier_changes.append({
                    'item': am['item_name'],
                    'before': bm['tier'],
                    'after': am['tier'],
                    'alert': am.get('alert_text', '')
                })

        result = {
            'delayed_leg': f"{target_leg['from_location']} → {target_leg['to_location']}",
            'delay_days': 7,
            'before_margins': before_margins,
            'after_margins': after_margins,
            'tier_changes': tier_changes,
            'description': f"Leg delayed by 7 days. {len(tier_changes)} items changed tier."
        }

    elif step_number == 3:
        # ── Step 3: Set Maitri link DOWN ──
        link_status['maitri'] = 'DOWN'
        result = {
            'station': 'maitri',
            'link_status': 'DOWN',
            'description': 'Maitri link set to DOWN. Station operates offline. Sync blocked.'
        }

    elif step_number == 4:
        # ── Step 4: Simulate offline operations ──
        actions_done = []

        # 4a. Log diesel consumption
        items = get_item_state(db, 'maitri')
        diesel_item = None
        for it in items.values():
            if 'diesel' in it['name'].lower() and it['category'] == 'fuel':
                diesel_item = it
                break
        if diesel_item:
            append_event(db, 'maitri', 'inventory.consumed', {
                'item_id': diesel_item['item_id'],
                'quantity': 50,
                'notes': 'Daily generator usage (offline)',
            }, 'maitri_lead')
            actions_done.append('Consumed 50L diesel (offline)')

        # 4b. Scan a crate as STORED
        crate_events = db.query(Event).filter(Event.type == 'cargo.created').all()
        if crate_events:
            sample_payload = json.loads(crate_events[0].payload) if isinstance(crate_events[0].payload, str) else crate_events[0].payload
            crate_id = sample_payload.get('crate_id', crate_events[0].id)
            append_event(db, 'maitri', 'cargo.checkpoint', {
                'crate_id': crate_id,
                'checkpoint_type': 'STORED',
                'location': 'Station Maitri, Bay A1',
                'condition_note': 'Scanned offline — intact',
            }, 'maitri_lead')
            actions_done.append(f'Scanned crate as STORED at Maitri')

        # 4c. Create a buddy sortie
        p_items = get_all_personnel(db)
        member_ids = [p['person_id'] for p in p_items.values() if p.get('station_id') == 'maitri'][:2]
        sortie_id = str(uuid.uuid4())
        if len(member_ids) >= 2:
            append_event(db, 'maitri', 'sortie.created', {
                'sortie_id': sortie_id,
                'name': 'Ice Core Sampling Sortie',
                'members': member_ids,
                'route': 'Maitri → Sample Point Alpha → Return',
                'expected_return_hours': 4,
                'checkin_interval_minutes': 1,  # 1 minute for demo
            }, 'maitri_lead')
            actions_done.append(f'Created sortie: Ice Core Sampling (check-in every 1 min)')

        # 4d. Trigger escalation check (simulating missed check-in)
        escalation_alerts = check_overdue_sorties(db, demo_mode=True)
        if escalation_alerts:
            actions_done.append(f'Escalation: {len(escalation_alerts)} alerts triggered')

            # Auto-create incident for EMERGENCY level
            for alert in escalation_alerts:
                if alert['level'] == 'EMERGENCY':
                    append_event(db, 'maitri', 'incident.created', {
                        'incident_id': str(uuid.uuid4()),
                        'type': 'missing_sortie',
                        'severity': 'CRITICAL',
                        'station_id': 'maitri',
                        'description': f"Sortie {alert['sortie_id']} has missed check-in and escalated to EMERGENCY",
                        'related_sortie_id': alert['sortie_id'],
                    }, 'system')
                    actions_done.append('Auto-created EMERGENCY incident for missing sortie')

        result = {
            'link_status': link_status.get('maitri', 'DOWN'),
            'actions': actions_done,
            'sortie_id': sortie_id if len(member_ids) >= 2 else None,
            'description': f'Performed {len(actions_done)} offline operations at Maitri.'
        }

    elif step_number == 5:
        # ── Step 5: Restore link & sync ──
        link_status['maitri'] = 'UP'

        # Count unsynced events
        unsynced = get_unsynced_events(db)
        unsynced_count = len(unsynced)

        # In single-node demo, mark all events as synced
        for ev in unsynced:
            ev.synced = True
        db.commit()

        result = {
            'link_status': 'UP',
            'events_synced': unsynced_count,
            'description': f'Link restored. {unsynced_count} events synced to HQ.'
        }

    elif step_number == 6:
        # ── Step 6: Tamper detection ──
        # Verify chain first (should be valid)
        before = verify_chain(db)

        # Tamper with an event
        third_event = db.query(Event).order_by(Event.lamport_clock.asc()).offset(2).first()
        if third_event:
            original_hash = third_event.hash
            third_event.hash = "TAMPERED_" + third_event.hash[:54]
            db.commit()

            # Verify again (should fail)
            after = verify_chain(db)

            # Restore the event
            third_event.hash = original_hash
            db.commit()

            result = {
                'before_verification': before,
                'tampered_event_id': third_event.id,
                'after_verification': after,
                'restored': True,
                'description': 'Tampered with event hash, chain verification detected the break, then restored.'
            }
        else:
            result = {'error': 'No events to tamper with'}

    else:
        result = {'error': f'Unknown step {step_number}'}

    demo_state['current_step'] = step_number
    if step_number not in demo_state['completed_steps']:
        demo_state['completed_steps'].append(step_number)
    demo_state['results'][str(step_number)] = result

    return {"status": "ok", "step": step_number, "result": result}


@router.get("/status")
def get_demo_status():
    return demo_state


def get_all_personnel(db):
    """Derive personnel state from events."""
    personnel = {}
    events = db.query(Event).filter(
        Event.type.like('personnel.%')
    ).order_by(Event.lamport_clock.asc()).all()
    for event in events:
        payload = json.loads(event.payload) if isinstance(event.payload, str) else event.payload
        if event.type == 'personnel.created':
            pid = payload.get('person_id', event.id)
            personnel[pid] = {
                'person_id': pid,
                'name': payload.get('name'),
                'role': payload.get('role'),
                'station_id': payload.get('station_id'),
                'medical_clearance': payload.get('medical_clearance'),
                'expedition_id': payload.get('expedition_id'),
                'location': payload.get('station_id', 'hq'),
            }
        elif event.type == 'personnel.movement':
            pid = payload.get('person_id')
            if pid in personnel:
                personnel[pid]['location'] = payload.get('to_location', personnel[pid].get('location'))
    return personnel
