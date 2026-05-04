/**
 * Pramana AI — App Root
 * React Router: /login (public), / + /claims/:id (protected)
 */

import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ProtectedRoute } from './components/ProtectedRoute';
import LoginPage from './pages/Login';
import Dashboard from './pages/Dashboard';
import ClaimDetailPage from './pages/ClaimDetail';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      staleTime: 30_000,
      refetchOnWindowFocus: false,
    },
  },
});

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <Routes>
          {/* Public */}
          <Route path="/login" element={<LoginPage />} />

          {/* Protected */}
          <Route element={<ProtectedRoute />}>
            <Route path="/"           element={<Dashboard />} />
            <Route path="/claims"     element={<Dashboard />} />
            <Route path="/claims/:id" element={<ClaimDetailPage />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </QueryClientProvider>
  );
}
