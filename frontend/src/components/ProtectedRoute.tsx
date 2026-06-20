import { Navigate, Outlet } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

export function ProtectedRoute({ role }: { role?: "field_worker" | "manager" }) {
  const { user, isAuthenticated } = useAuth();

  if (!isAuthenticated) return <Navigate to="/login" replace />;
  if (role && user?.role !== role) {
    if (user?.role === "manager") return <Navigate to="/manager" replace />;
    return <Navigate to="/app/log" replace />;
  }
  return <Outlet />;
}
