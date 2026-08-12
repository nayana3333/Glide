import { Navigate, Route, Routes } from "react-router-dom";
import NavBar from "./components/NavBar.jsx";
import { AuthProvider, useAuth } from "./context/AuthContext.jsx";
import Auth from "./pages/Auth.jsx";
import Buffer from "./pages/Buffer.jsx";
import Dashboard from "./pages/Dashboard.jsx";
import Forecast from "./pages/Forecast.jsx";
import IncomeLog from "./pages/IncomeLog.jsx";
import Insights from "./pages/Insights.jsx";

function ProtectedLayout({ children }) {
  const { user, loading } = useAuth();
  if (loading) return <div className="page">Loading...</div>;
  if (!user) return <Navigate to="/login" replace />;
  return (
    <>
      <NavBar />
      {children}
    </>
  );
}

function AppRoutes() {
  const { user, loading } = useAuth();

  return (
    <Routes>
      <Route
        path="/login"
        element={loading ? <div className="page">Loading...</div> : user ? <Navigate to="/dashboard" replace /> : <Auth />}
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
    </AuthProvider>
  );
}
