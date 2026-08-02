import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../AuthContext';

const DEMO_USERS = [
  { user: 'admin', pass: 'admin123', role: 'Administrator' },
  { user: 'commissioner', pass: 'commissioner123', role: 'Commissioner' },
  { user: 'analyst', pass: 'analyst123', role: 'Analyst' },
];

export default function Login() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const [username, setUsername] = useState('admin');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  async function submit(e) {
    e.preventDefault();
    setError(''); setLoading(true);
    try {
      await login(username, password);
      navigate('/app');
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div
      className="min-h-screen flex items-center justify-center relative"
      style={{
        backgroundImage: `radial-gradient(circle at 20% 20%, rgba(61,139,253,0.18), transparent 45%),
                           radial-gradient(circle at 85% 80%, rgba(139,92,246,0.18), transparent 45%),
                           linear-gradient(rgba(7,9,18,0.55), rgba(7,9,18,0.75)),
                           url('/bg/login-bg.jpg')`,
        backgroundSize: 'cover',
        backgroundPosition: 'center',
      }}
    >
      <form onSubmit={submit} className="glass-card w-[400px] p-9 text-center relative z-10">
        <div className="pulse-logo relative w-14 h-14 mx-auto mb-3 rounded-full" style={{ background: 'radial-gradient(circle, #3D8BFD 0%, transparent 70%)' }} />
        <h1 className="font-display font-bold text-xl mb-1">CrimeSense CDT</h1>
        <div className="text-text-dim text-[11px] tracking-widest uppercase mb-6">Smart City Digital Twin &middot; Chennai</div>

        {error && <div className="bg-signal-red/10 border border-signal-red/30 text-signal-red text-sm rounded-lg py-2 px-3 mb-4">{error}</div>}

        <label className="text-xs text-text-dim block text-left mb-1">Officer ID</label>
        <input value={username} onChange={(e) => setUsername(e.target.value)} className="w-full mb-4 bg-white/5 border border-white/10 rounded-lg px-3 py-2 text-sm outline-none focus:border-neon-blue" placeholder="admin" />

        <label className="text-xs text-text-dim block text-left mb-1">Secure Key</label>
        <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} className="w-full mb-6 bg-white/5 border border-white/10 rounded-lg px-3 py-2 text-sm outline-none focus:border-neon-blue" placeholder="••••••••" />

        <button disabled={loading} className="w-full bg-neon-blue hover:bg-blue-600 transition-colors rounded-lg py-2.5 text-sm font-semibold">
          {loading ? 'Authenticating…' : 'Authenticate'}
        </button>

        <div className="text-text-dim text-xs mt-5 text-left">
          Demo credentials:
          <ul className="mt-1 font-mono space-y-0.5">
            {DEMO_USERS.map((u) => <li key={u.user}>{u.user} / {u.pass} <span className="text-text-dim/70">({u.role})</span></li>)}
          </ul>
        </div>
      </form>
    </div>
  );
}
