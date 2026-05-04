/**
 * Pramana AI — NLPCodingPanel
 * Perbandingan koding yang diklaim RS vs saran AI.
 * Supports: diagnosa utama, diagnosa sekunder, dan prosedur (ICD-9).
 * Ref: frontend-design.md §5.5
 */

import type { NLPCodingEntry } from '../../lib/mockData';

interface NLPCodingPanelProps {
  diagnosaUtama: NLPCodingEntry;
  diagnosaSekunder: NLPCodingEntry[];
  prosedur?: NLPCodingEntry[];
}

function ConfidenceBar({ value }: { value: number }) {
  const pct = Math.round(value * 100);
  return (
    <div style={{ marginTop: '8px' }}>
      <div className="confidence-bar-track">
        <div className="confidence-bar-fill" style={{ width: `${pct}%` }} />
      </div>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: '3px' }}>
        <span style={{ fontSize: '10px', color: 'var(--text-muted)' }}>Confidence</span>
        <span style={{ fontFamily: 'var(--font-mono)', fontSize: '11px', color: value >= 0.75 ? 'var(--risk-low)' : 'var(--risk-medium)', fontWeight: 500 }}>
          {pct}%{value < 0.75 ? ' ⚠' : ''}
        </span>
      </div>
    </div>
  );
}

function CodingRow({ entry, label }: { entry: NLPCodingEntry; label: string }) {
  return (
    <div style={{ marginBottom: '16px' }}>
      <p style={{ fontSize: '11px', fontWeight: 600, color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: '8px' }}>
        {label}
        {!entry.saran.match && (
          <span style={{ marginLeft: '10px', color: 'var(--risk-medium)', fontSize: '10px', background: 'var(--risk-medium-bg)', border: '1px solid var(--risk-medium-border)', padding: '2px 6px', borderRadius: '3px' }}>
            ⚠ MISMATCH TERDETEKSI
          </span>
        )}
        {entry.saran.match && (
          <span style={{ marginLeft: '10px', color: 'var(--risk-low)', fontSize: '10px', background: 'var(--risk-low-bg)', border: '1px solid var(--risk-low-border)', padding: '2px 6px', borderRadius: '3px' }}>
            ✓ SESUAI
          </span>
        )}
      </p>
      <div className="coding-pair">
        {/* RS */}
        <div className="coding-box">
          <p className="coding-box-label">Diklaim RS</p>
          <p className="coding-icd">{entry.diklaim.kode}</p>
          <p className="coding-desc">{entry.diklaim.desc}</p>
        </div>
        {/* AI */}
        <div className={`coding-box ${entry.saran.match ? 'match' : 'mismatch'}`}>
          <div style={{ display: 'flex', justifyContent: 'space-between' }}>
            <p className="coding-box-label">Saran AI</p>
            {entry.saran.match
              ? <span style={{ fontSize: '12px', color: 'var(--risk-low)' }}>✓</span>
              : <span style={{ fontSize: '12px', color: 'var(--risk-medium)' }}>⚠ FLAG</span>
            }
          </div>
          <p className="coding-icd">{entry.saran.kode}</p>
          <p className="coding-desc">{entry.saran.desc}</p>
          <ConfidenceBar value={entry.saran.confidence} />
        </div>
      </div>
      {entry.flag_reason && (
        <p style={{ fontSize: '12px', color: 'var(--risk-medium)', background: 'var(--risk-medium-bg)', border: '1px solid var(--risk-medium-border)', borderRadius: '4px', padding: '8px 12px', marginTop: '-4px' }}>
          ↑ {entry.flag_reason}
        </p>
      )}
    </div>
  );
}

/** Summary section: count matches and mismatches */
function CodingSummary({ diagnosaUtama, diagnosaSekunder, prosedur }: NLPCodingPanelProps) {
  const allEntries = [diagnosaUtama, ...diagnosaSekunder, ...(prosedur || [])];
  const matches = allEntries.filter((e) => e.saran.match).length;
  const mismatches = allEntries.filter((e) => !e.saran.match).length;
  const avgConfidence = allEntries.reduce((sum, e) => sum + e.saran.confidence, 0) / allEntries.length;

  return (
    <div style={{
      display: 'flex',
      gap: '20px',
      padding: '12px 0 16px',
      borderBottom: '1px solid var(--border-subtle)',
      marginBottom: '16px',
    }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
        <span style={{ width: '8px', height: '8px', borderRadius: '50%', backgroundColor: 'var(--risk-low)', display: 'inline-block' }} />
        <span style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>Sesuai:</span>
        <span style={{ fontFamily: 'var(--font-mono)', fontSize: '13px', fontWeight: 500, color: 'var(--risk-low)' }}>{matches}</span>
      </div>
      {mismatches > 0 && (
        <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
          <span style={{ width: '8px', height: '8px', borderRadius: '50%', backgroundColor: 'var(--risk-medium)', display: 'inline-block' }} />
          <span style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>Mismatch:</span>
          <span style={{ fontFamily: 'var(--font-mono)', fontSize: '13px', fontWeight: 500, color: 'var(--risk-medium)' }}>{mismatches}</span>
        </div>
      )}
      <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
        <span style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>Avg Confidence:</span>
        <span style={{
          fontFamily: 'var(--font-mono)',
          fontSize: '13px',
          fontWeight: 500,
          color: avgConfidence >= 0.75 ? 'var(--risk-low)' : 'var(--risk-medium)',
        }}>
          {Math.round(avgConfidence * 100)}%
        </span>
      </div>
    </div>
  );
}

export function NLPCodingPanel({ diagnosaUtama, diagnosaSekunder, prosedur }: NLPCodingPanelProps) {
  return (
    <div style={{ padding: '20px' }}>
      <CodingSummary
        diagnosaUtama={diagnosaUtama}
        diagnosaSekunder={diagnosaSekunder}
        prosedur={prosedur}
      />
      <CodingRow entry={diagnosaUtama} label="Diagnosa Utama (ICD-10)" />
      {diagnosaSekunder.map((entry, i) => (
        <CodingRow key={i} entry={entry} label={`Diagnosa Sekunder ${i + 1} (ICD-10)`} />
      ))}
      {prosedur && prosedur.length > 0 && (
        <>
          <div style={{ height: '1px', background: 'var(--border-subtle)', margin: '8px 0 16px' }} />
          {prosedur.map((entry, i) => (
            <CodingRow key={`p${i}`} entry={entry} label={`Prosedur ${i + 1} (ICD-9-CM)`} />
          ))}
        </>
      )}
    </div>
  );
}
