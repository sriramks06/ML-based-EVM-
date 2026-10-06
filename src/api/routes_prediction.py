from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import os

from src.database import get_db, Prediction
from src.schemas import ProjectWeekRequest, PredictionResponse, SimulationRequest
from src.predict import load_models, prepare_prediction_features, predict_cost, predict_duration
from src.run_prediction import get_project_week_data

router = APIRouter(prefix="/predict", tags=["Prediction"])

# Lazy load models to avoid crashing on import if models don't exist yet
cost_model, schedule_model = None, None

def get_ml_models():
    global cost_model, schedule_model
    if cost_model is None or schedule_model is None:
        try:
            cost_model, schedule_model = load_models()
        except Exception as e:
            raise HTTPException(status_code=500, detail="Machine learning models failed to load. Ensure Phase 5 is completed.")
    return cost_model, schedule_model

@router.post("", response_model=PredictionResponse)
def predict_project_outcome(request: ProjectWeekRequest, db: Session = Depends(get_db)):
    data_dict = get_project_week_data(db, request.project_id, request.week)
    
    if not data_dict:
        raise HTTPException(status_code=404, detail=f"Week {request.week} was not found for Project {request.project_id}.")
        
    c_model, s_model = get_ml_models()
    
    try:
        X = prepare_prediction_features(data_dict)
        predicted_cost, _ = predict_cost(c_model, X)
        predicted_duration, _ = predict_duration(s_model, X)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Prediction failed due to invalid data schema.")
        
    spi = data_dict['SPI'] if data_dict['SPI'] > 0 else 0.001
    traditional_estimated_duration = data_dict['Planned_Duration'] / spi
    
    # Save to database
    try:
        db.query(Prediction).filter_by(project_id=request.project_id, week=request.week).delete()
        prediction_record = Prediction(
            project_id=request.project_id,
            week=request.week,
            predicted_final_cost=predicted_cost,
            predicted_final_duration=predicted_duration,
            cost_model="API ML Model",
            schedule_model="API ML Model"
        )
        db.add(prediction_record)
        db.commit()
    except Exception as e:
        db.rollback()
        # Non-fatal to API response if saving fails, but good to log in real app
        pass

    return PredictionResponse(
        project_id=request.project_id,
        week=request.week,
        BAC=data_dict['BAC'],
        planned_duration=data_dict['Planned_Duration'],
        predicted_final_cost=predicted_cost,
        predicted_final_duration=predicted_duration,
        traditional_eac=data_dict['EAC'],
        traditional_estimated_duration=traditional_estimated_duration
    )

@router.post("/simulate", response_model=PredictionResponse)
def simulate_project_outcome(request: SimulationRequest, db: Session = Depends(get_db)):
    from src.schemas import SimulationRequest
    data_dict = get_project_week_data(db, request.project_id, request.week)
    
    if not data_dict:
        raise HTTPException(status_code=404, detail=f"Week {request.week} was not found for Project {request.project_id}.")
        
    # Apply overrides
    for k, v in request.overrides.items():
        if k in data_dict:
            data_dict[k] = v
            
    c_model, s_model = get_ml_models()
    
    try:
        X = prepare_prediction_features(data_dict)
        predicted_cost, _ = predict_cost(c_model, X)
        predicted_duration, _ = predict_duration(s_model, X)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Simulation failed due to invalid data schema.")
        
    spi = data_dict['SPI'] if data_dict['SPI'] > 0 else 0.001
    traditional_estimated_duration = data_dict['Planned_Duration'] / spi

    return PredictionResponse(
        project_id=request.project_id,
        week=request.week,
        BAC=data_dict['BAC'],
        planned_duration=data_dict['Planned_Duration'],
        predicted_final_cost=predicted_cost,
        predicted_final_duration=predicted_duration,
        traditional_eac=data_dict['EAC'],
        traditional_estimated_duration=traditional_estimated_duration
    )
