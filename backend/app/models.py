from sqlalchemy import Column, String, Integer, Text, Boolean, Index
from app.database import Base
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Dict, Any

class Event(Base):
    __tablename__ = 'events'
    id = Column(String(36), primary_key=True)
    node_id = Column(String(20), nullable=False)
    type = Column(String(100), nullable=False)
    payload = Column(Text, nullable=False)
    actor = Column(String(50), nullable=False)
    created_at = Column(String(50), nullable=False)
    lamport_clock = Column(Integer, nullable=False)
    prev_hash = Column(String(64), nullable=False)
    hash = Column(String(64), nullable=False)
    synced = Column(Boolean, default=False)

    __table_args__ = (
        Index('ix_events_node_lamport', 'node_id', 'lamport_clock'),
        Index('ix_events_synced', 'synced'),
    )

class User(Base):
    __tablename__ = 'users'
    id = Column(String(36), primary_key=True)
    username = Column(String(50), unique=True, nullable=False)
    password_hash = Column(String(200), nullable=False)
    role = Column(String(30), nullable=False)
    station_id = Column(String(20), nullable=True)
    full_name = Column(String(100), nullable=False)

# Pydantic Schemas
class EventCreate(BaseModel):
    type: str
    payload: Dict[str, Any]

class EventOut(BaseModel):
    id: str
    node_id: str
    type: str
    payload: Any
    actor: str
    created_at: str
    lamport_clock: int
    prev_hash: str
    hash: str
    model_config = ConfigDict(from_attributes=True)

class UserOut(BaseModel):
    id: str
    username: str
    role: str
    station_id: Optional[str]
    full_name: str
    model_config = ConfigDict(from_attributes=True)

class LoginRequest(BaseModel):
    username: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = 'bearer'
    user: UserOut

class ExpeditionCreate(BaseModel):
    name: str
    year: str
    description: str

class LegCreate(BaseModel):
    expedition_id: str
    from_location: str
    to_location: str
    vessel: str
    start_date: str
    end_date: str
    capacity_tonnes: float
    capacity_m3: float

class CrateCreate(BaseModel):
    contents: str
    criticality_class: str
    hazmat_class: Optional[str] = None
    weight_kg: float
    destination: str
    leg_id: Optional[str] = None

class CheckpointCreate(BaseModel):
    crate_id: str
    checkpoint_type: str
    location: str
    condition_note: Optional[str] = None
    lat: Optional[float] = None
    lon: Optional[float] = None

class InventoryItemCreate(BaseModel):
    name: str
    category: str
    criticality_class: str
    location_bay: str
    batch: Optional[str] = None
    expiry_date: Optional[str] = None
    quantity: float
    unit: str
    planned_daily_rate: float

class ConsumptionCreate(BaseModel):
    item_id: str
    quantity: float
    notes: Optional[str] = None

class StockCountCreate(BaseModel):
    item_id: str
    counted_quantity: float
    notes: Optional[str] = None

class PersonnelCreate(BaseModel):
    name: str
    role: str
    expedition_id: Optional[str] = None
    station_id: Optional[str] = None
    medical_clearance: str

class MovementCreate(BaseModel):
    person_id: str
    from_location: str
    to_location: str
    movement_type: str

class SortieCreate(BaseModel):
    name: str
    members: List[str]
    route: str
    expected_return_hours: float
    checkin_interval_minutes: int

class CheckInCreate(BaseModel):
    sortie_id: str
    person_id: str
    notes: Optional[str] = None
    lat: Optional[float] = None
    lon: Optional[float] = None

class IncidentCreate(BaseModel):
    type: str
    severity: str
    station_id: str
    description: str
    related_sortie_id: Optional[str] = None
    related_item_id: Optional[str] = None

class IncidentActionCreate(BaseModel):
    incident_id: str
    action_type: str
    notes: str

class VesselPositionCreate(BaseModel):
    vessel_name: str
    lat: float
    lon: float
    heading: Optional[float] = None
    speed_knots: Optional[float] = None
    notes: Optional[str] = None

class SyncPushRequest(BaseModel):
    events: List[Dict[str, Any]]

class MarginResult(BaseModel):
    item_id: str
    item_name: str
    station_id: str
    quantity: float
    avg_daily_consumption: float
    safety_factor: float
    days_of_stock: float
    days_to_resupply: Optional[float] = None
    survival_margin: Optional[float] = None
    tier: str
    resupply_date: Optional[str] = None
    data_age_days: float
    criticality_class: str
    unit: str
    alert_text: Optional[str] = None
