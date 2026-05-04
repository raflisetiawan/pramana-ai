/**
 * Pramana AI — Dashboard Triage
 * StatsHeader + ClaimTable + Filter. Verifikator menghabiskan 70% waktu di sini.
 * Ref: frontend-design.md §6.2
 *
 * Task 4.2.5: Statistik ringkas di header — total klaim, % per risk level
 */

import { useState, useEffect, useRef } from 'react';
import { AppSidebar } from '../components/layout/AppSidebar';
import { TopBar } from '../components/layout/TopBar';
import { ClaimTable } from '../components/claims/ClaimTable';
import { RiskBadge } from '../components/risk/RiskBadge';
import { MOCK_CLAIMS, MOCK_HOSPITALS, MOCK_STATS } from '../lib/mockData';

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
  suffix,
  trend,
  trendLabel,
  accent,
  subItems,
}: {
  label: string;
  value: number;
  suffix?: string;
  trend?: number;
  trendLabel?: string;
  accent?: string;
  subItems?: { label: string; value: string; color: string }[];
}) {
  const displayed = useCountUp(value);
  const trendUp = (trend ?? 0) > 0;

  return (
    <div className="stat-card">
      <p className="stat-card-label">{label}</p>
      <p className="stat-card-value" style={accent ? { color: accent } : {}}>
        {displayed.toLocaleString('id-ID')}{suffix && <span style={{ fontSize: '16px', opacity: 0.7 }}>{suffix}</span>}
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
      {subItems && (
        <div style={{ marginTop: '8px', display: 'flex', gap: '10px' }}>
          {subItems.map((item) => (
            <div key={item.label} style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
              <span style={{
                width: '8px',
                height: '8px',
                borderRadius: '50%',
                backgroundColor: item.color,
                display: 'inline-block',
                flexShrink: 0,
              }} />
              <span style={{ fontSize: '11px', color: 'var(--text-secondary)' }}>
                {item.label}
              </span>
              <span style={{
                fontFamily: 'var(--font-mono)',
                fontSize: '11px',
                fontWeight: 500,
                color: item.color,
              }}>
                {item.value}
              </span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

/* ── Risk Distribution Mini Bar ── */
function RiskDistributionBar({ pctHigh, pctMedium, pctLow }: { pctHigh: number; pctMedium: number; pctLow: number }) {
  return (
    <div style={{ marginTop: '10px' }}>
      <div style={{
        display: 'flex',
        height: '6px',
        borderRadius: '3px',
        overflow: 'hidden',
        backgroundColor: 'var(--bg-overlay)',
      }}>
        <div style={{ width: `${pctHigh}%`, backgroundColor: 'var(--risk-high)', transition: 'width 600ms ease-out' }} />
        <div style={{ width: `${pctMedium}%`, backgroundColor: 'var(--risk-medium)', transition: 'width 600ms ease-out' }} />
        <div style={{ width: `${pctLow}%`, backgroundColor: 'var(--risk-low)', transition: 'width 600ms ease-out' }} />
      </div>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: '6px' }}>
        <span style={{ fontSize: '10px', color: 'var(--risk-high)', fontFamily: 'var(--font-mono)', fontWeight: 500 }}>
          {pctHigh}% High
        </span>
        <span style={{ fontSize: '10px', color: 'var(--risk-medium)', fontFamily: 'var(--font-mono)', fontWeight: 500 }}>
          {pctMedium}% Med
        </span>
        <span style={{ fontSize: '10px', color: 'var(--risk-low)', fontFamily: 'var(--font-mono)', fontWeight: 500 }}>
          {pctLow}% Low
        </span>
      </div>
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
          {/* Stats Header — Task 4.2.5 */}
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
                {/* Card 1: Total Klaim + risk distribution bar */}
                <div className="stat-card">
                  <p className="stat-card-label">Total Klaim</p>
                  <p className="stat-card-value">{MOCK_STATS.total}</p>
                  <RiskDistributionBar
                    pctHigh={MOCK_STATS.pct_high}
                    pctMedium={MOCK_STATS.pct_medium}
                    pctLow={MOCK_STATS.pct_low}
                  />
                </div>

                {/* Card 2: High Risk + trend */}
                <StatCard
                  label="High Risk"
                  value={MOCK_STATS.high_risk}
                  trend={MOCK_STATS.high_risk_delta}
                  trendLabel="vs kemarin"
                  accent="var(--risk-high)"
                  subItems={[
                    { label: '', value: `${MOCK_STATS.pct_high}%`, color: 'var(--risk-high)' },
                  ]}
                />

                {/* Card 3: Menunggu Verifikasi */}
                <StatCard
                  label="Menunggu Verifikasi"
                  value={MOCK_STATS.pending}
                  accent="var(--status-pending)"
                />

                {/* Card 4: Diproses Hari Ini */}
                <StatCard
                  label="Diproses Hari Ini"
                  value={MOCK_STATS.processed_today}
                  accent="var(--risk-low)"
                />
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
            <ClaimTable claims={MOCK_CLAIMS} loading={loading} hospitals={MOCK_HOSPITALS} />
          </div>
        </div>
      </div>
    </div>
  );
}
