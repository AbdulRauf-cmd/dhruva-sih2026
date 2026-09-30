import axios from 'axios';

const api = axios.create({
  baseURL: '/api',
});

// Add JWT token interceptor
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('dhruva_token');
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

// Auth
export const login = (username: string, password: string) => api.post('/auth/login', { username, password });
export const getMe = () => api.get('/auth/me');

// Expeditions
export const getExpeditions = () => api.get('/expeditions');
export const createExpedition = (data: any) => api.post('/expeditions', data);
export const delayLeg = (legId: string, days: number) => api.post(`/legs/${legId}/delay`, { delay_days: days });
export const getLegManifest = (legId: string) => api.get(`/legs/${legId}/manifest`);
export const validateLeg = (legId: string) => api.get(`/legs/${legId}/validate`);

// Cargo
export const getCrates = () => api.get('/cargo/crates');
export const createCrate = (data: any) => api.post('/cargo/crates', data);
export const logCheckpoint = (data: any) => api.post('/cargo/checkpoint', data);
export const getCrateQR = (id: string) => api.get(`/cargo/crates/${id}/qr`);
export const getOverdueCargo = () => api.get('/cargo/overdue');
export const logVesselPosition = (data: any) => api.post('/cargo/vessel-position', data);
export const getVesselPositions = () => api.get('/cargo/vessel-positions');

// Inventory
export const getInventory = (stationId?: string) => api.get(stationId ? `/inventory/${stationId}` : '/inventory');
export const createInventoryItem = (data: any) => api.post('/inventory/items', data);
export const logConsumption = (data: any) => api.post('/inventory/consume', data);
export const logStockCount = (data: any) => api.post('/inventory/count', data);
export const getMargins = (stationId?: string) => api.get(stationId ? `/inventory/margins?station_id=${stationId}` : '/inventory/margins');
export const getExpiringItems = () => api.get('/inventory/expiring');

// Personnel
export const getPersonnel = () => api.get('/personnel');
export const createPerson = (data: any) => api.post('/personnel', data);
export const logMovement = (data: any) => api.post('/personnel/movement', data);
export const getWhereNow = () => api.get('/personnel/where-now');
export const getSorties = () => api.get('/personnel/sorties');
export const createSortie = (data: any) => api.post('/personnel/sorties', data);
export const checkInSortie = (sortieId: string, data: any) => api.post(`/personnel/sorties/${sortieId}/checkin`, data);
export const completeSortie = (sortieId: string) => api.post(`/personnel/sorties/${sortieId}/complete`);
export const checkEscalations = () => api.get('/personnel/sorties/check-escalations');

// Emergency
export const getIncidents = () => api.get('/incidents');
export const createIncident = (data: any) => api.post('/incidents', data);
export const addIncidentAction = (id: string, data: any) => api.post(`/incidents/${id}/action`, data);
export const getActiveIncidents = () => api.get('/incidents/active');

// Sync
export const triggerSync = () => api.post('/sync/trigger');
export const getSyncStatus = () => api.get('/sync/status');
export const getPendingEvents = () => api.get('/sync/pending');

// Admin
export const setLinkStatus = (stationId: string, status: string) => api.post(`/admin/link/${stationId}`, { status });
export const getLinkStatuses = () => api.get('/admin/link');
export const tamperEvent = (eventId: string) => api.post(`/admin/tamper/${eventId}`);

// Dashboard
export const getDashboardSummary = () => api.get('/dashboard/summary');

// Audit
export const verifyChain = () => api.get('/audit/verify');
export const getAuditEvents = (limit?: number, offset?: number) => api.get(`/audit/events?limit=${limit || 50}&offset=${offset || 0}`);

// Demo
export const runDemoStep = (step: number) => api.post(`/demo/step/${step}`);
export const getDemoStatus = () => api.get('/demo/status');

export default api;
