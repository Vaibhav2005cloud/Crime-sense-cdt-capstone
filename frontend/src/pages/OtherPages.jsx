import { useEffect, useState } from 'react';
import { api } from '../api';

export function Allocation() {
  const [data, setData] = useState(null);
  useEffect(() => { api.allocation().then(setData); }, []);
  if (!data) return <div className="text-text-dim">Solving assignment…</div>;
  return (
    <div className="space-y-4">
      <div className="glass-card p-4 text-sm text-text-mid">
        <span className="text-signal-green font-semibold">REAL</span> — solved with <code>scipy.optimize.linear_sum_assignment</code> (Hungarian algorithm). Total weighted cost: <span className="font-mono">{data.total_cost}</span>
      </div>
      <div className="glass-card p-5">
        <table className="w-full text-sm">
          <thead className="text-text-dim text-xs uppercase"><tr><th className="text-left py-1">Unit</th><th className="text-left">ETA</th><th className="text-left">Zone</th><th className="text-left">Risk</th></tr></thead>
          <tbody>
            {data.allocation.map((a) => (
              <tr key={a.unit} className="border-t border-white/5"><td className="py-1">{a.unit}</td><td>{a.response_time_min} min</td><td>{a.zone}</td><td className="font-mono">{a.zone_risk}</td></tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

export function Explainable() {
  const [data, setData] = useState(null);
  useEffect(() => { api.explainable().then(setData); }, []);
  if (!data) return <div className="text-text-dim">Loading model importances…</div>;
  const Bar = ({ feat, val, color }) => (
    <div className="flex items-center justify-between text-sm py-1">
      <span>{feat}</span>
      <div className="flex items-center gap-2 flex-1 mx-3"><div className="h-1.5 bg-white/10 rounded flex-1"><div className="h-1.5 rounded" style={{ width: `${val * 400}%`, background: color }} /></div><span className="font-mono text-xs">{val}</span></div>
    </div>
  );
  return (
    <div className="grid grid-cols-2 gap-4">
      <div className="glass-card p-5"><h3 className="text-sm font-semibold mb-3">Crime-Type Model — Top Drivers <span className="text-signal-green text-xs">REAL</span></h3>{data.crime_type_model.map(([f, v]) => <Bar key={f} feat={f} val={v} color="#3D8BFD" />)}</div>
      <div className="glass-card p-5"><h3 className="text-sm font-semibold mb-3">Deployment Model — Top Drivers <span className="text-signal-green text-xs">REAL</span></h3>{data.deployment_model.map(([f, v]) => <Bar key={f} feat={f} val={v} color="#8B5CF6" />)}</div>
    </div>
  );
}

export function WhatIf() {
  const [scenarios, setScenarios] = useState({});
  const [zone, setZone] = useState('Central');
  const [scenario, setScenario] = useState('');
  const [result, setResult] = useState(null);
  useEffect(() => { api.whatifScenarios().then((s) => { setScenarios(s); setScenario(Object.keys(s)[0]); }); }, []);

  async function run(e) {
    e.preventDefault();
    setResult(await api.whatif(zone, scenario));
  }

  return (
    <div className="grid grid-cols-2 gap-6">
      <form onSubmit={run} className="glass-card p-6 space-y-3">
        <h3 className="text-sm font-semibold mb-2">Configure Scenario</h3>
        <label className="text-xs text-text-dim block">Zone
          <select value={zone} onChange={(e) => setZone(e.target.value)} className="w-full mt-1 bg-white/5 border border-white/10 rounded px-2 py-1 text-sm">
            {['North', 'Central', 'West', 'East', 'South'].map((z) => <option key={z}>{z}</option>)}
          </select>
        </label>
        <label className="text-xs text-text-dim block">Scenario
          <select value={scenario} onChange={(e) => setScenario(e.target.value)} className="w-full mt-1 bg-white/5 border border-white/10 rounded px-2 py-1 text-sm">
            {Object.entries(scenarios).map(([k, s]) => <option key={k} value={k}>{s.label}</option>)}
          </select>
        </label>
        <button className="w-full bg-neon-blue hover:bg-blue-600 rounded py-2 text-sm font-semibold mt-2">Run Simulation</button>
      </form>
      <div className="glass-card p-6">
        {result ? (
          <>
            <h3 className="font-semibold mb-1">{result.scenario} — {result.zone}</h3>
            <p className="text-xs text-text-dim mb-4">{result.note}</p>
            <div className="grid grid-cols-3 text-center mb-4">
              <div><div className="font-mono text-xl font-bold">{result.base_risk}</div><div className="text-[10px] text-text-dim">Baseline</div></div>
              <div><div className="font-mono text-xl font-bold" style={{ color: result.delta > 0 ? '#FB4570' : '#22D3A6' }}>{result.delta > 0 ? '+' : ''}{result.delta}</div><div className="text-[10px] text-text-dim">Delta</div></div>
              <div><div className="font-mono text-xl font-bold">{result.new_risk}</div><div className="text-[10px] text-text-dim">Projected</div></div>
            </div>
            <div className="text-xs text-text-dim mb-1">Re-allocation <span className="text-signal-green">REAL</span></div>
            {result.allocation.map((a) => <div key={a.unit} className="flex justify-between text-sm py-0.5"><span>{a.unit}</span><span>{a.zone} ({a.zone_risk})</span></div>)}
          </>
        ) : <p className="text-text-dim text-sm">Run a scenario to see the projected impact.</p>}
      </div>
    </div>
  );
}

export function Copilot() {
  const [brief, setBrief] = useState('');
  const [history, setHistory] = useState([]);
  const [q, setQ] = useState('');
  useEffect(() => { api.dailyBrief().then((r) => setBrief(r.brief)); }, []);

  async function ask(e) {
    e.preventDefault();
    if (!q.trim()) return;
    const question = q; setQ('');
    setHistory((h) => [...h, { role: 'user', text: question }]);
    const r = await api.copilot(question);
    setHistory((h) => [...h, { role: 'ai', text: r.answer }]);
  }

  return (
    <div>
      <div
        className="rounded-2xl mb-4 h-28 border border-white/10"
        style={{
          backgroundImage: `linear-gradient(90deg, rgba(7,9,18,0.35), rgba(7,9,18,0.75)), url('/bg/copilot-bg.jpg')`,
          backgroundSize: 'cover',
          backgroundPosition: 'center',
        }}
      />
      <div className="grid grid-cols-2 gap-6">
        <div className="glass-card p-5"><h3 className="text-sm font-semibold mb-2">Daily Tactical Brief</h3><pre className="whitespace-pre-wrap font-mono text-xs text-text-mid">{brief}</pre></div>
        <div className="glass-card p-5 flex flex-col h-[420px]">
          <h3 className="text-sm font-semibold mb-2">Ask the Copilot</h3>
          <div className="flex-1 overflow-auto space-y-2 mb-3">
            {history.map((m, i) => (
              <div key={i} className={m.role === 'user' ? 'text-right' : ''}>
                <span className={`text-[10px] px-2 py-0.5 rounded ${m.role === 'user' ? 'bg-neon-blue/30' : 'bg-white/10'}`}>{m.role === 'user' ? 'You' : 'Copilot'}</span>
                <div className="text-sm mt-1">{m.text}</div>
              </div>
            ))}
          </div>
          <form onSubmit={ask} className="flex gap-2">
            <input value={q} onChange={(e) => setQ(e.target.value)} placeholder="Ask about zones, patrols, crime types…" className="flex-1 bg-white/5 border border-white/10 rounded px-3 py-2 text-sm" />
            <button className="bg-neon-blue rounded px-4 text-sm">Send</button>
          </form>
        </div>
      </div>
    </div>
  );
}

export function Reports() {
  return (
    <div className="grid grid-cols-2 gap-6">
      <div className="glass-card p-8 text-center">
        <h3 className="font-semibold mb-2">Executive Intelligence Report</h3>
        <p className="text-xs text-text-dim mb-4">Real risk index + real Hungarian-algorithm allocation, bundled into a PDF.</p>
        <a href={api.reportPdfUrl()} className="inline-block bg-neon-blue rounded px-4 py-2 text-sm font-semibold">Download PDF</a>
      </div>
    </div>
  );
}
