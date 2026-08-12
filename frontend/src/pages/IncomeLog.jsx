import { useEffect, useState } from "react";
import { useAuth } from "../context/AuthContext.jsx";
import { api } from "../services/api.js";

const PLATFORMS = ["Ola", "Uber", "Swiggy", "Zomato", "UrbanCompany"];
const EMPTY_FORM = {
  week_start: "",
  platform: PLATFORMS[0],
  hours_worked: "",
  trips_completed: "",
  gross_earnings: "",
  fuel_cost: "",
};

export default function IncomeLog() {
  const { user } = useAuth();
  const [earnings, setEarnings] = useState([]);
  const [form, setForm] = useState(EMPTY_FORM);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  function load() {
    if (!user) return;
    api
      .getEarnings(user.id)
      .then((rows) => setEarnings(rows.slice().reverse()))
      .catch((err) => setError(err.message));
  }

  useEffect(load, [user]);

  function update(field, value) {
    setForm((f) => ({ ...f, [field]: value }));
  }

  async function handleSubmit(e) {
    e.preventDefault();
    setError("");
    setBusy(true);
    try {
      await api.addEarnings({
        week_start: form.week_start,
        platform: form.platform,
        hours_worked: Number(form.hours_worked),
        trips_completed: Number(form.trips_completed),
        gross_earnings: Number(form.gross_earnings),
        fuel_cost: Number(form.fuel_cost),
      });
      setForm(EMPTY_FORM);
      load();
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="page">
      <h1>Income Log</h1>

      <form className="card" onSubmit={handleSubmit}>
        <div className="card-label">Log a week's earnings</div>
        <div className="form-grid">
          <label className="field">
            Week start
            <input
              type="date"
              required
              value={form.week_start}
              onChange={(e) => update("week_start", e.target.value)}
            />
          </label>
          <label className="field">
            Platform
            <select value={form.platform} onChange={(e) => update("platform", e.target.value)}>
              {PLATFORMS.map((p) => (
                <option key={p} value={p}>
                  {p}
                </option>
              ))}
            </select>
          </label>
          <label className="field">
            Hours worked
            <input
              type="number"
              step="0.1"
              required
              value={form.hours_worked}
              onChange={(e) => update("hours_worked", e.target.value)}
            />
          </label>
          <label className="field">
            Trips completed
            <input
              type="number"
              required
              value={form.trips_completed}
              onChange={(e) => update("trips_completed", e.target.value)}
            />
          </label>
          <label className="field">
            Gross earnings (Rs.)
            <input
              type="number"
              step="0.01"
              required
              value={form.gross_earnings}
              onChange={(e) => update("gross_earnings", e.target.value)}
            />
          </label>
          <label className="field">
            Fuel cost (Rs.)
            <input
              type="number"
              step="0.01"
              required
              value={form.fuel_cost}
              onChange={(e) => update("fuel_cost", e.target.value)}
            />
          </label>
        </div>
        {error && <div className="form-error">{error}</div>}
        <button className="btn btn-primary" type="submit" disabled={busy}>
          {busy ? "Saving..." : "Add week"}
        </button>
      </form>

      <div className="card">
        <div className="card-label">History ({earnings.length} weeks)</div>
        <table className="table">
          <thead>
            <tr>
              <th>Week</th>
              <th>Platform</th>
              <th>Hours</th>
              <th>Trips</th>
              <th>Gross</th>
              <th>Fuel</th>
              <th>Net</th>
            </tr>
          </thead>
          <tbody>
            {earnings.map((row) => (
              <tr key={row.id}>
                <td>{row.week_start}</td>
                <td>{row.platform}</td>
                <td>{row.hours_worked}</td>
                <td>{row.trips_completed}</td>
                <td>Rs.{Math.round(row.gross_earnings).toLocaleString()}</td>
                <td>Rs.{Math.round(row.fuel_cost).toLocaleString()}</td>
                <td>Rs.{Math.round(row.net_earnings).toLocaleString()}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
