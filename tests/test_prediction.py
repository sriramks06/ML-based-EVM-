import pytest
import os
import sys
import pandas as pd
import numpy as np

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.predict import (
    load_models, prepare_prediction_features, 
    predict_cost, predict_duration, get_explainability, PREDICTION_FEATURES
)

@pytest.fixture(scope="module")
def models():
    """Load real models trained in Phase 5."""
    return load_models()

@pytest.fixture
def sample_row():
    return {
        'BAC': 100000.0,
        'Planned_Duration': 20,
        'PV': 50000.0,
        'EV': 45000.0,
        'AC': 55000.0,
        'CPI': 0.818,
        'SPI': 0.9,
        'EAC': 122222.2,
        'Requirement_Volatility': 0.05,
        'Change_Requests': 2,
        'Scope_Change_Percentage': 0.02,
        'Task_Completion_Rate': 0.1,
        'Resource_Utilization': 1.1,
        'Team_Experience': 3.0,
        'Task_Complexity': 7.0,
        'Defect_Rate': 0.05,
        'Rework_Rate': 0.05,
        'Dependency_Delays': 1,
        'Delay_Severity': 0.2,
        'Project_Completion_Percentage': 0.5
    }

def test_models_load_successfully(models):
    cost_model, schedule_model = models
    assert cost_model is not None
    assert schedule_model is not None

def test_prediction_schema(sample_row):
    X = prepare_prediction_features(sample_row)
    assert list(X.columns) == PREDICTION_FEATURES
    
def test_missing_features_detected(sample_row):
    bad_row = sample_row.copy()
    del bad_row['PV']
    with pytest.raises(ValueError):
        prepare_prediction_features(bad_row)

def test_predictions_return_numeric(models, sample_row):
    cost_model, schedule_model = models
    X = prepare_prediction_features(sample_row)
    
    cost_pred, cost_factors = predict_cost(cost_model, X)
    sched_pred, sched_factors = predict_duration(schedule_model, X)
    
    assert isinstance(cost_pred, float)
    assert isinstance(sched_pred, float)
    assert cost_pred > 0
    assert sched_pred > 0

def test_explainability(models, sample_row):
    cost_model, schedule_model = models
    X = prepare_prediction_features(sample_row)
    
    _, cost_factors = predict_cost(cost_model, X)
    assert len(cost_factors) == 5
    assert cost_factors[0]['rank'] == 1
    assert 'feature' in cost_factors[0]
    assert 'importance' in cost_factors[0]
    
    # Check sorting
    assert cost_factors[0]['importance'] >= cost_factors[1]['importance']
    
    # Verify feature names are valid
    for factor in cost_factors:
        assert factor['feature'] in PREDICTION_FEATURES
