import { useCallback, useEffect, useState } from "react";
import "./OperationalWorkspace.css";

const API = import.meta.env.VITE_API_BASE_URL || "/api";

async function api(path, token, options = {}) {
  const response = await fetch(API + path, {
    ...options,
    headers: {
      Accept: "application/json",
      Authorization: "Token " + token,
      ...(options.body ? { "Content-Type": "application/json" } : {}),
    },
  });
  const body = await response.json().catch(() => ({}));
  if (!response.ok) {
    const message = body?.detail || JSON.stringify(body);
    throw new Error(response.status + ": " + message);
  }
  return body;
}

export default function OperationalWorkspace({ token, user }) {
  const [snapshot, setSnapshot] = useState(null);
  const [accountId, setAccountId] = useState("");
  const [amount, setAmount] = useState("999999.00");
  const [merchant, setMerchant] = useState("UnexpectedMerchant");
  const [location, setLocation] = useState("UnusualLocation");
  const [transactionType, setTransactionType] = useState("Withdrawal");
  const [resolutionNote, setResolutionNote] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");

  const refresh = useCallback(async (filter = "") => {
    const params = filter ? "?account_id=" + encodeURIComponent(filter) : "";
    const data = await api("/operations/" + params, token);
    setSnapshot(data);
    setError("");
    return data;
  }, [token]);

  useEffect(() => {
    let active = true;
    const params = accountId ? "?account_id=" + encodeURIComponent(accountId) : "";
    api("/operations/" + params, token)
      .then((data) => { if (active) { setSnapshot(data); setError(""); } })
      .catch((e) => { if (active) setError(e.message); });
    return () => { active = false; };
  }, [token, accountId]);

  const transact = async (event) => {
    event.preventDefault();
    if (!accountId || busy) return;
    setBusy(true); setError(""); setMessage("");
    try {
      const tx = await api("/transactions/", token, {
        method: "POST",
        body: JSON.stringify({
          account: Number(accountId),
          amount,
          transaction_type: transactionType,
          merchant: merchant.trim(),
          location: location.trim(),
          transaction_time: new Date().toISOString(),
          status: "Completed",
        }),
      });
      const current = await refresh(accountId);
      const prediction = current.predictions.find((item) => item.transaction === tx.transaction_id);
      if (!prediction) throw new Error("Transaction saved, but its prediction was not returned.");
      setMessage("Created synthetic transaction #" + tx.transaction_id +
        ". Stored behavioural score: " + prediction.fraud_probability +
        "; flagged: " + String(prediction.prediction) + ".");
    } catch (e) {
      setError(e.message);
    } finally { setBusy(false); }
  };

  const resolve = async (alert) => {
    if (busy) return;
    if (resolutionNote.trim().length < 10) {
      setError("A written investigation decision of at least 10 characters is required.");
      return;
    }
    setBusy(true); setError(""); setMessage("");
    try {
      const result = await api("/alerts/" + alert.alert_id + "/", token, {
        method: "PATCH",
        body: JSON.stringify({
          is_resolved: true, resolution_note: resolutionNote.trim(),
        }),
      });
      if (!result.is_resolved) throw new Error("The API did not confirm resolution.");
      const refreshed = await refresh(accountId);
      if (!refreshed.alerts.some((a) => a.alert_id === result.alert_id && a.is_resolved)) {
        throw new Error("Alert resolution did not persist to the read-back snapshot.");
      }
      setResolutionNote("");
      setMessage("Alert #" + alert.alert_id + " resolved and audit-logged, with original evidence retained.");
    } catch (e) { setError(e.message); }
    finally { setBusy(false); }
  };

  const accounts = snapshot?.accounts || [];
  const transactions = snapshot?.transactions || [];
  const predictions = snapshot?.predictions || [];
  const alerts = snapshot?.alerts || [];
  const audit = snapshot?.audit_logs || [];
  const predictionByTx = new Map(predictions.map((p) => [p.transaction, p]));
  return (
    <main className="ops-root">
      <header className="ops-hero">
        <p>LIVE OPERATIONS · SYNTHETIC DATA</p>
        <h1>Transactions and alert investigations</h1>
        <span>{user.role} · {user.branch || "All branches"} · Recent records are permission-scoped.</span>
      </header>

      {error && <div role="alert" className="ops-notice ops-error">{error}</div>}
      {message && <div role="status" className="ops-notice ops-success">{message}</div>}

      <div className="ops-card">
        <label htmlFor="ops-account">Account to investigate</label>
        <div className="ops-actions">
          <select id="ops-account" value={accountId} onChange={(e) => setAccountId(e.target.value)} disabled={busy}>
            <option value="">Recent records across authorized accounts</option>
            {accounts.map((account) => (
              <option value={account.account_id} key={account.account_id}>
                {account.account_number} · ID {account.account_id}
              </option>
            ))}
          </select>
          <button type="button" disabled={busy} onClick={() => refresh(accountId)}>Refresh verified records</button>
        </div>
        <small>Shows at most 35 accounts and alerts and 30 transactions. A manager never sees another branch.</small>
      </div>

      <section className="ops-card">
        <h2>Create a synthetic transaction</h2>
        <form onSubmit={transact} className="ops-form">
          <label>Amount <input type="number" step="0.01" min="0.01" required value={amount} onChange={(e) => setAmount(e.target.value)} /></label>
          <label>Type <select value={transactionType} onChange={(e) => setTransactionType(e.target.value)}>
            <option>Withdrawal</option><option>Purchase</option><option>Payment</option><option>Deposit</option><option>Transfer</option>
          </select></label>
          <label>Merchant <input maxLength={100} required value={merchant} onChange={(e) => setMerchant(e.target.value)} /></label>
          <label>Location <input maxLength={100} required value={location} onChange={(e) => setLocation(e.target.value)} /></label>
          <button type="submit" disabled={busy || !accountId}>
            {busy ? "Saving…" : "Create and verify transaction"}
          </button>
        </form>
        <p className="ops-disclaimer">The transaction is a demo record and does not move money or update a reconciled ledger. Risk scores are not calibrated fraud probabilities.</p>
      </section>

      <section className="ops-card">
        <h2>Recent transactions and stored screening results</h2>
        <div className="ops-table-scroll"><table>
          <thead><tr><th>Transaction</th><th>Amount</th><th>Merchant</th><th>Screening</th><th>Risk score</th></tr></thead>
          <tbody>{transactions.map((tx) => {
            const p = predictionByTx.get(tx.transaction_id);
            return <tr key={tx.transaction_id}><td>#{tx.transaction_id}</td>
              <td>{tx.amount}</td><td>{tx.merchant}</td>
              <td>{p ? (p.prediction ? "Flagged" : "Not flagged") : "No saved screening"}</td>
              <td>{p ? p.fraud_probability : "—"}</td></tr>;
          })}</tbody>
        </table></div>
      </section>

      <section className="ops-card">
        <h2>Alert review and resolution</h2>
        <p>Resolution is deliberate: supply a reason, preserve the original alert, and verify the audit entry.</p>
        <label htmlFor="ops-resolution-note">Investigation conclusion</label>
        <textarea id="ops-resolution-note" rows={2} maxLength={500}
          placeholder="Explain why this alert has been reviewed and resolved"
          value={resolutionNote} onChange={(e) => setResolutionNote(e.target.value)} />
        <div className="ops-alert-list">{alerts.length ? alerts.map((a) => (
          <div className="ops-alert" key={a.alert_id}>
            <div><strong>#{a.alert_id} · Transaction #{a.transaction} · {a.severity}</strong>
              <p>{a.message}</p>
              <small>{a.is_resolved ? "Resolved" : "Open for investigation"}</small>
            </div>
            {!a.is_resolved && <button type="button" disabled={busy} onClick={() => resolve(a)}>Resolve with reason</button>}
          </div>
        )) : <p>No alerts in this authorized scope.</p>}</div>
      </section>

      <section className="ops-card">
        <h2>Immutable audit trail</h2>
        <div className="ops-audit-list">{audit.map((item) => (
          <div key={item.log_id}><time>{item.log_time}</time> <span>{item.action}</span></div>
        ))}</div>
      </section>
    </main>
  );
}
