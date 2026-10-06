from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from src.database import get_db, RiskAssessment
from src.schemas import ProjectWeekRequest, RiskResponse, ExplanationResponse
from src.predict import load_models, prepare_prediction_features, predict_cost, predict_duration
from src.run_prediction import get_project_week_data
from src.risk import generate_risk_assessment
from src.api.routes_prediction import get_ml_models

router = APIRouter(tags=["Risk and Explainability"])

@router.post("/risk", response_model=RiskResponse)
def calculate_risk(request: ProjectWeekRequest, db: Session = Depends(get_db)):
    data_dict = get_project_week_data(db, request.project_id, request.week)
    if not data_dict:
        raise HTTPException(status_code=404, detail=f"Week {request.week} was not found for Project {request.project_id}.")
        
    c_model, s_model = get_ml_models()
    X = prepare_prediction_features(data_dict)
    
    predicted_cost, _ = predict_cost(c_model, X)
    predicted_duration, _ = predict_duration(s_model, X)
    
    risk_results = generate_risk_assessment(
        predicted_cost=predicted_cost,
        bac=data_dict['BAC'],
        predicted_duration=predicted_duration,
        planned_duration=data_dict['Planned_Duration']
    )
    
    # Save to database
    try:
        db.query(RiskAssessment).filter_by(project_id=request.project_id, week=request.week).delete()
        risk_record = RiskAssessment(
            project_id=request.project_id,
            week=request.week,
            cost_risk=risk_results['cost_risk'],
            schedule_risk=risk_results['schedule_risk'],
            overall_risk=risk_results['overall_risk'],
            cost_overrun_percentage=risk_results['cost_overrun_percentage'],
            schedule_overrun_percentage=risk_results['schedule_overrun_percentage']
        )
        db.add(risk_record)
        db.commit()
    except Exception:
        db.rollback()
        pass

    return RiskResponse(**risk_results)

@router.post("/explanation", response_model=ExplanationResponse)
def get_explanation(request: ProjectWeekRequest, db: Session = Depends(get_db)):
    data_dict = get_project_week_data(db, request.project_id, request.week)
    if not data_dict:
        raise HTTPException(status_code=404, detail=f"Week {request.week} was not found for Project {request.project_id}.")
        
    c_model, s_model = get_ml_models()
    X = prepare_prediction_features(data_dict)
    
    _, cost_factors = predict_cost(c_model, X)
    _, schedule_factors = predict_duration(s_model, X)
    
    return ExplanationResponse(
        top_cost_factors=cost_factors,
        top_schedule_factors=schedule_factors
    )
