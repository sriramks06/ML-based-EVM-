import sys
import os
import json
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '.')))

from src.main import app
from src.database import SessionLocal, RiskAssessment

client = TestClient(app)

def verify_real_data():
    session = SessionLocal()
    
    # Find one of each risk type from the DB
    low_risk = session.query(RiskAssessment).filter_by(overall_risk='LOW').first()
    med_risk = session.query(RiskAssessment).filter_by(overall_risk='MEDIUM').first()
    high_risk = session.query(RiskAssessment).filter_by(overall_risk='HIGH').first()
    
    cases = []
    if low_risk: cases.append((low_risk.project_id, low_risk.week, 'LOW'))
    if med_risk: cases.append((med_risk.project_id, med_risk.week, 'MEDIUM'))
    if high_risk: cases.append((high_risk.project_id, high_risk.week, 'HIGH'))
    
    for pid, week, expected_risk in cases:
        print("=" * 60)
        print(f"Testing /analyze for Project {pid} Week {week} (Expected Risk: {expected_risk})")
        
        response = client.post("/analyze", json={"project_id": pid, "week": week})
        if response.status_code != 200:
            print(f"Failed! {response.status_code}: {response.text}")
            continue
            
        data = response.json()
        print(f"Risk Output: {data['risk']['overall_risk']}")
        print(f"Cost Predicted: ${data['prediction']['predicted_final_cost']:,.2f}")
        print(f"Duration Predicted: {data['prediction']['predicted_final_duration']:.2f} weeks")
        print(f"Recommendations count: {len(data['recommendations'])}")
        print("=" * 60 + "\n")
        
    session.close()

if __name__ == "__main__":
    verify_real_data()
