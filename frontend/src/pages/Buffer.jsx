import { useEffect, useState } from "react";
import { useAuth } from "../context/AuthContext.jsx";
import { api } from "../services/api.js";

export default function Buffer() {
  const { user } = useAuth();
  const [state, setState] = useState(null);
  const [amount, setAmount] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  function load() {
    if (!user) return;
    api
      .getBuffer(user.id)
      .then(setState)
      .catch((err) => setError(err.message));
  }

  useEffect(load, [user]);

  async function handleAction(action) {
    setError("");
    const value = Number(amount);
    if (!value || value <= 0) {
      setError("Enter an amount greater than 0");
      return;
    }
    setBusy(true);
    try {
      if (action === "deposit") await api.deposit(value);
      else await api.withdraw(value);
      setAmount("");
      load();
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  }

  if (!state) return <div className="page">Loading...</div>;

  return (
    <div className="page">
      <h1>Buffer</h1>

      <div className="card">
        <div className="card-label">Current balance</div>
        <div className="card-value large">Rs.{Math.round(state.balance).toLocaleString()}</div>

        <div className="buffer-actions">
          <input
            type="number"
            min={1}
            placeholder="Amount"
            value={amount}
            onChange={(e) => setAmount(e.target.value)}
          />
          <button className="btn btn-primary" disabled={busy} onClick={() => handleAction("deposit")}>
            Deposit
          </button>
          <button className="btn btn-ghost" disabled={busy} onClick={() => handleAction("withdraw")}>
            Withdraw
          </button>
        </div>
        {error && <div className="form-error">{error}</div>}
        <p className="field-hint">
          Manual deposits/withdrawals are on top of the automatic weekly save/release schedule — every
          transaction here is something you confirmed, not an automatic action.
        </p>
      </div>

      <div className="card">
        <div className="card-label">Transaction history</div>
        <table className="table">
          <thead>
            <tr>
              <th>Week</th>
              <th>Kind</th>
              <th>Amount</th>
              <th>Balance after</th>
            </tr>
          </thead>
          <tbody>
            {state.transactions.map((t) => (
              <tr key={t.id}>
                <td>{t.week_start}</td>
                <td>{t.kind.replaceAll("_", " ")}</td>
                <td>Rs.{Math.round(t.amount).toLocaleString()}</td>
                <td>Rs.{Math.round(t.balance_after).toLocaleString()}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
