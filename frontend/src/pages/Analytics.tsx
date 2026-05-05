/**
 * Pramana AI — Analytics Page (Mock)
 * Halaman analytics dengan charts dan statistik
 */

import { AppSidebar } from '../components/layout/AppSidebar';
import { TopBar } from '../components/layout/TopBar';

export default function AnalyticsPage() {
  return (
    <div className="app-layout">
      <AppSidebar />
      <div className="main-content">
        <TopBar title="Analytics & Insights" subtitle="Statistik dan tren verifikasi klaim" />
      
      <div className="page-content page-enter">
        {/* Stats Overview */}
        <div className="stats-grid" style={{ marginBottom: '24px' }}>
          <div className="stat-card">
            <div className="stat-card-label">Total Klaim (30 Hari)</div>
            <div className="stat-card-value">8,247</div>
            <div className="stat-card-trend trend-up">
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <polyline points="23 6 13.5 15.5 8.5 10.5 1 18" />
                <polyline points="17 6 23 6 23 12" />
              </svg>
              <span>+12.5% vs bulan lalu</span>
            </div>
          </div>

          <div className="stat-card">
            <div className="stat-card-label">Rata-rata Risk Score</div>
            <div className="stat-card-value">42.3</div>
            <div className="stat-card-trend trend-down">
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <polyline points="23 18 13.5 8.5 8.5 13.5 1 6" />
                <polyline points="17 18 23 18 23 12" />
              </svg>
              <span>-3.2% (membaik)</span>
            </div>
          </div>

          <div className="stat-card">
            <div className="stat-card-label">Waktu Verifikasi Rata-rata</div>
            <div className="stat-card-value" style={{ fontSize: '24px' }}>4.2 hari</div>
            <div className="stat-card-trend trend-down">
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <polyline points="23 18 13.5 8.5 8.5 13.5 1 6" />
                <polyline points="17 18 23 18 23 12" />
              </svg>
              <span>-2.1 hari (membaik)</span>
            </div>
          </div>

          <div className="stat-card">
            <div className="stat-card-label">Akurasi Model NLP</div>
            <div className="stat-card-value" style={{ fontSize: '24px' }}>94.7%</div>
            <div className="stat-card-trend trend-up">
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <polyline points="23 6 13.5 15.5 8.5 10.5 1 18" />
                <polyline points="17 6 23 6 23 12" />
              </svg>
              <span>+1.2%</span>
            </div>
          </div>
        </div>

        {/* Charts Grid */}
        <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: '20px', marginBottom: '24px' }}>
          {/* Trend Chart */}
          <div className="panel">
            <div className="panel-header">Tren Klaim per Hari (30 Hari Terakhir)</div>
            <div style={{ padding: '24px', height: '320px', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <div style={{ textAlign: 'center', color: 'var(--text-muted)' }}>
                <svg width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" style={{ margin: '0 auto 12px' }}>
                  <line x1="18" y1="20" x2="18" y2="10" />
                  <line x1="12" y1="20" x2="12" y2="4" />
                  <line x1="6" y1="20" x2="6" y2="14" />
                </svg>
                <p style={{ fontSize: '13px' }}>Chart akan ditampilkan di sini</p>
                <p style={{ fontSize: '11px', marginTop: '4px' }}>Menggunakan Recharts untuk visualisasi</p>
              </div>
            </div>
          </div>

          {/* Risk Distribution */}
          <div className="panel">
            <div className="panel-header">Distribusi Risk Level</div>
            <div style={{ padding: '24px' }}>
              {[
                { level: 'Low Risk', count: 5234, percentage: 63.5, color: 'var(--risk-low)' },
                { level: 'Medium Risk', count: 2156, percentage: 26.1, color: 'var(--risk-medium)' },
                { level: 'High Risk', count: 857, percentage: 10.4, color: 'var(--risk-high)' },
              ].map((item) => (
                <div key={item.level} style={{ marginBottom: '20px' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '6px' }}>
                    <span style={{ fontSize: '12px', color: 'var(--text-secondary)', fontWeight: 600 }}>{item.level}</span>
                    <span style={{ fontSize: '12px', fontFamily: 'var(--font-mono)', color: 'var(--text-primary)' }}>
                      {item.count.toLocaleString()} ({item.percentage}%)
                    </span>
                  </div>
                  <div style={{ height: '8px', background: 'var(--bg-elevated)', borderRadius: '4px', overflow: 'hidden' }}>
                    <div style={{ height: '100%', width: `${item.percentage}%`, background: item.color, transition: 'width 600ms ease-out' }} />
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Top Hospitals & Top Diagnoses */}
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px', marginBottom: '24px' }}>
          {/* Top Hospitals */}
          <div className="panel">
            <div className="panel-header">Top 5 Rumah Sakit (Volume Klaim)</div>
            <div style={{ padding: '20px' }}>
              <table style={{ width: '100%', fontSize: '13px' }}>
                <thead>
                  <tr style={{ borderBottom: '1px solid var(--border-subtle)' }}>
                    <th style={{ textAlign: 'left', padding: '8px 0', fontSize: '11px', fontWeight: 600, color: 'var(--text-secondary)', textTransform: 'uppercase' }}>#</th>
                    <th style={{ textAlign: 'left', padding: '8px 0', fontSize: '11px', fontWeight: 600, color: 'var(--text-secondary)', textTransform: 'uppercase' }}>Rumah Sakit</th>
                    <th style={{ textAlign: 'right', padding: '8px 0', fontSize: '11px', fontWeight: 600, color: 'var(--text-secondary)', textTransform: 'uppercase' }}>Klaim</th>
                    <th style={{ textAlign: 'right', padding: '8px 0', fontSize: '11px', fontWeight: 600, color: 'var(--text-secondary)', textTransform: 'uppercase' }}>Avg Risk</th>
                  </tr>
                </thead>
                <tbody>
                  {[
                    { rank: 1, name: 'RSUD Dr. Soetomo', claims: 1247, avgRisk: 38.2 },
                    { rank: 2, name: 'RS Haji Surabaya', claims: 982, avgRisk: 41.5 },
                    { rank: 3, name: 'RSUD Dr. Soedono', claims: 856, avgRisk: 45.1 },
                    { rank: 4, name: 'RS Islam Jemursari', claims: 743, avgRisk: 39.8 },
                    { rank: 5, name: 'RS Bhayangkara', claims: 621, avgRisk: 42.3 },
                  ].map((row) => (
                    <tr key={row.rank} style={{ borderBottom: '1px solid var(--border-subtle)' }}>
                      <td style={{ padding: '10px 0', color: 'var(--text-muted)' }}>{row.rank}</td>
                      <td style={{ padding: '10px 0', color: 'var(--text-primary)' }}>{row.name}</td>
                      <td style={{ padding: '10px 0', textAlign: 'right', fontFamily: 'var(--font-mono)', color: 'var(--text-primary)' }}>
                        {row.claims.toLocaleString()}
                      </td>
                      <td style={{ padding: '10px 0', textAlign: 'right', fontFamily: 'var(--font-mono)', color: row.avgRisk > 40 ? 'var(--risk-medium)' : 'var(--risk-low)' }}>
                        {row.avgRisk}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* Top Diagnoses */}
          <div className="panel">
            <div className="panel-header">Top 5 Diagnosa (Frekuensi)</div>
            <div style={{ padding: '20px' }}>
              <table style={{ width: '100%', fontSize: '13px' }}>
                <thead>
                  <tr style={{ borderBottom: '1px solid var(--border-subtle)' }}>
                    <th style={{ textAlign: 'left', padding: '8px 0', fontSize: '11px', fontWeight: 600, color: 'var(--text-secondary)', textTransform: 'uppercase' }}>#</th>
                    <th style={{ textAlign: 'left', padding: '8px 0', fontSize: '11px', fontWeight: 600, color: 'var(--text-secondary)', textTransform: 'uppercase' }}>Kode ICD</th>
                    <th style={{ textAlign: 'left', padding: '8px 0', fontSize: '11px', fontWeight: 600, color: 'var(--text-secondary)', textTransform: 'uppercase' }}>Diagnosa</th>
                    <th style={{ textAlign: 'right', padding: '8px 0', fontSize: '11px', fontWeight: 600, color: 'var(--text-secondary)', textTransform: 'uppercase' }}>Jumlah</th>
                  </tr>
                </thead>
                <tbody>
                  {[
                    { rank: 1, code: 'I10', name: 'Essential Hypertension', count: 1456 },
                    { rank: 2, code: 'E11.9', name: 'Type 2 Diabetes Mellitus', count: 1289 },
                    { rank: 3, code: 'N18.5', name: 'CKD Stage 5', count: 987 },
                    { rank: 4, code: 'I50.0', name: 'Congestive Heart Failure', count: 876 },
                    { rank: 5, code: 'J18.9', name: 'Pneumonia', count: 743 },
                  ].map((row) => (
                    <tr key={row.rank} style={{ borderBottom: '1px solid var(--border-subtle)' }}>
                      <td style={{ padding: '10px 0', color: 'var(--text-muted)' }}>{row.rank}</td>
                      <td style={{ padding: '10px 0', fontFamily: 'var(--font-mono)', color: 'var(--accent-secondary)', fontSize: '12px' }}>
                        {row.code}
                      </td>
                      <td style={{ padding: '10px 0', color: 'var(--text-primary)' }}>{row.name}</td>
                      <td style={{ padding: '10px 0', textAlign: 'right', fontFamily: 'var(--font-mono)', color: 'var(--text-primary)' }}>
                        {row.count.toLocaleString()}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>

        {/* Model Performance */}
        <div className="panel">
          <div className="panel-header">Performa Model AI</div>
          <div style={{ padding: '24px' }}>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '24px' }}>
              {[
                { metric: 'Precision', value: '92.4%', desc: 'Akurasi prediksi positif' },
                { metric: 'Recall', value: '89.7%', desc: 'Deteksi anomali yang benar' },
                { metric: 'F1 Score', value: '91.0%', desc: 'Harmonic mean P & R' },
                { metric: 'AUC-ROC', value: '0.947', desc: 'Area under curve' },
              ].map((item) => (
                <div key={item.metric} style={{ textAlign: 'center' }}>
                  <div style={{ fontSize: '11px', color: 'var(--text-secondary)', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: '8px' }}>
                    {item.metric}
                  </div>
                  <div style={{ fontFamily: 'var(--font-mono)', fontSize: '32px', fontWeight: 500, color: 'var(--text-primary)', lineHeight: 1, marginBottom: '6px' }}>
                    {item.value}
                  </div>
                  <div style={{ fontSize: '11px', color: 'var(--text-muted)' }}>
                    {item.desc}
                  </div>
                </div>
              ))}
            </div>

            <div className="divider" />

            <div style={{ display: 'flex', gap: '32px', justifyContent: 'center' }}>
              <div style={{ textAlign: 'center' }}>
                <div style={{ fontSize: '11px', color: 'var(--text-secondary)', marginBottom: '6px' }}>Model Version</div>
                <div style={{ fontFamily: 'var(--font-mono)', fontSize: '14px', color: 'var(--text-primary)' }}>
                  rf_xgb_ensemble_v1.2
                </div>
              </div>
              <div style={{ textAlign: 'center' }}>
                <div style={{ fontSize: '11px', color: 'var(--text-secondary)', marginBottom: '6px' }}>Last Trained</div>
                <div style={{ fontFamily: 'var(--font-mono)', fontSize: '14px', color: 'var(--text-primary)' }}>
                  15 Jan 2025
                </div>
              </div>
              <div style={{ textAlign: 'center' }}>
                <div style={{ fontSize: '11px', color: 'var(--text-secondary)', marginBottom: '6px' }}>Training Samples</div>
                <div style={{ fontFamily: 'var(--font-mono)', fontSize: '14px', color: 'var(--text-primary)' }}>
                  10,247
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Coming Soon Notice */}
        <div style={{ marginTop: '32px', padding: '20px', background: 'var(--accent-glow)', border: '1px solid rgba(47,129,247,0.3)', borderRadius: '6px', textAlign: 'center' }}>
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="var(--accent-secondary)" strokeWidth="2" style={{ margin: '0 auto 8px' }}>
            <circle cx="12" cy="12" r="10" />
            <line x1="12" y1="16" x2="12" y2="12" />
            <line x1="12" y1="8" x2="12.01" y2="8" />
          </svg>
          <p style={{ fontSize: '13px', color: 'var(--accent-secondary)', fontWeight: 600, marginBottom: '4px' }}>
            Halaman Analytics dalam Pengembangan
          </p>
          <p style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>
            Chart interaktif dan export laporan akan tersedia di versi berikutnya
          </p>
        </div>
      </div>
      </div>
    </div>
  );
}
