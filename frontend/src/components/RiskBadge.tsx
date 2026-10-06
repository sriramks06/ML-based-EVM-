import React from 'react';
import type { RiskLevel } from '../types';
import { RISK_COLORS } from '../utils/helpers';

interface RiskBadgeProps { level: RiskLevel; size?: 'sm' | 'md' | 'lg'; }

const sizes = { sm: '0.65rem', md: '0.8rem', lg: '1rem' };

export const RiskBadge: React.FC<RiskBadgeProps> = ({ level, size = 'md' }) => (
  <span style={{
    background: RISK_COLORS[level].bg,
    color: RISK_COLORS[level].text,
    border: `1px solid ${RISK_COLORS[level].border}`,
    borderRadius: '6px',
    padding: '3px 10px',
    fontSize: sizes[size],
    fontWeight: 700,
    letterSpacing: '0.05em',
    textTransform: 'uppercase',
  }}>
    {level}
  </span>
);
