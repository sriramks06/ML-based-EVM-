import React, { useState } from 'react';
import { simulateProjectOutcome } from '../services/api';
import { formatCurrency } from '../utils/helpers';
import { SectionCard } from './SectionCard';
import type { PredictionResponse } from '../types';

interface Props {
  projectId: number;
  week: number;
  originalPrediction: PredictionResponse;
}

export const SimulatorPanel: React.FC<Props> = ({ projectId, week, originalPrediction }) => {
  const [delaySeverity, setDelaySeverity] = useState<number>(5);
  const [resourceUtil, setResourceUtil] = useState<number>(0.8);
  const [teamExperience, setTeamExperience] = useState<number>(0.5);
  const [taskComplexity, setTaskComplexity] = useState<number>(5);
  
  const [simPrediction, setSimPrediction] = useState<PredictionResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSimulate = async () => {
    setLoading(true);
    setError('');
    try {
      const overrides = {
        Delay_Severity: delaySeverity,
        Resource_Utilization: resourceUtil,
        Team_Experience: teamExperience,
        Task_Complexity: taskComplexity
      };
      const res = await simulateProjectOutcome(projectId, week, overrides);
      setSimPrediction(res);
    } catch (err) {
      setError('Simulation failed.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <SectionCard title="What-If Scenario Simulator" icon="🎛️">
      <div className="simulator-controls" style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem', marginBottom: '1rem' }}>
        <div>
          <label style={{display: 'block', fontSize: '0.85rem', fontWeight: 600}}>Delay Severity (1-10): {delaySeverity}</label>
          <input type="range" min="1" max="10" step="1" value={delaySeverity} onChange={e => setDelaySeverity(Number(e.target.value))} style={{width: '100%'}}/>
        </div>
        <div>
          <label style={{display: 'block', fontSize: '0.85rem', fontWeight: 600}}>Resource Utilization (0-1): {resourceUtil}</label>
          <input type="range" min="0" max="1" step="0.05" value={resourceUtil} onChange={e => setResourceUtil(Number(e.target.value))} style={{width: '100%'}}/>
        </div>
        <div>
          <label style={{display: 'block', fontSize: '0.85rem', fontWeight: 600}}>Team Experience (0-1): {teamExperience}</label>
          <input type="range" min="0" max="1" step="0.05" value={teamExperience} onChange={e => setTeamExperience(Number(e.target.value))} style={{width: '100%'}}/>
        </div>
        <div>
          <label style={{display: 'block', fontSize: '0.85rem', fontWeight: 600}}>Task Complexity (1-10): {taskComplexity}</label>
          <input type="range" min="1" max="10" step="1" value={taskComplexity} onChange={e => setTaskComplexity(Number(e.target.value))} style={{width: '100%'}}/>
        </div>
      </div>
      <button onClick={handleSimulate} disabled={loading} className="btn-analyze" style={{width: '100%', marginBottom: '1rem'}}>
        {loading ? 'Simulating...' : 'Run Simulation'}
      </button>

      {error && <div style={{ color: 'red' }}>{error}</div>}

      {simPrediction && (
        <div style={{ background: 'var(--bg-card)', padding: '1rem', borderRadius: '8px', border: '1px solid var(--border)', marginTop: '1rem' }}>
          <h4 style={{ margin: '0 0 0.5rem 0' }}>Simulation Results</h4>
          <div style={{ display: 'flex', justifyContent: 'space-between', borderBottom: '1px solid var(--border)', paddingBottom: '0.5rem' }}>
            <span><strong>Cost Forecast:</strong></span>
            <span>
              {formatCurrency(simPrediction.predicted_final_cost)} 
              <span style={{ fontSize: '0.85rem', marginLeft: '0.5rem', color: simPrediction.predicted_final_cost > originalPrediction.predicted_final_cost ? 'red' : 'green' }}>
                ({formatCurrency(simPrediction.predicted_final_cost - originalPrediction.predicted_final_cost)} vs original)
              </span>
            </span>
          </div>
          <div style={{ display: 'flex', justifyContent: 'space-between', paddingTop: '0.5rem' }}>
            <span><strong>Schedule Forecast:</strong></span>
            <span>
              {simPrediction.predicted_final_duration.toFixed(1)} wks
              <span style={{ fontSize: '0.85rem', marginLeft: '0.5rem', color: simPrediction.predicted_final_duration > originalPrediction.predicted_final_duration ? 'red' : 'green' }}>
                ({(simPrediction.predicted_final_duration - originalPrediction.predicted_final_duration).toFixed(1)} wks vs original)
              </span>
            </span>
          </div>
        </div>
      )}
    </SectionCard>
  );
};
