import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext.jsx";

const ARCHETYPES = ["full_time_driver", "part_time_delivery", "multi_platform"];
const PLATFORMS = ["Ola", "Uber", "Swiggy", "Zomato", "UrbanCompany"];

export default function Auth() {
  const [mode, setMode] = useState("login"); // "login" | "register"
  const [form, setForm] = useState({
    name: "",
    phone: "",
    password: "",
    archetype: ARCHETYPES[0],
    platform: PLATFORMS[0],
    demo_worker_id: "",
  });
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const { login, register } = useAuth();
  const navigate = useNavigate();

  function update(field, value) {
    setForm((f) => ({ ...f, [field]: value }));
  }

  async function handleSubmit(e) {
    e.preventDefault();
    setError("");
    setBusy(true);
    try {
      if (mode === "login") {
        await login(form.phone, form.password);
      } else {
        await register({
          name: form.name,
          phone: form.phone,
          password: form.password,
          archetype: form.archetype,
          platform: form.platform,
          demo_worker_id: form.demo_worker_id ? Number(form.demo_worker_id) : null,
        });
      }
      navigate("/dashboard");
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="auth-page">
      <form className="card auth-card" onSubmit={handleSubmit}>
        <h1 className="auth-title">Glide</h1>
        <p className="auth-subtitle">Predictive income smoothing for gig workers</p>

        <div className="auth-tabs">
          <button
            type="button"
            className={"auth-tab" + (mode === "login" ? " active" : "")}
            onClick={() => setMode("login")}
          >
            Log in
          </button>
          <button
            type="button"
            className={"auth-tab" + (mode === "register" ? " active" : "")}
            onClick={() => setMode("register")}
          >
            Register
          </button>
        </div>

        {mode === "register" && (
          <label className="field">
            Name
            <input required value={form.name} onChange={(e) => update("name", e.target.value)} />
          </label>
        )}

        <label className="field">
          Phone
          <input required value={form.phone} onChange={(e) => update("phone", e.target.value)} />
        </label>

        <label className="field">
          Password
          <input
            required
            type="password"
            minLength={6}
            value={form.password}
            onChange={(e) => update("password", e.target.value)}
          />
        </label>

        {mode === "register" && (
          <>
            <label className="field">
              Worker type
              <select value={form.archetype} onChange={(e) => update("archetype", e.target.value)}>
                {ARCHETYPES.map((a) => (
                  <option key={a} value={a}>
                    {a.replaceAll("_", " ")}
                  </option>
                ))}
              </select>
            </label>

            <label className="field">
              Primary platform
              <select value={form.platform} onChange={(e) => update("platform", e.target.value)}>
                {PLATFORMS.map((p) => (
                  <option key={p} value={p}>
                    {p}
                  </option>
                ))}
              </select>
            </label>

            <label className="field">
              Demo worker ID (optional, 1-200)
              <input
                type="number"
                min={1}
                max={200}
                placeholder="Leave blank to start with no history"
                value={form.demo_worker_id}
                onChange={(e) => update("demo_worker_id", e.target.value)}
              />
              <span className="field-hint">
                Seeds this account with a synthetic worker's earnings history so the dashboard has
                real data immediately.
              </span>
            </label>
          </>
        )}

        {error && <div className="form-error">{error}</div>}

        <button className="btn btn-primary" type="submit" disabled={busy}>
          {busy ? "Please wait..." : mode === "login" ? "Log in" : "Create account"}
        </button>
      </form>
    </div>
  );
}
