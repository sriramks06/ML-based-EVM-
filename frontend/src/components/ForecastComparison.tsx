import React from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from 'recharts';
import { SectionCard } from './SectionCard';
import { formatCurrency } from '../utils/helpers';
import type { PredictionResponse } from '../types';

interface ForecastComparisonProps { prediction: PredictionResponse; }

export const ForecastComparison: React.FC<ForecastComparisonProps> = ({ prediction }) => {
  const costData = [
    { name: 'EVM EAC', value: Math.round(prediction.traditional_eac), fill: '#6366f1' },
    { name: 'ML Forecast', value: Math.round(prediction.predicted_final_cost), fill: '#f43f5e' },
    { name: 'Budget (BAC)', value: Math.round(prediction.BAC), fill: '#10b981' },
  ];

  const scheduleData = [
    { name: 'EVM Est.', value: parseFloat(prediction.traditional_estimated_duration.toFixed(1)), fill: '#6366f1' },
    { name: 'ML Forecast', value: parseFloat(prediction.predicted_final_duration.toFixed(1)), fill: '#f43f5e' },
    { name: 'Planned', value: prediction.planned_duration, fill: '#10b981' },
  ];

  return (
    <SectionCard title="Traditional EVM vs ML Forecast" icon="⚖️">
      <div className="two-col-charts">
        <div>
          <p className="chart-sub-title">Cost Forecast ($)</p>
          <ResponsiveContainer width="100%" height={200}>
            <BarChart data={costData} margin={{ top: 5, right: 10, left: 10, bottom: 5 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="var(--grid-line)" vertical={false} />
              <XAxis dataKey="name" tick={{ fontSize: 11, fill: 'var(--text-muted)' }} />
              <YAxis tickFormatter={v => `$${(v / 1000).toFixed(0)}k`} tick={{ fontSize: 11, fill: 'var(--text-muted)' }} />
              <Tooltip formatter={(v) => formatCurrency(Number(v))} contentStyle={{ background: 'var(--card-bg)', border: '1px solid var(--border)', borderRadius: 8 }} />
              <Bar dataKey="value" radius={[6, 6, 0, 0]}>
                {costData.map((entry, index) => <Cell key={index} fill={entry.fill} />)}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
        <div>
          <p className="chart-sub-title">Duration Forecast (weeks)</p>
          <ResponsiveContainer width="100%" height={200}>
            <BarChart data={scheduleData} margin={{ top: 5, right: 10, left: 10, bottom: 5 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="var(--grid-line)" vertical={false} />
              <XAxis dataKey="name" tick={{ fontSize: 11, fill: 'var(--text-muted)' }} />
              <YAxis tick={{ fontSize: 11, fill: 'var(--text-muted)' }} />
              <Tooltip contentStyle={{ background: 'var(--card-bg)', border: '1px solid var(--border)', borderRadius: 8 }} />
              <Bar dataKey="value" radius={[6, 6, 0, 0]}>
                {scheduleData.map((entry, index) => <Cell key={index} fill={entry.fill} />)}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>
      <div className="legend-row">
        <span><span className="dot" style={{background:'#6366f1'}} /> Traditional EVM</span>
        <span><span className="dot" style={{background:'#f43f5e'}} /> ML Prediction</span>
        <span><span className="dot" style={{background:'#10b981'}} /> Baseline</span>
      </div>
    </SectionCard>
  );
};
