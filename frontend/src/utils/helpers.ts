import type { RiskLevel } from '../types';

export const RISK_COLORS: Record<RiskLevel, { bg: string; text: string; badge: string; border: string }> = {
  LOW:    { bg: 'var(--risk-low-bg)',    text: 'var(--risk-low-text)',    badge: 'badge-low',    border: 'var(--risk-low-border)' },
  MEDIUM: { bg: 'var(--risk-med-bg)',    text: 'var(--risk-med-text)',    badge: 'badge-medium', border: 'var(--risk-med-border)' },
  HIGH:   { bg: 'var(--risk-high-bg)',   text: 'var(--risk-high-text)',   badge: 'badge-high',   border: 'var(--risk-high-border)' },
};

export const formatCurrency = (v: number) =>
  new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD', maximumFractionDigits: 0 }).format(v);

export const formatPct = (v: number) => `${v >= 0 ? '+' : ''}${v.toFixed(1)}%`;

export const cpiLabel = (cpi: number) => cpi >= 1 ? '▲ Favorable' : '▼ Unfavorable';
export const spiLabel = (spi: number) => spi >= 1 ? '▲ On Schedule' : '▼ Behind Schedule';
