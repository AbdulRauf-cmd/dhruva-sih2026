import { useState, useEffect } from 'react';
import { getCrates, logCheckpoint, getVesselPositions } from '../api';
import { TierBadge } from '../components/TierBadge';
import { MapContainer, TileLayer, Marker, Popup } from 'react-leaflet';
import { Html5QrcodeScanner } from 'html5-qrcode';
import { Package, Scan } from 'lucide-react';

export function Cargo() {
  const [crates, setCrates] = useState<any[]>([]);
  const [positions, setPositions] = useState<any[]>([]);
  const [scanning, setScanning] = useState(false);
  const [scannedId, setScannedId] = useState('');
  const [checkpointStatus, setCheckpointStatus] = useState('LOADED');
  const [checkpointLoc, setCheckpointLoc] = useState('');

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      const [cr, pos] = await Promise.all([getCrates(), getVesselPositions()]);
      setCrates(cr.data);
      setPositions(pos.data);
    } catch (e) {
      console.error(e);
    }
  };

  useEffect(() => {
    if (scanning) {
      const scanner = new Html5QrcodeScanner("qr-reader", { fps: 10, qrbox: 250 }, false);
      scanner.render((text) => {
        setScannedId(text);
        setScanning(false);
        scanner.clear();
      }, (err) => {});
      return () => { scanner.clear().catch(e => {}); };
    }
  }, [scanning]);

  const handleCheckpoint = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await logCheckpoint({ crate_id: scannedId, status: checkpointStatus, location: checkpointLoc });
      setScannedId('');
      fetchData();
      alert("Checkpoint logged!");
    } catch (err) {
      alert("Failed to log checkpoint");
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-bold">Cargo & Logistics</h1>
        <button onClick={() => setScanning(!scanning)} className="btn-primary flex items-center gap-2">
          <Scan className="w-5 h-5" /> {scanning ? 'Cancel Scan' : 'Scan QR'}
        </button>
      </div>

      {scanning && (
        <div className="card max-w-md mx-auto">
          <div id="qr-reader" className="w-full bg-white text-black"></div>
        </div>
      )}

      {scannedId && (
        <div className="card max-w-md mx-auto border-blue-500 border-2">
          <h2 className="font-bold mb-4 flex items-center gap-2"><Package/> Log Checkpoint for: {scannedId}</h2>
          <form onSubmit={handleCheckpoint} className="space-y-4">
            <select value={checkpointStatus} onChange={e => setCheckpointStatus(e.target.value)} className="input-field">
              <option value="LOADED">LOADED</option>
              <option value="IN_TRANSIT">IN TRANSIT</option>
              <option value="UNLOADED">UNLOADED</option>
              <option value="STORED">STORED</option>
            </select>
            <input type="text" value={checkpointLoc} onChange={e => setCheckpointLoc(e.target.value)} placeholder="Location" className="input-field" required />
            <button type="submit" className="btn-success w-full">Save Checkpoint</button>
          </form>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 card">
          <h2 className="text-xl font-bold mb-4">Vessel Tracking</h2>
          <div className="h-96 rounded-lg overflow-hidden border border-slate-700 relative z-0">
            <MapContainer center={[-70, 75]} zoom={3} style={{ height: '100%', width: '100%' }}>
              <TileLayer url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" />
              {positions.map((p, i) => (
                <Marker key={i} position={[p.lat, p.lng]}>
                  <Popup>{p.vessel}</Popup>
                </Marker>
              ))}
            </MapContainer>
          </div>
        </div>

        <div className="card overflow-y-auto max-h-[500px]">
          <h2 className="text-xl font-bold mb-4">Crates</h2>
          <div className="space-y-3">
            {crates.map(c => (
              <div key={c.id} className="p-3 bg-slate-900 rounded border border-slate-700 flex flex-col gap-2">
                <div className="flex justify-between items-start">
                  <span className="font-mono text-sm font-bold text-blue-400">{c.id}</span>
                  <TierBadge tier={c.criticality} />
                </div>
                <div className="text-sm">{c.contents}</div>
                <div className="text-xs text-slate-400 flex justify-between">
                  <span>Dest: {c.destination}</span>
                  <span className="font-bold text-white">{c.status}</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
