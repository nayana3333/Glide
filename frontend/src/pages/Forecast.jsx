import { useEffect, useState } from "react";
import { CartesianGrid, Legend, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import DipBadge from "../components/DipBadge.jsx";
import { useAuth } from "../context/AuthContext.jsx";
import { api } from "../services/api.js";

export default function Forecast() {
  const { user } = useAuth();
  const [forecast, setForecast] = useState(null);
  const [explanation, setExplanation] = useState(null);
  const [explainError, setExplainError] = useState("");
  const [error, setError] = useState("");

  useEffect(() => {
    if (!user) return;
    api
      .getForecast(user.id)
      .then(setForecast)
      .catch((err) => setError(err.message));
    api
      .getExplanation(user.id)
      .then(setExplanation)
      .catch((err) => setExplainError(err.message));
  }, [user]);

  if (error) return <div className="page form-error">{error}</div>;
  if (!forecast) return <div className="page">Loading...</div>;

  const chartData = forecast.forecast.map((w) => ({
    week: w.week_start,
    predicted: Math.round(w.yhat),
    lower: w.yhat_lower != null ? Math.round(w.yhat_lower) : null,
    upper: w.yhat_upper != null ? Math.round(w.yhat_upper) : null,
  }));

  const contributions = explanation
    ? Object.entries(explanation.contributions).sort((a, b) => a[1] - b[1])
    : [];
  const maxAbs = Math.max(1, ...contributions.map(([, v]) => Math.abs(v)));

  return (
    <div className="page">
      <h1>Forecast</h1>
      <p className="page-subtitle">
        Model: {forecast.model_used} · Rolling average: Rs.{Math.round(forecast.rolling_avg).toLocaleString()}
      </p>

      <div className="card chart-card">
        <ResponsiveContainer width="100%" height={300}>
          <LineChart data={chartData}>
            <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
            <XAxis dataKey="week" tick={{ fontSize: 11 }} />
            <YAxis tick={{ fontSize: 11 }} />
            <Tooltip />
            <Legend />
            <Line type="monotone" dataKey="predicted" name="Predicted" stroke="var(--accent)" strokeWidth={2} />
            <Line type="monotone" dataKey="upper" name="Upper (80%)" stroke="var(--muted)" strokeDasharray="4 4" dot={false} />
            <Line type="monotone" dataKey="lower" name="Lower (80%)" stroke="var(--muted)" strokeDasharray="4 4" dot={false} />
          </LineChart>
        </ResponsiveContainer>
      </div>

      <div className="card">
        <div className="card-label">Week-by-week</div>
        <table className="table">
          <thead>
            <tr>
              <th>Week</th>
              <th>Predicted</th>
              <th>Range</th>
              <th>Alert</th>
            </tr>
          </thead>
          <tbody>
            {forecast.forecast.map((w) => (
              <tr key={w.week_start}>
                <td>{w.week_start}</td>
                <td>Rs.{Math.round(w.yhat).toLocaleString()}</td>
                <td>
                  {w.yhat_lower != null
                    ? `Rs.${Math.round(w.yhat_lower).toLocaleString()} – Rs.${Math.round(w.yhat_upper).toLocaleString()}`
                    : "—"}
                </td>
                <td>
                  <DipBadge level={w.dip_level} />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="card">
        <div className="card-label">Why this forecast (SHAP)</div>
        {explainError && <div className="field-hint">{explainError}</div>}
        {explanation && (
          <>
            <p className="page-subtitle">
              Predicted Rs.{Math.round(explanation.predicted).toLocaleString()} vs recent 4-week average
              Rs.{Math.round(explanation.rolling_avg_4wk).toLocaleString()}
            </p>
            <div className="shap-bars">
              {contributions.map(([label, value]) => (
                <div className="shap-row" key={label}>
                  <span className="shap-label">{label}</span>
                  <div className="shap-track">
                    <div
                      className={"shap-fill " + (value < 0 ? "negative" : "positive")}
                      style={{ width: `${(Math.abs(value) / maxAbs) * 100}%` }}
                    />
                  </div>
                  <span className="shap-value">
                    {value < 0 ? "-" : "+"}Rs.{Math.round(Math.abs(value)).toLocaleString()}
                  </span>
                </div>
              ))}
            </div>
          </>
        )}
      </div>
    </div>
  );
}
