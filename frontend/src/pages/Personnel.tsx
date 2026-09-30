import { useState, useEffect } from 'react';
import { getPersonnel, getWhereNow, getSorties, createSortie, checkInSortie, completeSortie, checkEscalations } from '../api';
import { TierBadge } from '../components/TierBadge';

export function Personnel() {
  const [personnel, setPersonnel] = useState<any[]>([]);
  const [whereNow, setWhereNow] = useState<Record<string, any[]>>({});
  const [sorties, setSorties] = useState<any[]>([]);

  // New sortie state
  const [sortieName, setSortieName] = useState('');
  const [selectedMembers, setSelectedMembers] = useState<string[]>([]);
  const [route, setRoute] = useState('');
  const [expectedReturn, setExpectedReturn] = useState('');
  const [checkInInterval, setCheckInInterval] = useState('60');

  const fetchData = async () => {
    try {
      const [pRes, wRes, sRes] = await Promise.all([getPersonnel(), getWhereNow(), getSorties()]);
      setPersonnel(pRes.data);
      setWhereNow(wRes.data);
      setSorties(sRes.data);
    } catch (e) {
      console.error(e);
    }
  };

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 30000);
    return () => clearInterval(interval);
  }, []);

  const handleCreateSortie = async (e: React.FormEvent) => {
    e.preventDefault();
    if (selectedMembers.length < 2) {
      alert("Buddy system requires at least 2 members.");
      return;
    }
    try {
      await createSortie({
        name: sortieName,
        members: selectedMembers,
        route,
        expected_return: new Date(expectedReturn).toISOString(),
        check_in_interval: parseInt(checkInInterval)
      });
      fetchData();
      setSortieName('');
      setSelectedMembers([]);
      setRoute('');
      setExpectedReturn('');
    } catch (e) {
      alert("Failed to create sortie");
    }
  };

  const handleCheckIn = async (id: string) => {
    try {
      await checkInSortie(id, { timestamp: new Date().toISOString(), status: 'OK' });
      fetchData();
    } catch (e) {
      alert("Failed to check in");
    }
  };

  const handleCompleteSortie = async (id: string) => {
    try {
      await completeSortie(id);
      fetchData();
    } catch (e) {
      alert("Failed to complete sortie");
    }
  };

  const handleCheckEscalations = async () => {
    try {
      await checkEscalations();
      fetchData();
    } catch (e) {
      alert("Failed to check escalations");
    }
  };

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">Personnel & Safety</h1>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="card space-y-4">
          <div className="flex justify-between items-center">
            <h2 className="text-xl font-bold">Active Sorties</h2>
            <button onClick={handleCheckEscalations} className="btn-primary py-2 px-4 text-sm">Check Escalations</button>
          </div>
          <div className="space-y-4">
            {sorties.map(s => (
              <div key={s.id} className="p-4 bg-slate-900 border border-slate-700 rounded-lg flex flex-col gap-4">
                <div className="flex justify-between items-start">
                  <div>
                    <h3 className="font-bold text-lg">{s.name}</h3>
                    <div className="text-sm text-slate-400">Route: {s.route}</div>
                    <div className="text-sm text-slate-400">Members: {s.members.length} personnel</div>
                  </div>
                  <TierBadge tier={s.escalation_level === 'NORMAL' ? 'GREEN' : s.escalation_level === 'WARNING' ? 'AMBER' : 'RED'} label={s.escalation_level} />
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <button onClick={() => handleCheckIn(s.id)} className="btn-success w-full h-16 text-lg shadow-lg">Check In NOW</button>
                  <button onClick={() => handleCompleteSortie(s.id)} className="btn-primary w-full h-16 bg-slate-600 hover:bg-slate-500">End Sortie</button>
                </div>
              </div>
            ))}
            {sorties.length === 0 && <p className="text-slate-400">No active sorties.</p>}
          </div>

          <div className="border-t border-slate-700 pt-4 mt-4">
            <h3 className="text-lg font-bold mb-3">Create Buddy Sortie</h3>
            <form onSubmit={handleCreateSortie} className="space-y-3">
              <input type="text" placeholder="Sortie Name" value={sortieName} onChange={e => setSortieName(e.target.value)} className="input-field" required />
              <select multiple value={selectedMembers} onChange={e => setSelectedMembers(Array.from(e.target.selectedOptions, option => option.value))} className="input-field h-24" required>
                {personnel.map(p => <option key={p.id} value={p.id}>{p.name} ({p.role})</option>)}
              </select>
              <p className="text-xs text-slate-400 mt-1">Hold Ctrl/Cmd to select multiple. Min 2 required.</p>
              <input type="text" placeholder="Route / Location" value={route} onChange={e => setRoute(e.target.value)} className="input-field" required />
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs text-slate-400 mb-1">Expected Return</label>
                  <input type="datetime-local" value={expectedReturn} onChange={e => setExpectedReturn(e.target.value)} className="input-field" required />
                </div>
                <div>
                  <label className="block text-xs text-slate-400 mb-1">Check-in Interval (min)</label>
                  <input type="number" value={checkInInterval} onChange={e => setCheckInInterval(e.target.value)} className="input-field" required />
                </div>
              </div>
              <button type="submit" className="btn-primary w-full">Start Sortie</button>
            </form>
          </div>
        </div>

        <div className="space-y-6">
          <div className="card">
            <h2 className="text-xl font-bold mb-4">Who is Where Now</h2>
            <div className="space-y-4">
              {Object.entries(whereNow).map(([loc, people]) => (
                <div key={loc} className="border border-slate-700 rounded-lg p-3">
                  <h3 className="font-bold text-slate-300 mb-2 border-b border-slate-700 pb-1">{loc}</h3>
                  <div className="flex flex-wrap gap-2">
                    {people.map(p => (
                      <span key={p.id} className="bg-slate-800 px-2 py-1 rounded text-sm">{p.name}</span>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div className="card overflow-x-auto">
            <h2 className="text-xl font-bold mb-4">Personnel Roster</h2>
            <table className="w-full text-sm text-left">
              <thead className="bg-slate-700">
                <tr>
                  <th className="px-3 py-2 rounded-tl-lg">Name</th>
                  <th className="px-3 py-2">Role</th>
                  <th className="px-3 py-2 rounded-tr-lg">Clearance</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-700">
                {personnel.map(p => (
                  <tr key={p.id}>
                    <td className="px-3 py-2 font-medium">{p.name}</td>
                    <td className="px-3 py-2">{p.role}</td>
                    <td className="px-3 py-2"><TierBadge tier={p.clearance_status === 'CLEARED' ? 'GREEN' : 'RED'} label={p.clearance_status} /></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
}
