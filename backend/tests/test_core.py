import pytest
import json
import uuid
from datetime import datetime, timezone, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database import Base
from app.models import Event, User
from app.event_store import append_event, verify_chain, compute_hash
from app.services import (
    compute_survival_margin, check_hazmat_conflicts,
    merge_events, get_item_state, get_active_sorties, check_overdue_sorties
)


@pytest.fixture
def db():
    engine = create_engine('sqlite:///:memory:')
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


# ── Hash Chain Tests ─────────────────────────────────────

def test_hash_chain_valid(db):
    """Appending events creates a valid hash chain."""
    append_event(db, 'hq', 'test.event1', {'data': 1}, 'admin')
    append_event(db, 'hq', 'test.event2', {'data': 2}, 'admin')
    append_event(db, 'hq', 'test.event3', {'data': 3}, 'admin')
    res = verify_chain(db)
    assert res['valid'] is True
    assert res['total_events'] == 3


def test_hash_chain_tamper_detected(db):
    """Tampering with an event hash is detected."""
    append_event(db, 'hq', 'test.event1', {'data': 1}, 'admin')
    append_event(db, 'hq', 'test.event2', {'data': 2}, 'admin')
    res = verify_chain(db)
    assert res['valid'] is True

    # Tamper with the first event's hash
    ev = db.query(Event).order_by(Event.lamport_clock.asc()).first()
    ev.hash = "0000" + ev.hash[4:]
    db.commit()

    res2 = verify_chain(db)
    assert res2['valid'] is False
    assert res2['broken_at'] is not None


def test_hash_chain_empty(db):
    """Empty chain is valid."""
    res = verify_chain(db)
    assert res['valid'] is True
    assert res['total_events'] == 0


def test_prev_hash_linkage(db):
    """Each event's prev_hash matches the prior event's hash."""
    e1 = append_event(db, 'hq', 'test.a', {'x': 1}, 'admin')
    e2 = append_event(db, 'hq', 'test.b', {'x': 2}, 'admin')
    assert e2.prev_hash == e1.hash
    assert e1.prev_hash == '0' * 64


# ── Survival Margin Engine Tests ─────────────────────────

def test_survival_margin_red_tier(db):
    """Item with low stock relative to consumption should be RED."""
    item_id = str(uuid.uuid4())
    # Create item: 150 liters, C1, daily rate 25
    append_event(db, 'maitri', 'inventory.created', {
        'item_id': item_id,
        'name': 'Emergency Heating Fuel',
        'category': 'fuel',
        'criticality_class': 'C1',
        'quantity': 150,
        'unit': 'liters',
        'planned_daily_rate': 25,
        'location_bay': 'Emergency Store',
    }, 'admin')

    # Create a resupply leg arriving in 30 days
    leg_id = str(uuid.uuid4())
    future = (datetime.now(timezone.utc) + timedelta(days=30)).isoformat()
    append_event(db, 'hq', 'leg.created', {
        'leg_id': leg_id,
        'expedition_id': 'exp1',
        'from_location': 'Cape Town',
        'to_location': 'maitri',
        'vessel': 'MV Test',
        'start_date': datetime.now(timezone.utc).isoformat(),
        'end_date': future,
        'capacity_tonnes': 1000,
        'capacity_m3': 2000,
    }, 'admin')

    m = compute_survival_margin(db, 'maitri', item_id)
    # 150 / (25 * 1.5) = 4 days of stock
    # survival_margin = 4 - 30 = -26
    assert m.tier in ('RED', 'BLACK')
    assert m.safety_factor == 1.5
    assert m.days_of_stock < 10


def test_survival_margin_green_tier(db):
    """Item with high stock should be GREEN."""
    item_id = str(uuid.uuid4())
    append_event(db, 'maitri', 'inventory.created', {
        'item_id': item_id,
        'name': 'Rice',
        'category': 'food',
        'criticality_class': 'C2',
        'quantity': 500,
        'unit': 'kg',
        'planned_daily_rate': 5,
        'location_bay': 'Pantry',
    }, 'admin')

    # Create a resupply leg arriving in 30 days
    leg_id = str(uuid.uuid4())
    future = (datetime.now(timezone.utc) + timedelta(days=30)).isoformat()
    append_event(db, 'hq', 'leg.created', {
        'leg_id': leg_id,
        'expedition_id': 'exp1',
        'from_location': 'Cape Town',
        'to_location': 'maitri',
        'vessel': 'MV Test',
        'start_date': datetime.now(timezone.utc).isoformat(),
        'end_date': future,
        'capacity_tonnes': 1000,
        'capacity_m3': 2000,
    }, 'admin')

    m = compute_survival_margin(db, 'maitri', item_id)
    # 500 / (5 * 1.25) = 80 days. margin = 80 - 30 = 50. GREEN
    assert m.tier == 'GREEN'
    assert m.safety_factor == 1.25


def test_survival_margin_safety_factors(db):
    """Different criticality classes use different safety factors."""
    for cc, expected_sf in [('C1', 1.5), ('C2', 1.25), ('C3', 1.0)]:
        item_id = str(uuid.uuid4())
        append_event(db, 'test_station', 'inventory.created', {
            'item_id': item_id,
            'name': f'Test Item {cc}',
            'category': 'test',
            'criticality_class': cc,
            'quantity': 100,
            'unit': 'units',
            'planned_daily_rate': 1,
            'location_bay': 'Test',
        }, 'admin')

        m = compute_survival_margin(db, 'test_station', item_id)
        assert m.safety_factor == expected_sf


# ── Hazmat Conflict Tests ────────────────────────────────

def test_hazmat_conflict_detected():
    """Flammable liquid + oxidizer should conflict."""
    crates = [
        {'crate_id': '1', 'hazmat_class': 'flammable_liquid'},
        {'crate_id': '2', 'hazmat_class': 'oxidizer'},
    ]
    conflicts = check_hazmat_conflicts(crates)
    assert len(conflicts) == 1
    assert 'incompatible' in conflicts[0]['reason']


def test_hazmat_compatible():
    """Two flammable liquids should be compatible."""
    crates = [
        {'crate_id': '1', 'hazmat_class': 'flammable_liquid'},
        {'crate_id': '2', 'hazmat_class': 'flammable_liquid'},
    ]
    conflicts = check_hazmat_conflicts(crates)
    assert len(conflicts) == 0


def test_hazmat_no_hazmat():
    """Non-hazmat crates should have no conflicts."""
    crates = [
        {'crate_id': '1', 'hazmat_class': None},
        {'crate_id': '2', 'hazmat_class': None},
    ]
    conflicts = check_hazmat_conflicts(crates)
    assert len(conflicts) == 0


def test_hazmat_gas_oxidizer_conflict():
    """Flammable gas + oxidizer should conflict."""
    crates = [
        {'crate_id': '1', 'hazmat_class': 'flammable_gas'},
        {'crate_id': '2', 'hazmat_class': 'oxidizer'},
    ]
    conflicts = check_hazmat_conflicts(crates)
    assert len(conflicts) == 1


# ── Sync Merge Tests ─────────────────────────────────────

def test_merge_events_idempotent(db):
    """Merging the same event twice should not create duplicates."""
    ev1 = {
        'id': 'test-merge-1', 'node_id': 'maitri', 'type': 'test.event',
        'payload': json.dumps({'data': 1}), 'actor': 'admin',
        'created_at': '2026-01-01T00:00:00Z', 'lamport_clock': 1,
        'prev_hash': '0' * 64, 'hash': 'abc123'
    }
    result1 = merge_events(db, [ev1])
    assert result1['merged'] == 1
    assert result1['skipped'] == 0

    # Merge again
    result2 = merge_events(db, [ev1])
    assert result2['merged'] == 0
    assert result2['skipped'] == 1

    assert db.query(Event).count() == 1


def test_merge_multiple_events(db):
    """Merging multiple events at once works correctly."""
    events = [
        {
            'id': f'test-multi-{i}', 'node_id': 'maitri', 'type': 'test.event',
            'payload': json.dumps({'data': i}), 'actor': 'admin',
            'created_at': '2026-01-01T00:00:00Z', 'lamport_clock': i,
            'prev_hash': '0' * 64, 'hash': f'hash{i}'
        }
        for i in range(5)
    ]
    result = merge_events(db, events)
    assert result['merged'] == 5
    assert db.query(Event).count() == 5


# ── Escalation Timer Tests ───────────────────────────────

def test_escalation_overdue_sortie(db):
    """A sortie with a missed check-in should trigger escalation."""
    # Create a sortie that's already overdue
    sortie_id = str(uuid.uuid4())
    # Set created_at to 2 hours ago
    old_time = (datetime.now(timezone.utc) - timedelta(hours=2)).isoformat()

    event = Event(
        id=str(uuid.uuid4()),
        node_id='maitri',
        type='sortie.created',
        payload=json.dumps({
            'sortie_id': sortie_id,
            'name': 'Test Sortie',
            'members': ['p1', 'p2'],
            'route': 'A → B → A',
            'expected_return_hours': 4,
            'checkin_interval_minutes': 30,
        }),
        actor='maitri_lead',
        created_at=old_time,
        lamport_clock=1,
        prev_hash='0' * 64,
        hash='testhash1',
        synced=False
    )
    db.add(event)
    db.commit()

    # Check escalations (120 min overdue, interval=30, so 90 min overdue)
    # Should trigger EMERGENCY level (>60 min overdue)
    alerts = check_overdue_sorties(db, demo_mode=False)
    assert len(alerts) > 0
    assert alerts[0]['level'] == 'EMERGENCY'


# ── Inventory State Derivation Tests ─────────────────────

def test_inventory_consumption_tracking(db):
    """Consumption events reduce inventory quantity."""
    item_id = str(uuid.uuid4())
    append_event(db, 'maitri', 'inventory.created', {
        'item_id': item_id, 'name': 'Test Item',
        'category': 'test', 'criticality_class': 'C2',
        'quantity': 100, 'unit': 'units',
        'planned_daily_rate': 5, 'location_bay': 'A1',
    }, 'admin')

    append_event(db, 'maitri', 'inventory.consumed', {
        'item_id': item_id, 'quantity': 30, 'notes': 'Used',
    }, 'admin')

    items = get_item_state(db, 'maitri')
    assert items[item_id]['quantity'] == 70


def test_inventory_adjustment(db):
    """Stock count adjustments set quantity to counted value."""
    item_id = str(uuid.uuid4())
    append_event(db, 'maitri', 'inventory.created', {
        'item_id': item_id, 'name': 'Test',
        'category': 'test', 'criticality_class': 'C3',
        'quantity': 100, 'unit': 'units',
        'planned_daily_rate': 1, 'location_bay': 'A1',
    }, 'admin')

    append_event(db, 'maitri', 'inventory.adjustment', {
        'item_id': item_id, 'counted_quantity': 85, 'notes': 'Counted',
    }, 'admin')

    items = get_item_state(db, 'maitri')
    assert items[item_id]['quantity'] == 85
