/**
 * Pramana AI — NLPCodingPanel
 * Perbandingan koding yang diklaim RS vs saran AI.
 * Ref: frontend-design.md §5.5
 */

interface CodingEntry {
  diklaim: { kode: string; desc: string };
  saran:   { kode: string; desc: string; confidence: number; match: boolean };
  flag_reason?: string;
}

interface NLPCodingPanelProps {
  diagnosaUtama: CodingEntry;
  diagnosaSekunder: CodingEntry[];
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

function CodingRow({ entry, label }: { entry: CodingEntry; label: string }) {
  return (
    <div style={{ marginBottom: '16px' }}>
      <p style={{ fontSize: '11px', fontWeight: 600, color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: '8px' }}>
        {label}
        {!entry.saran.match && (
          <span style={{ marginLeft: '10px', color: 'var(--risk-medium)', fontSize: '10px', background: 'var(--risk-medium-bg)', border: '1px solid var(--risk-medium-border)', padding: '2px 6px', borderRadius: '3px' }}>
            ⚠ MISMATCH TERDETEKSI
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

export function NLPCodingPanel({ diagnosaUtama, diagnosaSekunder }: NLPCodingPanelProps) {
  return (
    <div style={{ padding: '20px' }}>
      <CodingRow entry={diagnosaUtama} label="Diagnosa Utama" />
      {diagnosaSekunder.map((entry, i) => (
        <CodingRow key={i} entry={entry} label={`Diagnosa Sekunder ${i + 1}`} />
      ))}
    </div>
  );
}
