import { Navigate } from 'react-router-dom';
import { useAuth } from './AuthContext';

export default function ProtectedRoute({ children }) {
  const { user, ready } = useAuth();
  if (!ready) return <div className="min-h-screen flex items-center justify-center text-text-dim">Loading…</div>;
  if (!user) return <Navigate to="/login" replace />;
  return children;
}
