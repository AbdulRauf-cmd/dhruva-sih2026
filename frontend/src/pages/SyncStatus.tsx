import { useState, useEffect } from 'react';
import { getSyncStatus, triggerSync, setLinkStatus } from '../api';
import { SyncStatus as SyncStatusType } from '../types';

export function SyncStatus() {
  const [statuses, setStatuses] = useState<SyncStatusType[]>([]);
  const [syncing, setSyncing] = useState(false);

  const fetchStatus = async () => {
    try {
      const res = await getSyncStatus();
      setStatuses(res.data);
    } catch (e) {
      console.error(e);
    }
  };

  useEffect(() => {
    fetchStatus();
    const interval = setInterval(fetchStatus, 10000);
    return () => clearInterval(interval);
  }, []);

  const handleSync = async () => {
    setSyncing(true);
    try {
      await triggerSync();
      await fetchStatus();
    } catch (e) {
      alert("Sync failed");
    } finally {
      setSyncing(false);
    }
  };

  const handleToggleLink = async (nodeId: string, currentStatus: string) => {
    try {
      await setLinkStatus(nodeId, currentStatus === 'UP' ? 'DOWN' : 'UP');
      fetchStatus();
    } catch (e) {
      alert("Failed to toggle link");
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-bold">Satellite Link & Sync Status</h1>
        <button onClick={handleSync} disabled={syncing} className="btn-primary flex items-center gap-2">
          {syncing ? 'Syncing...' : 'Force Sync Now'}
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {statuses.map(s => (
          <div key={s.node_id} className={`card border-t-4 ${s.link_status === 'UP' ? 'border-t-green-500' : 'border-t-red-500'}`}>
            <div className="flex justify-between items-start mb-4">
              <h2 className="text-xl font-bold">{s.node_id}</h2>
              <button 
                onClick={() => handleToggleLink(s.node_id, s.link_status)}
                className={`px-3 py-1 rounded text-xs font-bold ${s.link_status === 'UP' ? 'bg-green-500/20 text-green-400' : 'bg-red-500/20 text-red-400'}`}
              >
                LINK {s.link_status}
              </button>
            </div>
            
            <div className="space-y-3">
              <div className="flex justify-between text-sm">
                <span className="text-slate-400">Last Sync</span>
                <span className="font-medium">{s.last_sync ? new Date(s.last_sync).toLocaleString() : 'Never'}</span>
              </div>
              <div className="flex justify-between text-sm items-center">
                <span className="text-slate-400">Pending Events</span>
                <span className={`px-2 py-1 rounded-full text-xs font-bold ${s.pending_events > 0 ? 'bg-amber-500 text-black' : 'bg-slate-700'}`}>
                  {s.pending_events}
                </span>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
