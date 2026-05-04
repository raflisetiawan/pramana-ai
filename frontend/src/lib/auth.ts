/**
 * Pramana AI — Auth Store (Zustand)
 *
 * Task 4.1.3: JWT stored in memory (NOT localStorage) + auto-refresh.
 *
 * Security: tokens are kept in JS memory only. On page refresh they are
 * lost, requiring the user to log in again (or use refresh-token cookie
 * when implemented server-side).
 */

import { create } from 'zustand';
import { api } from './api';

/* -------------------------------------------------------------------------- */
/* Types                                                                      */
/* -------------------------------------------------------------------------- */

export interface User {
  id: string;
  username: string;
  full_name: string;
  role: 'verifikator' | 'admin_rs' | 'admin_bpjs' | 'supervisor';
}

interface AuthState {
  /* State */
  user: User | null;
  accessToken: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;

  /* Actions */
  login: (username: string, password: string) => Promise<boolean>;
  logout: () => void;
  refreshToken: () => Promise<boolean>;
  clearError: () => void;
}

/* -------------------------------------------------------------------------- */
/* Demo users — used when backend is not running                              */
/* -------------------------------------------------------------------------- */

const DEMO_USERS: Record<string, { password: string; user: User }> = {
  'admin': {
    password: 'admin123',
    user: {
      id: '20000000-0000-0000-0000-000000000001',
      username: 'admin',
      full_name: 'Super Admin',
      role: 'admin_bpjs',
    },
  },
  'admin@pramana.ai': {
    password: 'admin123',
    user: {
      id: '20000000-0000-0000-0000-000000000001',
      username: 'admin@pramana.ai',
      full_name: 'Super Admin',
      role: 'admin_bpjs',
    },
  },
  'verifikator1@bpjs.go.id': {
    password: 'verif123',
    user: {
      id: '20000000-0000-0000-0000-000000000002',
      username: 'verifikator1@bpjs.go.id',
      full_name: 'Dr. Andi Wijaya',
      role: 'verifikator',
    },
  },
  'verifikator': {
    password: 'verif123',
    user: {
      id: '20000000-0000-0000-0000-000000000002',
      username: 'verifikator',
      full_name: 'Dr. Andi Wijaya',
      role: 'verifikator',
    },
  },
  'admin_rs': {
    password: 'rsadmin123',
    user: {
      id: '20000000-0000-0000-0000-000000000004',
      username: 'admin_rs',
      full_name: 'Admin RS Soetomo',
      role: 'admin_rs',
    },
  },
};

/**
 * Attempt offline demo login against hardcoded users.
 * Returns the User if credentials match, or null.
 */
function tryDemoLogin(username: string, password: string): User | null {
  const entry = DEMO_USERS[username.toLowerCase()];
  if (entry && entry.password === password) {
    return entry.user;
  }
  return null;
}

/* -------------------------------------------------------------------------- */
/* Refresh timer                                                              */
/* -------------------------------------------------------------------------- */

let refreshTimer: ReturnType<typeof setTimeout> | null = null;

function scheduleRefresh(store: AuthState, expiresInMs: number) {
  if (refreshTimer) clearTimeout(refreshTimer);
  // Refresh 60 seconds before expiry
  const refreshAt = Math.max(expiresInMs - 60_000, 10_000);
  refreshTimer = setTimeout(() => {
    store.refreshToken();
  }, refreshAt);
}

function clearRefreshTimer() {
  if (refreshTimer) {
    clearTimeout(refreshTimer);
    refreshTimer = null;
  }
}

/* -------------------------------------------------------------------------- */
/* Store                                                                      */
/* -------------------------------------------------------------------------- */

export const useAuthStore = create<AuthState>((set, get) => ({
  user: null,
  accessToken: null,
  isAuthenticated: false,
  isLoading: false,
  error: null,

  login: async (username: string, password: string): Promise<boolean> => {
    set({ isLoading: true, error: null });

    try {
      const response = await api.post('/api/v1/auth/login', {
        username,
        password,
      });

      const { access_token, user, expires_in } = response.data;

      // Store in memory — never localStorage
      set({
        user,
        accessToken: access_token,
        isAuthenticated: true,
        isLoading: false,
        error: null,
      });

      // Set Authorization header for subsequent requests
      api.defaults.headers.common['Authorization'] = `Bearer ${access_token}`;

      // Schedule auto-refresh
      const expiresMs = (expires_in || 480 * 60) * 1000; // default 8h
      scheduleRefresh(get(), expiresMs);

      return true;
    } catch (err: unknown) {
      // -----------------------------------------------------------------
      // Fallback: if the backend is not available, try demo login.
      // Covers: network error, 502 (proxy can't reach backend),
      //         404 (auth endpoint not implemented yet).
      // -----------------------------------------------------------------
      const status = (err as { response?: { status?: number } })?.response?.status;
      const isBackendUnavailable =
        (err as { code?: string })?.code === 'ERR_NETWORK' ||
        !(err as { response?: unknown })?.response ||
        status === 502 ||
        status === 404;

      if (isBackendUnavailable) {
        const demoUser = tryDemoLogin(username, password);
        if (demoUser) {
          const fakeToken = 'demo_token_' + Date.now();
          set({
            user: demoUser,
            accessToken: fakeToken,
            isAuthenticated: true,
            isLoading: false,
            error: null,
          });
          api.defaults.headers.common['Authorization'] = `Bearer ${fakeToken}`;
          console.warn('[Auth] Backend offline — using demo login for:', demoUser.username);
          return true;
        }
      }

      const message =
        (err as { response?: { data?: { detail?: string } } })?.response?.data
          ?.detail || 'Login gagal. Periksa username dan password.';

      set({
        user: null,
        accessToken: null,
        isAuthenticated: false,
        isLoading: false,
        error: message,
      });
      return false;
    }
  },

  logout: () => {
    clearRefreshTimer();
    delete api.defaults.headers.common['Authorization'];

    set({
      user: null,
      accessToken: null,
      isAuthenticated: false,
      isLoading: false,
      error: null,
    });
  },

  refreshToken: async (): Promise<boolean> => {
    try {
      const response = await api.post('/api/v1/auth/refresh');
      const { access_token, expires_in } = response.data;

      set({ accessToken: access_token });
      api.defaults.headers.common['Authorization'] = `Bearer ${access_token}`;

      const expiresMs = (expires_in || 480 * 60) * 1000;
      scheduleRefresh(get(), expiresMs);

      return true;
    } catch {
      // Refresh failed — force logout
      get().logout();
      return false;
    }
  },

  clearError: () => set({ error: null }),
}));
