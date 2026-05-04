/**
 * Pramana AI — ShapChart
 * Horizontal bar chart untuk SHAP values (faktor risiko).
 * Uses Recharts BarChart for the factor bars + CSS for the risk score gauge.
 * Ref: frontend-design.md §5.4
 */

import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Cell,
  ResponsiveContainer,
  Tooltip,
} from 'recharts';

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
  jumlah_prosedur:         'Jumlah Prosedur',
};

/* Custom tooltip */
function ChartTooltip({ active, payload }: { active?: boolean; payload?: Array<{ payload: { name: string; value: number; label: string } }> }) {
  if (!active || !payload?.length) return null;
  const d = payload[0].payload;
  return (
    <div style={{
      background: 'var(--bg-elevated)',
      border: '1px solid var(--border-default)',
      borderRadius: '4px',
      padding: '8px 12px',
      boxShadow: '0 4px 12px rgba(0,0,0,0.4)',
      maxWidth: '240px',
    }}>
      <p style={{ fontSize: '12px', fontWeight: 600, color: 'var(--text-primary)', marginBottom: '4px' }}>
        {d.name}
      </p>
      <p style={{ fontFamily: 'var(--font-mono)', fontSize: '12px', color: d.value > 0 ? 'var(--risk-high)' : 'var(--risk-low)', marginBottom: '2px' }}>
        {d.value > 0 ? '+' : ''}{d.value.toFixed(2)}
      </p>
      {d.label && <p style={{ fontSize: '11px', color: 'var(--text-secondary)' }}>{d.label}</p>}
    </div>
  );
}

export function ShapChart({ score, factors }: ShapChartProps) {
  // Separate and sort by absolute value
  const positive = factors.filter(f => f.value > 0).sort((a, b) => b.value - a.value);
  const negative = factors.filter(f => f.value < 0).sort((a, b) => a.value - b.value);

  // Build chart data for Recharts: all factors combined, sorted by absolute value
  const allSorted = [...factors].sort((a, b) => Math.abs(b.value) - Math.abs(a.value));
  const chartData = allSorted.map((f) => ({
    name: FEATURE_LABELS[f.feature] || f.feature,
    value: f.value,
    absValue: Math.abs(f.value),
    label: f.label,
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

      {/* SHAP Bar Chart (Recharts) */}
      <p style={{ fontSize: '11px', fontWeight: 600, color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: '0.07em', marginBottom: '12px' }}>
        Faktor Kontribusi (SHAP Values)
      </p>

      <div style={{ width: '100%', height: chartData.length * 44 + 10 }}>
        <ResponsiveContainer width="100%" height="100%">
          <BarChart
            data={chartData}
            layout="vertical"
            margin={{ top: 0, right: 40, left: 0, bottom: 0 }}
            barSize={14}
          >
            <XAxis
              type="number"
              hide
              domain={['dataMin', 'dataMax']}
            />
            <YAxis
              type="category"
              dataKey="name"
              tick={{ fontSize: 11, fill: '#8B949E' }}
              width={120}
              tickLine={false}
              axisLine={false}
            />
            <Tooltip
              content={<ChartTooltip />}
              cursor={{ fill: 'var(--bg-overlay)', opacity: 0.5 }}
            />
            <Bar
              dataKey="value"
              radius={[3, 3, 3, 3]}
              animationBegin={200}
              animationDuration={600}
              animationEasing="ease-out"
              label={({ x, y, width: w, height: h, value }) => (
                <text
                  x={(x as number) + (w as number) + (value as number > 0 ? 6 : -6)}
                  y={(y as number) + (h as number) / 2}
                  fill={value as number > 0 ? '#B91C1C' : '#1A7F37'}
                  fontSize={11}
                  fontFamily="'IBM Plex Mono', monospace"
                  fontWeight={500}
                  dominantBaseline="central"
                  textAnchor={value as number > 0 ? 'start' : 'end'}
                >
                  {value as number > 0 ? '+' : ''}{(value as number).toFixed(2)}
                </text>
              )}
            >
              {chartData.map((entry, index) => (
                <Cell
                  key={index}
                  fill={entry.value > 0 ? 'var(--risk-high)' : 'var(--risk-low)'}
                  fillOpacity={0.8}
                />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>

      {/* Legend descriptors */}
      <div style={{ marginTop: '12px', display: 'flex', gap: '16px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
          <span style={{ width: '12px', height: '4px', borderRadius: '2px', backgroundColor: 'var(--risk-high)', opacity: 0.8, display: 'inline-block' }} />
          <span style={{ fontSize: '10px', color: 'var(--text-muted)' }}>↑ Meningkatkan Risiko</span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
          <span style={{ width: '12px', height: '4px', borderRadius: '2px', backgroundColor: 'var(--risk-low)', opacity: 0.8, display: 'inline-block' }} />
          <span style={{ fontSize: '10px', color: 'var(--text-muted)' }}>↓ Menurunkan Risiko</span>
        </div>
      </div>

      {/* Detailed factor list below chart */}
      {positive.length > 0 && (
        <div style={{ marginTop: '20px' }}>
          <p style={{ fontSize: '10px', fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.07em', marginBottom: '8px' }}>
            Detail Faktor Pendorong
          </p>
          {positive.map((f) => (
            f.label ? (
              <p key={f.feature} style={{ fontSize: '11px', color: 'var(--text-secondary)', display: 'flex', gap: '6px', alignItems: 'flex-start', marginBottom: '4px' }}>
                <span style={{ color: 'var(--risk-high)', flexShrink: 0, marginTop: '1px' }}>⚠</span>
                {f.label}
              </p>
            ) : null
          ))}
        </div>
      )}
    </div>
  );
}
