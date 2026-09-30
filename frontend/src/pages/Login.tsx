import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../auth';

export function Login() {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const { login } = useAuth();
  const navigate = useNavigate();

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      await login(username, password);
      navigate('/');
    } catch (err) {
      setError('Invalid credentials or network error.');
    } finally {
      setLoading(false);
    }
  };

  const autofill = (u: string, p: string) => {
    setUsername(u);
    setPassword(p);
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-slate-900 p-4">
      <div className="card max-w-md w-full">
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold text-white mb-2 tracking-wider">DHRUVA - ध्रुव</h1>
          <p className="text-slate-400 text-sm mb-1">Digital Hub for Resource Utilization & Voyage Administration</p>
          <p className="text-slate-500 text-xs">Indian Polar Programme - NCPOR</p>
        </div>

        {error && <div className="mb-4 p-3 bg-red-500/20 border border-red-500 text-red-300 rounded-lg text-sm">{error}</div>}

        <form onSubmit={handleLogin} className="space-y-4 mb-8">
          <div>
            <input type="text" value={username} onChange={e => setUsername(e.target.value)} placeholder="Username" className="input-field" required />
          </div>
          <div>
            <input type="password" value={password} onChange={e => setPassword(e.target.value)} placeholder="Password" className="input-field" required />
          </div>
          <button type="submit" disabled={loading} className="btn-primary w-full">
            {loading ? 'Authenticating...' : 'Sign In'}
          </button>
        </form>

        <div className="border-t border-slate-700 pt-6">
          <h3 className="text-sm font-semibold text-slate-300 mb-4">Demo Credentials (Click to auto-fill)</h3>
          <div className="overflow-x-auto">
            <table className="w-full text-sm text-left text-slate-400">
              <thead className="text-xs text-slate-300 uppercase bg-slate-700/50">
                <tr><th className="px-3 py-2 rounded-tl-lg">Role</th><th className="px-3 py-2">Username</th><th className="px-3 py-2 rounded-tr-lg">Password</th></tr>
              </thead>
              <tbody className="divide-y divide-slate-700">
                <tr className="hover:bg-slate-700 cursor-pointer transition-colors" onClick={() => autofill('admin', 'admin123')}>
                  <td className="px-3 py-2">HQ Planner</td><td className="px-3 py-2">admin</td><td className="px-3 py-2">admin123</td>
                </tr>
                <tr className="hover:bg-slate-700 cursor-pointer transition-colors" onClick={() => autofill('voyage1', 'voyage123')}>
                  <td className="px-3 py-2">Voyage Leader</td><td className="px-3 py-2">voyage1</td><td className="px-3 py-2">voyage123</td>
                </tr>
                <tr className="hover:bg-slate-700 cursor-pointer transition-colors" onClick={() => autofill('maitri_lead', 'maitri123')}>
                  <td className="px-3 py-2">Station Lead (Maitri)</td><td className="px-3 py-2">maitri_lead</td><td className="px-3 py-2">maitri123</td>
                </tr>
                <tr className="hover:bg-slate-700 cursor-pointer transition-colors" onClick={() => autofill('bharati_lead', 'bharati123')}>
                  <td className="px-3 py-2">Station Lead (Bharati)</td><td className="px-3 py-2">bharati_lead</td><td className="px-3 py-2">bharati123</td>
                </tr>
                <tr className="hover:bg-slate-700 cursor-pointer transition-colors" onClick={() => autofill('medical1', 'medical123')}>
                  <td className="px-3 py-2">Medical Officer</td><td className="px-3 py-2">medical1</td><td className="px-3 py-2">medical123</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
}
