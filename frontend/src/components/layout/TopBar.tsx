/**
 * Pramana AI — TopBar
 * Height 56px, sticky, breadcrumb + notifikasi + avatar.
 * Ref: frontend-design.md §6.2
 */

interface TopBarProps {
  title: string;
  subtitle?: string;
}

export function TopBar({ title, subtitle }: TopBarProps) {
  return (
    <header className="topbar">
      {/* Left: title/breadcrumb */}
      <div style={{ flex: 1 }}>
        <h1 style={{ fontFamily: 'var(--font-display)', fontSize: '16px', fontWeight: 600, color: 'var(--text-primary)', margin: 0, lineHeight: 1 }}>
          {title}
        </h1>
        {subtitle && (
          <p style={{ fontSize: '11px', color: 'var(--text-muted)', marginTop: '2px' }}>{subtitle}</p>
        )}
      </div>

      {/* Right: actions */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
        {/* Notification bell */}
        <button
          id="topbar-notifications-btn"
          aria-label="Notifikasi"
          style={{ background: 'none', border: 'none', color: 'var(--text-secondary)', cursor: 'pointer', padding: '6px', borderRadius: '6px', display: 'flex', position: 'relative' }}
        >
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"/>
            <path d="M13.73 21a2 2 0 0 1-3.46 0"/>
          </svg>
          {/* Unread dot */}
          <span style={{ position: 'absolute', top: '4px', right: '4px', width: '7px', height: '7px', background: 'var(--risk-high)', borderRadius: '50%', border: '1.5px solid var(--bg-surface)' }} />
        </button>

        {/* Divider */}
        <div style={{ width: '1px', height: '20px', background: 'var(--border-subtle)' }} />

        {/* Timestamp */}
        <span style={{ fontFamily: 'var(--font-mono)', fontSize: '11px', color: 'var(--text-muted)' }}>
          {new Date().toLocaleDateString('id-ID', { weekday: 'short', day: '2-digit', month: 'short' })}
        </span>
      </div>
    </header>
  );
}
