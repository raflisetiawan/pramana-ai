/**
 * Pramana AI — ClaimFilterBar
 * Filter bar: risk level, RS, tanggal, pencarian
 * Ref: frontend-design.md §5.2
 */

import { useState } from 'react';

export interface FilterState {
  riskLevel: string;
  status: string;
  search: string;
}

interface ClaimFilterBarProps {
  filters: FilterState;
  onChange: (f: FilterState) => void;
  totalShown: number;
  totalAll: number;
}

export function ClaimFilterBar({ filters, onChange, totalShown, totalAll }: ClaimFilterBarProps) {
  const set = (key: keyof FilterState, val: string) =>
    onChange({ ...filters, [key]: val });

  return (
    <div style={{ padding: '12px 20px', borderBottom: '1px solid var(--border-subtle)', display: 'flex', alignItems: 'center', gap: '8px', flexWrap: 'wrap' }}>
      {/* Risk Level filter */}
      <select
        className="filter-select"
        value={filters.riskLevel}
        onChange={(e) => set('riskLevel', e.target.value)}
        aria-label="Filter risk level"
        id="filter-risk-level"
      >
        <option value="">● Semua Risk</option>
        <option value="high">● HIGH RISK</option>
        <option value="medium">● MED RISK</option>
        <option value="low">● LOW RISK</option>
      </select>

      {/* Status filter */}
      <select
        className="filter-select"
        value={filters.status}
        onChange={(e) => set('status', e.target.value)}
        aria-label="Filter status"
        id="filter-status"
      >
        <option value="">Status ▾</option>
        <option value="pending">Menunggu</option>
        <option value="in_review">Direview</option>
        <option value="approved">Disetujui</option>
        <option value="returned">Dikembalikan</option>
        <option value="escalated">Dieskalasi</option>
      </select>

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

      {/* Count */}
      <span style={{ fontSize: '12px', color: 'var(--text-muted)', whiteSpace: 'nowrap' }}>
        Menampilkan <strong style={{ color: 'var(--text-secondary)' }}>{totalShown}</strong> dari {totalAll} klaim
      </span>

      {/* Reset chip — show if any filter active */}
      {(filters.riskLevel || filters.status || filters.search) && (
        <button
          className="filter-chip"
          onClick={() => onChange({ riskLevel: '', status: '', search: '' })}
          id="filter-reset-btn"
          style={{ marginLeft: '4px' }}
        >
          Reset ×
        </button>
      )}
    </div>
  );
}
