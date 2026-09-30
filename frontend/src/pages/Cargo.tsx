import { useState, useEffect } from 'react';
import { getCrates, logCheckpoint, getVesselPositions } from '../api';
import { TierBadge } from '../components/TierBadge';
import { MapContainer, TileLayer, Marker, Popup } from 'react-leaflet';
import { Html5QrcodeScanner } from 'html5-qrcode';
import { Package, Scan, AlertTriangle, ShieldCheck, MapPin, CheckCircle2 } from 'lucide-react';
import L from 'leaflet';

// Fix leaflet default marker icons in bundlers
delete (L.Icon.Default.prototype as any)._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png',
  iconUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png',
  shadowUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png',
});

export function Cargo() {
  const [crates, setCrates] = useState<any[]>([]);
  const [positions, setPositions] = useState<any[]>([]);
  const [scanning, setScanning] = useState(false);
  const [scannedId, setScannedId] = useState('');
  const [checkpointStatus, setCheckpointStatus] = useState('STORED');
  const [checkpointLoc, setCheckpointLoc] = useState('Station Maitri, Bay A1');
  const [filter, setFilter] = useState('ALL');

  const fetchData = async () => {
    try {
      const [cr, pos] = await Promise.all([getCrates(), getVesselPositions()]);
      setCrates(Array.isArray(cr.data) ? cr.data : []);
      setPositions(Array.isArray(pos.data) ? pos.data : []);
    } catch (e) {
      console.error('Error fetching cargo data:', e);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  useEffect(() => {
    let scanner: any = null;
    if (scanning) {
      try {
        scanner = new Html5QrcodeScanner('qr-reader', { fps: 10, qrbox: 250 }, false);
        scanner.render(
          (text: string) => {
            setScannedId(text);
            setScanning(false);
            scanner.clear();
          },
          (_err: any) => {}
        );
      } catch (e) {
        console.error('QR Scanner init error:', e);
      }
    }
    return () => {
      if (scanner) {
        scanner.clear().catch(() => {});
      }
    };
  }, [scanning]);

  const handleCheckpoint = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!scannedId) return;
    try {
      await logCheckpoint({
        crate_id: scannedId,
        checkpoint_type: checkpointStatus,
        location: checkpointLoc,
        condition_note: 'Verified in field',
      });
      setScannedId('');
      await fetchData();
      alert(`Checkpoint [${checkpointStatus}] logged successfully!`);
    } catch (err) {
      alert('Failed to log checkpoint');
    }
  };

  // Safe vessel position coordinate mapping (lon -> lng)
  const validPositions = positions
    .map(p => {
      const lat = typeof p.lat === 'number' ? p.lat : parseFloat(p.lat);
      const lng = typeof p.lon === 'number' ? p.lon : (typeof p.lng === 'number' ? p.lng : parseFloat(p.lon || p.lng));
      return {
        vessel: p.vessel_name || p.vessel || 'MV Vasundhara',
        lat,
        lng,
        notes: p.notes || '',
        speed: p.speed_knots || p.speed || 0,
      };
    })
    .filter(p => !isNaN(p.lat) && !isNaN(p.lng));

  const filteredCrates = crates.filter(c => {
    if (filter === 'ALL') return true;
    if (filter === 'HAZMAT') return Boolean(c.hazmat_class);
    return (c.status || 'CREATED') === filter;
  });

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h1 className="text-2xl font-bold text-white flex items-center gap-2">
            <Package className="w-6 h-6 text-blue-400" />
            Polar Cargo Tracking & Manifest
          </h1>
          <p className="text-sm text-slate-400 mt-1">
            End-to-end QR custody verification, IMDG hazmat segregation, and vessel voyage tracking
          </p>
        </div>
        <div className="flex items-center gap-3">
          <button
            onClick={() => setScanning(!scanning)}
            className="btn-primary flex items-center gap-2 text-sm px-4 py-2"
          >
            <Scan className="w-4 h-4" /> {scanning ? 'Close Camera' : 'Scan Crate QR'}
          </button>
        </div>
      </div>

      {scanning && (
        <div className="card max-w-md mx-auto border-2 border-blue-500 bg-slate-800">
          <div className="text-sm font-semibold mb-2 text-center text-blue-300">Point Camera at Crate QR Code</div>
          <div id="qr-reader" className="w-full bg-black text-white rounded overflow-hidden"></div>
        </div>
      )}

      {/* Checkpoint Quick Logger Form */}
      {scannedId && (
        <div className="card max-w-2xl mx-auto border-2 border-green-500 bg-slate-800/90 shadow-xl">
          <div className="flex justify-between items-center mb-3">
            <h2 className="font-bold text-lg text-green-300 flex items-center gap-2">
              <CheckCircle2 className="w-5 h-5 text-green-400" />
              Log Custody Checkpoint for Crate
            </h2>
            <button onClick={() => setScannedId('')} className="text-slate-400 hover:text-white text-sm">Cancel</button>
          </div>
          <div className="text-xs font-mono text-slate-300 bg-slate-900 p-2 rounded mb-4 break-all">
            Target ID: {scannedId}
          </div>
          <form onSubmit={handleCheckpoint} className="grid grid-cols-1 sm:grid-cols-3 gap-3">
            <div>
              <label className="text-xs text-slate-400 block mb-1">Status Transition</label>
              <select
                value={checkpointStatus}
                onChange={e => setCheckpointStatus(e.target.value)}
                className="input-field text-sm"
              >
                <option value="LOADED">LOADED</option>
                <option value="IN_TRANSIT">IN TRANSIT</option>
                <option value="OFFLOADED">OFFLOADED</option>
                <option value="STORED">STORED</option>
              </select>
            </div>
            <div>
              <label className="text-xs text-slate-400 block mb-1">Checkpoint Location</label>
              <input
                type="text"
                value={checkpointLoc}
                onChange={e => setCheckpointLoc(e.target.value)}
                placeholder="e.g. Maitri Bay A1"
                className="input-field text-sm"
                required
              />
            </div>
            <div className="flex items-end">
              <button type="submit" className="btn-success w-full text-sm font-semibold h-[48px]">
                Submit Checkpoint
              </button>
            </div>
          </form>
        </div>
      )}

      {/* Grid: Map + Crates */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left: Vessel Tracking Map */}
        <div className="lg:col-span-2 card flex flex-col">
          <div className="flex justify-between items-center mb-3">
            <h2 className="text-lg font-bold text-white flex items-center gap-2">
              <MapPin className="w-5 h-5 text-red-400" />
              Antarctic Vessel Positioning (AIS/Satellite)
            </h2>
            <span className="text-xs bg-slate-700 px-2.5 py-1 rounded-full text-slate-300">
              {validPositions.length} Vessel(s) Online
            </span>
          </div>

          <div className="h-[420px] rounded-lg overflow-hidden border border-slate-700 relative z-0">
            <MapContainer
              center={validPositions.length > 0 ? [validPositions[0].lat, validPositions[0].lng] : [-70.0, 30.0]}
              zoom={3}
              style={{ height: '100%', width: '100%', background: '#0f172a' }}
            >
              <TileLayer
                url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                attribution="&copy; OpenStreetMap"
              />
              {validPositions.map((p, i) => (
                <Marker key={i} position={[p.lat, p.lng]}>
                  <Popup>
                    <div className="text-slate-900 font-sans">
                      <div className="font-bold text-sm">{p.vessel}</div>
                      <div className="text-xs">Lat: {p.lat.toFixed(2)}, Lon: {p.lng.toFixed(2)}</div>
                      {p.notes && <div className="text-xs italic mt-1">{p.notes}</div>}
                    </div>
                  </Popup>
                </Marker>
              ))}
            </MapContainer>
          </div>
        </div>

        {/* Right: Crates List */}
        <div className="card flex flex-col h-[500px]">
          <div className="flex justify-between items-center mb-3">
            <h2 className="text-lg font-bold text-white">Cargo Crates ({filteredCrates.length})</h2>
            <select
              value={filter}
              onChange={e => setFilter(e.target.value)}
              className="bg-slate-700 text-xs px-2.5 py-1 rounded border border-slate-600 text-slate-200"
            >
              <option value="ALL">All Crates</option>
              <option value="HAZMAT">Hazmat Only</option>
              <option value="CREATED">Created</option>
              <option value="LOADED">Loaded</option>
              <option value="STORED">Stored</option>
            </select>
          </div>

          <div className="overflow-y-auto space-y-3 flex-1 pr-1">
            {filteredCrates.map(c => {
              const crateId = c.crate_id || c.id;
              const crit = c.criticality_class || c.criticality || 'C3';
              const isHazmat = Boolean(c.hazmat_class);
              return (
                <div
                  key={crateId}
                  onClick={() => setScannedId(crateId)}
                  className="p-3 bg-slate-900/90 rounded-lg border border-slate-700 hover:border-blue-500 cursor-pointer transition-colors"
                >
                  <div className="flex justify-between items-start gap-2 mb-1.5">
                    <span className="font-mono text-xs font-bold text-blue-400 truncate max-w-[170px]" title={crateId}>
                      {crateId.slice(0, 13)}...
                    </span>
                    <div className="flex items-center gap-1.5">
                      {isHazmat && (
                        <span className="px-1.5 py-0.5 bg-amber-500/20 text-amber-300 border border-amber-500/30 text-[10px] rounded font-bold flex items-center gap-0.5">
                          <AlertTriangle className="w-3 h-3" /> HAZMAT
                        </span>
                      )}
                      <TierBadge tier={crit} />
                    </div>
                  </div>

                  <div className="text-sm font-medium text-slate-200 line-clamp-1">{c.contents}</div>

                  <div className="mt-2 pt-2 border-t border-slate-800 flex justify-between items-center text-xs text-slate-400">
                    <span>Dest: <span className="capitalize text-slate-300">{c.destination}</span></span>
                    <span className="px-2 py-0.5 bg-slate-800 rounded font-semibold text-white">
                      {c.status || 'CREATED'}
                    </span>
                  </div>
                </div>
              );
            })}

            {filteredCrates.length === 0 && (
              <div className="text-center py-10 text-slate-500 text-sm">
                No crates found matching filter.
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
