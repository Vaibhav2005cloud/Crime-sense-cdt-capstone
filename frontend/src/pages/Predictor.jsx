import { useState } from 'react';
import { api } from '../api';

const ZONES = ['North', 'Central', 'West', 'East', 'South'];
const DAYS = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'];

export default function Predictor() {
  const [form, setForm] = useState({
    hour: 22, day_of_week: 'Friday', month: 7, zone: 'Central', district: 'T. Nagar',
    weather: 'Clear', is_festival_day: 0, is_weekend: 0, is_night: 1,
    population_density: 'High', street_lighting: 'Poor', alcohol_outlet_nearby: 1,
  });
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);

  const set = (k, v) => setForm((f) => ({ ...f, [k]: v }));

  async function submit(e) {
    e.preventDefault();
    setLoading(true);
    try {
      const r = await api.predict(form);
      setResult(r);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="grid grid-cols-2 gap-6">
      <form onSubmit={submit} className="glass-card p-6 space-y-3">
        <h3 className="text-sm font-semibold mb-2">Crime-Type Forecast <span className="text-signal-green text-xs">REAL — trained stacking classifier</span></h3>
        <div className="grid grid-cols-2 gap-3">
          <label className="text-xs text-text-dim">Hour
            <input type="number" min="0" max="23" value={form.hour} onChange={(e) => set('hour', Number(e.target.value))} className="w-full mt-1 bg-white/5 border border-white/10 rounded px-2 py-1 text-sm" />
          </label>
          <label className="text-xs text-text-dim">Day of Week
            <select value={form.day_of_week} onChange={(e) => set('day_of_week', e.target.value)} className="w-full mt-1 bg-white/5 border border-white/10 rounded px-2 py-1 text-sm">
              {DAYS.map((d) => <option key={d}>{d}</option>)}
            </select>
          </label>
          <label className="text-xs text-text-dim">Zone
            <select value={form.zone} onChange={(e) => set('zone', e.target.value)} className="w-full mt-1 bg-white/5 border border-white/10 rounded px-2 py-1 text-sm">
              {ZONES.map((z) => <option key={z}>{z}</option>)}
            </select>
          </label>
          <label className="text-xs text-text-dim">District
            <input value={form.district} onChange={(e) => set('district', e.target.value)} className="w-full mt-1 bg-white/5 border border-white/10 rounded px-2 py-1 text-sm" />
          </label>
          <label className="text-xs text-text-dim">Weather
            <select value={form.weather} onChange={(e) => set('weather', e.target.value)} className="w-full mt-1 bg-white/5 border border-white/10 rounded px-2 py-1 text-sm">
              <option>Clear</option><option>Rain</option><option>Cloudy</option><option>Foggy</option>
            </select>
          </label>
          <label className="text-xs text-text-dim">Street Lighting
            <select value={form.street_lighting} onChange={(e) => set('street_lighting', e.target.value)} className="w-full mt-1 bg-white/5 border border-white/10 rounded px-2 py-1 text-sm">
              <option>Poor</option><option>Moderate</option><option>Good</option>
            </select>
          </label>
        </div>
        <button className="w-full bg-neon-blue hover:bg-blue-600 transition-colors rounded py-2 text-sm font-semibold mt-2" disabled={loading}>
          {loading ? 'Predicting…' : 'Run Forecast'}
        </button>
      </form>

      <div className="glass-card p-6">
        {result ? (
          result.error ? (
            <p className="text-signal-red text-sm">{result.error}</p>
          ) : (
            <>
              <div className="text-xs text-text-dim mb-1">Predicted Crime Type</div>
              <div className="text-2xl font-display font-bold mb-4">{result.predicted_crime_type}</div>
              <div className="text-xs text-text-dim mb-2">Top 3 Probabilities</div>
              {result.top3.map(([type, p]) => (
                <div key={type} className="flex items-center justify-between text-sm py-1">
                  <span>{type}</span>
                  <div className="flex items-center gap-2 flex-1 mx-3">
                    <div className="h-1.5 bg-white/10 rounded flex-1"><div className="h-1.5 bg-neon-purple rounded" style={{ width: `${p * 100}%` }} /></div>
                    <span className="font-mono text-xs">{(p * 100).toFixed(1)}%</span>
                  </div>
                </div>
              ))}
            </>
          )
        ) : (
          <p className="text-text-dim text-sm">Fill in the scenario and run a forecast to see the model's prediction.</p>
        )}
      </div>
    </div>
  );
}
