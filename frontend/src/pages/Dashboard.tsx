import React, { useState, useEffect } from 'react';
import { fetchProjects, fetchProjectWeeks, analyzeProject } from '../services/api';
import type { Project, ProjectWeek, AnalysisResponse } from '../types';
import { MetricCard } from '../components/MetricCard';
import { SectionCard } from '../components/SectionCard';
import { RiskBadge } from '../components/RiskBadge';
import { TrendCharts } from '../components/TrendCharts';
import { ForecastComparison } from '../components/ForecastComparison';
import { ExplainabilityPanel } from '../components/ExplainabilityPanel';
import { RecommendationsPanel } from '../components/RecommendationsPanel';
import { SimulatorPanel } from '../components/SimulatorPanel';
import { RISK_COLORS, formatCurrency, formatPct, cpiLabel, spiLabel } from '../utils/helpers';

type Status = 'idle' | 'loading-weeks' | 'loading-analysis' | 'ready' | 'error';

const Dashboard: React.FC = () => {
  const [projects, setProjects] = useState<Project[]>([]);
  const [weeks, setWeeks] = useState<ProjectWeek[]>([]);
  const [selectedProject, setSelectedProject] = useState<number | ''>('');
  const [selectedWeek, setSelectedWeek] = useState<number | ''>('');
  const [analysis, setAnalysis] = useState<AnalysisResponse | null>(null);
  const [status, setStatus] = useState<Status>('idle');
  const [error, setError] = useState<string>('');

  // Load project list on mount
  useEffect(() => {
    fetchProjects()
      .then(setProjects)
      .catch(() => setError('Unable to load projects. Is the FastAPI backend running?'));
  }, []);

  // When project changes, load its weeks
  useEffect(() => {
    if (selectedProject === '') return;
    setSelectedWeek('');
    setAnalysis(null);
    setStatus('loading-weeks');
    fetchProjectWeeks(Number(selectedProject))
      .then(data => { setWeeks(data); setStatus('idle'); })
      .catch(() => { setError('Failed to load weeks.'); setStatus('error'); });
  }, [selectedProject]);

  const handleAnalyze = async () => {
    if (selectedProject === '' || selectedWeek === '') return;
    setStatus('loading-analysis');
    setError('');
    try {
      const result = await analyzeProject(Number(selectedProject), Number(selectedWeek));
      setAnalysis(result);
      setStatus('ready');
    } catch {
      setError('Unable to retrieve project analysis. Please check the backend.');
      setStatus('error');
    }
  };

  const riskColor = analysis ? RISK_COLORS[analysis.risk.overall_risk] : null;

  return (
    <div className="dashboard">
      {/* ── HEADER ── */}
      <header className="dash-header">
        <div className="header-brand">
          <div className="header-logo">EVM</div>
          <div>
            <h1 className="header-title">ML-Enhanced EVM</h1>
            <p className="header-sub">Predictive Project Risk Management</p>
          </div>
        </div>
        <div className="header-controls">
          <select
            className="select-control"
            value={selectedProject}
            onChange={e => setSelectedProject(e.target.value === '' ? '' : Number(e.target.value))}
          >
            <option value="">Select Project…</option>
            {projects.map(p => (
              <option key={p.project_id} value={p.project_id}>{p.project_name}</option>
            ))}
          </select>

          <select
            className="select-control"
            value={selectedWeek}
            onChange={e => setSelectedWeek(e.target.value === '' ? '' : Number(e.target.value))}
            disabled={weeks.length === 0}
          >
            <option value="">Select Week…</option>
            {weeks.map(w => <option key={w.week} value={w.week}>Week {w.week}</option>)}
          </select>

          <button
            className="btn-analyze"
            onClick={handleAnalyze}
            disabled={selectedProject === '' || selectedWeek === '' || status === 'loading-analysis'}
          >
            {status === 'loading-analysis' ? '⟳ Analyzing…' : '▶ Analyze'}
          </button>
          {analysis && (
            <button
              className="btn-analyze"
              style={{ background: '#475569' }}
              onClick={() => {
                const csv = `Project,${analysis.project.project_name}\nWeek,${analysis.prediction.week}\nEVM EAC,${analysis.prediction.traditional_eac}\nML Forecast,${analysis.prediction.predicted_final_cost}\nRisk,${analysis.risk.overall_risk}`;
                const blob = new Blob([csv], { type: 'text/csv' });
                const url = URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = `forecast_export_${analysis.project.project_id}_wk${analysis.prediction.week}.csv`;
                a.click();
              }}
            >
              📥 Export CSV
            </button>
          )}
        </div>
      </header>

      <main className="dash-main">
        {/* ── STATES ── */}
        {status === 'idle' && !analysis && (
          <div className="state-center">
            <div className="state-icon">📋</div>
            <h2>Select a project and week to begin analysis.</h2>
            <p>The ML forecast engine will predict final cost, duration, risk, and corrective actions.</p>
          </div>
        )}

        {status === 'loading-analysis' && (
          <div className="state-center">
            <div className="spinner" />
            <h2>Running project analysis…</h2>
            <p>Fetching EVM metrics, ML predictions, risk assessment, and recommendations.</p>
          </div>
        )}

        {status === 'error' && (
          <div className="state-center error">
            <div className="state-icon">⚠️</div>
            <h2>Analysis Failed</h2>
            <p>{error}</p>
          </div>
        )}

        {/* ── ANALYSIS RESULTS ── */}
        {status === 'ready' && analysis && (() => {
          const { project, prediction, risk, explanation, recommendations } = analysis;
          const week = weeks.find(w => w.week === prediction.week);

          return (
            <>
              {/* ── EXECUTIVE SUMMARY STRIP ── */}
              <div className="summary-strip">
                <MetricCard
                  label="CPI"
                  value={week?.CPI.toFixed(3) ?? '—'}
                  sub={cpiLabel(week?.CPI ?? 1)}
                  subColor={week && week.CPI >= 1 ? 'var(--risk-low-text)' : 'var(--risk-high-text)'}
                  accent={week && week.CPI >= 1 ? '#10b981' : '#f43f5e'}
                />
                <MetricCard
                  label="SPI"
                  value={week?.SPI.toFixed(3) ?? '—'}
                  sub={spiLabel(week?.SPI ?? 1)}
                  subColor={week && week.SPI >= 1 ? 'var(--risk-low-text)' : 'var(--risk-high-text)'}
                  accent={week && week.SPI >= 1 ? '#10b981' : '#f43f5e'}
                />
                <MetricCard
                  label="EVM EAC"
                  value={formatCurrency(prediction.traditional_eac)}
                  sub={`BAC: ${formatCurrency(prediction.BAC)}`}
                  accent="#6366f1"
                />
                <MetricCard
                  label="ML Final Cost"
                  value={formatCurrency(prediction.predicted_final_cost)}
                  sub={formatPct(risk.cost_overrun_percentage) + ' overrun'}
                  subColor={risk.cost_overrun_percentage > 0 ? 'var(--risk-high-text)' : 'var(--risk-low-text)'}
                  accent="#f43f5e"
                />
                <MetricCard
                  label="ML Duration"
                  value={`${prediction.predicted_final_duration.toFixed(1)} wks`}
                  sub={formatPct(risk.schedule_overrun_percentage) + ' vs plan'}
                  subColor={risk.schedule_overrun_percentage > 0 ? 'var(--risk-high-text)' : 'var(--risk-low-text)'}
                  accent="#f59e0b"
                />
                {/* Overall Risk – big card */}
                <div
                  className="metric-card risk-summary-card"
                  style={{ borderTop: `3px solid ${riskColor!.border}`, background: riskColor!.bg }}
                >
                  <div className="metric-label">Overall Risk</div>
                  <div className="risk-big-badge">
                    <RiskBadge level={risk.overall_risk} size="lg" />
                  </div>
                  <div className="risk-sub-row">
                    <span>Cost <RiskBadge level={risk.cost_risk} size="sm" /></span>
                    <span>Schedule <RiskBadge level={risk.schedule_risk} size="sm" /></span>
                  </div>
                </div>
              </div>

              {/* ── ALERTS ── */}
              {analysis.alerts && analysis.alerts.length > 0 && (
                <div className="alerts-strip" style={{ padding: '1rem', background: '#fee2e2', borderLeft: '4px solid #ef4444', borderRadius: '4px', marginBottom: '1rem' }}>
                  <h4 style={{ margin: '0 0 0.5rem 0', color: '#b91c1c' }}>System Alerts</h4>
                  <ul style={{ margin: 0, paddingLeft: '1.5rem', color: '#991b1b' }}>
                    {analysis.alerts.map((alert, i) => <li key={i}>{alert}</li>)}
                  </ul>
                </div>
              )}

              {/* ── PROJECT INFO BAR ── */}
              <div className="info-bar">
                <span><strong>Project:</strong> {project.project_name}</span>
                <span><strong>Week:</strong> {prediction.week}</span>
                <span><strong>BAC:</strong> {formatCurrency(project.BAC)}</span>
                <span><strong>Planned Duration:</strong> {project.planned_duration} weeks</span>
                {project.risk_profile && <span><strong>Risk Profile:</strong> {project.risk_profile}</span>}
              </div>

              {/* ── MAIN GRID ── */}
              <div className="main-grid">
                {/* EVM Performance */}
                <SectionCard title="EVM Performance" icon="📐">
                  <table className="evm-table">
                    <tbody>
                      {week && [
                        ['Planned Value (PV)', formatCurrency(week.PV), ''],
                        ['Earned Value (EV)', formatCurrency(week.EV), ''],
                        ['Actual Cost (AC)', formatCurrency(week.AC), ''],
                        ['CPI', week.CPI.toFixed(4), cpiLabel(week.CPI)],
                        ['SPI', week.SPI.toFixed(4), spiLabel(week.SPI)],
                        ['TCPI', week.TCPI !== Infinity ? week.TCPI.toFixed(4) : '—', 'To-Complete Perf. Index'],
                        ['EAC (EVM)', formatCurrency(week.EAC), ''],
                        ['EAC (ML Forecast)', formatCurrency(prediction.predicted_final_cost), ''],
                      ].map(([label, val, hint]) => (
                        <tr key={label}>
                          <td className="evm-label">{label}</td>
                          <td className="evm-val">{val}</td>
                          {hint && <td className="evm-hint">{hint}</td>}
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </SectionCard>

                {/* Forecast Comparison */}
                <ForecastComparison prediction={prediction} />
              </div>

              {/* ── TREND CHARTS ── */}
              <div className="chart-grid">
                <TrendCharts weeks={weeks} />
              </div>

              {/* ── BOTTOM GRID ── */}
              <div className="main-grid">
                <ExplainabilityPanel explanation={explanation} />
                <RecommendationsPanel recommendations={recommendations} />
              </div>

              {/* ── SIMULATOR ── */}
              <div style={{ marginTop: '2rem' }}>
                <SimulatorPanel projectId={project.project_id} week={prediction.week} originalPrediction={prediction} />
              </div>
            </>
          );
        })()}
      </main>

      <footer className="dash-footer">
        ML-Enhanced EVM · Academic Project · FastAPI + React · Data sourced from backend models
      </footer>
    </div>
  );
};

export default Dashboard;
