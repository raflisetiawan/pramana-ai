/**
 * Pramana AI — Dashboard Layout Shell
 *
 * Placeholder page for the triage dashboard (Task 4.2).
 * Includes sidebar, header, and main content area.
 */

import { useAuthStore } from '../lib/auth';
import { useNavigate } from 'react-router-dom';

export default function Dashboard() {
  const user = useAuthStore((s) => s.user);
  const logout = useAuthStore((s) => s.logout);
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  return (
    <div className="min-h-screen gradient-bg flex">
      {/* Sidebar */}
      <aside className="w-64 bg-[var(--color-surface-secondary)]/80 backdrop-blur-xl border-r border-[var(--color-surface-border)] flex flex-col">
        {/* Brand */}
        <div className="p-5 border-b border-[var(--color-surface-border)]">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-lg gradient-accent flex items-center justify-center shadow-md shadow-blue-500/20">
              <svg xmlns="http://www.w3.org/2000/svg" className="w-5 h-5 text-white" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
              </svg>
            </div>
            <div>
              <h1 className="text-sm font-bold text-white leading-tight">Pramana AI</h1>
              <p className="text-[10px] text-[var(--color-text-muted)]">Smart-Claim Co-Pilot</p>
            </div>
          </div>
        </div>

        {/* Nav items */}
        <nav className="flex-1 p-3 space-y-1">
          <a
            href="/"
            className="flex items-center gap-3 px-3 py-2.5 rounded-lg bg-blue-500/10 text-blue-400 font-medium text-sm"
          >
            <svg xmlns="http://www.w3.org/2000/svg" className="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <rect x="3" y="3" width="7" height="7" />
              <rect x="14" y="3" width="7" height="7" />
              <rect x="14" y="14" width="7" height="7" />
              <rect x="3" y="14" width="7" height="7" />
            </svg>
            Dashboard Triage
          </a>
        </nav>

        {/* User info */}
        <div className="p-4 border-t border-[var(--color-surface-border)]">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-full bg-gradient-to-br from-blue-500 to-violet-500 flex items-center justify-center text-white text-xs font-bold">
              {user?.full_name?.charAt(0)?.toUpperCase() || 'U'}
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium text-white truncate">
                {user?.full_name || 'User'}
              </p>
              <p className="text-[11px] text-[var(--color-text-muted)] capitalize">
                {user?.role?.replace('_', ' ') || 'Verifikator'}
              </p>
            </div>
            <button
              onClick={handleLogout}
              title="Keluar"
              className="p-1.5 rounded-lg text-[var(--color-text-muted)] hover:text-red-400 hover:bg-red-500/10"
            >
              <svg xmlns="http://www.w3.org/2000/svg" className="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4" />
                <polyline points="16 17 21 12 16 7" />
                <line x1="21" y1="12" x2="9" y2="12" />
              </svg>
            </button>
          </div>
        </div>
      </aside>

      {/* Main content */}
      <main className="flex-1 p-6 overflow-auto">
        {/* Header stats */}
        <div className="mb-6">
          <h2 className="text-xl font-bold text-white mb-1">Dashboard Triage</h2>
          <p className="text-sm text-[var(--color-text-secondary)]">
            Verifikasi klaim BPJS dengan bantuan AI — Human-in-the-Loop
          </p>
        </div>

        {/* Stat cards placeholder */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
          {[
            { label: 'Total Klaim', value: '—', icon: '📋', color: 'blue' },
            { label: 'Low Risk', value: '—', icon: '🟢', color: 'green' },
            { label: 'Medium Risk', value: '—', icon: '🟡', color: 'yellow' },
            { label: 'High Risk', value: '—', icon: '🔴', color: 'red' },
          ].map((stat) => (
            <div key={stat.label} className="glass-card p-4">
              <div className="flex items-center justify-between mb-2">
                <span className="text-[var(--color-text-secondary)] text-sm">{stat.label}</span>
                <span className="text-lg">{stat.icon}</span>
              </div>
              <p className="text-2xl font-bold text-white">{stat.value}</p>
            </div>
          ))}
        </div>

        {/* Table placeholder */}
        <div className="glass-card p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-white">Daftar Klaim</h3>
            <div className="text-sm text-[var(--color-text-muted)]">
              Akan diimplementasi di Task 4.2
            </div>
          </div>
          <div className="text-center py-16 text-[var(--color-text-muted)]">
            <svg xmlns="http://www.w3.org/2000/svg" className="w-12 h-12 mx-auto mb-3 opacity-30" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
              <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
              <polyline points="14 2 14 8 20 8" />
              <line x1="16" y1="13" x2="8" y2="13" />
              <line x1="16" y1="17" x2="8" y2="17" />
              <polyline points="10 9 9 9 8 9" />
            </svg>
            <p>ClaimTable akan muncul di sini</p>
            <p className="text-xs mt-1">Komponen tabel, filter, dan sorting — Task 4.2</p>
          </div>
        </div>
      </main>
    </div>
  );
}
