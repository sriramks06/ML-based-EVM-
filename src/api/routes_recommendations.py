from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from src.database import get_db, RiskAssessment
from src.schemas import ProjectWeekRequest, RecommendationResponse
from src.run_prediction import get_project_week_data
from src.recommendations import generate_recommendations, save_recommendations

router = APIRouter(prefix="/recommendations", tags=["Recommendations"])

@router.post("", response_model=RecommendationResponse)
def get_recommendations(request: ProjectWeekRequest, db: Session = Depends(get_db)):
    # 1. Retrieve current project data
    data_dict = get_project_week_data(db, request.project_id, request.week)
    if not data_dict:
        raise HTTPException(status_code=404, detail=f"Week {request.week} was not found for Project {request.project_id}.")
        
    # 2. Obtain existing/current risk assessment
    risk_record = db.query(RiskAssessment).filter_by(project_id=request.project_id, week=request.week).first()
    if not risk_record:
        # If not present in DB, we could generate it on the fly, but the spec says "Obtain existing/current risk assessment".
        # Let's fallback to calculating it if it's not saved yet to make the endpoint robust, or just raise an error.
        # Given this is an API, it's safer to require the risk assessment to be run first, or we can just mock a default dict if missing.
        # But wait, the Phase 8 instructions say "obtain existing/current risk assessment". 
        # I'll query it and convert to dict.
        raise HTTPException(status_code=400, detail="Risk assessment not found. Please run /risk first for this project-week.")
        
    risk_dict = {
        'overall_risk': risk_record.overall_risk
    }
    
    # 3. Run recommendation engine
    recs = generate_recommendations(data_dict, risk_dict)
    
    # Save to PostgreSQL (this handles deduplication internally)
    save_recommendations(db, request.project_id, request.week, recs)
    
    return RecommendationResponse(recommendations=recs)
