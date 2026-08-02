import { NavLink, Outlet, useNavigate } from 'react-router-dom';
import { useEffect, useState } from 'react';
import { useAuth } from './AuthContext';

const NAV = [
  { group: 'Command', items: [
    { to: '/app', label: 'Command Center', icon: '◆', desc: 'Everything at a glance' },
    { to: '/app/digital-twin', label: 'Cognitive Digital Twin', icon: '🌐', desc: 'Live Chennai map + heatmap' },
    { to: '/app/analytics', label: 'Analytics Center', icon: '📊', desc: 'Historical data charts' },
  ]},
  { group: 'AI Intelligence', items: [
    { to: '/app/predictor', label: 'Crime Forecasting', icon: '🧠', desc: 'Predict crime type for a scenario' },
    { to: '/app/allocation', label: 'Resource Allocation', icon: '⚙', desc: 'Best patrol-to-zone matching' },
    { to: '/app/explainable', label: 'Explainable AI', icon: '💡', desc: 'Why the model predicts what it does' },
    { to: '/app/copilot', label: 'AI Copilot', icon: '💬', desc: 'Ask questions in plain English' },
    { to: '/app/whatif', label: 'What-If Simulator', icon: '🎚', desc: 'Test a scenario\'s impact' },
  ]},
  { group: 'Reports', items: [
    { to: '/app/reports', label: 'Report Generator', icon: '📄', desc: 'Download a PDF briefing' },
  ]},
];

function Clock() {
  const [t, setT] = useState(new Date());
  useEffect(() => { const id = setInterval(() => setT(new Date()), 1000); return () => clearInterval(id); }, []);
  return <span className="font-mono text-signal-green text-sm">{t.toLocaleTimeString('en-GB')}</span>;
}

export default function Layout() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  async function handleLogout() {
    await logout();
    navigate('/login');
  }

  return (
    <div className="flex">
      <nav className="w-72 min-h-screen fixed bg-gradient-to-b from-[#0f1322] to-[#0a0d18] border-r border-white/10 flex flex-col">
        <div className="p-5 border-b border-white/10 flex items-center gap-3">
          <div className="pulse-logo relative w-8 h-8 rounded-full" style={{ background: 'radial-gradient(circle, #3D8BFD 0%, transparent 70%)' }} />
          <div>
            <h1 className="font-display font-bold text-sm">CrimeSense CDT v2</h1>
            <small className="text-text-dim text-[10px] tracking-wider uppercase">Chennai · Cognitive Twin</small>
          </div>
        </div>
        <div className="flex-1 overflow-y-auto py-2">
          {NAV.map((g) => (
            <div key={g.group}>
              <div className="text-[10px] uppercase tracking-wider text-text-dim px-6 pt-4 pb-1">{g.group}</div>
              {g.items.map((item) => (
                <NavLink key={item.to} to={item.to} end={item.to === '/app'}
                  className={({ isActive }) => `flex items-start gap-3 px-6 py-2.5 text-sm border-l-2 transition-colors ${isActive ? 'border-neon-blue bg-neon-blue/10 text-text-hi' : 'border-transparent text-text-mid hover:text-text-hi hover:bg-white/5'}`}>
                  <span className="mt-0.5">{item.icon}</span>
                  <span>
                    <div>{item.label}</div>
                    <div className="text-[10px] text-text-dim font-normal">{item.desc}</div>
                  </span>
                </NavLink>
              ))}
            </div>
          ))}
        </div>
        <div className="sidebar-footer p-4 border-t border-white/10">
          <div className="text-xs text-text-mid mb-2">
            <div className="font-semibold">{user?.name}</div>
            <div className="text-text-dim">{user?.role}</div>
          </div>
          <button onClick={handleLogout} className="w-full text-left text-signal-red text-sm flex items-center gap-2 hover:opacity-80">
            ⏻ Secure Logout
          </button>
        </div>
      </nav>
      <div className="ml-72 flex-1 min-h-screen">
        <div className="sticky top-0 z-40 backdrop-blur-lg bg-black/40 border-b border-white/10 px-8 py-3 flex items-center justify-between">
          <span className="text-xs bg-neon-blue/15 text-neon-blue border border-neon-blue/30 rounded-full px-3 py-1 font-semibold">
            <span className="inline-block w-2 h-2 rounded-full bg-signal-green mr-2 animate-pulse" />Digital Twin Sync Active
          </span>
          <Clock />
        </div>
        <div className="p-8">
          <Outlet />
        </div>
      </div>
    </div>
  );
}
