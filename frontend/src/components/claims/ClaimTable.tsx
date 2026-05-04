/**
 * Pramana AI — ClaimTable
 * Tabel utama verifikator. Kolom, hover, sticky header, high-risk row styling.
 * Ref: frontend-design.md §5.2
 */

import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import type { Claim } from '../../lib/types';
import { RiskBadge } from '../risk/RiskBadge';
import { ClaimStatusBadge } from './ClaimStatusBadge';
import { ClaimFilterBar, type FilterState } from './ClaimFilterBar';
import { formatRupiah, formatDate, maskPatientName, shortenHospitalName } from '../../lib/formatters';

interface ClaimTableProps {
  claims: Claim[];
  loading?: boolean;
}

function CopyableCode({ text }: { text: string }) {
  const [copied, setCopied] = useState(false);
  const copy = () => {
    navigator.clipboard.writeText(text).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 1500);
    });
  };
  return (
    <span
      className="copyable mono"
      onClick={(e) => { e.stopPropagation(); copy(); }}
      title={copied ? 'Disalin!' : 'Klik untuk salin'}
      style={{ fontFamily: 'var(--font-mono)', fontSize: '12px', cursor: 'copy', color: copied ? 'var(--accent-secondary)' : 'inherit' }}
    >
      {text}
    </span>
  );
}

function SkeletonTable() {
  return (
    <div style={{ padding: '12px 20px' }}>
      {Array.from({ length: 8 }).map((_, i) => (
        <div
          key={i}
          className="skeleton"
          style={{ height: '44px', marginBottom: '4px', borderRadius: '4px' }}
        />
      ))}
    </div>
  );
}

function EmptyState({ onReset }: { onReset: () => void }) {
  return (
    <div className="empty-state">
      <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1" opacity={0.4}>
        <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
        <polyline points="14 2 14 8 20 8"/>
        <line x1="16" y1="13" x2="8" y2="13"/>
        <line x1="16" y1="17" x2="8" y2="17"/>
      </svg>
      <p style={{ fontSize: '14px', color: 'var(--text-secondary)', margin: '4px 0' }}>Tidak ada klaim ditemukan</p>
      <p style={{ fontSize: '12px' }}>Coba ubah filter atau tanggal pencarian.</p>
      <button className="btn btn-ghost btn-sm" onClick={onReset} style={{ marginTop: '12px' }} id="empty-reset-btn">
        Reset Filter
      </button>
    </div>
  );
}

// ICD-10 tooltip hover
function IcdCell({ code, desc }: { code: string; desc: string }) {
  const [show, setShow] = useState(false);
  return (
    <span
      style={{ position: 'relative', cursor: 'default' }}
      onMouseEnter={() => setShow(true)}
      onMouseLeave={() => setShow(false)}
      title={desc}
    >
      <span style={{ fontFamily: 'var(--font-mono)', fontSize: '12px', color: 'var(--accent-secondary)' }}>{code}</span>
      {show && (
        <span style={{
          position: 'absolute',
          bottom: '100%',
          left: 0,
          background: 'var(--bg-elevated)',
          border: '1px solid var(--border-default)',
          borderRadius: '4px',
          padding: '6px 10px',
          fontSize: '12px',
          color: 'var(--text-primary)',
          whiteSpace: 'nowrap',
          zIndex: 10,
          marginBottom: '4px',
          boxShadow: '0 4px 12px rgba(0,0,0,0.4)',
        }}>
          {desc}
        </span>
      )}
    </span>
  );
}

export function ClaimTable({ claims, loading }: ClaimTableProps) {
  const navigate = useNavigate();
  const [sortDir, setSortDir] = useState<'asc' | 'desc'>('desc');
  const [filters, setFilters] = useState<FilterState>({ riskLevel: '', status: '', search: '' });

  const filtered = claims
    .filter((c) => !filters.riskLevel || c.risk_level === filters.riskLevel)
    .filter((c) => !filters.status || c.status === filters.status)
    .filter((c) => {
      const q = filters.search.toLowerCase();
      return !q || c.no_sep.toLowerCase().includes(q) || c.patient_name.toLowerCase().includes(q);
    })
    .sort((a, b) => sortDir === 'desc' ? b.risk_score - a.risk_score : a.risk_score - b.risk_score);

  const toggleSort = () => setSortDir((d) => d === 'desc' ? 'asc' : 'desc');

  if (loading) return <SkeletonTable />;

  return (
    <>
      <ClaimFilterBar
        filters={filters}
        onChange={setFilters}
        totalShown={filtered.length}
        totalAll={claims.length}
      />
      <div className="claim-table-wrapper" style={{ maxHeight: 'calc(100vh - 330px)' }}>
        {filtered.length === 0 ? (
          <EmptyState onReset={() => setFilters({ riskLevel: '', status: '', search: '' })} />
        ) : (
          <table className="claim-table">
            <thead>
              <tr>
                <th style={{ width: '140px' }}>Risk</th>
                <th style={{ width: '180px' }}>No. SEP</th>
                <th style={{ width: '150px' }}>Pasien</th>
                <th style={{ width: '200px' }}>RS Pengaju</th>
                <th style={{ width: '160px' }}>Diagnosa Utama</th>
                <th style={{ width: '130px' }} className="right">
                  <button
                    onClick={toggleSort}
                    style={{ background: 'none', border: 'none', color: 'inherit', cursor: 'pointer', fontWeight: 600, fontSize: '11px', letterSpacing: '0.07em', textTransform: 'uppercase', display: 'flex', alignItems: 'center', gap: '4px', marginLeft: 'auto' }}
                    id="sort-risk-btn"
                    title="Urutkan berdasarkan risk score"
                  >
                    Score {sortDir === 'desc' ? '↓' : '↑'}
                  </button>
                </th>
                <th style={{ width: '110px' }}>Tgl Pengajuan</th>
                <th style={{ width: '120px' }}>Status</th>
                <th style={{ width: '80px' }}>Aksi</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((c) => (
                <tr
                  key={c.id}
                  className={`${c.risk_level === 'high' ? 'high-risk' : ''} ${c.status === 'approved' ? 'verified' : ''}`}
                  onClick={() => navigate(`/claims/${c.id}`)}
                  tabIndex={0}
                  onKeyDown={(e) => e.key === 'Enter' && navigate(`/claims/${c.id}`)}
                >
                  <td>
                    <RiskBadge score={c.risk_score} level={c.risk_level} size="sm" />
                  </td>
                  <td>
                    <CopyableCode text={c.no_sep} />
                  </td>
                  <td style={{ fontSize: '13px' }}>{maskPatientName(c.patient_name)}</td>
                  <td style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>
                    {shortenHospitalName(c.hospital)}
                  </td>
                  <td>
                    <IcdCell code={c.diagnosa_utama} desc={c.diagnosa_utama_desc} />
                  </td>
                  <td className="right">
                    <span style={{ fontFamily: 'var(--font-mono)', fontSize: '12px', color: 'var(--text-secondary)' }}>
                      {formatRupiah(c.total_tagihan)}
                    </span>
                  </td>
                  <td style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>
                    {formatDate(c.tgl_pengajuan)}
                  </td>
                  <td><ClaimStatusBadge status={c.status} /></td>
                  <td>
                    <button
                      className="btn btn-ghost btn-sm"
                      onClick={(e) => { e.stopPropagation(); navigate(`/claims/${c.id}`); }}
                      id={`detail-btn-${c.id}`}
                    >
                      Detail →
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </>
  );
}
