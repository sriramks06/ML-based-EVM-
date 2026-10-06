import React from 'react';
import {
  XAxis, YAxis, CartesianGrid, Tooltip, Legend,
  LineChart, Line, ResponsiveContainer
} from 'recharts';
import { SectionCard } from './SectionCard';
import { formatCurrency } from '../utils/helpers';
import type { ProjectWeek } from '../types';

interface TrendChartsProps { weeks: ProjectWeek[]; }

export const TrendCharts: React.FC<TrendChartsProps> = ({ weeks }) => {
  const data = weeks.map(w => ({
    week: `W${w.week}`,
    PV: Math.round(w.PV),
    EV: Math.round(w.EV),
    AC: Math.round(w.AC),
    CPI: parseFloat(w.CPI.toFixed(3)),
    SPI: parseFloat(w.SPI.toFixed(3)),
  }));

  return (
    <>
      <SectionCard title="PV / EV / AC Over Time" icon="📈">
        <ResponsiveContainer width="100%" height={220}>
          <LineChart data={data} margin={{ top: 5, right: 16, left: 10, bottom: 5 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="var(--grid-line)" />
            <XAxis dataKey="week" tick={{ fontSize: 11, fill: 'var(--text-muted)' }} />
            <YAxis tickFormatter={v => `$${(v / 1000).toFixed(0)}k`} tick={{ fontSize: 11, fill: 'var(--text-muted)' }} />
            <Tooltip formatter={(v) => formatCurrency(Number(v))} contentStyle={{ background: 'var(--card-bg)', border: '1px solid var(--border)', borderRadius: 8 }} />
            <Legend />
            <Line type="monotone" dataKey="PV" stroke="#6366f1" strokeWidth={2} dot={false} name="Planned Value" />
            <Line type="monotone" dataKey="EV" stroke="#10b981" strokeWidth={2} dot={false} name="Earned Value" />
            <Line type="monotone" dataKey="AC" stroke="#f43f5e" strokeWidth={2} dot={false} name="Actual Cost" />
          </LineChart>
        </ResponsiveContainer>
      </SectionCard>

      <SectionCard title="CPI & SPI Trend" icon="📊">
        <ResponsiveContainer width="100%" height={220}>
          <LineChart data={data} margin={{ top: 5, right: 16, left: 10, bottom: 5 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="var(--grid-line)" />
            <XAxis dataKey="week" tick={{ fontSize: 11, fill: 'var(--text-muted)' }} />
            <YAxis domain={[0, 2]} tick={{ fontSize: 11, fill: 'var(--text-muted)' }} />
            <Tooltip contentStyle={{ background: 'var(--card-bg)', border: '1px solid var(--border)', borderRadius: 8 }} />
            <Legend />
            {/* Reference line at 1.0 */}
            <Line type="monotone" dataKey="CPI" stroke="#f59e0b" strokeWidth={2} dot={false} name="CPI" />
            <Line type="monotone" dataKey="SPI" stroke="#3b82f6" strokeWidth={2} dot={false} name="SPI" />
          </LineChart>
        </ResponsiveContainer>
        <p className="chart-note">Values &gt; 1.0 indicate favorable performance.</p>
      </SectionCard>
    </>
  );
};
