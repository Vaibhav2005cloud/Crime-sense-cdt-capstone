import { useEffect, useState } from 'react';
import { api, connectLiveFeed } from '../api';

export default function CommandCenter() {
  const [risk, setRisk] = useState({});
  const [modules, setModules] = useState({});
  const [incidents, setIncidents] = useState([]);
  const [summary, setSummary] = useState(null);

  useEffect(() => {
    api.analyticsSummary().then(setSummary).catch(() => {});
    const ws = connectLiveFeed((data) => {
      setRisk(data.risk);
      setModules(data.modules);
      setIncidents(data.incidents);
    });
    return () => ws.close();
  }, []);

  const topZone = Object.entries(risk).sort((a, b) => b[1] - a[1])[0];

  return (
    <div className="space-y-6">
      <div className="glass-card p-6 bg-gradient-to-br from-neon-blue/10 to-neon-purple/10 border border-white/10">
        <div className="text-xs uppercase tracking-wider text-text-dim mb-1">Live Operations Overview</div>
        <h2 className="text-xl font-display font-bold mb-1">
          {topZone ? `${topZone[0]} is the current highest-priority zone` : 'Loading live feed…'}
        </h2>
        {topZone && (
          <p className="text-text-mid text-sm">
            Blended Dynamic Risk Index: <span className="font-mono text-text-hi font-bold">{topZone[1]}/100</span>
            {summary && <> · {summary.total_incidents} historical incidents · {summary.high_severity} high-severity</>}
          </p>
        )}
      </div>

      <div>
        <h3 className="text-text-dim text-xs uppercase tracking-wider mb-2">Zone Risk Index (Live) — <span className="text-signal-green">REAL + SIM blend</span></h3>
        <div className="grid grid-cols-5 gap-3">
          {Object.entries(risk).map(([z, v]) => (
            <div key={z} className="glass-card p-4 text-center">
              <div className="text-xs text-text-dim">{z}</div>
              <div className="font-mono text-2xl font-bold">{v}</div>
              <div className="text-[10px] text-text-dim">Risk / 100</div>
            </div>
          ))}
        </div>
      </div>

      <div>
        <h3 className="text-text-dim text-xs uppercase tracking-wider mb-2">Digital Twin Module Grid — All Systems Initiated</h3>
        <div className="grid grid-cols-4 gap-3">
          {Object.entries(modules).map(([key, m]) => (
            <div key={key} className="glass-card p-4 relative">
              <span className={`absolute top-3 right-3 text-[9px] font-bold px-2 py-0.5 rounded-full uppercase ${m.kind === 'real' ? 'bg-signal-green/15 text-signal-green border border-signal-green/30' : 'bg-signal-amber/15 text-signal-amber border border-signal-amber/30'}`}>
                {m.kind === 'real' ? 'REAL' : 'SIM'}
              </span>
              <div className="text-sm font-semibold mb-1">{m.label}</div>
              {m.desc && <div className="text-[11px] text-text-mid mb-2 leading-snug">{m.desc}</div>}
              <div className="font-mono text-xl font-bold">{String(m.value)}</div>
              <div className="text-[10px] text-text-dim">{m.unit}</div>
            </div>
          ))}
        </div>
      </div>

      <div className="glass-card p-5">
        <h3 className="text-sm font-semibold mb-3">Live Incident Feed <span className="text-signal-amber text-xs">SIM</span></h3>
        <table className="w-full text-sm">
          <thead className="text-text-dim text-xs uppercase">
            <tr><th className="text-left py-1">ID</th><th className="text-left">Zone</th><th className="text-left">Type</th><th className="text-left">Severity</th><th className="text-left">Time</th></tr>
          </thead>
          <tbody className="font-mono text-text-mid">
            {incidents.map((inc) => (
              <tr key={inc.id} className="border-t border-white/5">
                <td className="py-1">{inc.id}</td><td>{inc.zone}</td><td>{inc.type}</td><td>{inc.severity}</td><td>{inc.time}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
