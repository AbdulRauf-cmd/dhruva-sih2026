import uuid
import json
from sqlalchemy.orm import Session
from app.models import User
from app.event_store import append_event
from app.auth import hash_password
from app.config import settings


def seed_data(db: Session):
    if db.query(User).first():
        return

    # ── Users ──────────────────────────────────────────────
    users = [
        {'username': 'admin', 'password': 'admin123', 'role': 'HQ_PLANNER', 'station_id': 'hq', 'full_name': 'Dr. Priya Sharma (HQ Planner)'},
        {'username': 'voyage1', 'password': 'voyage123', 'role': 'VOYAGE_LEADER', 'station_id': None, 'full_name': 'Capt. Rajesh Kumar'},
        {'username': 'maitri_lead', 'password': 'maitri123', 'role': 'STATION_LEAD', 'station_id': 'maitri', 'full_name': 'Dr. Anand Patel (Maitri Lead)'},
        {'username': 'bharati_lead', 'password': 'bharati123', 'role': 'STATION_LEAD', 'station_id': 'bharati', 'full_name': 'Dr. Kavita Singh (Bharati Lead)'},
        {'username': 'medical1', 'password': 'medical123', 'role': 'MEDICAL_OFFICER', 'station_id': 'maitri', 'full_name': 'Dr. Suresh Nair (Medical Officer)'},
    ]
    for u in users:
        user = User(
            id=str(uuid.uuid4()),
            username=u['username'],
            password_hash=hash_password(u['password']),
            role=u['role'],
            station_id=u['station_id'],
            full_name=u['full_name']
        )
        db.add(user)
    db.commit()

    node = settings.NODE_ID

    # ── Expedition ─────────────────────────────────────────
    exp_id = str(uuid.uuid4())
    append_event(db, node, 'expedition.created', {
        'expedition_id': exp_id,
        'name': 'Indian Antarctic Expedition 2026-27',
        'year': '2026',
        'description': '45th Indian Scientific Expedition to Antarctica — summer campaign'
    }, 'admin')

    leg_ids = []
    legs = [
        {'from': 'Goa', 'to': 'Cape Town', 'start': '2026-11-15T00:00:00+00:00', 'end': '2026-11-25T00:00:00+00:00'},
        {'from': 'Cape Town', 'to': 'Maitri', 'start': '2026-11-28T00:00:00+00:00', 'end': '2026-12-15T00:00:00+00:00'},
        {'from': 'Maitri', 'to': 'Bharati', 'start': '2026-12-18T00:00:00+00:00', 'end': '2026-12-25T00:00:00+00:00'},
        {'from': 'Bharati', 'to': 'Goa', 'start': '2027-02-15T00:00:00+00:00', 'end': '2027-03-20T00:00:00+00:00'},
    ]
    for lg in legs:
        lid = str(uuid.uuid4())
        leg_ids.append(lid)
        append_event(db, node, 'leg.created', {
            'leg_id': lid,
            'expedition_id': exp_id,
            'from_location': lg['from'],
            'to_location': lg['to'],
            'vessel': 'MV Vasundhara',
            'start_date': lg['start'],
            'end_date': lg['end'],
            'capacity_tonnes': 2000,
            'capacity_m3': 3000
        }, 'admin')

    # ── Inventory — Maitri (20 items) ──────────────────────
    maitri_items = [
        {'name': 'Diesel Fuel', 'category': 'fuel', 'cc': 'C1', 'qty': 8000, 'unit': 'liters', 'rate': 200, 'bay': 'Tank Farm A'},
        {'name': 'Aviation Fuel (JP-8)', 'category': 'fuel', 'cc': 'C1', 'qty': 2000, 'unit': 'liters', 'rate': 50, 'bay': 'Tank Farm B'},
        {'name': 'Emergency Heating Fuel', 'category': 'fuel', 'cc': 'C1', 'qty': 150, 'unit': 'liters', 'rate': 25, 'bay': 'Emergency Store'},
        {'name': 'LPG Cylinders', 'category': 'fuel', 'cc': 'C1', 'qty': 10, 'unit': 'cylinders', 'rate': 0.3, 'bay': 'Gas Store'},
        {'name': 'Fresh Water', 'category': 'water', 'cc': 'C1', 'qty': 5000, 'unit': 'liters', 'rate': 150, 'bay': 'Water Tank'},
        {'name': 'Rice', 'category': 'food', 'cc': 'C2', 'qty': 500, 'unit': 'kg', 'rate': 5, 'bay': 'Pantry A', 'exp': '2027-06-15'},
        {'name': 'Dal (Lentils)', 'category': 'food', 'cc': 'C2', 'qty': 200, 'unit': 'kg', 'rate': 2, 'bay': 'Pantry A', 'exp': '2027-05-20'},
        {'name': 'Cooking Oil', 'category': 'food', 'cc': 'C2', 'qty': 80, 'unit': 'liters', 'rate': 1, 'bay': 'Pantry B', 'exp': '2027-04-10'},
        {'name': 'Canned Food', 'category': 'food', 'cc': 'C2', 'qty': 300, 'unit': 'cans', 'rate': 5, 'bay': 'Pantry C', 'exp': '2027-08-01'},
        {'name': 'Oxygen Cylinders', 'category': 'medical', 'cc': 'C1', 'qty': 12, 'unit': 'cylinders', 'rate': 0.1, 'bay': 'Med Bay'},
        {'name': 'First Aid Kits', 'category': 'medical', 'cc': 'C1', 'qty': 8, 'unit': 'kits', 'rate': 0.05, 'bay': 'Med Bay'},
        {'name': 'Antibiotics', 'category': 'medical', 'cc': 'C1', 'qty': 30, 'unit': 'courses', 'rate': 0.2, 'bay': 'Med Bay', 'exp': '2027-03-15'},
        {'name': 'Generator Spare Parts', 'category': 'spares', 'cc': 'C2', 'qty': 15, 'unit': 'sets', 'rate': 0.1, 'bay': 'Workshop A'},
        {'name': 'Comm Equipment Spares', 'category': 'spares', 'cc': 'C2', 'qty': 5, 'unit': 'sets', 'rate': 0.05, 'bay': 'Workshop B'},
        {'name': 'Winter Clothing Sets', 'category': 'equipment', 'cc': 'C2', 'qty': 30, 'unit': 'sets', 'rate': 0.02, 'bay': 'Store Room 1'},
        {'name': 'Batteries (AA/AAA)', 'category': 'equipment', 'cc': 'C2', 'qty': 200, 'unit': 'units', 'rate': 3, 'bay': 'Store Room 2'},
        {'name': 'Scientific Instruments', 'category': 'scientific', 'cc': 'C3', 'qty': 20, 'unit': 'units', 'rate': 0.01, 'bay': 'Lab A'},
        {'name': 'Sample Collection Kits', 'category': 'scientific', 'cc': 'C3', 'qty': 100, 'unit': 'kits', 'rate': 2, 'bay': 'Lab B', 'exp': '2027-06-01'},
        {'name': 'Toilet Paper', 'category': 'supplies', 'cc': 'C3', 'qty': 100, 'unit': 'rolls', 'rate': 2, 'bay': 'Store Room 3'},
        {'name': 'UV Water Purifier Filters', 'category': 'spares', 'cc': 'C1', 'qty': 4, 'unit': 'filters', 'rate': 0.05, 'bay': 'Water Plant'},
    ]

    maitri_item_ids = {}
    for it in maitri_items:
        it_id = str(uuid.uuid4())
        maitri_item_ids[it['name']] = it_id
        append_event(db, 'maitri', 'inventory.created', {
            'item_id': it_id,
            'name': it['name'],
            'category': it['category'],
            'criticality_class': it['cc'],
            'quantity': it['qty'],
            'unit': it['unit'],
            'planned_daily_rate': it['rate'],
            'location_bay': it['bay'],
            'expiry_date': it.get('exp'),
        }, 'admin')

    # ── Inventory — Bharati (20 items) ─────────────────────
    bharati_items = [
        {'name': 'Diesel Fuel', 'category': 'fuel', 'cc': 'C1', 'qty': 6000, 'unit': 'liters', 'rate': 180, 'bay': 'Tank A'},
        {'name': 'Aviation Fuel (JP-8)', 'category': 'fuel', 'cc': 'C1', 'qty': 1500, 'unit': 'liters', 'rate': 40, 'bay': 'Tank B'},
        {'name': 'Emergency Heating Fuel', 'category': 'fuel', 'cc': 'C1', 'qty': 200, 'unit': 'liters', 'rate': 20, 'bay': 'Emergency'},
        {'name': 'LPG Cylinders', 'category': 'fuel', 'cc': 'C1', 'qty': 8, 'unit': 'cylinders', 'rate': 0.25, 'bay': 'Gas Store'},
        {'name': 'Fresh Water', 'category': 'water', 'cc': 'C1', 'qty': 4000, 'unit': 'liters', 'rate': 120, 'bay': 'Water Tank'},
        {'name': 'Rice', 'category': 'food', 'cc': 'C2', 'qty': 400, 'unit': 'kg', 'rate': 4, 'bay': 'Pantry A', 'exp': '2027-06-15'},
        {'name': 'Dal (Lentils)', 'category': 'food', 'cc': 'C2', 'qty': 150, 'unit': 'kg', 'rate': 1.5, 'bay': 'Pantry A', 'exp': '2027-05-20'},
        {'name': 'Cooking Oil', 'category': 'food', 'cc': 'C2', 'qty': 60, 'unit': 'liters', 'rate': 0.8, 'bay': 'Pantry B', 'exp': '2027-04-10'},
        {'name': 'Canned Food', 'category': 'food', 'cc': 'C2', 'qty': 250, 'unit': 'cans', 'rate': 4, 'bay': 'Pantry C', 'exp': '2027-08-01'},
        {'name': 'Oxygen Cylinders', 'category': 'medical', 'cc': 'C1', 'qty': 10, 'unit': 'cylinders', 'rate': 0.08, 'bay': 'Med Bay'},
        {'name': 'First Aid Kits', 'category': 'medical', 'cc': 'C1', 'qty': 6, 'unit': 'kits', 'rate': 0.04, 'bay': 'Med Bay'},
        {'name': 'Antibiotics', 'category': 'medical', 'cc': 'C1', 'qty': 25, 'unit': 'courses', 'rate': 0.15, 'bay': 'Med Bay', 'exp': '2027-03-15'},
        {'name': 'Generator Spare Parts', 'category': 'spares', 'cc': 'C2', 'qty': 10, 'unit': 'sets', 'rate': 0.08, 'bay': 'Workshop'},
        {'name': 'Comm Equipment Spares', 'category': 'spares', 'cc': 'C2', 'qty': 4, 'unit': 'sets', 'rate': 0.04, 'bay': 'Workshop'},
        {'name': 'Winter Clothing Sets', 'category': 'equipment', 'cc': 'C2', 'qty': 25, 'unit': 'sets', 'rate': 0.02, 'bay': 'Store Room'},
        {'name': 'Batteries (AA/AAA)', 'category': 'equipment', 'cc': 'C2', 'qty': 150, 'unit': 'units', 'rate': 2.5, 'bay': 'Store Room'},
        {'name': 'Scientific Instruments', 'category': 'scientific', 'cc': 'C3', 'qty': 15, 'unit': 'units', 'rate': 0.01, 'bay': 'Lab'},
        {'name': 'Sample Collection Kits', 'category': 'scientific', 'cc': 'C3', 'qty': 80, 'unit': 'kits', 'rate': 1.5, 'bay': 'Lab', 'exp': '2027-06-01'},
        {'name': 'Toilet Paper', 'category': 'supplies', 'cc': 'C3', 'qty': 80, 'unit': 'rolls', 'rate': 1.5, 'bay': 'Store'},
        {'name': 'UV Water Purifier Filters', 'category': 'spares', 'cc': 'C1', 'qty': 3, 'unit': 'filters', 'rate': 0.04, 'bay': 'Water Plant'},
    ]
    for it in bharati_items:
        it_id = str(uuid.uuid4())
        append_event(db, 'bharati', 'inventory.created', {
            'item_id': it_id,
            'name': it['name'],
            'category': it['category'],
            'criticality_class': it['cc'],
            'quantity': it['qty'],
            'unit': it['unit'],
            'planned_daily_rate': it['rate'],
            'location_bay': it['bay'],
            'expiry_date': it.get('exp'),
        }, 'admin')

    # ── Personnel (~25) ────────────────────────────────────
    personnel = [
        {'name': 'Dr. Vikram Sarabhai', 'role': 'Expedition Leader', 'sid': 'maitri', 'mc': 'CLEARED'},
        {'name': 'Lt. Cmdr. Arjun Reddy', 'role': 'Second-in-Command', 'sid': 'maitri', 'mc': 'CLEARED'},
        {'name': 'Dr. Meera Iyer', 'role': 'Glaciologist', 'sid': 'maitri', 'mc': 'CLEARED'},
        {'name': 'Amit Chowdhury', 'role': 'Mechanical Engineer', 'sid': 'maitri', 'mc': 'CLEARED'},
        {'name': 'Sneha Patil', 'role': 'Electrical Engineer', 'sid': 'maitri', 'mc': 'CLEARED'},
        {'name': 'Dr. Suresh Nair', 'role': 'Medical Officer', 'sid': 'maitri', 'mc': 'CLEARED'},
        {'name': 'Deepak Sharma', 'role': 'Cook', 'sid': 'maitri', 'mc': 'CLEARED'},
        {'name': 'Rajendra Prasad', 'role': 'Radio Operator', 'sid': 'maitri', 'mc': 'CLEARED'},
        {'name': 'Kiran Rao', 'role': 'Logistics Coordinator', 'sid': 'maitri', 'mc': 'CLEARED'},
        {'name': 'Sanjay Kulkarni', 'role': 'Diesel Mechanic', 'sid': 'maitri', 'mc': 'CLEARED'},
        {'name': 'Pavan Malhotra', 'role': 'Weather Observer', 'sid': 'maitri', 'mc': 'CLEARED'},
        {'name': 'Prakash Iyer', 'role': 'Safety Officer', 'sid': 'maitri', 'mc': 'CLEARED'},
        {'name': 'Lakshmi Narayan', 'role': 'Biologist', 'sid': 'maitri', 'mc': 'CLEARED'},
        {'name': 'Arun Joshi', 'role': 'Research Assistant', 'sid': 'maitri', 'mc': 'NOT_CLEARED'},
        {'name': 'Dr. Ravi Deshmukh', 'role': 'Meteorologist', 'sid': 'bharati', 'mc': 'CLEARED'},
        {'name': 'Dr. Anjali Gupta', 'role': 'Marine Biologist', 'sid': 'bharati', 'mc': 'PENDING'},
        {'name': 'Rahul Verma', 'role': 'IT Engineer', 'sid': 'bharati', 'mc': 'CLEARED'},
        {'name': 'Dr. Priyanka Das', 'role': 'Medical Officer', 'sid': 'bharati', 'mc': 'CLEARED'},
        {'name': 'Sunil Kumar', 'role': 'Cook', 'sid': 'bharati', 'mc': 'CLEARED'},
        {'name': 'Manoj Tiwari', 'role': 'Radio Operator', 'sid': 'bharati', 'mc': 'CLEARED'},
        {'name': 'Divya Menon', 'role': 'Geophysicist', 'sid': 'bharati', 'mc': 'CLEARED'},
        {'name': 'Nisha Aggarwal', 'role': 'Data Scientist', 'sid': 'bharati', 'mc': 'PENDING'},
        {'name': 'Venkat Subramanian', 'role': 'Structural Engineer', 'sid': 'bharati', 'mc': 'CLEARED'},
        {'name': 'Dr. Priya Sharma', 'role': 'Programme Director', 'sid': 'hq', 'mc': 'CLEARED'},
        {'name': 'Capt. Rajesh Kumar', 'role': 'Voyage Leader', 'sid': None, 'mc': 'CLEARED'},
    ]
    person_ids = {}
    for p in personnel:
        p_id = str(uuid.uuid4())
        person_ids[p['name']] = p_id
        append_event(db, node, 'personnel.created', {
            'person_id': p_id,
            'name': p['name'],
            'role': p['role'],
            'station_id': p['sid'],
            'medical_clearance': p['mc'],
            'expedition_id': exp_id,
        }, 'admin')

    # ── Cargo crates (~60) ─────────────────────────────────
    crate_defs = [
        # PACKED at Goa (10 crates)
        {'contents': 'Diesel Fuel Drums (200L x 10)', 'cc': 'C1', 'haz': 'flammable_liquid', 'wt': 1800, 'dest': 'maitri', 'cp': 'PACKED'},
        {'contents': 'Aviation Fuel Drums', 'cc': 'C1', 'haz': 'flammable_liquid', 'wt': 900, 'dest': 'maitri', 'cp': 'PACKED'},
        {'contents': 'LPG Cylinder Rack', 'cc': 'C1', 'haz': 'flammable_gas', 'wt': 300, 'dest': 'maitri', 'cp': 'PACKED'},
        {'contents': 'Oxidizer Chemicals', 'cc': 'C2', 'haz': 'oxidizer', 'wt': 200, 'dest': 'bharati', 'cp': 'PACKED'},
        {'contents': 'Rice Sacks (50kg x 20)', 'cc': 'C2', 'haz': None, 'wt': 1000, 'dest': 'maitri', 'cp': 'PACKED'},
        {'contents': 'Medical Supplies Box A', 'cc': 'C1', 'haz': None, 'wt': 50, 'dest': 'maitri', 'cp': 'PACKED'},
        {'contents': 'Medical Supplies Box B', 'cc': 'C1', 'haz': None, 'wt': 45, 'dest': 'bharati', 'cp': 'PACKED'},
        {'contents': 'Winter Gear Pallet 1', 'cc': 'C2', 'haz': None, 'wt': 400, 'dest': 'maitri', 'cp': 'PACKED'},
        {'contents': 'Lab Equipment Crate', 'cc': 'C3', 'haz': None, 'wt': 300, 'dest': 'bharati', 'cp': 'PACKED'},
        {'contents': 'Battery Boxes (Mixed)', 'cc': 'C2', 'haz': None, 'wt': 150, 'dest': 'maitri', 'cp': 'PACKED'},
        # LOADED on vessel (10 crates)
        {'contents': 'Diesel Fuel Drums (200L x 8)', 'cc': 'C1', 'haz': 'flammable_liquid', 'wt': 1440, 'dest': 'bharati', 'cp': 'LOADED'},
        {'contents': 'Generator Parts Crate', 'cc': 'C2', 'haz': None, 'wt': 500, 'dest': 'maitri', 'cp': 'LOADED'},
        {'contents': 'Comm Equipment', 'cc': 'C2', 'haz': None, 'wt': 200, 'dest': 'bharati', 'cp': 'LOADED'},
        {'contents': 'Food Supplies Pallet A', 'cc': 'C2', 'haz': None, 'wt': 800, 'dest': 'maitri', 'cp': 'LOADED'},
        {'contents': 'Food Supplies Pallet B', 'cc': 'C2', 'haz': None, 'wt': 700, 'dest': 'bharati', 'cp': 'LOADED'},
        {'contents': 'Scientific Kit A', 'cc': 'C3', 'haz': None, 'wt': 250, 'dest': 'maitri', 'cp': 'LOADED'},
        {'contents': 'Water Purification Filters', 'cc': 'C1', 'haz': None, 'wt': 100, 'dest': 'maitri', 'cp': 'LOADED'},
        {'contents': 'Clothing Supplies', 'cc': 'C2', 'haz': None, 'wt': 350, 'dest': 'bharati', 'cp': 'LOADED'},
        {'contents': 'Toiletries Pallet', 'cc': 'C3', 'haz': None, 'wt': 200, 'dest': 'maitri', 'cp': 'LOADED'},
        {'contents': 'Spare Parts Misc', 'cc': 'C2', 'haz': None, 'wt': 450, 'dest': 'bharati', 'cp': 'LOADED'},
        # IN_TRANSIT (10 crates)
        {'contents': 'Heating Fuel Emergency Reserve', 'cc': 'C1', 'haz': 'flammable_liquid', 'wt': 600, 'dest': 'maitri', 'cp': 'IN_TRANSIT'},
        {'contents': 'Oxygen Cylinders Rack', 'cc': 'C1', 'haz': 'flammable_gas', 'wt': 250, 'dest': 'maitri', 'cp': 'IN_TRANSIT'},
        {'contents': 'Antibiotic Shipment', 'cc': 'C1', 'haz': None, 'wt': 30, 'dest': 'maitri', 'cp': 'IN_TRANSIT'},
        {'contents': 'Fresh Produce (Frozen)', 'cc': 'C2', 'haz': None, 'wt': 500, 'dest': 'bharati', 'cp': 'IN_TRANSIT'},
        {'contents': 'Scientific Instruments B', 'cc': 'C3', 'haz': None, 'wt': 180, 'dest': 'bharati', 'cp': 'IN_TRANSIT'},
        {'contents': 'Fuel Additive Drums', 'cc': 'C2', 'haz': 'flammable_liquid', 'wt': 350, 'dest': 'maitri', 'cp': 'IN_TRANSIT'},
        {'contents': 'Welding Gas Cylinders', 'cc': 'C2', 'haz': 'flammable_gas', 'wt': 200, 'dest': 'bharati', 'cp': 'IN_TRANSIT'},
        {'contents': 'Sample Kits Large', 'cc': 'C3', 'haz': None, 'wt': 150, 'dest': 'maitri', 'cp': 'IN_TRANSIT'},
        {'contents': 'Emergency Rations', 'cc': 'C1', 'haz': None, 'wt': 400, 'dest': 'maitri', 'cp': 'IN_TRANSIT'},
        {'contents': 'Solar Panel Kit', 'cc': 'C3', 'haz': None, 'wt': 300, 'dest': 'bharati', 'cp': 'IN_TRANSIT'},
        # OFFLOADED at stations (15 crates)
        {'contents': 'Diesel Drums Lot-1', 'cc': 'C1', 'haz': 'flammable_liquid', 'wt': 1800, 'dest': 'maitri', 'cp': 'OFFLOADED'},
        {'contents': 'Rice Sacks Lot-1', 'cc': 'C2', 'haz': None, 'wt': 1000, 'dest': 'maitri', 'cp': 'OFFLOADED'},
        {'contents': 'Med Kit Alpha', 'cc': 'C1', 'haz': None, 'wt': 40, 'dest': 'maitri', 'cp': 'OFFLOADED'},
        {'contents': 'Generator Set A', 'cc': 'C2', 'haz': None, 'wt': 600, 'dest': 'maitri', 'cp': 'OFFLOADED'},
        {'contents': 'LPG Lot-1', 'cc': 'C1', 'haz': 'flammable_gas', 'wt': 250, 'dest': 'maitri', 'cp': 'OFFLOADED'},
        {'contents': 'Diesel Drums Lot-B1', 'cc': 'C1', 'haz': 'flammable_liquid', 'wt': 1500, 'dest': 'bharati', 'cp': 'OFFLOADED'},
        {'contents': 'Food Pallet Bharati-1', 'cc': 'C2', 'haz': None, 'wt': 800, 'dest': 'bharati', 'cp': 'OFFLOADED'},
        {'contents': 'Med Kit Bravo', 'cc': 'C1', 'haz': None, 'wt': 35, 'dest': 'bharati', 'cp': 'OFFLOADED'},
        {'contents': 'Weather Station Kit', 'cc': 'C3', 'haz': None, 'wt': 200, 'dest': 'bharati', 'cp': 'OFFLOADED'},
        {'contents': 'Plumbing Spares', 'cc': 'C2', 'haz': None, 'wt': 100, 'dest': 'maitri', 'cp': 'OFFLOADED'},
        {'contents': 'Water Filters Lot-1', 'cc': 'C1', 'haz': None, 'wt': 80, 'dest': 'maitri', 'cp': 'OFFLOADED'},
        {'contents': 'Canned Food Lot-M', 'cc': 'C2', 'haz': None, 'wt': 500, 'dest': 'maitri', 'cp': 'OFFLOADED'},
        {'contents': 'Battery Packs Delta', 'cc': 'C2', 'haz': None, 'wt': 120, 'dest': 'bharati', 'cp': 'OFFLOADED'},
        {'contents': 'Clothing Box Charlie', 'cc': 'C2', 'haz': None, 'wt': 200, 'dest': 'bharati', 'cp': 'OFFLOADED'},
        {'contents': 'Lab Chemicals (inert)', 'cc': 'C3', 'haz': None, 'wt': 150, 'dest': 'bharati', 'cp': 'OFFLOADED'},
        # STORED at stations (5 crates)
        {'contents': 'Emergency Med Cabinet', 'cc': 'C1', 'haz': None, 'wt': 25, 'dest': 'maitri', 'cp': 'STORED'},
        {'contents': 'Cooking Oil Drums', 'cc': 'C2', 'haz': None, 'wt': 400, 'dest': 'maitri', 'cp': 'STORED'},
        {'contents': 'Toilet Paper Bulk', 'cc': 'C3', 'haz': None, 'wt': 80, 'dest': 'maitri', 'cp': 'STORED'},
        {'contents': 'Emergency Blankets', 'cc': 'C1', 'haz': None, 'wt': 60, 'dest': 'bharati', 'cp': 'STORED'},
        {'contents': 'Stationery Supplies', 'cc': 'C3', 'haz': None, 'wt': 40, 'dest': 'bharati', 'cp': 'STORED'},
    ]

    checkpoint_sequence = {
        'PACKED': ['PACKED'],
        'LOADED': ['PACKED', 'LOADED'],
        'IN_TRANSIT': ['PACKED', 'LOADED', 'IN_TRANSIT'],
        'OFFLOADED': ['PACKED', 'LOADED', 'IN_TRANSIT', 'OFFLOADED'],
        'STORED': ['PACKED', 'LOADED', 'IN_TRANSIT', 'OFFLOADED', 'STORED'],
    }

    cp_locations = {
        'PACKED': 'NCPOR Warehouse, Goa',
        'LOADED': 'MV Vasundhara, Mormugao Port',
        'IN_TRANSIT': 'MV Vasundhara, Southern Ocean',
        'OFFLOADED': None,  # use destination
        'STORED': None,     # use destination + bay
    }

    for cd in crate_defs:
        crate_id = str(uuid.uuid4())
        append_event(db, node, 'cargo.created', {
            'crate_id': crate_id,
            'contents': cd['contents'],
            'criticality_class': cd['cc'],
            'hazmat_class': cd['haz'],
            'weight_kg': cd['wt'],
            'destination': cd['dest'],
            'leg_id': leg_ids[1] if cd['dest'] == 'maitri' else leg_ids[2],
        }, 'admin')

        for cp in checkpoint_sequence[cd['cp']]:
            loc = cp_locations[cp]
            if loc is None:
                loc = f"Station {cd['dest'].title()}"
            append_event(db, node, 'cargo.checkpoint', {
                'crate_id': crate_id,
                'checkpoint_type': cp,
                'location': loc,
                'condition_note': 'Good condition',
            }, 'admin')

    # ── Consumption events (recent, for avg daily calculation) ──
    # Log some recent diesel consumption at maitri
    diesel_id = maitri_item_ids.get('Diesel Fuel')
    if diesel_id:
        for day in range(14):
            append_event(db, 'maitri', 'inventory.consumed', {
                'item_id': diesel_id,
                'quantity': 200,
                'notes': f'Daily diesel usage day {day+1}',
            }, 'maitri_lead')

    ehf_id = maitri_item_ids.get('Emergency Heating Fuel')
    if ehf_id:
        for day in range(14):
            append_event(db, 'maitri', 'inventory.consumed', {
                'item_id': ehf_id,
                'quantity': 25,
                'notes': f'Emergency heating day {day+1}',
            }, 'maitri_lead')

    # ── Vessel position reports ────────────────────────────
    positions = [
        {'lat': 15.41, 'lon': 73.88, 'notes': 'Departed Mormugao Port, Goa'},
        {'lat': 5.0, 'lon': 65.0, 'notes': 'Indian Ocean transit'},
        {'lat': -10.0, 'lon': 55.0, 'notes': 'South of Madagascar'},
        {'lat': -33.92, 'lon': 18.42, 'notes': 'Approaching Cape Town'},
        {'lat': -45.0, 'lon': 10.0, 'notes': 'Southern Ocean'},
        {'lat': -60.0, 'lon': 5.0, 'notes': 'Approaching Antarctic waters'},
        {'lat': -70.77, 'lon': 11.73, 'notes': 'Near Maitri Station'},
    ]
    for pos in positions:
        append_event(db, node, 'vessel.position', {
            'vessel_name': 'MV Vasundhara',
            'lat': pos['lat'],
            'lon': pos['lon'],
            'heading': 180,
            'speed_knots': 14,
            'notes': pos['notes'],
        }, 'voyage1')

    print(f"[SEED] Seeded {node}: users={len(users)}, items={len(maitri_items)+len(bharati_items)}, crates={len(crate_defs)}, personnel={len(personnel)}")
