import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.database import SessionLocal, ProjectWeeklyData, Project, Prediction, RiskAssessment
from src.predict import load_models, prepare_prediction_features, predict_cost, predict_duration, format_explanation
from src.risk import generate_risk_assessment

def get_project_week_data(session, project_id, week):
    """Fetches a specific project-week observation and formats it as a dict for prediction."""
    result = session.query(
        ProjectWeeklyData, Project.BAC, Project.planned_duration.label('Planned_Duration')
    ).join(Project, ProjectWeeklyData.project_id == Project.project_id) \
     .filter(ProjectWeeklyData.project_id == project_id, ProjectWeeklyData.week == week) \
     .first()
     
    if not result:
        return None
        
    pw_data, bac, planned_duration = result
    
    # Convert SQLAlchemy model to dict and add the joined baseline values
    data_dict = {c.name: getattr(pw_data, c.name) for c in pw_data.__table__.columns}
    data_dict['BAC'] = bac
    data_dict['Planned_Duration'] = planned_duration
    
    return data_dict

def process_and_save_prediction(session, project_id, week, cost_model, schedule_model):
    """End-to-end prediction, risk analysis, and DB save for a project-week."""
    data_dict = get_project_week_data(session, project_id, week)
    if not data_dict:
        print(f"Error: No data found for Project {project_id} Week {week}")
        return False
        
    # Predict
    X = prepare_prediction_features(data_dict)
    
    predicted_cost, cost_factors = predict_cost(cost_model, X)
    predicted_duration, schedule_factors = predict_duration(schedule_model, X)
    
    # Calculate Risk
    risk_results = generate_risk_assessment(
        predicted_cost=predicted_cost,
        bac=data_dict['BAC'],
        predicted_duration=predicted_duration,
        planned_duration=data_dict['Planned_Duration']
    )
    
    # Explainability Interpretation
    cost_explanation = format_explanation(cost_factors, "cost")
    schedule_explanation = format_explanation(schedule_factors, "schedule")
    
    # Traditional EVM calculation for printing/comparison
    spi = data_dict['SPI'] if data_dict['SPI'] > 0 else 0.001
    traditional_estimated_duration = data_dict['Planned_Duration'] / spi
    
    # Print the End-to-End Demo Output
    print("=" * 60)
    print(f"PROJECT: {project_id} | WEEK: {week}")
    print("=" * 60)
    print(f"BAC: ${data_dict['BAC']:,.2f}")
    print(f"Planned Duration: {data_dict['Planned_Duration']} weeks")
    print("\n--- TRADITIONAL EVM ---")
    print(f"CPI: {data_dict['CPI']:.4f}")
    print(f"SPI: {data_dict['SPI']:.4f}")
    print(f"EAC (Cost): ${data_dict['EAC']:,.2f}")
    print(f"Estimated Duration (EVM): {traditional_estimated_duration:.2f} weeks")
    
    print("\n--- ML FORECAST ---")
    print(f"Predicted Final Cost: ${predicted_cost:,.2f}")
    print(f"Predicted Final Duration: {predicted_duration:.2f} weeks")
    
    print("\n--- RISK ASSESSMENT ---")
    print(f"Cost Overrun %: {risk_results['cost_overrun_percentage']:.2f}%")
    print(f"Schedule Overrun %: {risk_results['schedule_overrun_percentage']:.2f}%")
    print(f"Cost Risk: {risk_results['cost_risk']}")
    print(f"Schedule Risk: {risk_results['schedule_risk']}")
    print(f"Overall Risk: {risk_results['overall_risk']}")
    
    print("\n--- EXPLAINABILITY ---")
    print(f"Cost Interpretation: {cost_explanation}")
    print(f"Schedule Interpretation: {schedule_explanation}")
    
    print("Top 3 Cost Factors:")
    for f in cost_factors[:3]:
        print(f"  {f['rank']}. {f['feature']} (Importance: {f['importance']:.1f}%)")
        
    print("Top 3 Schedule Factors:")
    for f in schedule_factors[:3]:
        print(f"  {f['rank']}. {f['feature']} (Importance: {f['importance']:.1f}%)")
    
    # Save to PostgreSQL
    try:
        # Check if exists and delete to avoid duplicate key issues in demo
        session.query(Prediction).filter_by(project_id=project_id, week=week).delete()
        session.query(RiskAssessment).filter_by(project_id=project_id, week=week).delete()
        
        prediction_record = Prediction(
            project_id=project_id,
            week=week,
            predicted_final_cost=predicted_cost,
            predicted_final_duration=predicted_duration,
            cost_model="Linear Regression (from joblib)",
            schedule_model="Gradient Boosting (from joblib)"
        )
        
        risk_record = RiskAssessment(
            project_id=project_id,
            week=week,
            cost_risk=risk_results['cost_risk'],
            schedule_risk=risk_results['schedule_risk'],
            overall_risk=risk_results['overall_risk'],
            cost_overrun_percentage=risk_results['cost_overrun_percentage'],
            schedule_overrun_percentage=risk_results['schedule_overrun_percentage']
        )
        
        session.add(prediction_record)
        session.add(risk_record)
        session.commit()
        print("\n[SUCCESS] Saved prediction and risk results to database.")
    except Exception as e:
        session.rollback()
        print(f"\n[ERROR] Failed to save to database: {e}")
        
    print("=" * 60 + "\n")
    return True

def run_demo():
    print("Loading ML models...")
    cost_model, schedule_model = load_models()
    
    session = SessionLocal()
    
    # Select 3 diverse projects (e.g., from early, mid, late weeks, or different risk profiles)
    # Just grabbing 3 known combinations that should exist in the loaded DB.
    # Projects 1 (Stable), Project 10 (Cost-Risk), Project 50 (Schedule-Risk) - estimating these exist based on generator.
    demo_cases = [
        (1, 10),   # Project 1, Week 10
        (10, 21),  # Project 10, Week 21 (from our methodology check)
        (50, 15)   # Project 50, Week 15
    ]
    
    for pid, week in demo_cases:
        process_and_save_prediction(session, pid, week, cost_model, schedule_model)
        
    session.close()

if __name__ == "__main__":
    run_demo()
