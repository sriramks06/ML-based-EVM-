import React from 'react';
import { SectionCard } from './SectionCard';
import { RiskBadge } from './RiskBadge';
import type { Recommendation } from '../types';

interface RecommendationsPanelProps { recommendations: Recommendation[]; }

export const RecommendationsPanel: React.FC<RecommendationsPanelProps> = ({ recommendations }) => (
  <SectionCard title="Recommended Actions" icon="💡">
    {recommendations.length === 0 ? (
      <p className="empty-text">No recommendations triggered — project conditions are within thresholds.</p>
    ) : (
      <div className="rec-list">
        {recommendations.map((rec, i) => (
          <div key={i} className={`rec-item priority-${rec.priority.toLowerCase()}`}>
            <div className="rec-header">
              <RiskBadge level={rec.priority} size="sm" />
              <span className="rec-factor">{rec.risk_factor.replace(/_/g, ' ')}</span>
            </div>
            <p className="rec-explanation">{rec.explanation}</p>
            <p className="rec-action">→ {rec.recommendation}</p>
          </div>
        ))}
      </div>
    )}
  </SectionCard>
);
