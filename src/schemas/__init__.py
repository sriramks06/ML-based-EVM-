from pydantic import BaseModel, ConfigDict
from typing import Optional, List, Dict, Any

# ========================
# EVM Schemas
# ========================
class EVMRequest(BaseModel):
    BAC: float
    PV: float
    EV: float
    AC: float

class EVMResponse(BaseModel):
    PV: float
    EV: float
    AC: float
    CPI: float
    SPI: float
    EAC: float
    TCPI: float
    cpi_interpretation: str
    spi_interpretation: str

# ========================
# Database Model Schemas
# ========================
class ProjectResponse(BaseModel):
    project_id: int
    project_name: str
    BAC: float
    planned_duration: int
    risk_profile: Optional[str] = None
    
    model_config = ConfigDict(from_attributes=True)

class ProjectWeekResponse(BaseModel):
    week: int
    PV: float
    EV: float
    AC: float
    CPI: float
    SPI: float
    EAC: float
    TCPI: float
    
    model_config = ConfigDict(from_attributes=True)

class ProjectWeekRequest(BaseModel):
    project_id: int
    week: int

class SimulationRequest(BaseModel):
    project_id: int
    week: int
    overrides: Dict[str, float]

# ========================
# ML & Risk Schemas
# ========================
class PredictionResponse(BaseModel):
    project_id: int
    week: int
    BAC: float
    planned_duration: int
    predicted_final_cost: float
    predicted_final_duration: float
    traditional_eac: float
    traditional_estimated_duration: float

class RiskResponse(BaseModel):
    cost_overrun_percentage: float
    schedule_overrun_percentage: float
    cost_risk: str
    schedule_risk: str
    overall_risk: str

class ExplanationFactor(BaseModel):
    feature: str
    importance: float
    rank: int

class ExplanationResponse(BaseModel):
    top_cost_factors: List[ExplanationFactor]
    top_schedule_factors: List[ExplanationFactor]

class RecommendationItem(BaseModel):
    risk_factor: str
    explanation: str
    priority: str
    recommendation: str
    threshold: float
    triggered_value: float

class RecommendationResponse(BaseModel):
    recommendations: List[RecommendationItem]

# ========================
# Analyze Endpoint Schema
# ========================
class AnalyzeResponse(BaseModel):
    project: ProjectResponse
    prediction: PredictionResponse
    risk: RiskResponse
    explanation: ExplanationResponse
    recommendations: List[RecommendationItem]
    alerts: List[str]
