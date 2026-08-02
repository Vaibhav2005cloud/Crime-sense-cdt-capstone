import { useEffect, useState } from 'react';
import ReactECharts from 'echarts-for-react';
import { api } from '../api';

const darkBase = {
  backgroundColor: 'transparent',
  textStyle: { color: '#AEB8D4' },
  grid: { left: 40, right: 20, top: 30, bottom: 30 },
};

export default function Analytics() {
  const [data, setData] = useState(null);
  useEffect(() => { api.analyticsSummary().then(setData); }, []);
  if (!data) return <div className="text-text-dim">Loading real analytics…</div>;

  const byType = Object.entries(data.by_crime_type);
  const byHour = Object.entries(data.by_hour).sort((a, b) => Number(a[0]) - Number(b[0]));
  const byZone = Object.entries(data.by_zone);

  const typeChart = {
    ...darkBase,
    tooltip: {},
    xAxis: { type: 'category', data: byType.map(([k]) => k), axisLabel: { rotate: 30, color: '#AEB8D4' } },
    yAxis: { type: 'value', axisLabel: { color: '#AEB8D4' } },
    series: [{ type: 'bar', data: byType.map(([, v]) => v), itemStyle: { color: '#3D8BFD' } }],
  };
  const hourChart = {
    ...darkBase,
    tooltip: {},
    xAxis: { type: 'category', data: byHour.map(([k]) => `${k}:00`), axisLabel: { color: '#AEB8D4' } },
    yAxis: { type: 'value', axisLabel: { color: '#AEB8D4' } },
    series: [{ type: 'line', data: byHour.map(([, v]) => v), smooth: true, itemStyle: { color: '#8B5CF6' }, areaStyle: { opacity: 0.15 } }],
  };
  const zoneChart = {
    ...darkBase,
    tooltip: {},
    series: [{
      type: 'pie', radius: ['45%', '70%'],
      data: byZone.map(([k, v]) => ({ name: k, value: v })),
      label: { color: '#AEB8D4' },
      itemStyle: { borderColor: '#0b0f1c', borderWidth: 2 },
    }],
    color: ['#3D8BFD', '#8B5CF6', '#FF7A45', '#22D3A6', '#FFC24B'],
  };

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-4 gap-4">
        <div className="glass-card p-4 text-center"><div className="font-mono text-2xl font-bold">{data.total_incidents}</div><div className="text-xs text-text-dim">Historical Records</div></div>
        <div className="glass-card p-4 text-center"><div className="font-mono text-2xl font-bold">{data.high_severity}</div><div className="text-xs text-text-dim">High Severity</div></div>
        <div className="glass-card p-4 text-center"><div className="font-mono text-2xl font-bold">{data.night_share_pct}%</div><div className="text-xs text-text-dim">Night-time Share</div></div>
        <div className="glass-card p-4 text-center"><div className="font-mono text-2xl font-bold">{byZone.length}</div><div className="text-xs text-text-dim">Zones Covered</div></div>
      </div>
      <div className="grid grid-cols-2 gap-4">
        <div className="glass-card p-4"><h3 className="text-sm font-semibold mb-2">Incidents by Crime Type <span className="text-signal-green text-xs">REAL</span></h3><ReactECharts option={typeChart} style={{ height: 280 }} /></div>
        <div className="glass-card p-4"><h3 className="text-sm font-semibold mb-2">Incidents by Zone <span className="text-signal-green text-xs">REAL</span></h3><ReactECharts option={zoneChart} style={{ height: 280 }} /></div>
      </div>
      <div className="glass-card p-4"><h3 className="text-sm font-semibold mb-2">Incidents by Hour of Day <span className="text-signal-green text-xs">REAL</span></h3><ReactECharts option={hourChart} style={{ height: 260 }} /></div>
    </div>
  );
}
