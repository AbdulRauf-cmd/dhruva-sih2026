export interface User { id: string; username: string; role: string; station_id?: string; node_id?: string; full_name?: string; }
export interface TokenResponse { access_token: string; token_type: string; user: User; }
export interface Expedition { id: string; name: string; status: string; }
export interface Leg { id: string; expedition_id: string; vessel: string; from_node: string; to_node: string; start_date: string; end_date: string; status: string; }
export interface Crate { id: string; contents: string; criticality: string; status: string; destination: string; hazmat: boolean; }
export interface Checkpoint { id: string; crate_id: string; location: string; status: string; timestamp: string; note?: string; }
export interface InventoryItem { id: string; name: string; category: string; quantity: number; unit: string; criticality: string; expiry_date?: string; }
export interface ConsumptionRecord { id: string; item_id: string; quantity: number; date: string; }
export interface MarginResult { item_id: string; item_name: string; days_of_stock: number; tier: 'GREEN' | 'AMBER' | 'RED' | 'BLACK'; alert_text: string; details?: any; }
export interface Person { id: string; name: string; role: string; station_id: string; clearance_status: string; }
export interface Movement { id: string; person_id: string; from_location: string; to_location: string; date: string; }
export interface Sortie { id: string; name: string; members: string[]; route: string; expected_return: string; check_in_interval: number; last_check_in?: string; status: string; escalation_level: string; }
export interface CheckIn { id: string; sortie_id: string; timestamp: string; location?: string; status: string; }
export interface Incident { id: string; type: string; severity: string; description: string; status: string; created_at: string; }
export interface IncidentAction { id: string; incident_id: string; action: string; timestamp: string; }
export interface VesselPosition { vessel: string; lat: number; lng: number; timestamp: string; }
export interface SyncStatus { node_id: string; link_status: 'UP' | 'DOWN'; last_sync: string; pending_events: number; }
export interface DashboardSummary {
  stats: {
    expeditions: number;
    next_leg_date: string;
    crates_total: number;
    crates_overdue: number;
    inventory_items: number;
    inventory_alerts: number;
    personnel_total: number;
    personnel_on_station: number;
    active_incidents: number;
  };
  margins: { [stationId: string]: MarginResult[] };
  active_alerts: { text: string; tier: string }[];
  sorties: Sortie[];
  sync_status: SyncStatus[];
}
