import { Routes, Route, Navigate } from 'react-router-dom';
import { useAuth } from './auth';
import { Layout } from './components/Layout';
import { Login } from './pages/Login';
import { Dashboard } from './pages/Dashboard';
import { Expeditions } from './pages/Expeditions';
import { Cargo } from './pages/Cargo';
import { Inventory } from './pages/Inventory';
import { Personnel } from './pages/Personnel';
import { Emergency } from './pages/Emergency';
import { Audit } from './pages/Audit';
import { Demo } from './pages/Demo';
import { SyncStatus } from './pages/SyncStatus';

function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { user, loading } = useAuth();
  if (loading) return <div className="flex h-screen items-center justify-center bg-slate-900 text-white">Loading...</div>;
  if (!user) return <Navigate to="/login" />;
  return <Layout>{children}</Layout>;
}

function App() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route path="/" element={<ProtectedRoute><Dashboard /></ProtectedRoute>} />
      <Route path="/expeditions" element={<ProtectedRoute><Expeditions /></ProtectedRoute>} />
      <Route path="/cargo" element={<ProtectedRoute><Cargo /></ProtectedRoute>} />
      <Route path="/inventory" element={<ProtectedRoute><Inventory /></ProtectedRoute>} />
      <Route path="/personnel" element={<ProtectedRoute><Personnel /></ProtectedRoute>} />
      <Route path="/emergency" element={<ProtectedRoute><Emergency /></ProtectedRoute>} />
      <Route path="/audit" element={<ProtectedRoute><Audit /></ProtectedRoute>} />
      <Route path="/demo" element={<ProtectedRoute><Demo /></ProtectedRoute>} />
      <Route path="/sync" element={<ProtectedRoute><SyncStatus /></ProtectedRoute>} />
    </Routes>
  );
}

export default App;
