import { useState, useEffect } from 'react';
import { getDashboardSummary } from '../api';
import { DashboardSummary } from '../types';
import { TierBadge } from '../components/TierBadge';
import { useAuth } from '../auth';

export function Dashboard() {
  const [data, setData] = useState<DashboardSummary | null>(null);
  const { user } = useAuth();

  useEffect(() => {
    const fetchStats = async () => {
      try {
        const res = await getDashboardSummary();
        setData(res.data);
      } catch (e) {
        console.error("Dashboard fetch failed", e);
      }
    };
    fetchStats();
    const interval = setInterval(fetchStats, 30000);
    return () => clearInterval(interval);
  }, []);

  if (!data) return <div className="text-white">Loading...</div>;

  return (
    <div className="space-y-6">
      <header>
        <h1 className="text-2xl font-bold text-white">Command Console - {user?.node_id || 'NCPOR HQ'}</h1>
      </header>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
        <div className="card flex flex-col gap-2">
          <span className="text-slate-400 text-sm font-semibold uppercase tracking-wider">Expeditions</span>
          <span className="text-2xl font-bold">{data.stats.expeditions} Active</span>
          <span className="text-xs text-slate-500">Next Leg: {data.stats.next_leg_date}</span>
        </div>
        <div className="card flex flex-col gap-2">
          <span className="text-slate-400 text-sm font-semibold uppercase tracking-wider">Cargo</span>
          <span className="text-2xl font-bold">{data.stats.crates_total} Crates</span>
          <span className="text-xs text-red-400">{data.stats.crates_overdue} Overdue</span>
        </div>
        <div className="card flex flex-col gap-2">
          <span className="text-slate-400 text-sm font-semibold uppercase tracking-wider">Inventory</span>
          <span className="text-2xl font-bold">{data.stats.inventory_items} Items</span>
          <span className="text-xs text-amber-400">{data.stats.inventory_alerts} Alerts</span>
        </div>
        <div className="card flex flex-col gap-2">
          <span className="text-slate-400 text-sm font-semibold uppercase tracking-wider">Personnel</span>
          <span className="text-2xl font-bold">{data.stats.personnel_total} Total</span>
          <span className="text-xs text-slate-500">{data.stats.personnel_on_station} On Station</span>
        </div>
        <div className="card flex flex-col gap-2">
          <span className="text-slate-400 text-sm font-semibold uppercase tracking-wider">Emergency</span>
          <span className="text-2xl font-bold">{data.stats.active_incidents} Active</span>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Survival Margin Heatmap */}
        <div className="card">
          <h2 className="text-xl font-bold mb-4">Survival Margin Heatmap</h2>
          <div className="overflow-x-auto">
            <table className="w-full text-sm text-left text-slate-300">
              <thead>
                <tr>
                  <th className="py-2">Station</th>
                  <th className="py-2">Item</th>
                  <th className="py-2">Days of Stock</th>
                  <th className="py-2">Tier</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-700">
                {Object.entries(data.margins).map(([station, margins]) =>
                  margins.map((m, idx) => (
                    <tr key={`${station}-${m.item_id}`} className="hover:bg-slate-700/50">
                      {idx === 0 && <td rowSpan={margins.length} className="py-2 align-top font-semibold">{station}</td>}
                      <td className="py-2">{m.item_name}</td>
                      <td className="py-2 font-mono">{m.days_of_stock}</td>
                      <td className="py-2"><TierBadge tier={m.tier} /></td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>

        {/* Alerts & Sorties */}
        <div className="space-y-6">
          <div className="card">
            <h2 className="text-xl font-bold mb-4">Active Alerts</h2>
            <div className="space-y-3">
              {data.active_alerts.map((alert, i) => (
                <div key={i} className="flex gap-3 items-start p-3 bg-slate-900 rounded-lg border border-slate-700">
                  <TierBadge tier={alert.tier} />
                  <span className="text-sm flex-1">{alert.text}</span>
                </div>
              ))}
              {data.active_alerts.length === 0 && <span className="text-slate-500">No active alerts.</span>}
            </div>
          </div>
          
          <div className="card">
            <h2 className="text-xl font-bold mb-4">Active Sorties</h2>
            <div className="space-y-3">
              {data.sorties.map(s => (
                <div key={s.id} className="p-3 bg-slate-900 rounded-lg border border-slate-700 flex justify-between items-center">
                  <div>
                    <div className="font-semibold">{s.name}</div>
                    <div className="text-xs text-slate-400">Expected return: {new Date(s.expected_return).toLocaleString()}</div>
                  </div>
                  <TierBadge tier={s.escalation_level === 'NORMAL' ? 'GREEN' : s.escalation_level === 'WARNING' ? 'AMBER' : 'RED'} label={s.escalation_level} />
                </div>
              ))}
              {data.sorties.length === 0 && <span className="text-slate-500">No active sorties.</span>}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
