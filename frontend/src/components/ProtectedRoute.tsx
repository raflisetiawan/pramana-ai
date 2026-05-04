/**
 * Pramana AI — Protected Route Component
 *
 * Task 4.1.4: Redirect to /login if the user has no valid JWT in memory.
 */

import { Navigate, Outlet, useLocation } from 'react-router-dom';
import { useAuthStore } from '../lib/auth';

export function ProtectedRoute() {
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated);
  const location = useLocation();

  if (!isAuthenticated) {
    // Save the attempted URL so we can redirect after login
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  return <Outlet />;
}
