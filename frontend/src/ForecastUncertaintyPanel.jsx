import {useEffect,useState} from "react";
import "./OperationalWorkspace.css";
const API=import.meta.env.VITE_API_BASE_URL||"/api";
export default function ForecastUncertaintyPanel({token}){
  const [report,setReport]=useState(null),[error,setError]=useState("");
  useEffect(()=>{
    let cancelled=false;
    fetch(API+"/forecast-uncertainty/?months=12",{headers:{Authorization:"Token "+token}})
      .then(async r=>{const x=await r.json();if(!r.ok)throw new Error(x.detail||"Uncertainty API failed");return x;})
      .then(v=>{if(!cancelled)setReport(v);})
      .catch(e=>{if(!cancelled)setError(e.message)});
    return()=>{cancelled=true};
  },[token]);
  return <section className="ops-root">
    <div className="ops-card">
      <h2>Exploratory Seasonal-Naive uncertainty</h2>
      <p>Empirical bounds use horizon-specific past forecast errors. With only 24 synthetic months, most long horizons are unavailable. These are not validated financial guarantees or SARIMA confidence intervals.</p>
      {error&&<p role="alert">{error}</p>}
      {!error&&!report&&<p>Loading historical uncertainty evidence…</p>}
      {report&&["income","expense"].map(series=><div key={series}>
        <h3>{series==="income"?"Income":"Expense"} · {report.data[series].history_months} months history</h3>
        <div className="ops-table-scroll"><table>
          <thead><tr><th>Horizon</th><th>Baseline forecast</th><th>80% nominal lower</th><th>80% nominal upper</th><th>Calibration observations</th><th>Status</th></tr></thead>
          <tbody>{report.data[series].horizons.map(row=><tr key={row.horizon_months}>
            <td>{row.horizon_months} month(s)</td><td>{row.point_forecast??"—"}</td>
            <td>{row.lower??"Unavailable"}</td><td>{row.upper??"Unavailable"}</td>
            <td>{row.calibration_samples}</td>
            <td>{row.status==="illustrative_empirical_interval"?"Exploratory":"Insufficient data"}</td>
          </tr>)}</tbody>
        </table></div>
      </div>)}
      {report&&<p>{report.restrictions.join(" ")}</p>}
    </div>
  </section>;
}
