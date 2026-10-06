import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.database import SessionLocal, ProjectWeeklyData, RiskAssessment, Prediction, Recommendation
from src.recommendations import generate_recommendations, save_recommendations
from src.run_prediction import process_and_save_prediction
from src.predict import load_models

def get_risk_assessment_for_project(session, project_id, week):
    """Fetches the pre-calculated risk assessment from the database."""
    risk_record = session.query(RiskAssessment).filter_by(project_id=project_id, week=week).first()
    if not risk_record:
        return None
        
    return {
        'cost_overrun_percentage': risk_record.cost_overrun_percentage,
        'schedule_overrun_percentage': risk_record.schedule_overrun_percentage,
        'cost_risk': risk_record.cost_risk,
        'schedule_risk': risk_record.schedule_risk,
        'overall_risk': risk_record.overall_risk
    }

def get_project_data(session, project_id, week):
    """Fetches project condition metrics from the database."""
    pw_record = session.query(ProjectWeeklyData).filter_by(project_id=project_id, week=week).first()
    if not pw_record:
        return None
    
    return {c.name: getattr(pw_record, c.name) for c in pw_record.__table__.columns}

def print_recommendations(project_id, week, overall_risk, recommendations):
    print("=" * 60)
    print(f"Project: {project_id}")
    print(f"Week: {week}\n")
    print(f"Overall Risk: {overall_risk}\n")
    
    if not recommendations:
        print("Recommendations: None (Project is healthy)")
    else:
        print("Recommendations:\n")
        for rec in recommendations:
            print(f"[{rec['priority']}]")
            print(rec['explanation'])
            print(f"-> {rec['recommendation']}\n")
    print("=" * 60)

def run_demo():
    session = SessionLocal()
    
    cost_model, schedule_model = load_models()
    
    # We will pick 3 projects. 
    # Based on phase 6 and synthetic data structure:
    # Let's use Project 1 (High Risk at Week 10), Project 2 (Stable), Project 50 (Med/High Risk)
    
    # Let's dynamically find examples in the DB to guarantee they exist and match profiles
    
    # Find a LOW risk project (usually stable projects like 2, 3, 4 late in the schedule)
    low_risk = session.query(RiskAssessment).filter_by(overall_risk='LOW').first()
    # Find a MEDIUM risk project
    med_risk = session.query(RiskAssessment).filter_by(overall_risk='MEDIUM').first()
    # Find a HIGH risk project
    high_risk = session.query(RiskAssessment).filter_by(overall_risk='HIGH').first()
    
    demo_cases = []
    
    # Fallback IDs just in case
    cases = [(1, 10), (2, 5), (50, 15)]
    
    if low_risk: cases[0] = (low_risk.project_id, low_risk.week)
    if med_risk: cases[1] = (med_risk.project_id, med_risk.week)
    if high_risk: cases[2] = (high_risk.project_id, high_risk.week)
    
    for pid, week in cases:
        # Guarantee prediction and risk data exists first
        process_and_save_prediction(session, pid, week, cost_model, schedule_model)
        
        # Load Risk and Data
        risk = get_risk_assessment_for_project(session, pid, week)
        data = get_project_data(session, pid, week)
        
        if not risk or not data:
            print(f"Failed to load data for Project {pid} Week {week}")
            continue
            
        # Generate Recommendations
        recs = generate_recommendations(data, risk)
        
        # Save to PostgreSQL
        saved = save_recommendations(session, pid, week, recs)
        
        # Display Output
        print_recommendations(pid, week, risk['overall_risk'], recs)
        
        if saved:
            print(f"[SUCCESS] Saved {len(recs)} recommendations to database.\n")
            
    session.close()

if __name__ == "__main__":
    run_demo()
