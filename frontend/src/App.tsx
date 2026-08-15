import { Navigate, Route, Routes } from "react-router-dom";
import { Toaster } from "@/components/ui/sonner";
import NavBar from "@/components/NavBar";
import { AuthProvider, useAuth } from "@/context/AuthContext";
import Auth from "@/pages/Auth";
import Buffer from "@/pages/Buffer";
import Dashboard from "@/pages/Dashboard";
import Forecast from "@/pages/Forecast";
import IncomeLog from "@/pages/IncomeLog";
import Insights from "@/pages/Insights";
import type { ReactNode } from "react";

function ProtectedLayout({ children }: { children: ReactNode }) {
  const { user, loading } = useAuth();
  if (loading) return <div className="p-6 text-muted-foreground">Loading...</div>;
  if (!user) return <Navigate to="/login" replace />;
  return (
    <>
      <NavBar />
      <main className="mx-auto max-w-5xl px-4 py-6 sm:px-6">{children}</main>
    </>
  );
}

function AppRoutes() {
  const { user, loading } = useAuth();

  return (
    <Routes>
      <Route
        path="/login"
        element={
          loading ? (
            <div className="p-6 text-muted-foreground">Loading...</div>
          ) : user ? (
            <Navigate to="/dashboard" replace />
          ) : (
            <Auth />
          )
        }
      />
      <Route
        path="/dashboard"
        element={
          <ProtectedLayout>
            <Dashboard />
          </ProtectedLayout>
        }
      />
      <Route
        path="/forecast"
        element={
          <ProtectedLayout>
            <Forecast />
          </ProtectedLayout>
        }
      />
      <Route
        path="/buffer"
        element={
          <ProtectedLayout>
            <Buffer />
          </ProtectedLayout>
        }
      />
      <Route
        path="/income"
        element={
          <ProtectedLayout>
            <IncomeLog />
          </ProtectedLayout>
        }
      />
      <Route
        path="/insights"
        element={
          <ProtectedLayout>
            <Insights />
          </ProtectedLayout>
        }
      />
      <Route path="*" element={<Navigate to="/dashboard" replace />} />
    </Routes>
  );
}

export default function App() {
  return (
    <AuthProvider>
      <AppRoutes />
      <Toaster position="top-right" richColors />
    </AuthProvider>
  );
}
