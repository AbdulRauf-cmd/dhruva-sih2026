import { Link, useLocation } from 'react-router-dom';
import { useAuth } from '../auth';
import { LayoutDashboard, Ship, Package, Warehouse, Users, AlertTriangle, Shield, RefreshCw, Play, LogOut, Menu } from 'lucide-react';
import { useState } from 'react';

const NAV_ITEMS = [
  { path: '/', label: 'Dashboard', icon: LayoutDashboard },
  { path: '/expeditions', label: 'Expeditions', icon: Ship },
  { path: '/cargo', label: 'Cargo', icon: Package },
  { path: '/inventory', label: 'Inventory', icon: Warehouse },
  { path: '/personnel', label: 'Personnel', icon: Users },
  { path: '/emergency', label: 'Emergency', icon: AlertTriangle },
  { path: '/audit', label: 'Audit Trail', icon: Shield },
  { path: '/sync', label: 'Sync Status', icon: RefreshCw },
  { path: '/demo', label: 'Demo', icon: Play },
];

export function Layout({ children }: { children: React.ReactNode }) {
  const { user, logout } = useAuth();
  const location = useLocation();
  const [sidebarOpen, setSidebarOpen] = useState(false);

  return (
    <div className="flex h-screen bg-slate-900 text-white overflow-hidden">
      {/* Sidebar */}
      <div className={`fixed inset-y-0 left-0 z-50 w-64 bg-slate-800 transform transition-transform duration-200 ease-in-out md:relative md:translate-x-0 ${sidebarOpen ? 'translate-x-0' : '-translate-x-full'}`}>
        <div className="flex items-center justify-between h-16 px-4 bg-slate-900 border-b border-slate-700">
          <span className="text-xl font-bold tracking-wider">DHRUVA</span>
          <button className="md:hidden" onClick={() => setSidebarOpen(false)}>
            <Menu className="w-6 h-6" />
          </button>
        </div>
        <nav className="p-4 space-y-2 overflow-y-auto h-[calc(100vh-4rem)]">
          {NAV_ITEMS.map((item) => {
            const Icon = item.icon;
            const active = location.pathname === item.path;
            return (
              <Link key={item.path} to={item.path} className={`flex items-center gap-3 px-4 py-3 rounded-lg transition-colors ${active ? 'bg-blue-600 text-white' : 'text-slate-300 hover:bg-slate-700 hover:text-white'}`} onClick={() => setSidebarOpen(false)}>
                <Icon className="w-5 h-5" />
                <span className="font-medium">{item.label}</span>
              </Link>
            );
          })}
        </nav>
      </div>

      {/* Main Content */}
      <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
        {/* Topbar */}
        <header className="flex items-center justify-between h-16 px-4 sm:px-6 bg-slate-800 border-b border-slate-700">
          <div className="flex items-center gap-4">
            <button className="md:hidden text-slate-300 hover:text-white" onClick={() => setSidebarOpen(true)}>
              <Menu className="w-6 h-6" />
            </button>
            <div className="hidden sm:block">
              <span className="font-semibold text-lg">{user?.node_id || 'HQ Planner'}</span>
              <span className="ml-2 px-2 py-1 text-xs bg-slate-700 rounded-full text-slate-300">{user?.role}</span>
            </div>
          </div>
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-2 px-3 py-1 bg-slate-700 rounded-full">
              <div className="w-2 h-2 rounded-full bg-green-500 animate-pulse"></div>
              <span className="text-sm font-medium">Link UP</span>
            </div>
            <div className="hidden sm:flex items-center gap-2">
              <span className="text-sm font-medium">{user?.username}</span>
            </div>
            <button onClick={logout} className="p-2 text-slate-300 hover:text-white hover:bg-slate-700 rounded-lg transition-colors">
              <LogOut className="w-5 h-5" />
            </button>
          </div>
        </header>

        {/* Page Content */}
        <main className="flex-1 overflow-auto p-4 sm:p-6 md:p-8 bg-slate-900">
          {children}
        </main>
      </div>
    </div>
  );
}
