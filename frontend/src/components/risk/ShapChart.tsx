/**
 * Pramana AI — ShapChart
 * Horizontal bar chart untuk SHAP values (faktor risiko).
 * Ref: frontend-design.md §5.4
 */

// Menggunakan custom CSS bars (lebih ringan, animasi lebih presisi)

interface ShapFactor {
  feature: string;
  value: number;
  label: string;
}

interface ShapChartProps {
  score: number;
  factors: ShapFactor[];
}

const FEATURE_LABELS: Record<string, string> = {
  rasio_terhadap_ina_cbgs: 'Rasio vs INA-CBGs',
  tagihan_per_hari:        'Tagihan/Hari',
  pola_historis_rs:        'Pola Historis RS',
  los:                     'Length of Stay',
  diagnosa_utama:          'Diagnosa Utama',
};

export function ShapChart({ score, factors }: ShapChartProps) {
  const sorted = [...factors].sort((a, b) => Math.abs(b.value) - Math.abs(a.value));

  const data = sorted.map((f) => ({
    name: FEATURE_LABELS[f.feature] || f.feature,
    value: f.value,
    label: f.label,
    abs: Math.abs(f.value),
  }));

  // Risk score bar colour
  const scoreColor =
    score >= 70 ? 'var(--risk-high)' :
    score >= 40 ? 'var(--risk-medium)' :
    'var(--risk-low)';

  return (
    <div style={{ padding: '20px' }}>
      {/* Overall risk score bar */}
      <div style={{ marginBottom: '24px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
          <span style={{ fontFamily: 'var(--font-sans)', fontSize: '12px', color: 'var(--text-secondary)', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.06em' }}>
            Risk Score
          </span>
          <span style={{ fontFamily: 'var(--font-mono)', fontSize: '18px', fontWeight: 500, color: scoreColor }}>
            {score} / 100
          </span>
        </div>
        <div style={{ height: '8px', background: 'var(--bg-overlay)', borderRadius: '4px', overflow: 'hidden' }}>
          <div
            style={{
              height: '100%',
              width: `${score}%`,
              background: `linear-gradient(to right, var(--risk-low), var(--risk-medium) 60%, var(--risk-high))`,
              borderRadius: '4px',
              transition: 'width 600ms ease-out',
            }}
          />
        </div>
      </div>

      {/* Divider */}
      <div style={{ height: '1px', background: 'var(--border-subtle)', marginBottom: '16px' }} />

      {/* Faktor Pendorong */}
      <div style={{ marginBottom: '12px' }}>
        <p style={{ fontSize: '11px', fontWeight: 600, color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: '0.07em', marginBottom: '12px' }}>
          ↑ Faktor Risiko
        </p>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
          {data.filter(d => d.value > 0).map((d) => (
            <div key={d.name}>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '4px' }}>
                <span style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>{d.name}</span>
                <span style={{ fontFamily: 'var(--font-mono)', fontSize: '12px', color: 'var(--risk-high)', fontWeight: 500 }}>
                  +{d.value.toFixed(2)}
                </span>
              </div>
              <div style={{ height: '5px', background: 'var(--bg-overlay)', borderRadius: '3px', overflow: 'hidden' }}>
                <div
                  style={{
                    height: '100%',
                    width: `${Math.min(d.abs * 300, 100)}%`,
                    background: 'var(--risk-high)',
                    opacity: 0.8,
                    borderRadius: '3px',
                    transition: 'width 600ms ease-out',
                  }}
                />
              </div>
              {d.label && (
                <p style={{ fontSize: '11px', color: 'var(--text-muted)', marginTop: '3px' }}>{d.label}</p>
              )}
            </div>
          ))}
        </div>
      </div>

      {/* Faktor Penurun */}
      {data.some(d => d.value < 0) && (
        <div style={{ marginTop: '16px' }}>
          <p style={{ fontSize: '11px', fontWeight: 600, color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: '0.07em', marginBottom: '12px' }}>
            ↓ Faktor Penurun
          </p>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
            {data.filter(d => d.value < 0).map((d) => (
              <div key={d.name}>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '4px' }}>
                  <span style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>{d.name}</span>
                  <span style={{ fontFamily: 'var(--font-mono)', fontSize: '12px', color: 'var(--risk-low)', fontWeight: 500 }}>
                    {d.value.toFixed(2)}
                  </span>
                </div>
                <div style={{ height: '5px', background: 'var(--bg-overlay)', borderRadius: '3px', overflow: 'hidden' }}>
                  <div
                    style={{
                      height: '100%',
                      width: `${Math.min(d.abs * 300, 100)}%`,
                      background: 'var(--risk-low)',
                      opacity: 0.8,
                      borderRadius: '3px',
                      transition: 'width 600ms ease-out',
                    }}
                  />
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
