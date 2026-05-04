/**
 * Pramana AI — ClaimFilterBar
 * Filter bar: risk level (Hijau/Kuning/Merah), RS, tanggal, pencarian
 * Ref: frontend-design.md §5.2
 */

export interface FilterState {
  riskLevel: string;
  hospital: string;
  dateFrom: string;
  dateTo: string;
  search: string;
}

export const INITIAL_FILTERS: FilterState = {
  riskLevel: '',
  hospital: '',
  dateFrom: '',
  dateTo: '',
  search: '',
};

interface ClaimFilterBarProps {
  filters: FilterState;
  onChange: (f: FilterState) => void;
  totalShown: number;
  totalAll: number;
  hospitals: string[];
}

/** Check if any filter is active */
export function hasActiveFilters(f: FilterState): boolean {
  return !!(f.riskLevel || f.hospital || f.dateFrom || f.dateTo || f.search);
}

export function ClaimFilterBar({ filters, onChange, totalShown, totalAll, hospitals }: ClaimFilterBarProps) {
  const set = (key: keyof FilterState, val: string) =>
    onChange({ ...filters, [key]: val });

  const activeChips: { key: keyof FilterState; label: string }[] = [];

  if (filters.riskLevel) {
    const riskLabels: Record<string, string> = { high: 'High Risk', medium: 'Med Risk', low: 'Low Risk' };
    activeChips.push({ key: 'riskLevel', label: riskLabels[filters.riskLevel] || filters.riskLevel });
  }
  if (filters.hospital) {
    activeChips.push({ key: 'hospital', label: filters.hospital.length > 20 ? filters.hospital.slice(0, 18) + '…' : filters.hospital });
  }
  if (filters.dateFrom) {
    activeChips.push({ key: 'dateFrom', label: `Dari: ${filters.dateFrom}` });
  }
  if (filters.dateTo) {
    activeChips.push({ key: 'dateTo', label: `Sampai: ${filters.dateTo}` });
  }

  return (
    <div style={{ padding: '12px 20px', borderBottom: '1px solid var(--border-subtle)', display: 'flex', flexDirection: 'column', gap: '8px' }}>
      {/* Row 1: filters + search */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flexWrap: 'wrap' }}>
        {/* Risk Level filter */}
        <select
          className="filter-select"
          value={filters.riskLevel}
          onChange={(e) => set('riskLevel', e.target.value)}
          aria-label="Filter risk level"
          id="filter-risk-level"
        >
          <option value="">● Semua Risk</option>
          <option value="high">🔴 HIGH RISK</option>
          <option value="medium">🟡 MED RISK</option>
          <option value="low">🟢 LOW RISK</option>
        </select>

        {/* RS filter */}
        <select
          className="filter-select"
          value={filters.hospital}
          onChange={(e) => set('hospital', e.target.value)}
          aria-label="Filter rumah sakit"
          id="filter-hospital"
        >
          <option value="">Semua RS</option>
          {hospitals.map((h) => (
            <option key={h} value={h}>{h.length > 30 ? h.slice(0, 28) + '…' : h}</option>
          ))}
        </select>

        {/* Date range */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
          <input
            type="date"
            className="filter-select"
            value={filters.dateFrom}
            onChange={(e) => set('dateFrom', e.target.value)}
            aria-label="Tanggal dari"
            id="filter-date-from"
            style={{ minWidth: '130px' }}
          />
          <span style={{ color: 'var(--text-muted)', fontSize: '12px' }}>—</span>
          <input
            type="date"
            className="filter-select"
            value={filters.dateTo}
            onChange={(e) => set('dateTo', e.target.value)}
            aria-label="Tanggal sampai"
            id="filter-date-to"
            style={{ minWidth: '130px' }}
          />
        </div>

        {/* Search */}
        <div className="search-wrapper" style={{ marginLeft: 'auto' }}>
          <svg className="search-icon" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/>
          </svg>
          <input
            className="search-input"
            type="text"
            placeholder="Cari No. SEP, Pasien..."
            value={filters.search}
            onChange={(e) => set('search', e.target.value)}
            id="filter-search"
            aria-label="Cari klaim"
          />
        </div>
      </div>

      {/* Row 2: active chips + result count */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '6px', flexWrap: 'wrap' }}>
        {/* Active filter chips */}
        {activeChips.map((chip) => (
          <span key={chip.key} className="filter-chip">
            {chip.label}
            <button
              onClick={() => set(chip.key, '')}
              aria-label={`Hapus filter ${chip.label}`}
            >
              ×
            </button>
          </span>
        ))}

        {/* Count */}
        <span style={{ fontSize: '12px', color: 'var(--text-muted)', whiteSpace: 'nowrap', marginLeft: activeChips.length ? '4px' : '0' }}>
          Menampilkan <strong style={{ color: 'var(--text-secondary)' }}>{totalShown}</strong> dari {totalAll} klaim
        </span>

        {/* Reset all */}
        {hasActiveFilters(filters) && (
          <button
            className="filter-chip"
            onClick={() => onChange(INITIAL_FILTERS)}
            id="filter-reset-btn"
            style={{ marginLeft: 'auto' }}
          >
            Reset Semua ×
          </button>
        )}
      </div>
    </div>
  );
}
