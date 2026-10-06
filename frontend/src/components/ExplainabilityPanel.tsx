import React from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Cell, ResponsiveContainer } from 'recharts';
import { SectionCard } from './SectionCard';
import type { ExplanationResponse } from '../types';

interface ExplainabilityPanelProps { explanation: ExplanationResponse; }

const PALETTE = ['#6366f1', '#8b5cf6', '#a78bfa', '#c4b5fd', '#ddd6fe'];

export const ExplainabilityPanel: React.FC<ExplainabilityPanelProps> = ({ explanation }) => {
  const costData = explanation.top_cost_factors.map(f => ({
    name: f.feature.replace(/_/g, ' '),
    value: parseFloat(f.importance.toFixed(1)),
  }));
  const schedData = explanation.top_schedule_factors.map(f => ({
    name: f.feature.replace(/_/g, ' '),
    value: parseFloat(f.importance.toFixed(1)),
  }));

  const FactorChart = ({ data, title }: { data: typeof costData; title: string }) => (
    <div>
      <p className="chart-sub-title">{title}</p>
      <ResponsiveContainer width="100%" height={190}>
        <BarChart data={data} layout="vertical" margin={{ top: 0, right: 20, left: 80, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="var(--grid-line)" horizontal={false} />
          <XAxis type="number" unit="%" tick={{ fontSize: 10, fill: 'var(--text-muted)' }} />
          <YAxis type="category" dataKey="name" tick={{ fontSize: 10, fill: 'var(--text-muted)' }} width={80} />
          <Tooltip formatter={(v) => `${Number(v).toFixed(1)}%`} contentStyle={{ background: 'var(--card-bg)', border: '1px solid var(--border)', borderRadius: 8 }} />
          <Bar dataKey="value" radius={[0, 6, 6, 0]}>
            {data.map((_, i) => <Cell key={i} fill={PALETTE[i % PALETTE.length]} />)}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );

  return (
    <SectionCard title="Top Prediction Factors" icon="🔍">
      <div className="two-col-charts">
        <FactorChart data={costData} title="Cost Prediction Signals" />
        <FactorChart data={schedData} title="Schedule Prediction Signals" />
      </div>
      <p className="disclaimer-note">
        ⚠️ These factors represent model signals contributing to the prediction. They should not be interpreted as proof of causation.
      </p>
    </SectionCard>
  );
};
