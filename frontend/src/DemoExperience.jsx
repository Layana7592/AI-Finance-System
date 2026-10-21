import { useEffect, useRef, useState } from "react";
import AnalyticsDashboard from "./App.jsx";
import OperationalWorkspace from "./OperationalWorkspace.jsx";
import SyntheticLedgerWorkspace from "./SyntheticLedgerWorkspace.jsx";
import ForecastUncertaintyPanel from "./ForecastUncertaintyPanel.jsx";
import "./DemoExperience.css";

const API = import.meta.env.VITE_API_BASE_URL || "/api";
const TOKEN_KEY = "finance_api_token";
const STEPS = [
  "Dashboard analytics",
  "Locate presenter account",
  "Create suspicious synthetic transaction",
  "Read saved fraud prediction",
  "Verify alert creation",
  "Verify the audit trail",
  "Read stored forecasts",
  "Generate management report",
];

async function request(path, token, options = {}) {
  const response = await fetch(API + path, {
    ...options,
    headers: {
      Accept: "application/json",
      ...(token ? { Authorization: "Token " + token } : {}),
      ...(options.body ? { "Content-Type": "application/json" } : {}),
      ...(options.headers || {}),
    },
  });
  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    const detail = typeof data.detail === "string"
      ? data.detail
      : (data.error || JSON.stringify(data));
    throw new Error(path + ": " + response.status + " " + detail);
  }
  return data;
}

function asList(payload) {
  return Array.isArray(payload) ? payload : (payload?.results || []);
}

function seconds(ms) {
  return (ms / 1000).toFixed(1) + "s";
}

export default function DemoExperience() {
  const [token, setToken] = useState(() => sessionStorage.getItem(TOKEN_KEY) || "");
  const [user, setUser] = useState(null);
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [loginBusy, setLoginBusy] = useState(false);
  const [loginError, setLoginError] = useState("");
  const [logoutError, setLogoutError] = useState("");
  const [signingOut, setSigningOut] = useState(false);
  const [mode, setMode] = useState("demo");
  const [running, setRunning] = useState(false);
  const [records, setRecords] = useState([]);
  const [runError, setRunError] = useState("");
  const [started, setStarted] = useState(null);
  const [finished, setFinished] = useState(null);
  const [clock, setClock] = useState(Date.now());
  const [evidence, setEvidence] = useState({});
  const runningRef = useRef(false);

  useEffect(() => {
    if (!token) {
      setUser(null);
      return;
    }
    let cancelled = false;
    request("/me/", token).then((person) => {
      if (!cancelled) setUser(person);
    }).catch(() => {
      if (!cancelled) {
        sessionStorage.removeItem(TOKEN_KEY);
        setToken("");
        setUser(null);
        setLoginError("Your session expired. Please sign in again.");
      }
    });
    return () => { cancelled = true; };
  }, [token]);

  useEffect(() => {
    if (!running) return undefined;
    const interval = setInterval(() => setClock(Date.now()), 250);
    return () => clearInterval(interval);
  }, [running]);

  async function login(event) {
    event.preventDefault();
    if (loginBusy) return;
    setLoginBusy(true);
    setLoginError("");
    try {
      const auth = await request("/token/", "", {
        method: "POST",
        body: JSON.stringify({ username, password }),
      });
      if (!auth.token) throw new Error("The login response contained no token.");
      const person = await request("/me/", auth.token);
      if (!person.can_run_demo && !person.can_use_operations) {
        throw new Error("The authenticated operations workspace requires an Admin or Manager role.");
      }
      sessionStorage.setItem(TOKEN_KEY, auth.token);
      setToken(auth.token);
      setUser(person);
      setPassword("");
      setMode(person.can_run_demo ? "demo" : "operations");
    } catch (error) {
      sessionStorage.removeItem(TOKEN_KEY);
      setLoginError(error.message);
    } finally {
      setLoginBusy(false);
    }
  }

  async function logout() {
    if (runningRef.current || signingOut || !token) return;
    setSigningOut(true);
    setLogoutError("");
    try {
      // The token must be revoked on the server before local state is cleared.
      await request("/logout/", token, { method: "POST" });
      sessionStorage.removeItem(TOKEN_KEY);
      setToken("");
      setUser(null);
      setEvidence({});
      setRecords([]);
      setRunError("");
      setMode("demo");
    } catch (error) {
      // Do not claim sign-out succeeded when the old server token may still work.
      setLogoutError("Sign-out could not revoke the server token: " + error.message);
    } finally {
      setSigningOut(false);
    }
  }

  async function runStep(index, action) {
    const mark = performance.now();
    setRecords((items) => [...items, { index, status: "running", duration: null, detail: "" }]);
    try {
      const outcome = await action();
      setRecords((items) => items.map((item) => item.index === index
        ? { ...item, status: "pass", duration: seconds(performance.now() - mark), detail: outcome.detail }
        : item));
      return outcome;
    } catch (error) {
      setRecords((items) => items.map((item) => item.index === index
        ? { ...item, status: "fail", duration: seconds(performance.now() - mark), detail: error.message }
        : item));
      throw error;
    }
  }

  async function startDemo() {
    if (runningRef.current || !token || !user?.can_run_demo) return;
    runningRef.current = true;
    setRunning(true);
    setRunError("");
    setRecords([]);
    setEvidence({});
    setFinished(null);
    const startedAt = Date.now();
    setStarted(startedAt);
    setClock(startedAt);
    const findings = {};
    try {
      await runStep(0, async () => {
        const dash = await request("/dashboard/", token);
        if (!dash || typeof dash !== "object") throw new Error("No dashboard data returned.");
        findings.dashboard = dash;
        setEvidence({ ...findings });
        return { detail: "Verified backend dashboard response received" };
      });

      await runStep(1, async () => {
        const accounts = asList(await request("/accounts/", token));
        const account = accounts.find((a) => a.account_number === "DEMO-ACCOUNT-2026");
        if (!account) throw new Error("Presenter account missing: run prepare_demo_presenter first.");
        findings.account = account;
        setEvidence({ ...findings });
        return { detail: "Account " + account.account_number + " (ID " + account.account_id + ")" };
      });

      await runStep(2, async () => {
        const tx = await request("/transactions/", token, {
          method: "POST",
          body: JSON.stringify({
            account: findings.account.account_id,
            amount: "999999999.00",
            transaction_type: "Transfer",
            merchant: `DemoMerchant-${Date.now()}`,
            location: `DemoLocation-${Date.now()}`,
            transaction_time: new Date().toISOString(),
            status: "Completed",
          }),
        });
        if (!tx.transaction_id) throw new Error("No transaction ID was returned.");
        findings.transaction = tx;
        setEvidence({ ...findings });
        return { detail: "Created transaction #" + tx.transaction_id + " (synthetic, not a real payment)" };
      });

      await runStep(3, async () => {
        const predictions = asList(await request("/fraud-predictions/", token));
        const result = predictions.find((p) => p.transaction === findings.transaction.transaction_id);
        if (!result) throw new Error("Prediction missing for newly created transaction.");
        if (!result.prediction) throw new Error("This controlled suspicious transaction was not flagged.");
        findings.prediction = result;
        setEvidence({ ...findings });
        return { detail: "Flagged, risk score " + result.fraud_probability + " (NOT calibrated probability), " + result.model_version };
      });

      await runStep(4, async () => {
        const alerts = asList(await request("/alerts/", token));
        const alert = alerts.find((a) => a.transaction === findings.transaction.transaction_id);
        if (!alert) throw new Error("No persisted alert for this suspicious transaction.");
        findings.alert = alert;
        setEvidence({ ...findings });
        return { detail: "Alert #" + alert.alert_id + ": " + alert.severity + "; unresolved=" + !alert.is_resolved };
      });

      await runStep(5, async () => {
        const logs = asList(await request("/audit-logs/", token));
        const log = logs.find((a) => a.action?.includes("Transaction " + findings.transaction.transaction_id + " created"));
        if (!log) throw new Error("Audit log missing for created transaction.");
        findings.audit = log;
        setEvidence({ ...findings });
        return { detail: "Audit #" + log.log_id + ": action persisted" };
      });

      await runStep(6, async () => {
        const forecasts = asList(await request("/forecasts/", token));
        if (forecasts.length !== 12) throw new Error("Expected 12 saved forecasts; found " + forecasts.length);
        findings.forecasts = forecasts;
        setEvidence({ ...findings });
        return { detail: "Confirmed 12 saved forecast months, " + forecasts[0].forecast_month + " onward" };
      });

      await runStep(7, async () => {
        const report = await request("/report/", token);
        if (!report?.report || !report?.verified_results) {
          throw new Error("Management report missing report text or verified numerical evidence.");
        }
        findings.report = report;
        setEvidence({ ...findings });
        return {
          detail: report.report_source === "gemini"
            ? "Gemini report generated from Python metrics"
            : "Deterministic fallback report; Gemini unavailable (disclosed)",
        };
      });
      setFinished(Date.now());
    } catch (error) {
      setRunError(error.message);
      setFinished(Date.now());
    } finally {
      runningRef.current = false;
      setRunning(false);
    }
  }

  if (!token || !user) {
    return (
      <main className="demo-login-layout">
        <form className="demo-login" onSubmit={login} aria-label="Sign in">
          <div className="demo-brand">AF / PGDDSA</div>
          <h1>AI Finance System</h1>
          <p>Academic demonstration — synthetic transaction analytics</p>
          <label htmlFor="demo-user">Username</label>
          <input id="demo-user" autoComplete="username" value={username}
            onChange={(event) => setUsername(event.target.value)} required />
          <label htmlFor="demo-pass">Password</label>
          <input id="demo-pass" type="password" autoComplete="current-password"
            value={password} onChange={(event) => setPassword(event.target.value)} required />
          <button type="submit" disabled={loginBusy}>
            {loginBusy ? "Signing in…" : "Sign in"}
          </button>
          {loginError && <p role="alert" className="demo-error">{loginError}</p>}
          <small>Presenter access is created locally through prepare_demo_presenter. No credentials are embedded in this website.</small>
        </form>
      </main>
    );
  }

  const completed = records.filter((r) => r.status === "pass").length;
  const elapsed = started ? seconds((finished || clock) - started) : "Not started";
  const allDone = finished && completed === STEPS.length && !runError;
  return (
    <div className="demo-root">
      <nav className="demo-nav" aria-label="Application navigation">
        <strong>AI Finance System <span> / PGDDSA Demonstration</span></strong>
        <div className="demo-nav-right">
          {user.can_run_demo && <button type="button" aria-pressed={mode === "demo"} onClick={() => setMode("demo")}>Guided demo</button>}
          {user.can_use_operations && <button type="button" aria-pressed={mode === "operations"} onClick={() => setMode("operations")}>Operations</button>}
          {user.can_use_operations && <button type="button" aria-pressed={mode === "ledger"} onClick={() => setMode("ledger")}>Synthetic ledger</button>}
          {user.can_view_global_analytics && <button type="button" aria-pressed={mode === "analytics"} onClick={() => setMode("analytics")}>Analytics dashboard</button>}
          <span className="demo-identity">{user.username} · {user.role}</span>
          <button type="button" onClick={logout} disabled={running || signingOut}>{signingOut ? "Signing out…" : "Sign out"}</button>
        </div>
      </nav>
      {logoutError && <p role="alert" className="demo-error">{logoutError}</p>}
      {mode === "analytics" && user.can_view_global_analytics ? (
        <><div className="demo-full-dashboard"><AnalyticsDashboard /></div><ForecastUncertaintyPanel token={token}/></>
      ) : mode === "ledger" && user.can_use_operations ? (
        <SyntheticLedgerWorkspace token={token} user={user}/>
      ) : mode === "operations" || !user.can_run_demo ? (
        <OperationalWorkspace token={token} user={user} />
      ) : (
        <main className="demo-main">
          <div className="demo-heading">
            <div>
              <p className="demo-eyebrow">LIVE, BACKEND-VERIFIED WALKTHROUGH</p>
              <h1>One transaction. Eight verified steps.</h1>
              <p>Every step calls the real Django API. No mocked transactions, alerts, or metrics.</p>
            </div>
            <div className="demo-timer" aria-live="polite">
              <span>Elapsed time</span><strong>{elapsed}</strong>
              <small>{completed}/{STEPS.length} verified</small>
            </div>
          </div>
          <div className="demo-actions">
            <button type="button" onClick={startDemo} disabled={running} className="demo-start">
              {running ? "Demonstration running…" : started ? "Run another timed demonstration" : "Start timed demonstration"}
            </button>
            <span>Presenter identity and the demonstration account must be prepared in advance.</span>
          </div>
          {allDone && <p className="demo-success" role="status">Demo complete — 8/8 backend checks verified in {elapsed}.</p>}
          {runError && <p className="demo-error" role="alert">Demo stopped after {completed} successful steps: {runError}</p>}
          <div className="demo-step-list">
            {STEPS.map((label, index) => {
              const record = records.find((item) => item.index === index);
              return (
                <section className={"demo-step " + (record?.status || "pending")} key={label}
                  aria-label={label}>
                  <span className="demo-index">{String(index + 1).padStart(2, "0")}</span>
                  <div>
                    <h2>{label}</h2>
                    <p>{record?.detail || "Awaiting backend verification"}</p>
                  </div>
                  <strong>{record?.status || "pending"}{record?.duration ? " · " + record.duration : ""}</strong>
                </section>
              );
            })}
          </div>
          {evidence.transaction && (
            <section className="demo-evidence">
              <h2>Verified transaction evidence</h2>
              <p>Transaction #{evidence.transaction.transaction_id} — synthetic withdrawal {evidence.transaction.amount}</p>
              {evidence.prediction && <p>Behavioural risk score: {evidence.prediction.fraud_probability}; flagged: {String(evidence.prediction.prediction)}; model: {evidence.prediction.model_version}</p>}
              {evidence.alert && <p>Alert #{evidence.alert.alert_id} — {evidence.alert.message}</p>}
              {evidence.audit && <p>Audit event #{evidence.audit.log_id} — {evidence.audit.action}</p>}
              {evidence.forecasts && <p>Saved forecast records: {evidence.forecasts.length}</p>}
              {evidence.report && <p>Management report source: {evidence.report.report_source}. {evidence.report.gemini_available ? "AI interpretation available." : "Fallback mode disclosed."}</p>}
              {evidence.report && <details><summary>Show management report</summary><pre>{evidence.report.report}</pre></details>}
            </section>
          )}
          <p className="demo-disclaimer">Research prototype using synthetic data. The live risk score is heuristic, not a fraud probability. Isolation Forest evaluation and forecasting are separate research benchmarks. No money moves.</p>
        </main>
      )}
    </div>
  );
}
