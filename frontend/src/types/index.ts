// ─── Projects ──────────────────────────────────────────────────
export interface Project {
  project_id: number;
  project_name: string;
  BAC: number;
  planned_duration: number;
  risk_profile: string | null;
}

export interface ProjectWeek {
  week: number;
  PV: number;
  EV: number;
  AC: number;
  CPI: number;
  SPI: number;
  EAC: number;
  TCPI: number;
}

// ─── Prediction ─────────────────────────────────────────────────
export interface PredictionResponse {
  project_id: number;
  week: number;
  BAC: number;
  planned_duration: number;
  predicted_final_cost: number;
  predicted_final_duration: number;
  traditional_eac: number;
  traditional_estimated_duration: number;
}

// ─── Risk ────────────────────────────────────────────────────────
export type RiskLevel = 'LOW' | 'MEDIUM' | 'HIGH';

export interface RiskResponse {
  cost_overrun_percentage: number;
  schedule_overrun_percentage: number;
  cost_risk: RiskLevel;
  schedule_risk: RiskLevel;
  overall_risk: RiskLevel;
}

// ─── Explainability ─────────────────────────────────────────────
export interface ExplanationFactor {
  feature: string;
  importance: number;
  rank: number;
}

export interface ExplanationResponse {
  top_cost_factors: ExplanationFactor[];
  top_schedule_factors: ExplanationFactor[];
}

// ─── Recommendations ────────────────────────────────────────────
export interface Recommendation {
  risk_factor: string;
  explanation: string;
  priority: RiskLevel;
  recommendation: string;
  threshold: number;
  triggered_value: number;
}

// ─── Full Analysis ───────────────────────────────────────────────
export interface AnalysisResponse {
  project: Project;
  prediction: PredictionResponse;
  risk: RiskResponse;
  explanation: ExplanationResponse;
  recommendations: Recommendation[];
  alerts: string[];
}
