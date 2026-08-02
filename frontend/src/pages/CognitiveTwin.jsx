import { useEffect, useRef, useState } from 'react';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import 'leaflet.heat';
import { api, connectLiveFeed } from '../api';

function riskColor(v) {
  if (v >= 75) return '#FB4570';
  if (v >= 55) return '#FF7A45';
  if (v >= 35) return '#FFC24B';
  return '#22D3A6';
}

export default function CognitiveTwin() {
  const mapRef = useRef(null);
  const containerRef = useRef(null);
  const heatLayerRef = useRef(null);
  const zoneLayerRef = useRef(null);
  const patrolLayerRef = useRef(null);
  const droneLayerRef = useRef(null);

  const [selectedZone, setSelectedZone] = useState(null);
  const [reasoning, setReasoning] = useState(null);
  const [reasoningLoading, setReasoningLoading] = useState(false);
  const [showHeat, setShowHeat] = useState(true);
  const [showPatrols, setShowPatrols] = useState(true);
  const [showDrones, setShowDrones] = useState(true);
  const [liveRisk, setLiveRisk] = useState({});

  async function openZone(zone) {
    setSelectedZone(zone);
    setReasoningLoading(true);
    try {
      const r = await api.zoneReasoning(zone);
      setReasoning(r);
    } finally {
      setReasoningLoading(false);
    }
  }

  useEffect(() => {
    if (!containerRef.current || mapRef.current) return;

    // Real Chennai basemap (CARTO dark tiles show actual streets/labels —
    // far more legible for a 5-zone city view than a distant 3D globe).
    const map = L.map(containerRef.current, { zoomControl: true }).setView([13.0827, 80.2707], 11);
    L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
      attribution: '&copy; OpenStreetMap &copy; CARTO', maxZoom: 19,
    }).addTo(map);
    mapRef.current = map;

    zoneLayerRef.current = L.layerGroup().addTo(map);
    patrolLayerRef.current = L.layerGroup().addTo(map);
    droneLayerRef.current = L.layerGroup().addTo(map);

    Promise.all([api.zoneRisk(), api.zoneCoords(), api.incidentPoints()]).then(([risk, coords, points]) => {
      setLiveRisk(risk);

      // REAL — live heatmap from actual historical incident points, weighted by severity
      const heatPoints = points.map((p) => [p.lat, p.lng, p.severity / 10]);
      heatLayerRef.current = L.heatLayer(heatPoints, {
        radius: 28, blur: 22, maxZoom: 13,
        gradient: { 0.2: '#22D3A6', 0.4: '#FFC24B', 0.6: '#FF7A45', 1.0: '#FB4570' },
      }).addTo(map);

      const bounds = [];
      Object.keys(coords).forEach((zone) => {
        const { latitude, longitude } = coords[zone];
        bounds.push([latitude, longitude]);
        const r = risk[zone] ?? 50;
        const marker = L.circleMarker([latitude, longitude], {
          radius: 14 + r / 6, color: riskColor(r), fillColor: riskColor(r), fillOpacity: 0.25, weight: 2,
        }).bindTooltip(`<b>${zone}</b><br/>DRI ${r}/100 — click for details`, { direction: 'top' });
        marker.on('click', () => openZone(zone));
        marker.addTo(zoneLayerRef.current);

        // simulated patrol + drone markers near the zone centroid
        const pLat = latitude + (Math.random() - 0.5) * 0.025;
        const pLng = longitude + (Math.random() - 0.5) * 0.025;
        L.marker([pLat, pLng], { icon: L.divIcon({ className: '', html: '<div style="font-size:16px;">🚓</div>' }) })
          .bindTooltip(`Patrol unit — ${zone} sector (simulated)`).addTo(patrolLayerRef.current);

        const dLat = latitude + (Math.random() - 0.5) * 0.04;
        const dLng = longitude + (Math.random() - 0.5) * 0.04;
        L.marker([dLat, dLng], { icon: L.divIcon({ className: '', html: '<div style="font-size:15px;">🛰️</div>' }) })
          .bindTooltip(`UAV coverage — ${zone} (simulated)`).addTo(droneLayerRef.current);
      });
      if (bounds.length) map.fitBounds(bounds, { padding: [40, 40] });
    });

    const ws = connectLiveFeed((data) => setLiveRisk(data.risk));
    return () => {
      ws.close();
      map.remove();
      mapRef.current = null;
    };
  }, []);

  useEffect(() => {
    const map = mapRef.current;
    if (!map || !heatLayerRef.current) return;
    if (showHeat) map.addLayer(heatLayerRef.current); else map.removeLayer(heatLayerRef.current);
  }, [showHeat]);
  useEffect(() => {
    const map = mapRef.current;
    if (!map || !patrolLayerRef.current) return;
    if (showPatrols) map.addLayer(patrolLayerRef.current); else map.removeLayer(patrolLayerRef.current);
  }, [showPatrols]);
  useEffect(() => {
    const map = mapRef.current;
    if (!map || !droneLayerRef.current) return;
    if (showDrones) map.addLayer(droneLayerRef.current); else map.removeLayer(droneLayerRef.current);
  }, [showDrones]);

  return (
    <div>
      <div
        className="rounded-2xl mb-3 h-24 border border-white/10"
        style={{
          backgroundImage: `linear-gradient(90deg, rgba(7,9,18,0.35), rgba(7,9,18,0.75)), url('/bg/heatmap-bg.jpg')`,
          backgroundSize: 'cover',
          backgroundPosition: 'center',
        }}
      />
    <div className="grid grid-cols-3 gap-4">
      <div className="col-span-2 space-y-3">
        <div className="glass-card p-2">
          <div ref={containerRef} style={{ height: '600px', borderRadius: '14px', overflow: 'hidden' }} />
        </div>
        <div className="glass-card p-3 flex flex-wrap gap-5 text-sm">
          <label className="flex items-center gap-2"><input type="checkbox" checked={showHeat} onChange={(e) => setShowHeat(e.target.checked)} /> Live Risk Heatmap <span className="text-signal-green text-xs">REAL</span></label>
          <label className="flex items-center gap-2"><input type="checkbox" checked={showPatrols} onChange={(e) => setShowPatrols(e.target.checked)} /> Patrol Units <span className="text-signal-amber text-xs">SIM</span></label>
          <label className="flex items-center gap-2"><input type="checkbox" checked={showDrones} onChange={(e) => setShowDrones(e.target.checked)} /> Drone Coverage <span className="text-signal-amber text-xs">SIM</span></label>
        </div>
        <p className="text-xs text-text-dim">
          Click any zone marker for the Cognitive layer's reasoning — a real, factor-by-factor breakdown of why that
          zone's risk score is what it is, not just the number.
        </p>
      </div>

      <div className="space-y-3">
        <div className="glass-card p-4">
          <h3 className="text-sm font-semibold mb-3">Zone Risk (Live)</h3>
          {Object.entries(liveRisk).map(([z, v]) => (
            <button key={z} onClick={() => openZone(z)} className={`w-full flex justify-between items-center py-2 px-2 rounded-lg mb-1 text-sm transition-colors ${selectedZone === z ? 'bg-white/10' : 'hover:bg-white/5'}`}>
              <span>{z}</span><span className="font-mono font-bold" style={{ color: riskColor(v) }}>{v}</span>
            </button>
          ))}
        </div>

        <div className="glass-card p-4 min-h-[280px]">
          <h3 className="text-sm font-semibold mb-3">Cognitive Reasoning <span className="text-signal-green text-xs">REAL</span></h3>
          {!selectedZone && <p className="text-text-dim text-sm">Select a zone to see why its risk score is what it is.</p>}
          {reasoningLoading && <p className="text-text-dim text-sm">Reasoning…</p>}
          {reasoning && !reasoningLoading && (
            <>
              <p className="text-sm text-text-mid mb-4">{reasoning.narrative}</p>
              <div className="text-xs text-text-dim mb-2">Contributing factors</div>
              {Object.entries(reasoning.factors).map(([k, v]) => (
                <div key={k} className="flex items-center justify-between text-xs py-1">
                  <span className="capitalize">{k.replaceAll('_', ' ')}</span>
                  <div className="flex items-center gap-2 flex-1 mx-2"><div className="h-1.5 bg-white/10 rounded flex-1"><div className="h-1.5 rounded bg-neon-blue" style={{ width: `${Math.min(100, v * 2)}%` }} /></div><span className="font-mono">{v}</span></div>
                </div>
              ))}
              {reasoning.recommended_unit && (
                <div className="mt-4 text-xs bg-neon-blue/10 border border-neon-blue/30 rounded-lg p-3">
                  Recommended: <b>{reasoning.recommended_unit.unit}</b> (ETA {reasoning.recommended_unit.response_time_min} min)
                </div>
              )}
            </>
          )}
        </div>
      </div>
    </div>
    </div>
  );
}
