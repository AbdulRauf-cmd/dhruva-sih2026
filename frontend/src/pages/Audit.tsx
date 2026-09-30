import { useState, useEffect } from 'react';
import { getAuditEvents, verifyChain, tamperEvent } from '../api';

export function Audit() {
  const [events, setEvents] = useState<any[]>([]);
  const [verifyResult, setVerifyResult] = useState<any>(null);
  const [loading, setLoading] = useState(false);

  const fetchEvents = async () => {
    try {
      const res = await getAuditEvents(50, 0);
      setEvents(res.data);
    } catch (e) {
      console.error(e);
    }
  };

  useEffect(() => {
    fetchEvents();
  }, []);

  const handleVerify = async () => {
    setLoading(true);
    try {
      const res = await verifyChain();
      setVerifyResult(res.data);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  const handleTamper = async (id: string) => {
    if (!confirm("This will maliciously alter the event payload, breaking the hash chain. Continue?")) return;
    try {
      await tamperEvent(id);
      fetchEvents();
      setVerifyResult(null);
    } catch (e) {
      alert("Failed to tamper");
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-bold">Immutable Audit Trail</h1>
        <button onClick={handleVerify} disabled={loading} className="btn-primary">
          {loading ? 'Verifying...' : 'Verify Cryptographic Chain'}
        </button>
      </div>

      {verifyResult && (
        <div className={`card ${verifyResult.valid ? 'bg-green-900/30 border-green-500/50' : 'bg-red-900/30 border-red-500/50'}`}>
          <div className="flex items-center gap-3">
            <span className="text-2xl">{verifyResult.valid ? '✅' : '❌'}</span>
            <div>
              <h3 className={`font-bold ${verifyResult.valid ? 'text-green-400' : 'text-red-400'}`}>
                {verifyResult.valid ? 'Chain Verified Successfully' : 'Chain Integrity Compromised!'}
              </h3>
              <p className="text-sm text-slate-300">
                {verifyResult.valid 
                  ? `Checked ${verifyResult.checked_count} events. All cryptographic hashes match.` 
                  : `Broken at event index ${verifyResult.broken_at_index} (ID: ${verifyResult.broken_event_id}). Hash mismatch detected.`}
              </p>
            </div>
          </div>
        </div>
      )}

      <div className="card overflow-x-auto">
        <table className="w-full text-sm text-left font-mono">
          <thead className="text-xs uppercase bg-slate-700 text-slate-300">
            <tr>
              <th className="px-4 py-3 rounded-tl-lg">Lamport</th>
              <th className="px-4 py-3">Timestamp</th>
              <th className="px-4 py-3">Node</th>
              <th className="px-4 py-3">Type</th>
              <th className="px-4 py-3">Hash (Truncated)</th>
              <th className="px-4 py-3 rounded-tr-lg">Action</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-700">
            {events.map((e) => (
              <tr key={e.id} className="hover:bg-slate-700/50">
                <td className="px-4 py-3 text-blue-400">{e.lamport_clock}</td>
                <td className="px-4 py-3 text-slate-400">{new Date(e.created_at).toLocaleString()}</td>
                <td className="px-4 py-3 text-amber-400">{e.node_id}</td>
                <td className="px-4 py-3 font-bold">{e.event_type}</td>
                <td className="px-4 py-3 text-slate-500" title={e.hash}>{e.hash?.substring(0, 16)}...</td>
                <td className="px-4 py-3">
                  <button onClick={() => handleTamper(e.id)} className="text-xs bg-red-900/50 text-red-400 px-2 py-1 rounded hover:bg-red-900 transition-colors">Tamper</button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
