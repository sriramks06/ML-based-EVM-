import os
import pandas as pd
import numpy as np
import joblib
from sklearn.model_selection import GroupShuffleSplit
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from src.database import SessionLocal, ProjectWeeklyData, Project

# Approved features from Phase 3, plus BAC and Planned_Duration which are known baselines
FEATURES = [
    'BAC', 'Planned_Duration', # Baseline context (Justification: provides required scale for absolute predictions)
    'PV', 'EV', 'AC', 'CPI', 'SPI', 'EAC',
    'Requirement_Volatility', 'Change_Requests', 'Scope_Change_Percentage',
    'Task_Completion_Rate', 'Resource_Utilization', 'Team_Experience',
    'Task_Complexity', 'Defect_Rate', 'Rework_Rate', 'Dependency_Delays',
    'Delay_Severity', 'Project_Completion_Percentage'
]

def load_training_data():
    """Loads project-week data from the PostgreSQL/SQLite database."""
    session = SessionLocal()
    try:
        # Querying the weekly data and joining with the Project table to get BAC and Planned_Duration
        query = session.query(
            ProjectWeeklyData.project_id,
            ProjectWeeklyData.week,
            Project.BAC,
            Project.planned_duration.label('Planned_Duration'),
            ProjectWeeklyData.PV,
            ProjectWeeklyData.EV,
            ProjectWeeklyData.AC,
            ProjectWeeklyData.CPI,
            ProjectWeeklyData.SPI,
            ProjectWeeklyData.EAC,
            ProjectWeeklyData.Requirement_Volatility,
            ProjectWeeklyData.Change_Requests,
            ProjectWeeklyData.Scope_Change_Percentage,
            ProjectWeeklyData.Task_Completion_Rate,
            ProjectWeeklyData.Resource_Utilization,
            ProjectWeeklyData.Team_Experience,
            ProjectWeeklyData.Task_Complexity,
            ProjectWeeklyData.Defect_Rate,
            ProjectWeeklyData.Rework_Rate,
            ProjectWeeklyData.Dependency_Delays,
            ProjectWeeklyData.Delay_Severity,
            ProjectWeeklyData.Project_Completion_Percentage,
            ProjectWeeklyData.Final_Cost,
            ProjectWeeklyData.Final_Duration
        ).join(Project, ProjectWeeklyData.project_id == Project.project_id)
        
        df = pd.read_sql(query.statement, session.bind)
        return df
    finally:
        session.close()

def split_projects(df, test_size=0.2, random_state=42):
    """Splits data such that entire projects are kept together (no data leakage)."""
    gss = GroupShuffleSplit(n_splits=1, test_size=test_size, random_state=random_state)
    train_idx, test_idx = next(gss.split(df, groups=df['project_id']))
    
    train_df = df.iloc[train_idx].copy()
    test_df = df.iloc[test_idx].copy()
    
    return train_df, test_df

def prepare_features(df):
    """Extracts X and y, ensuring no leakage features are present in X."""
    X = df[FEATURES].copy()
    
    # Fill any remaining NaNs or Infinities just in case
    X.replace([np.inf, -np.inf], np.nan, inplace=True)
    X = X.fillna(0)
    
    y_cost = df['Final_Cost']
    y_schedule = df['Final_Duration']
    
    return X, y_cost, y_schedule

def build_model_pipelines():
    """Creates a dictionary of initialized models wrapped in pipelines."""
    pipelines = {
        'Linear Regression': Pipeline([
            ('scaler', StandardScaler()),
            ('regressor', LinearRegression())
        ]),
        'Random Forest': Pipeline([
            ('scaler', StandardScaler()),
            ('regressor', RandomForestRegressor(n_estimators=100, random_state=42))
        ]),
        'Gradient Boosting': Pipeline([
            ('scaler', StandardScaler()),
            ('regressor', GradientBoostingRegressor(n_estimators=100, random_state=42))
        ])
    }
    return pipelines

def train_cost_models(X_train, y_train):
    """Trains all candidate models for cost prediction."""
    models = build_model_pipelines()
    for name, pipeline in models.items():
        pipeline.fit(X_train, y_train)
    return models

def train_schedule_models(X_train, y_train):
    """Trains all candidate models for schedule prediction."""
    models = build_model_pipelines()
    for name, pipeline in models.items():
        pipeline.fit(X_train, y_train)
    return models

def evaluate_models(models, X_test, y_test, target_name=""):
    """Calculates evaluation metrics and returns a summary dataframe."""
    results = []
    for name, pipeline in models.items():
        predictions = pipeline.predict(X_test)
        mae = mean_absolute_error(y_test, predictions)
        rmse = np.sqrt(mean_squared_error(y_test, predictions))
        r2 = r2_score(y_test, predictions)
        
        results.append({
            'Model': name,
            'MAE': mae,
            'RMSE': rmse,
            'R²': r2
        })
        
    df_results = pd.DataFrame(results)
    print(f"\n{target_name.upper()} PREDICTION")
    print("-" * 50)
    print(df_results.to_string(index=False))
    
    # Select best model based on MAE
    best_model_name = df_results.loc[df_results['MAE'].idxmin()]['Model']
    best_model = models[best_model_name]
    
    return df_results, best_model_name, best_model

def evaluate_traditional_evm_baseline(test_df):
    """Calculates metrics for Traditional EVM baseline on the test set."""
    # Cost Baseline: Traditional EAC
    eac_predictions = test_df['EAC']
    y_cost = test_df['Final_Cost']
    
    cost_mae = mean_absolute_error(y_cost, eac_predictions)
    cost_rmse = np.sqrt(mean_squared_error(y_cost, eac_predictions))
    cost_r2 = r2_score(y_cost, eac_predictions)
    
    # Schedule Baseline: Estimated Duration (Planned_Duration / SPI)
    # Using SPI > 0 to avoid division by zero
    test_df_safe = test_df.copy()
    test_df_safe['SPI'] = test_df_safe['SPI'].replace(0, 0.001)
    test_df_safe['Estimated_Duration'] = test_df_safe['Planned_Duration'] / test_df_safe['SPI']
    
    # Replace infinite/unreasonable duration forecasts with max threshold
    test_df_safe['Estimated_Duration'] = test_df_safe['Estimated_Duration'].clip(upper=200)
    
    ed_predictions = test_df_safe['Estimated_Duration']
    y_schedule = test_df_safe['Final_Duration']
    
    sched_mae = mean_absolute_error(y_schedule, ed_predictions)
    sched_rmse = np.sqrt(mean_squared_error(y_schedule, ed_predictions))
    sched_r2 = r2_score(y_schedule, ed_predictions)
    
    baseline_results = {
        'Traditional EVM (Cost)': {'MAE': cost_mae, 'RMSE': cost_rmse, 'R²': cost_r2},
        'Traditional EVM (Schedule)': {'MAE': sched_mae, 'RMSE': sched_rmse, 'R²': sched_r2}
    }
    return baseline_results

def save_models(cost_model, schedule_model, output_dir='models'):
    """Persists the trained pipelines (which include scalers) to disk."""
    os.makedirs(output_dir, exist_ok=True)
    cost_path = os.path.join(output_dir, 'cost_model.pkl')
    schedule_path = os.path.join(output_dir, 'schedule_model.pkl')
    
    joblib.dump(cost_model, cost_path)
    joblib.dump(schedule_model, schedule_path)
    
    return cost_path, schedule_path

def main():
    os.makedirs('reports', exist_ok=True)
    
    print("Loading data from database...")
    df = load_training_data()
    total_projects = df['project_id'].nunique()
    
    print(f"Splitting {total_projects} projects into train/test groups (80/20)...")
    train_df, test_df = split_projects(df)
    
    train_projects = train_df['project_id'].nunique()
    test_projects = test_df['project_id'].nunique()
    
    print(f"Train set: {len(train_df)} rows ({train_projects} projects)")
    print(f"Test set: {len(test_df)} rows ({test_projects} projects)")
    
    X_train, y_cost_train, y_schedule_train = prepare_features(train_df)
    X_test, y_cost_test, y_schedule_test = prepare_features(test_df)
    
    print("\nTraining Cost Models...")
    cost_models = train_cost_models(X_train, y_cost_train)
    cost_results, best_cost_name, best_cost_model = evaluate_models(cost_models, X_test, y_cost_test, "Cost")
    
    print("\nTraining Schedule Models...")
    schedule_models = train_schedule_models(X_train, y_schedule_train)
    schedule_results, best_schedule_name, best_schedule_model = evaluate_models(schedule_models, X_test, y_schedule_test, "Schedule")
    
    print("\nEvaluating Traditional EVM Baselines...")
    baseline_results = evaluate_traditional_evm_baseline(test_df)
    print("-" * 50)
    print(f"EVM EAC (Cost)     - MAE: {baseline_results['Traditional EVM (Cost)']['MAE']:.2f}, RMSE: {baseline_results['Traditional EVM (Cost)']['RMSE']:.2f}, R²: {baseline_results['Traditional EVM (Cost)']['R²']:.4f}")
    print(f"EVM Est (Schedule) - MAE: {baseline_results['Traditional EVM (Schedule)']['MAE']:.2f}, RMSE: {baseline_results['Traditional EVM (Schedule)']['RMSE']:.2f}, R²: {baseline_results['Traditional EVM (Schedule)']['R²']:.4f}")
    
    # Save best models
    cost_path, sched_path = save_models(best_cost_model, best_schedule_model)
    print(f"\nModels saved to:\n- {cost_path}\n- {sched_path}")
    
    # Write reports
    metrics_df = pd.concat([
        cost_results.assign(Target='Cost'),
        schedule_results.assign(Target='Schedule')
    ])
    metrics_df.to_csv('reports/model_metrics.csv', index=False)
    
    with open('reports/model_evaluation.txt', 'w') as f:
        f.write("ML-Enhanced EVM Model Evaluation Report\n")
        f.write("="*50 + "\n\n")
        f.write(f"Total Projects: {total_projects}\n")
        f.write(f"Train Projects: {train_projects} ({len(train_df)} rows)\n")
        f.write(f"Test Projects: {test_projects} ({len(test_df)} rows)\n\n")
        
        f.write("Features Used:\n")
        f.write(", ".join(FEATURES) + "\n\n")
        
        f.write("COST MODELS\n")
        f.write("-" * 50 + "\n")
        f.write(cost_results.to_string(index=False) + "\n\n")
        f.write(f"Best Cost Model: {best_cost_name}\n\n")
        
        f.write("SCHEDULE MODELS\n")
        f.write("-" * 50 + "\n")
        f.write(schedule_results.to_string(index=False) + "\n\n")
        f.write(f"Best Schedule Model: {best_schedule_name}\n\n")
        
        f.write("BASELINE EVM COMPARISON (Test Set)\n")
        f.write("-" * 50 + "\n")
        f.write(f"Cost (Traditional EAC)      - MAE: {baseline_results['Traditional EVM (Cost)']['MAE']:.2f}, RMSE: {baseline_results['Traditional EVM (Cost)']['RMSE']:.2f}, R²: {baseline_results['Traditional EVM (Cost)']['R²']:.4f}\n")
        f.write(f"Schedule (Planned/SPI)      - MAE: {baseline_results['Traditional EVM (Schedule)']['MAE']:.2f}, RMSE: {baseline_results['Traditional EVM (Schedule)']['RMSE']:.2f}, R²: {baseline_results['Traditional EVM (Schedule)']['R²']:.4f}\n")

if __name__ == "__main__":
    main()
