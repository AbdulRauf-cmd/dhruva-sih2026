import { useState, useEffect } from 'react';
import { getExpeditions, createExpedition, delayLeg } from '../api';

export function Expeditions() {
  const [expeditions, setExpeditions] = useState<any[]>([]);
  
  useEffect(() => {
    loadExpeditions();
  }, []);

  const loadExpeditions = async () => {
    try {
      const res = await getExpeditions();
      setExpeditions(res.data);
    } catch (e) {
      console.error(e);
    }
  };

  const handleDelay = async (legId: string) => {
    const days = prompt("Enter days to delay:");
    if (days && !isNaN(Number(days))) {
      try {
        await delayLeg(legId, Number(days));
        loadExpeditions();
      } catch (e) {
        alert("Failed to delay leg");
      }
    }
  };

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">Expeditions</h1>
      {expeditions.map(exp => (
        <div key={exp.id} className="card space-y-4">
          <div className="flex justify-between items-center border-b border-slate-700 pb-2">
            <h2 className="text-xl font-bold">{exp.name} <span className="text-sm font-normal text-slate-400">({exp.status})</span></h2>
          </div>
          <div className="space-y-4 relative mt-6">
            <div className="w-full bg-slate-900 rounded-lg p-4 overflow-x-auto">
              <div className="min-w-[800px] space-y-2">
                {exp.legs?.map((leg: any) => {
                  const start = new Date(leg.start_date);
                  const end = new Date(leg.end_date);
                  const expStart = new Date(exp.legs[0].start_date);
                  const totalDuration = new Date(exp.legs[exp.legs.length-1].end_date).getTime() - expStart.getTime();
                  const left = ((start.getTime() - expStart.getTime()) / totalDuration) * 100;
                  const width = ((end.getTime() - start.getTime()) / totalDuration) * 100;

                  return (
                    <div key={leg.id} className="relative h-12 bg-slate-800 rounded">
                      <div 
                        className={`absolute h-full rounded flex items-center px-2 text-xs font-bold truncate ${leg.status === 'COMPLETED' ? 'bg-green-600' : leg.status === 'ACTIVE' ? 'bg-blue-600' : 'bg-slate-600'}`}
                        style={{ left: `${left}%`, width: `${width}%` }}
                        title={`${leg.vessel}: ${leg.from_node} -> ${leg.to_node}`}
                      >
                        {leg.vessel} ({leg.from_node}→{leg.to_node})
                      </div>
                      <div className="absolute right-0 top-0 h-full flex items-center pr-2">
                        <button onClick={() => handleDelay(leg.id)} className="text-xs bg-slate-700 hover:bg-slate-600 px-2 py-1 rounded">Delay</button>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}
