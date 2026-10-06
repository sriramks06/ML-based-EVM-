import pytest
import pandas as pd
import numpy as np
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.features import (
    validate_features, build_targets, prepare_ml_dataset, 
    EXPECTED_FEATURES, TARGETS, IDENTIFIERS
)

@pytest.fixture
def sample_df():
    df = pd.DataFrame({
        'Project_ID': [1, 2],
        'Week': [1, 1],
        'PV': [100.0, 200.0],
        'EV': [90.0, 180.0],
        'AC': [110.0, 190.0],
        'CPI': [0.818, 0.947],
        'SPI': [0.9, 0.9],
        'EAC': [1222.2, 2111.1],
        'Requirement_Volatility': [0.05, 0.02],
        'Change_Requests': [1, 0],
        'Scope_Change_Percentage': [0.01, 0.0],
        'Task_Completion_Rate': [0.04, 0.05],
        'Resource_Utilization': [1.1, 0.9],
        'Team_Experience': [5.0, 8.0],
        'Task_Complexity': [6.0, 4.0],
        'Defect_Rate': [0.02, 0.01],
        'Rework_Rate': [0.03, 0.01],
        'Dependency_Delays': [1, 0],
        'Delay_Severity': [0.1, 0.0],
        'Project_Completion_Percentage': [0.1, 0.2],
        'Final_Cost': [1500.0, 2000.0],
        'Final_Duration': [30, 25],
        'BAC': [1000.0, 2000.0], # Extra col to exclude
        'Risk_Profile': ['Cost', 'Stable'] # Extra col to exclude
    })
    return df

def test_required_columns_exist(sample_df):
    validate_features(sample_df) # Should pass cleanly
    
    with pytest.raises(ValueError):
        validate_features(sample_df.drop(columns=['PV']))

def test_targets_exist(sample_df):
    y_cost, y_duration = build_targets(sample_df)
    assert len(y_cost) == 2
    assert len(y_duration) == 2
    assert y_cost.iloc[0] == 1500.0
    
def test_identifiers_preserved(sample_df):
    df_final, X, y_cost, y_duration = prepare_ml_dataset(sample_df)
    assert 'Project_ID' in df_final.columns
    assert 'Week' in df_final.columns

def test_targets_not_in_x(sample_df):
    df_final, X, y_cost, y_duration = prepare_ml_dataset(sample_df)
    assert 'Final_Cost' not in X.columns
    assert 'Final_Duration' not in X.columns
    
def test_no_target_leakage():
    # Targets should not be explicitly requested as features
    assert 'Final_Cost' not in EXPECTED_FEATURES
    assert 'Final_Duration' not in EXPECTED_FEATURES
    
def test_no_nan_or_inf(sample_df):
    sample_df.loc[0, 'CPI'] = np.inf
    sample_df.loc[1, 'Requirement_Volatility'] = np.nan
    
    df_final, X, y_c, y_d = prepare_ml_dataset(sample_df)
    
    assert not np.isinf(X['CPI']).any()
    assert not X['Requirement_Volatility'].isna().any()

def test_feature_count(sample_df):
    df_final, X, y_c, y_d = prepare_ml_dataset(sample_df)
    assert len(X.columns) == len(EXPECTED_FEATURES)

def test_pipeline_consistent_output(sample_df):
    df_final1, X1, yc1, yd1 = prepare_ml_dataset(sample_df)
    df_final2, X2, yc2, yd2 = prepare_ml_dataset(sample_df)
    
    pd.testing.assert_frame_equal(df_final1, df_final2)
    pd.testing.assert_frame_equal(X1, X2)
