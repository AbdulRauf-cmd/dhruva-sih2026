import { useState, useEffect } from 'react';
import { getSyncStatus, triggerSync, setLinkStatus } from '../api';
import { RefreshCw, Radio, HardDrive, ArrowUpRight, CheckCircle2, AlertCircle } from 'lucide-react';

interface StationSyncInfo {
  node_id: string;
  link_status: 'UP' | 'DOWN';
  last_sync: string | null;
  pending_events: number;
}

export function SyncStatus() {
  const [statuses, setStatuses] = useState<StationSyncInfo[]>([
    { node_id: 'maitri', link_status: 'UP', last_sync: 'Up to date', pending_events: 0 },
    { node_id: 'bharati', link_status: 'UP', last_sync: 'Up to date', pending_events: 0 },
    { node_id: 'himadri', link_status: 'UP', last_sync: 'Up to date', pending_events: 0 },
  ]);
  const [syncing, setSyncing] = useState(false);
  const [lastRefreshed, setLastRefreshed] = useState<string>(new Date().toLocaleTimeString());

  const fetchStatus = async () => {
    try {
      const res = await getSyncStatus();
      if (Array.isArray(res.data)) {
        setStatuses(res.data);
      } else if (res.data && res.data.nodes) {
        setStatuses(res.data.nodes);
      } else if (res.data && typeof res.data === 'object') {
        setStatuses(prev => prev.map(s => ({
          ...s,
          link_status: (s.node_id === 'maitri' && res.data.link_state) ? res.data.link_state : s.link_status,
          pending_events: res.data.pending_count !== undefined ? res.data.pending_count : s.pending_events,
        })));
      }
      setLastRefreshed(new Date().toLocaleTimeString());
    } catch (e) {
      console.error('Error fetching sync status:', e);
    }
  };

  useEffect(() => {
    fetchStatus();
    const interval = setInterval(fetchStatus, 5000);
    return () => clearInterval(interval);
  }, []);

  const handleSync = async () => {
    setSyncing(true);
    try {
      await triggerSync();
      await fetchStatus();
      alert('Event synchronization triggered successfully.');
    } catch (e: any) {
      alert('Sync completed or station offline.');
      await fetchStatus();
    } finally {
      setSyncing(false);
    }
  };

  const handleToggleLink = async (nodeId: string, currentStatus: string) => {
    const nextStatus = currentStatus === 'UP' ? 'DOWN' : 'UP';
    try {
      await setLinkStatus(nodeId, nextStatus);
      setStatuses(prev => prev.map(s => s.node_id === nodeId ? { ...s, link_status: nextStatus } : s));
      await fetchStatus();
    } catch (e) {
      alert('Failed to toggle satellite link status.');
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h1 className="text-2xl font-bold text-white flex items-center gap-2">
            <Radio className="w-6 h-6 text-blue-400" />
            Polar Satellite Mesh & Sync Status
          </h1>
          <p className="text-sm text-slate-400 mt-1">
            Real-time link simulation and Lamport-clock event synchronization between Antarctic nodes and HQ
          </p>
        </div>
        <div className="flex items-center gap-3">
          <span className="text-xs text-slate-400">Refreshed: {lastRefreshed}</span>
          <button
            onClick={handleSync}
            disabled={syncing}
            className="btn-primary flex items-center gap-2 text-sm px-4 py-2"
          >
            <RefreshCw className={`w-4 h-4 ${syncing ? 'animate-spin' : ''}`} />
            {syncing ? 'Syncing...' : 'Trigger Sync'}
          </button>
        </div>
      </div>

      {/* Node Status Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {statuses.map(s => {
          const isUp = s.link_status === 'UP';
          return (
            <div
              key={s.node_id}
              className={`card border-t-4 transition-all duration-200 ${isUp ? 'border-t-green-500 shadow-green-950/20' : 'border-t-red-500 shadow-red-950/20'}`}
            >
              <div className="flex justify-between items-start mb-4">
                <div>
                  <div className="text-xs text-slate-400 uppercase tracking-wider font-semibold">Station Node</div>
                  <h2 className="text-2xl font-bold text-white capitalize">{s.node_id}</h2>
                </div>
                <button
                  onClick={() => handleToggleLink(s.node_id, s.link_status)}
                  className={`px-3 py-1.5 rounded-lg text-xs font-bold tracking-wider transition-colors flex items-center gap-1.5 ${isUp ? 'bg-green-500/20 text-green-400 border border-green-500/40 hover:bg-green-500/30' : 'bg-red-500/20 text-red-400 border border-red-500/40 hover:bg-red-500/30'}`}
                >
                  <span className={`w-2 h-2 rounded-full ${isUp ? 'bg-green-400 animate-pulse' : 'bg-red-400'}`}></span>
                  LINK {s.link_status}
                </button>
              </div>

              <div className="space-y-3 pt-2 border-t border-slate-700/60">
                <div className="flex justify-between text-sm items-center">
                  <span className="text-slate-400 flex items-center gap-1.5">
                    <Radio className="w-4 h-4 text-slate-500" /> Connection
                  </span>
                  <span className={`font-semibold ${isUp ? 'text-green-400' : 'text-red-400'}`}>
                    {isUp ? 'Online (Iridium Sat)' : 'Offline (Disconnected)'}
                  </span>
                </div>

                <div className="flex justify-between text-sm items-center">
                  <span className="text-slate-400 flex items-center gap-1.5">
                    <HardDrive className="w-4 h-4 text-slate-500" /> Pending Outbox
                  </span>
                  <span className={`px-2.5 py-0.5 rounded-full text-xs font-bold ${s.pending_events > 0 ? 'bg-amber-500/30 text-amber-300 border border-amber-500/50' : 'bg-slate-700/60 text-slate-300'}`}>
                    {s.pending_events} events
                  </span>
                </div>

                <div className="flex justify-between text-sm items-center">
                  <span className="text-slate-400">Sync Health</span>
                  <span className="text-slate-300 flex items-center gap-1 text-xs">
                    {s.pending_events === 0 && isUp ? (
                      <><CheckCircle2 className="w-3.5 h-3.5 text-green-400" /> Synced to HQ</>
                    ) : (
                      <><AlertCircle className="w-3.5 h-3.5 text-amber-400" /> Queue buffered</>
                    )}
                  </span>
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {/* Architectural Explainer Card */}
      <div className="card bg-slate-800/70 border border-slate-700">
        <h3 className="font-semibold text-base text-blue-300 mb-2 flex items-center gap-2">
          <ArrowUpRight className="w-4 h-4 text-blue-400" />
          Event Sourcing & Offline-First Protocol
        </h3>
        <p className="text-sm text-slate-300 leading-relaxed">
          When satellite connectivity drops, remote station nodes (Maitri & Bharati) continue writing events to local embedded SQLite storage with cryptographic SHA-256 hash chains. Upon reconnection, events are transmitted to HQ PostgreSQL and merged with Lamport logical timestamp ordering to resolve causal dependencies with zero merge conflicts.
        </p>
      </div>
    </div>
  );
}
