from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from src.database import get_db
from src.schemas import ProjectWeekRequest, AnalyzeResponse, ProjectResponse
from src.api.routes_prediction import predict_project_outcome
from src.api.routes_risk import calculate_risk, get_explanation
from src.api.routes_recommendations import get_recommendations

router = APIRouter(prefix="/analyze", tags=["Orchestration"])

@router.post("", response_model=AnalyzeResponse)
def analyze_project(request: ProjectWeekRequest, db: Session = Depends(get_db)):
    """Orchestrates the complete workflow: EVM -> ML -> Risk -> Explainability -> Recommendations."""
    
    # 1. Fetch Project Info
    from src.database import Project
    project = db.query(Project).filter(Project.project_id == request.project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail=f"Project {request.project_id} was not found.")
        
    project_resp = ProjectResponse.model_validate(project)
    
    # 2. Prediction (also saves to DB)
    try:
        prediction_resp = predict_project_outcome(request, db)
    except HTTPException as e:
        raise e
        
    # 3. Risk (also saves to DB)
    risk_resp = calculate_risk(request, db)
    
    # 4. Explainability
    explanation_resp = get_explanation(request, db)
    
    # 5. Recommendations (also saves to DB)
    recs_resp = get_recommendations(request, db)
    
    # 6. Automated Alerts Logic
    alerts = []
    # If ML prediction diverges by more than 10% from traditional EAC
    if prediction_resp.traditional_eac > 0:
        divergence = abs(prediction_resp.predicted_final_cost - prediction_resp.traditional_eac) / prediction_resp.traditional_eac
        if divergence > 0.10:
            alerts.append(f"⚠️ Forecast Divergence Alert: ML model predicts a final cost {(divergence*100):.1f}% different than traditional EVM EAC. Investigate hidden risks.")
            
    if risk_resp.overall_risk == 'HIGH':
        alerts.append("🚨 High Risk Alert: Immediate corrective action is required.")
    
    return AnalyzeResponse(
        project=project_resp,
        prediction=prediction_resp,
        risk=risk_resp,
        explanation=explanation_resp,
        recommendations=recs_resp.recommendations,
        alerts=alerts
    )
