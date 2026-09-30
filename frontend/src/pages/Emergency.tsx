import { useState, useEffect } from 'react';
import { getIncidents, createIncident, addIncidentAction } from '../api';
import { TierBadge } from '../components/TierBadge';

export function Emergency() {
  const [incidents, setIncidents] = useState<any[]>([]);
  const [type, setType] = useState('MEDICAL');
  const [severity, setSeverity] = useState('AMBER');
  const [description, setDescription] = useState('');

  const fetchIncidents = async () => {
    try {
      const res = await getIncidents();
      setIncidents(res.data);
    } catch (e) {
      console.error(e);
    }
  };

  useEffect(() => {
    fetchIncidents();
    const interval = setInterval(fetchIncidents, 30000);
    return () => clearInterval(interval);
  }, []);

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await createIncident({ type, severity, description });
      fetchIncidents();
      setDescription('');
    } catch (e) {
      alert("Failed to create incident");
    }
  };

  const handleAction = async (id: string, action: string) => {
    try {
      await addIncidentAction(id, { action, timestamp: new Date().toISOString() });
      fetchIncidents();
    } catch (e) {
      alert("Failed to add action");
    }
  };

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-red-500 flex items-center gap-2">Emergency Response</h1>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="card lg:col-span-1 border-red-500/30 border-2">
          <h2 className="text-xl font-bold mb-4">Declare Emergency</h2>
          <form onSubmit={handleCreate} className="space-y-4">
            <select value={type} onChange={e => setType(e.target.value)} className="input-field" required>
              <option value="MEDICAL">MEDICAL</option>
              <option value="FIRE">FIRE</option>
              <option value="SYSTEM_FAILURE">SYSTEM FAILURE</option>
              <option value="MISSING_PERSON">MISSING PERSON</option>
              <option value="ENVIRONMENTAL">ENVIRONMENTAL</option>
            </select>
            <select value={severity} onChange={e => setSeverity(e.target.value)} className="input-field" required>
              <option value="AMBER">AMBER (Warning)</option>
              <option value="RED">RED (Critical)</option>
              <option value="BLACK">BLACK (Fatal/Loss of Asset)</option>
            </select>
            <textarea placeholder="Description of situation..." value={description} onChange={e => setDescription(e.target.value)} className="input-field h-32 py-3" required />
            <button type="submit" className="btn-danger w-full text-lg shadow-lg shadow-red-500/20">Declare Incident</button>
          </form>
        </div>

        <div className="lg:col-span-2 space-y-4">
          <h2 className="text-xl font-bold">Active Incidents</h2>
          {incidents.filter(i => i.status !== 'RESOLVED').map(inc => (
            <div key={inc.id} className="card border-l-4 border-l-red-500">
              <div className="flex justify-between items-start mb-4">
                <div>
                  <div className="flex items-center gap-3 mb-1">
                    <span className="font-bold text-lg">{inc.type}</span>
                    <TierBadge tier={inc.severity} />
                  </div>
                  <div className="text-sm text-slate-400">Declared: {new Date(inc.created_at).toLocaleString()}</div>
                </div>
                <div className="px-3 py-1 bg-slate-700 rounded font-bold">{inc.status}</div>
              </div>
              <p className="mb-4 bg-slate-900 p-3 rounded">{inc.description}</p>
              
              <div className="flex flex-wrap gap-2 mb-4">
                {inc.status === 'OPEN' && <button onClick={() => handleAction(inc.id, 'ACKNOWLEDGED')} className="btn-primary py-2 px-4">Acknowledge</button>}
                {(inc.status === 'OPEN' || inc.status === 'ACKNOWLEDGED') && <button onClick={() => handleAction(inc.id, 'RESPONDING')} className="btn-primary py-2 px-4 bg-amber-600 hover:bg-amber-700">Mark Responding</button>}
                <button onClick={() => handleAction(inc.id, 'RESOLVED')} className="btn-success py-2 px-4">Resolve</button>
              </div>

              {inc.actions?.length > 0 && (
                <div className="mt-4 pt-4 border-t border-slate-700">
                  <h4 className="text-sm font-bold text-slate-400 mb-2">Action Log</h4>
                  <ul className="space-y-2 text-sm">
                    {inc.actions.map((act: any) => (
                      <li key={act.id} className="flex gap-4">
                        <span className="text-slate-500">{new Date(act.timestamp).toLocaleTimeString()}</span>
                        <span className="font-medium text-blue-300">{act.action}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          ))}
          {incidents.filter(i => i.status !== 'RESOLVED').length === 0 && (
            <div className="card bg-green-500/10 border-green-500/30 text-green-400 text-center py-8">
              No active incidents.
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
