import { useState } from 'react';
import { runDemoStep } from '../api';

export function Demo() {
  const [results, setResults] = useState<Record<number, any>>({});
  const [loading, setLoading] = useState<Record<number, boolean>>({});

  const steps = [
    { num: 1, title: "View Command Console", desc: "Fetches dashboard summary, shows margin heatmap and stats." },
    { num: 2, title: "Delay Ship Leg by 7 Days", desc: "Calls delay endpoint, shows before/after margins, items turning RED/BLACK." },
    { num: 3, title: "Set Maitri Link DOWN", desc: "Sets link to DOWN, confirms offline mode." },
    { num: 4, title: "Simulate Offline Operations", desc: "As station: logs consumption, scans crate as STORED, starts sortie, triggers missed check-in escalation." },
    { num: 5, title: "Restore Link & Sync", desc: "Sets link UP, triggers sync, shows events syncing to HQ." },
    { num: 6, title: "Tamper Detection", desc: "Tampers with an event, runs chain verification, shows broken link." }
  ];

  const handleExecute = async (stepNum: number) => {
    setLoading({ ...loading, [stepNum]: true });
    try {
      const res = await runDemoStep(stepNum);
      setResults({ ...results, [stepNum]: { success: true, data: res.data } });
    } catch (e: any) {
      setResults({ ...results, [stepNum]: { success: false, error: e.response?.data?.detail || e.message } });
    } finally {
      setLoading({ ...loading, [stepNum]: false });
    }
  };

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <div className="text-center mb-8">
        <h1 className="text-3xl font-bold mb-2">DHRUVA Demo Script</h1>
        <p className="text-slate-400">Follow these steps to see all features in action</p>
      </div>

      <div className="space-y-4">
        {steps.map(step => (
          <div key={step.num} className="card flex flex-col gap-4">
            <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
              <div>
                <h2 className="text-xl font-bold text-blue-400">Step {step.num}: {step.title}</h2>
                <p className="text-slate-300 text-sm mt-1">{step.desc}</p>
              </div>
              <button 
                onClick={() => handleExecute(step.num)} 
                disabled={loading[step.num]}
                className="btn-primary whitespace-nowrap min-w-[120px]"
              >
                {loading[step.num] ? 'Running...' : 'Execute'}
              </button>
            </div>

            {results[step.num] && (
              <div className={`p-4 rounded-lg text-sm font-mono overflow-x-auto ${results[step.num].success ? 'bg-slate-900 border border-slate-700' : 'bg-red-900/20 border border-red-500/50 text-red-300'}`}>
                {results[step.num].success ? (
                  <pre>{JSON.stringify(results[step.num].data, null, 2)}</pre>
                ) : (
                  <div>Error: {results[step.num].error}</div>
                )}
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
