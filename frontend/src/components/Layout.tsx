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

// Role-based navigation permissions
const ROLE_PERMISSIONS: Record<string, string[]> = {
  HQ_PLANNER: ['/', '/expeditions', '/cargo', '/inventory', '/personnel', '/emergency', '/audit', '/sync', '/demo'],
  VOYAGE_LEADER: ['/', '/expeditions', '/cargo', '/personnel', '/emergency', '/demo'],
  STATION_LEAD: ['/', '/cargo', '/inventory', '/personnel', '/emergency', '/sync', '/demo'],
  MEDICAL_OFFICER: ['/', '/inventory', '/personnel', '/emergency', '/demo'],
};

export function Layout({ children }: { children: React.ReactNode }) {
  const { user, logout } = useAuth();
  const location = useLocation();
  const [sidebarOpen, setSidebarOpen] = useState(false);

  const allowedPaths = (user?.role && ROLE_PERMISSIONS[user.role]) || ROLE_PERMISSIONS.HQ_PLANNER;
  const visibleNavItems = NAV_ITEMS.filter(item => allowedPaths.includes(item.path));

  const roleLabels: Record<string, string> = {
    HQ_PLANNER: 'HQ Master Planner',
    VOYAGE_LEADER: 'Voyage Leader',
    STATION_LEAD: 'Station Lead',
    MEDICAL_OFFICER: 'Medical Officer',
  };

  return (
    <div className="flex h-screen bg-slate-900 text-white overflow-hidden">
      {/* Sidebar */}
      <div className={`fixed inset-y-0 left-0 z-50 w-64 bg-slate-800 transform transition-transform duration-200 ease-in-out md:relative md:translate-x-0 ${sidebarOpen ? 'translate-x-0' : '-translate-x-full'}`}>
        <div className="flex items-center justify-between h-16 px-4 bg-slate-900 border-b border-slate-700">
          <div className="flex items-center gap-2">
            <span className="text-xl font-bold tracking-wider text-blue-400">DHRUVA</span>
            <span className="text-xs px-1.5 py-0.5 bg-blue-900/60 text-blue-300 rounded border border-blue-700/50">2026</span>
          </div>
          <button className="md:hidden" onClick={() => setSidebarOpen(false)}>
            <Menu className="w-6 h-6" />
          </button>
        </div>

        {/* User Role Card in Sidebar */}
        <div className="p-3 mx-3 my-3 bg-slate-900/80 rounded-lg border border-slate-700/60">
          <div className="text-xs text-slate-400 uppercase tracking-wider font-semibold">Active Role</div>
          <div className="font-medium text-sm text-blue-300">{roleLabels[user?.role || ''] || user?.role}</div>
          <div className="text-xs text-slate-400 truncate">{user?.full_name || user?.username}</div>
          {user?.station_id && (
            <div className="mt-1 text-[11px] text-amber-400 font-mono">Station: {user.station_id.toUpperCase()}</div>
          )}
        </div>

        <nav className="p-3 space-y-1.5 overflow-y-auto h-[calc(100vh-10.5rem)]">
          {visibleNavItems.map((item) => {
            const Icon = item.icon;
            const active = location.pathname === item.path;
            return (
              <Link
                key={item.path}
                to={item.path}
                className={`flex items-center gap-3 px-4 py-3 rounded-lg transition-colors ${active ? 'bg-blue-600 text-white shadow-md' : 'text-slate-300 hover:bg-slate-700 hover:text-white'}`}
                onClick={() => setSidebarOpen(false)}
              >
                <Icon className="w-5 h-5" />
                <span className="font-medium text-sm">{item.label}</span>
              </Link>
            );
          })}
        </nav>
      </div>

      {/* Main Content */}
      <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
        {/* Topbar */}
        <header className="flex items-center justify-between h-16 px-4 sm:px-6 bg-slate-800 border-b border-slate-700">
          <div className="flex items-center gap-3">
            <button className="md:hidden text-slate-300 hover:text-white" onClick={() => setSidebarOpen(true)}>
              <Menu className="w-6 h-6" />
            </button>
            <div>
              <span className="font-semibold text-base sm:text-lg">{user?.full_name || user?.username}</span>
              <span className="ml-2.5 px-2.5 py-0.5 text-xs bg-blue-500/20 text-blue-300 border border-blue-500/30 rounded-full font-semibold">
                {user?.role?.replace('_', ' ')}
              </span>
            </div>
          </div>
          <div className="flex items-center gap-3 sm:gap-4">
            <div className="flex items-center gap-2 px-3 py-1 bg-slate-700/80 rounded-full border border-slate-600/50">
              <div className="w-2 h-2 rounded-full bg-green-500 animate-pulse"></div>
              <span className="text-xs sm:text-sm font-medium text-slate-200">
                {user?.station_id ? `${user.station_id.toUpperCase()} (LINK UP)` : 'HQ NODE (ONLINE)'}
              </span>
            </div>
            <button
              onClick={logout}
              title="Sign Out"
              className="flex items-center gap-1.5 px-3 py-1.5 text-slate-300 hover:text-white hover:bg-slate-700 rounded-lg transition-colors text-sm"
            >
              <LogOut className="w-4 h-4" />
              <span className="hidden sm:inline">Logout</span>
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
