import React from 'react';

interface MetricCardProps {
  label: string;
  value: string;
  sub?: string;
  subColor?: string;
  accent?: string;
  icon?: React.ReactNode;
}

export const MetricCard: React.FC<MetricCardProps> = ({ label, value, sub, subColor, accent, icon }) => (
  <div className="metric-card" style={accent ? { borderTop: `3px solid ${accent}` } : {}}>
    <div className="metric-card-header">
      <span className="metric-label">{label}</span>
      {icon && <span className="metric-icon">{icon}</span>}
    </div>
    <div className="metric-value">{value}</div>
    {sub && <div className="metric-sub" style={subColor ? { color: subColor } : {}}>{sub}</div>}
  </div>
);
