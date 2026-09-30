import { useState, useEffect } from 'react';
import { getInventory, logConsumption, getMargins } from '../api';
import { TierBadge } from '../components/TierBadge';

export function Inventory() {
  const [inventory, setInventory] = useState<any[]>([]);
  const [margins, setMargins] = useState<any[]>([]);
  const [selectedItem, setSelectedItem] = useState('');
  const [consumeQty, setConsumeQty] = useState('');

  const fetchData = async () => {
    try {
      const [invRes, marRes] = await Promise.all([getInventory(), getMargins()]);
      setInventory(invRes.data);
      setMargins(marRes.data);
    } catch (e) {
      console.error(e);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const handleConsume = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedItem || !consumeQty) return;
    try {
      await logConsumption({ item_id: selectedItem, quantity: Number(consumeQty), date: new Date().toISOString() });
      setConsumeQty('');
      fetchData();
      alert('Consumption logged successfully');
    } catch (err) {
      alert('Failed to log consumption');
    }
  };

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">Inventory & Survival Margins</h1>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="card lg:col-span-1">
          <h2 className="text-xl font-bold mb-4">Quick Consume</h2>
          <form onSubmit={handleConsume} className="space-y-4">
            <select value={selectedItem} onChange={e => setSelectedItem(e.target.value)} className="input-field" required>
              <option value="">Select Item</option>
              {inventory.map(item => <option key={item.id} value={item.id}>{item.name} ({item.quantity} {item.unit})</option>)}
            </select>
            <input type="number" step="any" value={consumeQty} onChange={e => setConsumeQty(e.target.value)} placeholder="Quantity" className="input-field" required />
            <button type="submit" className="btn-primary w-full">Log Consumption</button>
          </form>
        </div>

        <div className="card lg:col-span-2">
          <h2 className="text-xl font-bold mb-4">Survival Margins</h2>
          <div className="space-y-3">
            {margins.map((m, i) => (
              <div key={i} className="p-4 bg-slate-900 rounded-lg border border-slate-700 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                <div>
                  <div className="font-bold text-lg">{m.item_name}</div>
                  <div className="text-sm text-slate-400">{m.alert_text}</div>
                </div>
                <div className="flex items-center gap-4">
                  <div className="text-2xl font-mono">{m.days_of_stock} <span className="text-sm text-slate-500">days</span></div>
                  <TierBadge tier={m.tier} />
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      <div className="card">
        <h2 className="text-xl font-bold mb-4">Stock Ledger</h2>
        <div className="overflow-x-auto">
          <table className="w-full text-sm text-left">
            <thead className="bg-slate-700 text-slate-300">
              <tr>
                <th className="px-4 py-3 rounded-tl-lg">Item Name</th>
                <th className="px-4 py-3">Category</th>
                <th className="px-4 py-3">Quantity</th>
                <th className="px-4 py-3">Unit</th>
                <th className="px-4 py-3 rounded-tr-lg">Criticality</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-700">
              {inventory.map(item => (
                <tr key={item.id} className="hover:bg-slate-700/50">
                  <td className="px-4 py-3 font-medium">{item.name}</td>
                  <td className="px-4 py-3">{item.category}</td>
                  <td className="px-4 py-3 font-mono">{item.quantity}</td>
                  <td className="px-4 py-3">{item.unit}</td>
                  <td className="px-4 py-3"><TierBadge tier={item.criticality} /></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
