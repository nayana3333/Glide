import { useEffect, useState } from "react";
import { CartesianGrid, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import DipBadge from "../components/DipBadge.jsx";
import { useAuth } from "../context/AuthContext.jsx";
import { api } from "../services/api.js";

export default function Dashboard() {
  const { user } = useAuth();
  const [data, setData] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!user) return;
    api
      .getDashboard(user.id)
      .then(setData)
      .catch((err) => setError(err.message));
  }, [user]);

  if (error) return <div className="page form-error">{error}</div>;
  if (!data) return <div className="page">Loading...</div>;

  const chartData = data.recent_earnings.map((e) => ({
    week: e.week_start,
    earnings: Math.round(e.net_earnings),
  }));

  return (
    <div className="page">
      <h1>Dashboard</h1>

      {data.latest_alert_message && (
        <div className="alert-banner">{data.latest_alert_message}</div>
      )}

      <div className="card-grid">
        <div className="card">
          <div className="card-label">Buffer balance</div>
          <div className="card-value">Rs.{Math.round(data.buffer_balance).toLocaleString()}</div>
        </div>

        {data.next_week_forecast && (
          <div className="card">
            <div className="card-label">Next week forecast</div>
            <div className="card-value">Rs.{Math.round(data.next_week_forecast.yhat).toLocaleString()}</div>
            <DipBadge level={data.next_week_forecast.dip_level} />
          </div>
        )}

        <div className="card">
          <div className="card-label">Recent weeks tracked</div>
          <div className="card-value">{data.recent_earnings.length}</div>
        </div>
      </div>

      <div className="card chart-card">
        <div className="card-label">Recent earnings</div>
        <ResponsiveContainer width="100%" height={280}>
          <LineChart data={chartData}>
            <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
            <XAxis dataKey="week" tick={{ fontSize: 11 }} />
            <YAxis tick={{ fontSize: 11 }} />
            <Tooltip />
            <Line type="monotone" dataKey="earnings" stroke="var(--accent)" strokeWidth={2} dot={false} />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
