/**
 * Pramana AI — Claim Detail Page
 * Layout dua kolom: info klaim (kiri) + analisis AI (kanan)
 * Panels: Info Klaim, Risk Score + SHAP, NLP Coding, Aksi Verifikator, Audit Trail
 * Ref: frontend-design.md §6.3
 *
 * Task 4.3.1 – 4.3.5
 */

import { useState, useCallback } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { AppSidebar } from '../components/layout/AppSidebar';
import { TopBar } from '../components/layout/TopBar';
import { RiskBadge } from '../components/risk/RiskBadge';
import { ShapChart } from '../components/risk/ShapChart';
import { NLPCodingPanel } from '../components/nlp/NLPCodingPanel';
import { ClaimStatusBadge } from '../components/claims/ClaimStatusBadge';
import {
  MOCK_CLAIMS,
  getRiskScoreForClaim,
  getNLPResultForClaim,
  getAuditTrailForClaim,
  type AuditEntry,
} from '../lib/mockData';
import { formatRupiah, formatDate, formatDateTime, maskPatientName } from '../lib/formatters';

/* ── Toast System ── */
type ToastType = 'success' | 'warning' | 'error' | 'info';

interface Toast {
  id: number;
  type: ToastType;
  message: string;
}

let toastCounter = 0;

function ToastContainer({ toasts, onDismiss }: { toasts: Toast[]; onDismiss: (id: number) => void }) {
  return (
    <div className="toast-container">
      {toasts.map((t) => (
        <div key={t.id} className={`toast ${t.type}`}>
          <span style={{ fontSize: '14px', flexShrink: 0 }}>
            {t.type === 'success' && '✓'}
            {t.type === 'warning' && '⚠'}
            {t.type === 'error' && '✕'}
            {t.type === 'info' && 'ℹ'}
          </span>
          <div style={{ flex: 1 }}>
            <p style={{ fontSize: '13px', color: 'var(--text-primary)' }}>{t.message}</p>
          </div>
          <button
            onClick={() => onDismiss(t.id)}
            style={{ background: 'none', border: 'none', color: 'var(--text-muted)', cursor: 'pointer', padding: '2px', fontSize: '14px' }}
            aria-label="Tutup"
          >
            ×
          </button>
        </div>
      ))}
    </div>
  );
}

/* ── Audit Trail ── */
function AuditTrail({ entries }: { entries: AuditEntry[] }) {
  const dotColor: Record<AuditEntry['action_type'], string> = {
    system: 'var(--text-muted)',
    ai: 'var(--accent-primary)',
    approve: 'var(--risk-low)',
    return: 'var(--risk-medium)',
    escalate: 'var(--status-escalated)',
    resubmit: 'var(--accent-secondary)',
  };

  return (
    <div className="audit-trail">
      {entries.map((entry) => (
        <div key={entry.id} className="audit-item">
          <div
            className="audit-dot"
            style={{
              backgroundColor: dotColor[entry.action_type] || 'var(--accent-primary)',
              boxShadow: `0 0 0 1px ${dotColor[entry.action_type] || 'var(--accent-primary)'}`,
            }}
          />
          <div className="audit-content">
            <p className="audit-meta">
              <span style={{ fontFamily: 'var(--font-mono)', fontSize: '11px' }}>
                {formatDateTime(entry.timestamp)}
              </span>
              &nbsp;·&nbsp;
              <strong style={{ color: 'var(--text-primary)', fontWeight: 500 }}>{entry.user}</strong>
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

/* ── Confirmation Dialog ── */
function ConfirmDialog({
  open,
  title,
  message,
  confirmLabel,
  confirmClass,
  onConfirm,
  onCancel,
}: {
  open: boolean;
  title: string;
  message: string;
  confirmLabel: string;
  confirmClass: string;
  onConfirm: () => void;
  onCancel: () => void;
}) {
  if (!open) return null;
  return (
    <div style={{
      position: 'fixed',
      inset: 0,
      zIndex: 9998,
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      backgroundColor: 'rgba(0,0,0,0.6)',
      animation: 'page-in 150ms ease-out',
    }}>
      <div style={{
        backgroundColor: 'var(--bg-surface)',
        border: '1px solid var(--border-default)',
        borderRadius: '6px',
        padding: '24px',
        maxWidth: '380px',
        width: '90%',
        boxShadow: '0 12px 40px rgba(0,0,0,0.5)',
      }}>
        <h3 style={{ fontFamily: 'var(--font-sans)', fontSize: '16px', fontWeight: 600, color: 'var(--text-primary)', marginBottom: '8px' }}>
          {title}
        </h3>
        <p style={{ fontSize: '13px', color: 'var(--text-secondary)', marginBottom: '20px', lineHeight: 1.5 }}>
          {message}
        </p>
        <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '8px' }}>
          <button className="btn btn-ghost btn-sm" onClick={onCancel} id="confirm-cancel-btn">
            Batal
          </button>
          <button className={`btn ${confirmClass} btn-sm`} onClick={onConfirm} id="confirm-ok-btn">
            {confirmLabel}
          </button>
        </div>
      </div>
    </div>
  );
}

/* ── Action Panel ── */
function ActionPanel({
  isVerified,
  claimId,
  onToast,
}: {
  isVerified: boolean;
  claimId: string;
  onToast: (type: ToastType, message: string) => void;
}) {
  const [note, setNote] = useState('');
  const [selected, setSelected] = useState<'approve' | 'return' | 'escalate' | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [showConfirm, setShowConfirm] = useState(false);
  const [pendingAction, setPendingAction] = useState<'approve' | 'return' | 'escalate' | null>(null);

  const handleAction = (action: 'approve' | 'return' | 'escalate') => {
    if ((action === 'return' || action === 'escalate') && !note.trim()) {
      onToast('warning', 'Catatan wajib diisi untuk aksi Kembalikan atau Eskalasi.');
      return;
    }
    setPendingAction(action);
    setShowConfirm(true);
  };

  const executeAction = () => {
    if (!pendingAction) return;
    setShowConfirm(false);
    setSubmitting(true);

    // Simulate API call
    setTimeout(() => {
      const actionLabels = {
        approve: 'disetujui',
        return: 'dikembalikan ke RS',
        escalate: 'dieskalasi ke supervisor',
      };
      const sepShort = MOCK_CLAIMS.find((c) => c.id === claimId)?.no_sep.slice(0, 12) || claimId;
      onToast('success', `Klaim #${sepShort}… berhasil ${actionLabels[pendingAction]}.`);

      setSubmitting(false);
      setSelected(null);
      setPendingAction(null);
      setNote('');
    }, 800);
  };

  const confirmMessages: Record<string, { title: string; message: string; label: string; cls: string }> = {
    approve: {
      title: 'Setujui Klaim',
      message: 'Apakah Anda yakin ingin menyetujui klaim ini? Tindakan ini akan mengubah status klaim menjadi "Disetujui".',
      label: 'Ya, Setujui',
      cls: 'btn-approve',
    },
    return: {
      title: 'Kembalikan ke RS',
      message: 'Klaim akan dikembalikan ke rumah sakit untuk revisi. Pastikan catatan sudah lengkap.',
      label: 'Ya, Kembalikan',
      cls: 'btn-return',
    },
    escalate: {
      title: 'Eskalasi ke Supervisor',
      message: 'Klaim akan dieskalasi ke supervisor untuk review lebih lanjut. Pastikan catatan sudah lengkap.',
      label: 'Ya, Eskalasi',
      cls: 'btn-escalate',
    },
  };

  const confirmConfig = pendingAction ? confirmMessages[pendingAction] : null;

  return (
    <>
      <div style={{ padding: '20px' }}>
        <div style={{ display: 'flex', gap: '10px', marginBottom: '16px', flexWrap: 'wrap' }}>
          <button
            className="btn btn-approve"
            disabled={isVerified || submitting}
            onClick={() => { setSelected('approve'); handleAction('approve'); }}
            id="action-approve-btn"
          >
            <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5"><polyline points="20 6 9 17 4 12"/></svg>
            Setujui Klaim
          </button>
          <button
            className="btn btn-return"
            disabled={isVerified || submitting}
            onClick={() => setSelected('return')}
            id="action-return-btn"
          >
            <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><polyline points="9 14 4 9 9 4"/><path d="M20 20v-7a4 4 0 0 0-4-4H4"/></svg>
            Kembalikan ke RS
          </button>
          <button
            className="btn btn-escalate"
            disabled={isVerified || submitting}
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
              <span style={{ color: 'var(--text-muted)', textTransform: 'none', fontSize: '11px', marginLeft: '4px' }}>(wajib untuk {selected === 'return' ? 'pengembalian' : 'eskalasi'})</span>
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
                disabled={!note.trim() || submitting}
                onClick={() => handleAction(selected)}
                id="action-confirm-btn"
              >
                {submitting ? 'Memproses...' : 'Konfirmasi'}
              </button>
              <button className="btn btn-ghost btn-sm" onClick={() => setSelected(null)} id="action-cancel-btn">
                Batal
              </button>
            </div>
          </div>
        )}

        {isVerified && (
          <div style={{
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            fontSize: '12px',
            color: 'var(--text-muted)',
            marginTop: '8px',
            padding: '10px',
            background: 'var(--bg-elevated)',
            borderRadius: '4px',
          }}>
            <span style={{ fontSize: '16px' }}>ℹ</span>
            Klaim ini sudah diverifikasi. Aksi tidak tersedia.
          </div>
        )}
      </div>

      {/* Confirmation dialog */}
      {confirmConfig && (
        <ConfirmDialog
          open={showConfirm}
          title={confirmConfig.title}
          message={confirmConfig.message}
          confirmLabel={confirmConfig.label}
          confirmClass={confirmConfig.cls}
          onConfirm={executeAction}
          onCancel={() => { setShowConfirm(false); setPendingAction(null); }}
        />
      )}
    </>
  );
}

/* ── Claim Info Ratio Tag ── */
function RatioTag({ tagihan, tarif }: { tagihan: number; tarif: number }) {
  const ratio = tarif > 0 ? tagihan / tarif : 0;
  const pctDiff = Math.round((ratio - 1) * 100);
  const isAbove = pctDiff > 0;

  if (Math.abs(pctDiff) < 1) {
    return <span style={{ fontFamily: 'var(--font-mono)', fontSize: '11px', color: 'var(--risk-low)' }}>≈ Sesuai tarif</span>;
  }

  return (
    <span style={{
      fontFamily: 'var(--font-mono)',
      fontSize: '11px',
      fontWeight: 500,
      color: isAbove ? 'var(--risk-high)' : 'var(--risk-low)',
      background: isAbove ? 'var(--risk-high-bg)' : 'var(--risk-low-bg)',
      border: `1px solid ${isAbove ? 'var(--risk-high-border)' : 'var(--risk-low-border)'}`,
      padding: '2px 6px',
      borderRadius: '3px',
    }}>
      {isAbove ? '▲' : '▼'} {Math.abs(pctDiff)}% {isAbove ? 'di atas' : 'di bawah'} INA-CBGs
    </span>
  );
}

/* ── Claim Detail Page ── */
export default function ClaimDetailPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();

  const claim = MOCK_CLAIMS.find((c) => c.id === id) || MOCK_CLAIMS[0];
  const isVerified = claim.status === 'approved' || claim.status === 'returned';

  // Per-claim data
  const riskScore = getRiskScoreForClaim(claim.id);
  const nlpResult = getNLPResultForClaim(claim.id);
  const auditTrail = getAuditTrailForClaim(claim.id);

  // Build SHAP factors
  const shapFactors = Object.entries(riskScore.shap_values).map(([feature, value], i) => ({
    feature,
    value,
    label: riskScore.top_risk_factors[i] || '',
  }));

  // Toast state
  const [toasts, setToasts] = useState<Toast[]>([]);

  const addToast = useCallback((type: ToastType, message: string) => {
    const id = ++toastCounter;
    setToasts((prev) => [...prev.slice(-1), { id, type, message }]); // max 2
    setTimeout(() => setToasts((prev) => prev.filter((t) => t.id !== id)), 4000);
  }, []);

  const dismissToast = useCallback((id: number) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  }, []);

  return (
    <div className="app-layout">
      <AppSidebar />

      <div className="main-content">
        <TopBar title={`Detail Klaim — ${claim.no_sep.slice(0, 12)}…`} subtitle={maskPatientName(claim.patient_name)} />

        <div className="page-content page-enter">
          {/* Back */}
          <button
            className="btn btn-ghost btn-sm"
            onClick={() => navigate('/')}
            style={{ marginBottom: '16px' }}
            id="back-to-dashboard-btn"
          >
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><polyline points="15 18 9 12 15 6"/></svg>
            Kembali ke Dashboard
          </button>

          {/* ═══ Task 4.3.1: Two-column layout ═══ */}
          <div className="claim-detail-grid" style={{ marginBottom: '20px' }}>
            {/* ─── LEFT: Info Klaim ─── */}
            <div className="panel">
              <div className="panel-header" style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <span>Info Klaim</span>
                <ClaimStatusBadge status={claim.status} />
              </div>
              <div style={{ padding: '4px 20px 16px' }}>
                {[
                  { label: 'No. SEP', value: <span style={{ fontFamily: 'var(--font-mono)', fontSize: '13px' }}>{claim.no_sep}</span> },
                  { label: 'Nama Pasien', value: <span style={{ fontSize: '13px' }}>{maskPatientName(claim.patient_name)}</span> },
                  { label: 'Rumah Sakit', value: claim.hospital },
                  {
                    label: 'Diagnosa Utama',
                    value: (
                      <>
                        <span style={{ fontFamily: 'var(--font-mono)', color: 'var(--accent-secondary)' }}>{claim.diagnosa_utama}</span>
                        <span style={{ color: 'var(--text-secondary)', fontSize: '12px' }}> — {claim.diagnosa_utama_desc}</span>
                      </>
                    ),
                  },
                  {
                    label: 'Total Tagihan',
                    value: (
                      <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flexWrap: 'wrap' }}>
                        <span style={{ fontFamily: 'var(--font-mono)', color: claim.total_tagihan > claim.tarif_ina_cbgs ? 'var(--risk-medium)' : 'var(--text-primary)' }}>
                          {formatRupiah(claim.total_tagihan)}
                        </span>
                        <RatioTag tagihan={claim.total_tagihan} tarif={claim.tarif_ina_cbgs} />
                      </div>
                    ),
                  },
                  { label: 'Tarif INA-CBGs', value: <span style={{ fontFamily: 'var(--font-mono)' }}>{formatRupiah(claim.tarif_ina_cbgs)}</span> },
                  {
                    label: 'Tagihan/Hari',
                    value: (
                      <span style={{ fontFamily: 'var(--font-mono)', fontSize: '12px', color: 'var(--text-secondary)' }}>
                        {claim.los > 0 ? formatRupiah(Math.round(claim.total_tagihan / claim.los)) : '—'}
                      </span>
                    ),
                  },
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

            {/* ─── RIGHT: Risk Score + SHAP (Task 4.3.3) ─── */}
            <div className="panel">
              <div className="panel-header" style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                <span>Faktor Risiko</span>
                <RiskBadge score={riskScore.risk_score} level={riskScore.risk_level} size="md" />
              </div>
              <ShapChart score={riskScore.risk_score} factors={shapFactors} />

              {/* Top risk factors */}
              {riskScore.top_risk_factors.length > 0 && (
                <div style={{ padding: '0 20px 16px', borderTop: '1px solid var(--border-subtle)' }}>
                  <p style={{ fontSize: '11px', fontWeight: 600, color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: '0.06em', margin: '12px 0 8px' }}>
                    Temuan Utama
                  </p>
                  {riskScore.top_risk_factors.map((f, i) => (
                    <p key={i} style={{ fontSize: '12px', color: 'var(--text-secondary)', display: 'flex', gap: '8px', alignItems: 'flex-start', marginBottom: '6px' }}>
                      <span style={{ color: 'var(--risk-high)', marginTop: '1px', flexShrink: 0 }}>⚠</span>
                      {f}
                    </p>
                  ))}
                </div>
              )}
            </div>
          </div>

          {/* ═══ Task 4.3.2: NLP Coding Panel ═══ */}
          <div className="panel" style={{ marginBottom: '20px' }}>
            <div className="panel-header" style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
              <span>Analisis Koding ICD (NLP Engine)</span>
              {nlpResult.prosedur.length > 0 && (
                <span style={{ fontSize: '10px', color: 'var(--text-muted)', fontWeight: 400, textTransform: 'none', letterSpacing: 0 }}>
                  {[
                    '1 diagnosa utama',
                    nlpResult.diagnosaSekunder.length > 0 ? `${nlpResult.diagnosaSekunder.length} sekunder` : null,
                    `${nlpResult.prosedur.length} prosedur`,
                  ].filter(Boolean).join(' · ')}
                </span>
              )}
            </div>
            <NLPCodingPanel
              diagnosaUtama={nlpResult.diagnosa_utama}
              diagnosaSekunder={nlpResult.diagnosa_sekunder}
              prosedur={nlpResult.prosedur}
            />
          </div>

          {/* ═══ Task 4.3.4: Action Panel ═══ */}
          <div className="panel" style={{ marginBottom: '20px' }}>
            <div className="panel-header">Ambil Keputusan</div>
            <ActionPanel isVerified={isVerified} claimId={claim.id} onToast={addToast} />
          </div>

          {/* ═══ Task 4.3.5: Audit Trail ═══ */}
          <div className="panel">
            <div className="panel-header" style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
              <span>History Klaim</span>
              <span style={{ fontSize: '10px', color: 'var(--text-muted)', fontWeight: 400, textTransform: 'none', letterSpacing: 0 }}>
                {auditTrail.length} entri
              </span>
            </div>
            <AuditTrail entries={auditTrail} />
          </div>
        </div>
      </div>

      {/* Toast notifications */}
      <ToastContainer toasts={toasts} onDismiss={dismissToast} />
    </div>
  );
}
