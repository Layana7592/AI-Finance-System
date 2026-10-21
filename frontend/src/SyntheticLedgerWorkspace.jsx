import { useCallback, useEffect, useState } from "react";
import "./OperationalWorkspace.css";

const API = import.meta.env.VITE_API_BASE_URL || "/api";

async function request(path, token, options={}) {
  const response = await fetch(API + path, {
    ...options,
    headers: { Accept: "application/json", Authorization: "Token " + token,
      ...(options.body ? {"Content-Type":"application/json"} : {}) },
  });
  const json = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(
    typeof json.detail === "string" ? json.detail : JSON.stringify(json)
  );
  return json;
}

function operationKey() {
  return "demo-ledger-" + crypto.randomUUID();
}

export default function SyntheticLedgerWorkspace({token,user}) {
  const [data,setData]=useState(null);
  const [source,setSource]=useState("");
  const [destination,setDestination]=useState("");
  const [operation,setOperation]=useState("deposit");
  const [amount,setAmount]=useState("100.00");
  const [reversalId,setReversalId]=useState("");
  const [memo,setMemo]=useState("Synthetic study transaction");
  const [pendingKey,setPendingKey]=useState(operationKey);
  const [busy,setBusy]=useState(false);
  const [error,setError]=useState("");
  const [notice,setNotice]=useState("");

  const refresh=useCallback(async()=>{
    const updated=await request("/synthetic-ledger/",token);
    setData(updated);
    return updated;
  },[token]);
  useEffect(()=>{let ignore=false;request("/synthetic-ledger/",token)
    .then(x=>{if(!ignore)setData(x);})
    .catch(e=>{if(!ignore)setError(e.message);});
    return()=>{ignore=true;};
  },[token]);

  async function submit(e) {
    e.preventDefault();
    setBusy(true);setError("");setNotice("");
    try{
      const payload={
        operation,idempotency_key:pendingKey,memo,
        ...(operation==="reversal"
          ?{reversal_posting_id:Number(reversalId)}
          :{amount,account_id:Number(source),
              ...(operation==="transfer"?{destination_account_id:Number(destination)}:{})}),
      };
      const r=await request("/synthetic-ledger/",token,{method:"POST",body:JSON.stringify(payload)});
      const latest=await refresh();
      if(!latest.postings.some(p=>p.posting_id===r.posting.posting_id&&p.balanced)) {
        throw new Error("Posting created, but balanced read-back was not confirmed.");
      }
      setNotice((r.created?"Posted":"Idempotent retry")+
        ": #"+r.posting.posting_id+" / "+r.posting.operation+
        " / "+r.posting.amount+" (two balanced lines)");
      setPendingKey(operationKey());
    }catch(e){setError(e.message);}
    finally{setBusy(false);}
  }
  return <main className="ops-root">
    <header className="ops-hero">
      <p>ISOLATED SYNTHETIC ACCOUNTING SIMULATOR</p>
      <h1>Double-entry ledger and reconciliation</h1>
      <span>{user.role} · This ledger is NOT the original analytics transaction table or a real banking core.</span>
    </header>
    {error&&<div role="alert" className="ops-notice ops-error">{error}</div>}
    {notice&&<div role="status" className="ops-notice ops-success">{notice}</div>}
    <section className="ops-card">
      <h2>Post a balanced synthetic entry</h2>
      <form className="ops-form" onSubmit={submit}>
        <label>Operation
          <select value={operation} onChange={e=>{setOperation(e.target.value);setPendingKey(operationKey());}}>
            <option value="deposit">Simulated deposit</option>
            <option value="withdrawal">Simulated withdrawal</option>
            <option value="transfer">Simulated transfer</option>
            <option value="reversal">Reversal of posted entry</option>
          </select>
        </label>
        {operation!=="reversal"&&<label>Source account ID
          <input required type="number" min="1" value={source} onChange={e=>setSource(e.target.value)}/>
        </label>}
        {operation==="transfer"&&<label>Destination account ID
          <input required type="number" min="1" value={destination} onChange={e=>setDestination(e.target.value)}/>
        </label>}
        {operation==="reversal"?<label>Posting to reverse
          <input type="number" min="1" required value={reversalId} onChange={e=>setReversalId(e.target.value)}/>
        </label>:<label>Amount
          <input required type="number" min="0.01" step="0.01" value={amount} onChange={e=>setAmount(e.target.value)}/>
        </label>}
        <label>Memo (audit explanation)
          <input value={memo} maxLength={500} onChange={e=>setMemo(e.target.value)}/>
        </label>
        <button type="submit" disabled={busy}>{busy?"Posting…":"Post and verify balanced entry"}</button>
      </form>
      <p>Each new request receives a unique idempotency key; network retries preserve the existing key on error. Failed postings leave no lines or balance changes.</p>
    </section>
    <section className="ops-card">
      <h2>Ledger wallets (not legacy account balances)</h2>
      <div className="ops-table-scroll"><table>
        <thead><tr><th>Account ID</th><th>Account number</th><th>Current synthetic balance</th></tr></thead>
        <tbody>{(data?.wallets||[]).map(w=><tr key={w.account_id}>
          <td>{w.account_id}</td><td>{w.account_number}</td><td>{w.balance}</td></tr>)}</tbody>
      </table></div>
    </section>
    <section className="ops-card">
      <h2>Posted journal entries</h2>
      {(data?.postings||[]).map(post=><div className="ops-alert" key={post.posting_id}>
        <div>
          <strong>#{post.posting_id} · {post.operation} · {post.amount} · {post.balanced?"balanced":"UNBALANCED"}</strong>
          {post.lines.map((line,i)=><p key={i}>{line.side} · {line.code} · {line.amount}</p>)}
        </div></div>)}
    </section>
    {data?.reconciliation&&<section className="ops-card">
      <h2>Whole-ledger reconciliation — Admin only</h2>
      <p role="status">{data.reconciliation.balanced
        ?"All postings and wallet balances reconcile."
        :"Ledger discrepancy detected: "+data.reconciliation.issues.join(", ")}</p>
      <p>Postings: {data.reconciliation.postings}; wallet accounts: {data.reconciliation.wallets}; sum of signed balances: {data.reconciliation.total_balance}.</p>
    </section>}
    <p className="ops-disclaimer">{data?.disclaimer||"Synthetic accounting only."} Real deposits, payment infrastructure, legacy journals and account balances are not linked.</p>
  </main>;
}
