import os
import joblib
import numpy as np
import pandas as pd

# Must match exactly what was used in Phase 5
PREDICTION_FEATURES = [
    'BAC', 'Planned_Duration',
    'PV', 'EV', 'AC', 'CPI', 'SPI', 'EAC',
    'Requirement_Volatility', 'Change_Requests', 'Scope_Change_Percentage',
    'Task_Completion_Rate', 'Resource_Utilization', 'Team_Experience',
    'Task_Complexity', 'Defect_Rate', 'Rework_Rate', 'Dependency_Delays',
    'Delay_Severity', 'Project_Completion_Percentage'
]

def load_models(model_dir='models'):
    """Loads the pre-trained cost and schedule pipelines."""
    cost_path = os.path.join(model_dir, 'cost_model.pkl')
    schedule_path = os.path.join(model_dir, 'schedule_model.pkl')
    
    if not os.path.exists(cost_path) or not os.path.exists(schedule_path):
        raise FileNotFoundError("Trained models not found. Run Phase 5 training first.")
        
    cost_model = joblib.load(cost_path)
    schedule_model = joblib.load(schedule_path)
    
    return cost_model, schedule_model

def prepare_prediction_features(row_dict):
    """Converts a dictionary (or row) into the exact feature DataFrame expected by the models."""
    missing = [f for f in PREDICTION_FEATURES if f not in row_dict]
    if missing:
        raise ValueError(f"Missing required features for prediction: {missing}")
        
    df = pd.DataFrame([row_dict])
    X = df[PREDICTION_FEATURES].copy()
    
    # Handle NaNs / Infinities safely
    X.replace([np.inf, -np.inf], np.nan, inplace=True)
    X = X.fillna(0)
    
    return X

def get_explainability(pipeline, feature_names):
    """
    Extracts feature importance from the pipeline.
    Handles Linear Regression (coefficients) and Tree-based models (feature_importances_).
    Returns top 5 factors formatted as a list of dicts.
    """
    regressor = pipeline.named_steps['regressor']
    
    if hasattr(regressor, 'coef_'):
        # Linear Models
        importances = np.abs(regressor.coef_)
    elif hasattr(regressor, 'feature_importances_'):
        # Tree Models
        importances = regressor.feature_importances_
    else:
        return []
        
    # Normalize to 0-100 for display
    total_importance = np.sum(importances)
    if total_importance > 0:
        normalized = (importances / total_importance) * 100
    else:
        normalized = importances
        
    factors = []
    for name, imp in zip(feature_names, normalized):
        factors.append({'feature': name, 'importance': imp})
        
    # Sort descending and take top 5
    factors = sorted(factors, key=lambda x: x['importance'], reverse=True)[:5]
    
    # Add ranks
    for idx, factor in enumerate(factors):
        factor['rank'] = idx + 1
        
    return factors

def predict_cost(model, X):
    """Returns the cost prediction and explanation."""
    prediction = model.predict(X)[0]
    factors = get_explainability(model, PREDICTION_FEATURES)
    return float(prediction), factors

def predict_duration(model, X):
    """Returns the schedule prediction and explanation."""
    prediction = model.predict(X)[0]
    factors = get_explainability(model, PREDICTION_FEATURES)
    return float(prediction), factors

def format_explanation(factors, target_type):
    """Generates human-readable explanations from the top factors."""
    if not factors:
        return "Explanation unavailable for this model type."
        
    top_feature = factors[0]['feature'].replace('_', ' ')
    second_feature = factors[1]['feature'].replace('_', ' ')
    
    explanation = f"High '{top_feature}' is the primary model signal associated with this {target_type} prediction."
    explanation += f" Furthermore, '{second_feature}' is a significant contributing factor."
    
    return explanation
