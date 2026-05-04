/**
 * Pramana AI — Axios API Client
 *
 * Central HTTP client with:
 * - Base URL configuration
 * - 401 interceptor that triggers logout on expired tokens
 * - Response error normalization
 */

import axios from 'axios';

export const api = axios.create({
  baseURL: '',          // Proxied via Vite dev server
  timeout: 30_000,
  headers: {
    'Content-Type': 'application/json',
  },
});

/* -------------------------------------------------------------------------- */
/* Response interceptor — auto-logout on 401                                  */
/* -------------------------------------------------------------------------- */

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Lazy import to avoid circular dependency
      import('./auth').then(({ useAuthStore }) => {
        useAuthStore.getState().logout();
      });
    }
    return Promise.reject(error);
  },
);
