/**
 * Pramana AI — Dashboard Triage
 * StatsHeader + ClaimTable + Filter. Verifikator menghabiskan 70% waktu di sini.
 * Ref: frontend-design.md §6.2
 */

import { useState, useEffect, useRef } from 'react';
import { AppSidebar } from '../components/layout/AppSidebar';
import { TopBar } from '../components/layout/TopBar';
import { ClaimTable } from '../components/claims/ClaimTable';
import { RiskBadge } from '../components/risk/RiskBadge';
import { MOCK_CLAIMS, MOCK_STATS } from '../lib/mockData';

/* ── Count-up hook ── */
function useCountUp(target: number, duration = 800) {
  const [value, setValue] = useState(0);
  const started = useRef(false);
  useEffect(() => {
    if (started.current) return;
    started.current = true;
    const start = performance.now();
    const step = (now: number) => {
      const t = Math.min((now - start) / duration, 1);
      const ease = 1 - Math.pow(1 - t, 3);
      setValue(Math.round(ease * target));
      if (t < 1) requestAnimationFrame(step);
    };
    requestAnimationFrame(step);
  }, [target, duration]);
  return value;
}

/* ── Stat Card ── */
function StatCard({
  label,
  value,
  trend,
  trendLabel,
  accent,
}: {
  label: string;
  value: number;
  trend?: number;
  trendLabel?: string;
  accent?: string;
}) {
  const displayed = useCountUp(value);
  const trendUp = (trend ?? 0) > 0;

  return (
    <div className="stat-card">
      <p className="stat-card-label">{label}</p>
      <p className="stat-card-value" style={accent ? { color: accent } : {}}>
        {displayed.toLocaleString('id-ID')}
      </p>
      {trend !== undefined && (
        <p className={`stat-card-trend ${trendUp ? 'trend-up' : 'trend-down'}`}>
          <span>{trendUp ? '▲' : '▼'}</span>
          <span style={{ fontFamily: 'var(--font-mono)', fontSize: '11px' }}>
            {Math.abs(trend)}
          </span>
          {trendLabel && <span style={{ color: 'var(--text-muted)', marginLeft: '2px' }}>{trendLabel}</span>}
        </p>
      )}
    </div>
  );
}

/* ── Dashboard ── */
export default function Dashboard() {
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Simulasi fetch data
    const t = setTimeout(() => setLoading(false), 900);
    return () => clearTimeout(t);
  }, []);

  return (
    <div className="app-layout">
      <AppSidebar />

      <div className="main-content">
        <TopBar
          title="Dashboard Triage"
          subtitle="Verifikasi klaim BPJS dengan bantuan AI — Human-in-the-Loop"
        />

        <div className="page-content page-enter">
          {/* Stats Header */}
          <div className="stats-grid" style={{ marginBottom: '24px' }}>
            {loading ? (
              Array.from({ length: 4 }).map((_, i) => (
                <div key={i} className="stat-card">
                  <div className="skeleton" style={{ height: '12px', width: '60%', marginBottom: '12px', borderRadius: '3px' }} />
                  <div className="skeleton" style={{ height: '32px', width: '80%', marginBottom: '8px' }} />
                  <div className="skeleton" style={{ height: '10px', width: '40%' }} />
                </div>
              ))
            ) : (
              <>
                <StatCard label="Total Klaim Hari Ini" value={MOCK_STATS.total} />
                <StatCard
                  label="High Risk"
                  value={MOCK_STATS.high_risk}
                  trend={MOCK_STATS.high_risk_delta}
                  trendLabel="vs kemarin"
                  accent="var(--risk-high)"
                />
                <StatCard label="Menunggu Verifikasi" value={MOCK_STATS.pending} accent="var(--status-pending)" />
                <StatCard label="Diproses Hari Ini"   value={MOCK_STATS.processed_today} accent="var(--risk-low)" />
              </>
            )}
          </div>

          {/* Klaim Table Panel */}
          <div className="panel">
            <div className="panel-header" style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
              <span>Daftar Klaim</span>
              <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
                {/* Risk legend */}
                {(['high', 'medium', 'low'] as const).map((l) => (
                  <RiskBadge key={l} score={0} level={l} showScore={false} size="sm" />
                ))}
              </div>
            </div>
            <ClaimTable claims={MOCK_CLAIMS} loading={loading} />
          </div>
        </div>
      </div>
    </div>
  );
}
