import sys
import os
import pandas as pd
from sqlalchemy.exc import IntegrityError

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.database import SessionLocal, Project, ProjectWeeklyData

def load_data(filepath='data/processed/evm_dataset.csv'):
    print(f"Loading data from {filepath}...")
    df = pd.read_csv(filepath)
    
    # Simple data integrity checks before insertion
    invalid_rows = []
    
    # Validate non-negative cost and schedule values
    negative_mask = (df['PV'] < 0) | (df['EV'] < 0) | (df['AC'] < 0) | (df['Final_Cost'] < 0)
    if negative_mask.any():
        print(f"Warning: Found {negative_mask.sum()} rows with negative values.")
        invalid_rows.extend(df[negative_mask].index.tolist())
        
    # Check consistency of Final_Cost and Final_Duration
    project_groups = df.groupby('Project_ID')
    for pid, group in project_groups:
        if group['Final_Cost'].nunique() > 1:
            print(f"Error: Project {pid} has inconsistent Final_Cost.")
            invalid_rows.extend(group.index.tolist())
        if group['Final_Duration'].nunique() > 1:
            print(f"Error: Project {pid} has inconsistent Final_Duration.")
            invalid_rows.extend(group.index.tolist())
            
    invalid_rows = set(invalid_rows)
    if invalid_rows:
        print(f"Skipping {len(invalid_rows)} invalid rows.")
        df = df.drop(index=list(invalid_rows))
        
    session = SessionLocal()
    
    projects_inserted = 0
    weekly_inserted = 0
    skipped_records = 0
    
    try:
        # Load unique projects
        projects_df = df.groupby('Project_ID').first().reset_index()
        for _, row in projects_df.iterrows():
            # Check if project exists
            existing_project = session.query(Project).filter(Project.project_id == row['Project_ID']).first()
            if not existing_project:
                # Add default name if not present
                project_name = f"Project {int(row['Project_ID'])}"
                risk_profile = row['Risk_Profile'] if 'Risk_Profile' in row else "Unknown"
                
                project = Project(
                    project_id=int(row['Project_ID']),
                    project_name=project_name,
                    BAC=float(row['BAC']),
                    planned_duration=int(row['Planned_Duration']),
                    risk_profile=risk_profile
                )
                session.add(project)
                projects_inserted += 1
                
        session.commit()
        
        # Load weekly data
        for _, row in df.iterrows():
            weekly_record = ProjectWeeklyData(
                project_id=int(row['Project_ID']),
                week=int(row['Week']),
                PV=float(row['PV']),
                EV=float(row['EV']),
                AC=float(row['AC']),
                CPI=float(row['CPI']),
                SPI=float(row['SPI']),
                EAC=float(row['EAC']),
                Requirement_Volatility=float(row['Requirement_Volatility']),
                Change_Requests=int(row['Change_Requests']),
                Scope_Change_Percentage=float(row['Scope_Change_Percentage']),
                Task_Completion_Rate=float(row['Task_Completion_Rate']),
                Resource_Utilization=float(row['Resource_Utilization']),
                Team_Experience=float(row['Team_Experience']),
                Task_Complexity=float(row['Task_Complexity']),
                Defect_Rate=float(row['Defect_Rate']),
                Rework_Rate=float(row['Rework_Rate']),
                Dependency_Delays=int(row['Dependency_Delays']),
                Delay_Severity=float(row['Delay_Severity']),
                Project_Completion_Percentage=float(row['Project_Completion_Percentage']),
                Final_Cost=float(row['Final_Cost']),
                Final_Duration=int(row['Final_Duration'])
            )
            session.add(weekly_record)
            
            try:
                session.commit()
                weekly_inserted += 1
            except IntegrityError:
                session.rollback()
                skipped_records += 1
                
    except Exception as e:
        print(f"An error occurred: {e}")
        session.rollback()
    finally:
        session.close()
        
    print("\n--- Data Import Report ---")
    print(f"Projects inserted: {projects_inserted}")
    print(f"Weekly records inserted: {weekly_inserted}")
    print(f"Records skipped (duplicates/errors): {skipped_records}")
    print(f"Validation failures dropped: {len(invalid_rows)}")

if __name__ == "__main__":
    load_data()
