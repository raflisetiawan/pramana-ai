/**
 * Pramana AI — Claim Detail Page
 * Info klaim + Risk Score + NLP Coding + Aksi Verifikator + Audit Trail
 * Ref: frontend-design.md §6.3
 */

import { useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { AppSidebar } from '../components/layout/AppSidebar';
import { TopBar } from '../components/layout/TopBar';
import { RiskBadge } from '../components/risk/RiskBadge';
import { ShapChart } from '../components/risk/ShapChart';
import { NLPCodingPanel } from '../components/nlp/NLPCodingPanel';
import { ClaimStatusBadge } from '../components/claims/ClaimStatusBadge';
import { MOCK_CLAIMS, MOCK_RISK_SCORE, MOCK_NLP_RESULT, MOCK_AUDIT_TRAIL } from '../lib/mockData';
import { formatRupiah, formatDate, formatDateTime } from '../lib/formatters';

/* ── Audit Trail ── */
function AuditTrail() {
  return (
    <div className="audit-trail">
      {MOCK_AUDIT_TRAIL.map((entry) => (
        <div key={entry.id} className="audit-item">
          <div className="audit-dot" />
          <div className="audit-content">
            <p className="audit-meta">
              {formatDateTime(entry.timestamp)} &nbsp;·&nbsp; <strong style={{ color: 'var(--text-primary)', fontWeight: 500 }}>{entry.user}</strong>
              <span style={{ color: 'var(--text-muted)' }}> ({entry.role})</span>
            </p>
            <p className="audit-text">{entry.action}</p>
            {entry.note && (
              <div className="audit-note">"{entry.note}"</div>
            )}
          </div>
        </div>
      ))}
    </div>
  );
}

/* ── Action Panel ── */
function ActionPanel({ isVerified }: { isVerified: boolean }) {
  const [note, setNote] = useState('');
  const [selected, setSelected] = useState<'approve' | 'return' | 'escalate' | null>(null);
  const [submitted, setSubmitted] = useState(false);

  const handleAction = (action: 'approve' | 'return' | 'escalate') => {
    if (action === 'return' || action === 'escalate') {
      if (!note.trim()) { alert('Catatan wajib diisi untuk aksi ini.'); return; }
    }
    setSubmitted(true);
    // Simulasi submit
    setTimeout(() => {
      setSubmitted(false);
      setSelected(null);
      setNote('');
    }, 1500);
  };

  return (
    <div style={{ padding: '20px' }}>
      <div style={{ display: 'flex', gap: '10px', marginBottom: '16px', flexWrap: 'wrap' }}>
        <button
          className="btn btn-approve"
          disabled={isVerified || submitted}
          onClick={() => { setSelected('approve'); handleAction('approve'); }}
          id="action-approve-btn"
        >
          <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5"><polyline points="20 6 9 17 4 12"/></svg>
          Setujui Klaim
        </button>
        <button
          className="btn btn-return"
          disabled={isVerified || submitted}
          onClick={() => setSelected('return')}
          id="action-return-btn"
        >
          <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><polyline points="9 14 4 9 9 4"/><path d="M20 20v-7a4 4 0 0 0-4-4H4"/></svg>
          Kembalikan ke RS
        </button>
        <button
          className="btn btn-escalate"
          disabled={isVerified || submitted}
          onClick={() => setSelected('escalate')}
          id="action-escalate-btn"
        >
          <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><polyline points="18 15 12 9 6 15"/></svg>
          Eskalasi
        </button>
      </div>

      {/* Note field — tampil jika bukan approve */}
      {(selected === 'return' || selected === 'escalate') && (
        <div>
          <label className="form-label" htmlFor="action-note">
            Catatan <span style={{ color: 'var(--risk-high)' }}>*</span>
            <span style={{ color: 'var(--text-muted)', textTransform: 'none', fontSize: '11px', marginLeft: '4px' }}>(wajib)</span>
          </label>
          <textarea
            id="action-note"
            className="form-textarea"
            value={note}
            onChange={(e) => setNote(e.target.value)}
            placeholder="Berikan catatan untuk rumah sakit atau supervisor..."
          />
          <div style={{ display: 'flex', gap: '8px', marginTop: '10px' }}>
            <button
              className="btn btn-primary btn-sm"
              disabled={!note.trim() || submitted}
              onClick={() => handleAction(selected)}
              id={`action-confirm-btn`}
            >
              {submitted ? 'Memproses...' : 'Konfirmasi'}
            </button>
            <button className="btn btn-ghost btn-sm" onClick={() => setSelected(null)} id="action-cancel-btn">
              Batal
            </button>
          </div>
        </div>
      )}

      {isVerified && (
        <p style={{ fontSize: '12px', color: 'var(--text-muted)', marginTop: '8px' }}>
          ℹ Klaim ini sudah diverifikasi. Aksi tidak tersedia.
        </p>
      )}
    </div>
  );
}

/* ── Claim Detail Page ── */
export default function ClaimDetailPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();

  const claim = MOCK_CLAIMS.find((c) => c.id === id) || MOCK_CLAIMS[0];
  const isVerified = claim.status === 'approved' || claim.status === 'returned';

  // Build SHAP factors from mock
  const shapFactors = Object.entries(MOCK_RISK_SCORE.shap_values).map(([feature, value], i) => ({
    feature,
    value,
    label: MOCK_RISK_SCORE.top_risk_factors[i] || '',
  }));

  return (
    <div className="app-layout">
      <AppSidebar />

      <div className="main-content">
        <TopBar title={`Detail Klaim — ${claim.no_sep.slice(0, 12)}…`} subtitle="← Kembali ke Dashboard" />

        <div className="page-content page-enter">
          {/* Back */}
          <button
            className="btn btn-ghost btn-sm"
            onClick={() => navigate('/')}
            style={{ marginBottom: '16px' }}
            id="back-to-dashboard-btn"
          >
            ← Kembali ke Dashboard
          </button>

          {/* Top grid: Info + Risk Score */}
          <div className="claim-detail-grid" style={{ marginBottom: '20px' }}>
            {/* Info Klaim */}
            <div className="panel">
              <div className="panel-header" style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <span>Info Klaim</span>
                <ClaimStatusBadge status={claim.status} />
              </div>
              <div style={{ padding: '4px 20px 16px' }}>
                {[
                  { label: 'No. SEP', value: <span style={{ fontFamily: 'var(--font-mono)', fontSize: '13px' }}>{claim.no_sep}</span> },
                  { label: 'Rumah Sakit', value: claim.hospital },
                  { label: 'Diagnosa Utama', value: <><span style={{ fontFamily: 'var(--font-mono)', color: 'var(--accent-secondary)' }}>{claim.diagnosa_utama}</span> <span style={{ color: 'var(--text-secondary)', fontSize: '12px' }}>— {claim.diagnosa_utama_desc}</span></> },
                  { label: 'Total Tagihan', value: <span style={{ fontFamily: 'var(--font-mono)', color: claim.total_tagihan > claim.tarif_ina_cbgs ? 'var(--risk-medium)' : 'var(--text-primary)' }}>{formatRupiah(claim.total_tagihan)}</span> },
                  { label: 'Tarif INA-CBGs', value: <span style={{ fontFamily: 'var(--font-mono)' }}>{formatRupiah(claim.tarif_ina_cbgs)}</span> },
                  { label: 'Length of Stay', value: `${claim.los} hari` },
                  { label: 'Tgl Masuk', value: formatDate(claim.tgl_masuk) },
                  { label: 'Tgl Pulang', value: formatDate(claim.tgl_pulang) },
                  { label: 'Tgl Pengajuan', value: formatDate(claim.tgl_pengajuan) },
                ].map((row) => (
                  <div key={row.label} className="info-row">
                    <span className="info-label">{row.label}</span>
                    <span className="info-value">{row.value}</span>
                  </div>
                ))}
              </div>
            </div>

            {/* Risk Score Panel */}
            <div className="panel">
              <div className="panel-header" style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                <span>Risk Score</span>
                <RiskBadge score={MOCK_RISK_SCORE.risk_score} level={MOCK_RISK_SCORE.risk_level} size="md" />
              </div>
              <ShapChart score={MOCK_RISK_SCORE.risk_score} factors={shapFactors} />

              {/* Top risk factors */}
              {MOCK_RISK_SCORE.top_risk_factors.length > 0 && (
                <div style={{ padding: '0 20px 16px', borderTop: '1px solid var(--border-subtle)' }}>
                  <p style={{ fontSize: '11px', fontWeight: 600, color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: '0.06em', margin: '12px 0 8px' }}>
                    Temuan Utama
                  </p>
                  {MOCK_RISK_SCORE.top_risk_factors.map((f, i) => (
                    <p key={i} style={{ fontSize: '12px', color: 'var(--text-secondary)', display: 'flex', gap: '8px', alignItems: 'flex-start', marginBottom: '6px' }}>
                      <span style={{ color: 'var(--risk-high)', marginTop: '1px', flexShrink: 0 }}>⚠</span>
                      {f}
                    </p>
                  ))}
                </div>
              )}
            </div>
          </div>

          {/* NLP Coding Panel */}
          <div className="panel" style={{ marginBottom: '20px' }}>
            <div className="panel-header">Analisis Koding ICD (NLP Engine)</div>
            <NLPCodingPanel
              diagnosaUtama={MOCK_NLP_RESULT.diagnosa_utama}
              diagnosaSekunder={MOCK_NLP_RESULT.diagnosa_sekunder}
            />
          </div>

          {/* Action Panel */}
          <div className="panel" style={{ marginBottom: '20px' }}>
            <div className="panel-header">Ambil Keputusan</div>
            <ActionPanel isVerified={isVerified} />
          </div>

          {/* Audit Trail */}
          <div className="panel">
            <div className="panel-header">History Klaim</div>
            <AuditTrail />
          </div>
        </div>
      </div>
    </div>
  );
}
