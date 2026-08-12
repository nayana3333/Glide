import { useEffect, useMemo, useState } from "react";
import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { useAuth } from "../context/AuthContext.jsx";
import { api } from "../services/api.js";

function computeHealthScore(earnings, bufferBalance) {
  if (earnings.length < 4) return null;

  const values = earnings.map((e) => e.net_earnings);
  const mean = values.reduce((a, b) => a + b, 0) / values.length;
  const variance = values.reduce((a, b) => a + (b - mean) ** 2, 0) / values.length;
  const cv = mean > 0 ? Math.sqrt(variance) / mean : 1;

  const bufferWeeks = mean > 0 ? bufferBalance / mean : 0;
  const bufferScore = Math.min(bufferWeeks / 4, 1) * 40;

  const stabilityScore = Math.max(0, 1 - cv / 0.5) * 30;

  const recent = earnings.slice(-12);
  const recentDipRate = recent.filter((e) => e.net_earnings < mean * 0.8).length / recent.length;
  const dipScore = (1 - recentDipRate) * 30;

  return Math.round(bufferScore + stabilityScore + dipScore);
}

export default function Insights() {
  const { user } = useAuth();
  const [earnings, setEarnings] = useState(null);
  const [buffer, setBuffer] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!user) return;
    Promise.all([api.getEarnings(user.id), api.getBuffer(user.id)])
      .then(([e, b]) => {
        setEarnings(e);
        setBuffer(b);
      })
      .catch((err) => setError(err.message));
  }, [user]);

  const monthly = useMemo(() => {
    if (!earnings) return [];
    const byMonth = {};
    for (const row of earnings) {
      const month = row.week_start.slice(0, 7); // YYYY-MM
      byMonth[month] = (byMonth[month] || 0) + row.net_earnings;
    }
    return Object.entries(byMonth).map(([month, total]) => ({ month, total: Math.round(total) }));
  }, [earnings]);

  const bestWeeks = useMemo(() => {
    if (!earnings) return [];
    return earnings
      .slice()
      .sort((a, b) => b.net_earnings - a.net_earnings)
      .slice(0, 5);
  }, [earnings]);

  const healthScore = useMemo(() => {
    if (!earnings || !buffer) return null;
    return computeHealthScore(earnings, buffer.balance);
  }, [earnings, buffer]);

  if (error) return <div className="page form-error">{error}</div>;
  if (!earnings || !buffer) return <div className="page">Loading...</div>;

  return (
    <div className="page">
      <h1>Insights</h1>

      <div className="card-grid">
        <div className="card">
          <div className="card-label">Financial health score</div>
          <div className="card-value large">{healthScore ?? "—"}/100</div>
          <p className="field-hint">
            Project-defined heuristic (buffer coverage + income stability + recent dip frequency), not a
            credit bureau score.
          </p>
        </div>
        <div className="card">
          <div className="card-label">Weeks tracked</div>
          <div className="card-value">{earnings.length}</div>
        </div>
      </div>

      <div className="card chart-card">
        <div className="card-label">Monthly earnings trend</div>
        <ResponsiveContainer width="100%" height={280}>
          <BarChart data={monthly}>
            <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
            <XAxis dataKey="month" tick={{ fontSize: 11 }} />
            <YAxis tick={{ fontSize: 11 }} />
            <Tooltip />
            <Bar dataKey="total" fill="var(--accent)" radius={[4, 4, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>

      <div className="card">
        <div className="card-label">Best earning weeks</div>
        <table className="table">
          <thead>
            <tr>
              <th>Week</th>
              <th>Platform</th>
              <th>Net earnings</th>
            </tr>
          </thead>
          <tbody>
            {bestWeeks.map((w) => (
              <tr key={w.id}>
                <td>{w.week_start}</td>
                <td>{w.platform}</td>
                <td>Rs.{Math.round(w.net_earnings).toLocaleString()}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
