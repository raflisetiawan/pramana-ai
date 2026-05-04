/**
 * Pramana AI — Login Page
 * Split-screen: kiri branding, kanan form.
 * Ref: frontend-design.md §6.1
 */

import { useState, type FormEvent } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { useAuthStore } from '../lib/auth';

export default function LoginPage() {
  const [username, setUsername]     = useState('');
  const [password, setPassword]     = useState('');
  const [showPassword, setShowPass] = useState(false);

  const login      = useAuthStore((s) => s.login);
  const isLoading  = useAuthStore((s) => s.isLoading);
  const error      = useAuthStore((s) => s.error);
  const clearError = useAuthStore((s) => s.clearError);

  const navigate  = useNavigate();
  const location  = useLocation();
  const from = (location.state as { from?: { pathname: string } })?.from?.pathname || '/';

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    clearError();
    if (await login(username, password)) navigate(from, { replace: true });
  };

  return (
    <div className="login-page">
      {/* ── Kiri: Branding ── */}
      <div className="login-left">
        {/* Logo */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '48px' }}>
          <div style={{ width: '44px', height: '44px', background: 'var(--accent-primary)', borderRadius: '6px', display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>
            <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#fff" strokeWidth="2.5">
              <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
            </svg>
          </div>
          <div>
            <p style={{ fontFamily: 'var(--font-display)', fontSize: '20px', fontWeight: 600, color: 'var(--text-primary)' }}>Pramana AI</p>
            <p style={{ fontSize: '11px', color: 'var(--text-muted)', letterSpacing: '0.04em' }}>SMART-CLAIM CO-PILOT</p>
          </div>
        </div>

        {/* Tagline */}
        <h2 style={{ fontFamily: 'var(--font-display)', fontSize: '26px', fontWeight: 600, color: 'var(--text-primary)', lineHeight: 1.35, marginBottom: '16px' }}>
          "Validasi yang<br/>cerdas untuk<br/>sistem kesehatan<br/>nasional."
        </h2>
        <p style={{ fontSize: '13px', color: 'var(--text-secondary)', marginBottom: '48px' }}>
          — Dikembangkan oleh Siena Clinical
        </p>

        {/* Feature list */}
        {[
          'Risk scoring otomatis setiap klaim masuk',
          'NLP extraction kode ICD-10 dari resume medis',
          'SHAP explainability — keputusan yang dapat dipertanggungjawabkan',
        ].map((f) => (
          <div key={f} style={{ display: 'flex', alignItems: 'flex-start', gap: '10px', marginBottom: '12px' }}>
            <span style={{ color: 'var(--risk-low)', marginTop: '1px', flexShrink: 0 }}>
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3"><polyline points="20 6 9 17 4 12"/></svg>
            </span>
            <p style={{ fontSize: '13px', color: 'var(--text-secondary)', lineHeight: 1.5 }}>{f}</p>
          </div>
        ))}

        {/* Footer */}
        <div style={{ marginTop: 'auto', paddingTop: '32px', borderTop: '1px solid var(--border-subtle)' }}>
          <div style={{ display: 'flex', gap: '20px' }}>
            {[
              { val: '99.2%', label: 'Akurasi Model' },
              { val: '<100ms', label: 'Waktu Scoring' },
              { val: '10rb+', label: 'Klaim Terlatih' },
            ].map((m) => (
              <div key={m.label}>
                <p style={{ fontFamily: 'var(--font-mono)', fontSize: '16px', fontWeight: 500, color: 'var(--text-primary)' }}>{m.val}</p>
                <p style={{ fontSize: '10px', color: 'var(--text-muted)' }}>{m.label}</p>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* ── Kanan: Form ── */}
      <div className="login-right">
        <div className="login-form-container page-enter">
          <h2 style={{ fontFamily: 'var(--font-sans)', fontSize: '24px', fontWeight: 600, color: 'var(--text-primary)', marginBottom: '6px' }}>
            Selamat Datang Kembali
          </h2>
          <p style={{ fontSize: '13px', color: 'var(--text-secondary)', marginBottom: '32px' }}>
            BPJS Kesehatan · Verifikasi Klaim
          </p>

          {/* Error */}
          {error && (
            <div style={{ marginBottom: '16px', padding: '10px 14px', borderRadius: '6px', background: 'var(--risk-high-bg)', border: '1px solid var(--risk-high-border)', color: 'var(--risk-high)', fontSize: '13px', display: 'flex', alignItems: 'center', gap: '8px' }}>
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><circle cx="12" cy="12" r="10"/><line x1="15" y1="9" x2="9" y2="15"/><line x1="9" y1="9" x2="15" y2="15"/></svg>
              {error}
            </div>
          )}

          <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '18px' }}>
            {/* Username */}
            <div>
              <label htmlFor="login-username" className="form-label">Username atau Email</label>
              <input
                id="login-username"
                type="text"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                placeholder="username atau email@bpjs.go.id"
                required
                autoFocus
                autoComplete="username"
                className="form-input"
              />
            </div>

            {/* Password */}
            <div>
              <label htmlFor="login-password" className="form-label">Password</label>
              <div style={{ position: 'relative' }}>
                <input
                  id="login-password"
                  type={showPassword ? 'text' : 'password'}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="Password"
                  required
                  autoComplete="current-password"
                  className="form-input"
                  style={{ paddingRight: '42px' }}
                />
                <button
                  type="button"
                  onClick={() => setShowPass(!showPassword)}
                  aria-label={showPassword ? 'Sembunyikan password' : 'Tampilkan password'}
                  style={{ position: 'absolute', right: '10px', top: '50%', transform: 'translateY(-50%)', background: 'none', border: 'none', color: 'var(--text-muted)', cursor: 'pointer', padding: '4px', display: 'flex' }}
                >
                  {showPassword
                    ? <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94"/><path d="M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19"/><line x1="1" y1="1" x2="23" y2="23"/></svg>
                    : <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/></svg>
                  }
                </button>
              </div>
            </div>

            {/* Submit */}
            <button
              type="submit"
              id="login-submit-btn"
              disabled={isLoading || !username || !password}
              className="btn btn-primary"
              style={{ width: '100%', justifyContent: 'center', padding: '10px 16px', fontSize: '14px' }}
            >
              {isLoading
                ? <><svg className="animate-spin" width="16" height="16" viewBox="0 0 24 24" fill="none"><circle cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="3" strokeDasharray="32" strokeLinecap="round" style={{ opacity: 0.3 }}/><path fill="currentColor" d="M12 2a10 10 0 0 1 10 10h-3a7 7 0 0 0-7-7V2z"/></svg> Memproses...</>
                : 'Masuk ke Dashboard'
              }
            </button>
          </form>

          {/* Demo credentials */}
          <div style={{ marginTop: '28px', paddingTop: '20px', borderTop: '1px solid var(--border-subtle)' }}>
            <p style={{ fontSize: '11px', color: 'var(--text-muted)', marginBottom: '8px', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
              Demo Credentials
            </p>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '5px' }}>
              {[
                { user: 'admin', pass: 'admin123', role: 'Admin BPJS' },
                { user: 'verifikator', pass: 'verif123', role: 'Verifikator' },
                { user: 'admin_rs', pass: 'rsadmin123', role: 'Admin RS' },
              ].map((d) => (
                <button
                  key={d.user}
                  type="button"
                  onClick={() => { setUsername(d.user); setPassword(d.pass); }}
                  style={{ textAlign: 'left', background: 'var(--bg-elevated)', border: '1px solid var(--border-subtle)', borderRadius: '4px', padding: '6px 10px', cursor: 'pointer', fontSize: '12px', color: 'var(--text-secondary)', display: 'flex', gap: '8px', alignItems: 'center' }}
                >
                  <span style={{ fontFamily: 'var(--font-mono)', color: 'var(--accent-secondary)' }}>{d.user}</span>
                  <span style={{ color: 'var(--text-muted)' }}>·</span>
                  <span>{d.role}</span>
                </button>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
