import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';

function CountUp({ to, suffix = '', duration = 1400 }) {
  const [val, setVal] = useState(0);
  useEffect(() => {
    let start = null;
    function step(ts) {
      if (!start) start = ts;
      const progress = Math.min((ts - start) / duration, 1);
      setVal(Math.floor(progress * to));
      if (progress < 1) requestAnimationFrame(step);
    }
    requestAnimationFrame(step);
  }, [to, duration]);
  return <span>{val.toLocaleString()}{suffix}</span>;
}

const FEATURES = [
  { icon: '🌐', title: 'Cognitive Digital Twin', desc: 'A live, reasoning-enabled map of Chennai — not just markers, but a twin that explains why a zone is risky and what to do about it.' },
  { icon: '🔥', title: 'Live Risk Heatmap', desc: 'Real historical incident density blended with live simulated activity, rendered as a continuously updating heatmap.' },
  { icon: '🧠', title: 'Real ML Forecasting', desc: 'A genuinely trained stacking classifier predicts crime type from time, place, and environmental conditions.' },
  { icon: '⚙️', title: 'Optimized Patrol Allocation', desc: 'A real Hungarian-algorithm solver assigns patrol units to zones to minimize risk-weighted response time.' },
  { icon: '💬', title: 'AI Copilot', desc: 'Ask plain-English questions about zones, patrols, or crime types and get answers grounded in real data.' },
  { icon: '📄', title: 'One-Click Reporting', desc: 'Generate an executive PDF brief with real risk index, real allocation, and a tactical summary — instantly.' },
];

export default function Home() {
  return (
    <div className="min-h-screen text-text-hi">
      {/* Hero */}
      <section
        className="relative min-h-screen flex flex-col items-center justify-center text-center px-6 overflow-hidden"
        style={{
          backgroundImage: `radial-gradient(circle at 25% 15%, rgba(61,139,253,0.20), transparent 45%),
                             radial-gradient(circle at 80% 75%, rgba(139,92,246,0.20), transparent 45%),
                             linear-gradient(rgba(7,9,18,0.6), rgba(7,9,18,0.85)),
                             url('/bg/command-center.jpg')`,
          backgroundSize: 'cover', backgroundPosition: 'center',
        }}
      >
        {/* animated radar rings */}
        <div className="absolute w-[520px] h-[520px] rounded-full border border-neon-blue/20 animate-ping" style={{ animationDuration: '3.5s' }} />
        <div className="absolute w-[340px] h-[340px] rounded-full border border-neon-purple/20 animate-ping" style={{ animationDuration: '4.5s' }} />

        <span className="relative text-xs uppercase tracking-[3px] text-neon-blue border border-neon-blue/30 bg-neon-blue/10 rounded-full px-4 py-1 mb-6">
          Final-Year AI &amp; Data Science Capstone &middot; Chennai Metro
        </span>
        <h1 className="relative font-display font-bold text-5xl md:text-6xl leading-tight mb-5 max-w-3xl">
          CrimeSense <span className="text-neon-blue">CDT</span>
        </h1>
        <p className="relative text-text-mid max-w-xl mb-10 text-lg">
          A cognitive digital twin for crime hotspot detection &amp; intelligent security management —
          real machine learning, real optimization, and a live reasoning layer over the city itself.
        </p>
        <div className="relative flex gap-4">
          <Link to="/login" className="bg-neon-blue hover:bg-blue-600 transition-colors rounded-lg px-7 py-3 font-semibold text-sm">
            Enter Command Center →
          </Link>
          <a href="#features" className="border border-white/15 hover:border-white/30 transition-colors rounded-lg px-7 py-3 font-semibold text-sm">
            See what's inside
          </a>
        </div>

        <div className="relative grid grid-cols-3 gap-10 mt-16">
          <div><div className="font-mono text-3xl font-bold text-neon-blue"><CountUp to={5} /></div><div className="text-xs text-text-dim mt-1">Zones Modeled</div></div>
          <div><div className="font-mono text-3xl font-bold text-neon-purple"><CountUp to={1800} suffix="+" /></div><div className="text-xs text-text-dim mt-1">Historical Incidents</div></div>
          <div><div className="font-mono text-3xl font-bold text-signal-green"><CountUp to={30} suffix="+" /></div><div className="text-xs text-text-dim mt-1">Modules Live</div></div>
        </div>
      </section>

      {/* Features */}
      <section id="features" className="max-w-6xl mx-auto px-6 py-24">
        <div className="text-center mb-14">
          <div className="text-xs uppercase tracking-[3px] text-text-dim mb-3">What's actually running underneath</div>
          <h2 className="font-display font-bold text-3xl">Built to be real where it matters, honest where it isn't</h2>
        </div>
        <div className="grid md:grid-cols-3 gap-6">
          {FEATURES.map((f) => (
            <div key={f.title} className="glass-card p-6 hover:border-white/20 transition-colors">
              <div className="text-3xl mb-3">{f.icon}</div>
              <h3 className="font-semibold mb-2">{f.title}</h3>
              <p className="text-text-mid text-sm leading-relaxed">{f.desc}</p>
            </div>
          ))}
        </div>
      </section>

      <section className="text-center pb-24 px-6">
        <div className="glass-card max-w-2xl mx-auto p-10">
          <h3 className="font-display font-bold text-2xl mb-3">Ready to step into the Command Center?</h3>
          <p className="text-text-mid mb-6 text-sm">Log in with the demo credentials to explore every module live.</p>
          <Link to="/login" className="inline-block bg-neon-blue hover:bg-blue-600 transition-colors rounded-lg px-7 py-3 font-semibold text-sm">
            Log In →
          </Link>
        </div>
      </section>
    </div>
  );
}
