import pandas as pd
import numpy as np
import os

EXPECTED_FEATURES = [
    'PV', 'EV', 'AC', 'CPI', 'SPI', 'EAC',
    'Requirement_Volatility', 'Change_Requests', 'Scope_Change_Percentage',
    'Task_Completion_Rate', 'Resource_Utilization', 'Team_Experience',
    'Task_Complexity', 'Defect_Rate', 'Rework_Rate', 'Dependency_Delays',
    'Delay_Severity', 'Project_Completion_Percentage'
]
TARGETS = ['Final_Cost', 'Final_Duration']
IDENTIFIERS = ['Project_ID', 'Week']

def load_evm_data(filepath):
    """Loads the processed EVM dataset."""
    return pd.read_csv(filepath)

def handle_missing_and_infinite(df):
    """Replaces infinite values with NaN and safely handles missing data."""
    df = df.copy()
    
    # Track originally infinite or NaN rows for reporting
    missing_before = df.isna().sum().sum()
    inf_before = np.isinf(df.select_dtypes(include=np.number)).sum().sum()
    
    if missing_before > 0 or inf_before > 0:
        print(f"Warning: Found {missing_before} NaNs and {inf_before} Inf values in raw data.")
    
    # Replace inf with NaN
    df.replace([np.inf, -np.inf], np.nan, inplace=True)
    
    # We fill CPI/SPI/EAC infs. If AC is 0, CPI was inf. Fill with 1.0 (on budget).
    # If PV is 0, SPI was inf. Fill with 1.0 (on schedule).
    # EAC might be inf if CPI is 0. If BAC is present, we could use it, else 0.
    if 'CPI' in df.columns:
        df['CPI'] = df['CPI'].fillna(1.0)
    if 'SPI' in df.columns:
        df['SPI'] = df['SPI'].fillna(1.0)
    if 'EAC' in df.columns and 'BAC' in df.columns:
        df['EAC'] = df['EAC'].fillna(df['BAC'])
        
    # Fill remaining NaNs with 0 as a safe default for purely numeric ML input
    df = df.fillna(0)
    
    return df

def validate_features(df):
    """Check required columns exist and there is no target leakage in features."""
    missing_cols = [c for c in IDENTIFIERS + EXPECTED_FEATURES + TARGETS if c not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns: {missing_cols}")
        
    # Check for direct leakage
    if 'Final_Cost' in EXPECTED_FEATURES or 'Final_Duration' in EXPECTED_FEATURES:
        raise ValueError("Target leakage detected in EXPECTED_FEATURES")
        
def build_feature_matrix(df):
    """Extracts only the ML feature columns."""
    return df[EXPECTED_FEATURES]

def build_targets(df):
    """Extracts the target variables."""
    return df['Final_Cost'], df['Final_Duration']

def prepare_ml_dataset(df):
    """Full pipeline: handles missing values, validates, and builds ML datasets."""
    df_clean = handle_missing_and_infinite(df)
    validate_features(df_clean)
    
    X = build_feature_matrix(df_clean)
    y_cost, y_duration = build_targets(df_clean)
    
    # Keep identifiers and targets in the final dataset file
    df_final = df_clean[IDENTIFIERS + EXPECTED_FEATURES + TARGETS].copy()
    
    return df_final, X, y_cost, y_duration

if __name__ == "__main__":
    input_path = 'data/processed/evm_dataset.csv'
    output_path = 'data/processed/ml_dataset.csv'
    
    df = load_evm_data(input_path)
    df_final, X_features, y_cost, y_duration = prepare_ml_dataset(df)
    
    df_final.to_csv(output_path, index=False)
    
    # Output report
    print("--- ML Dataset Preparation Report ---")
    print(f"Number of rows processed: {len(df_final)}")
    print(f"Number of features (X): {len(EXPECTED_FEATURES)}")
    
    print("\nFeature names:")
    for f in EXPECTED_FEATURES:
        print(f"- {f}")
        
    print("\nTarget names:")
    for t in TARGETS:
        print(f"- {t}")
        
    print("\nMissing value summary (after handling):")
    print(df_final.isna().sum().to_string())
    
    print("\nExcluded columns and reasons for exclusion (preventing target leakage or unrelated to project state):")
    original_cols = set(df.columns)
    included_cols = set(IDENTIFIERS + EXPECTED_FEATURES + TARGETS)
    excluded = original_cols - included_cols
    for col in excluded:
        if col in ['BAC', 'Planned_Duration']:
            reason = "Not explicitly requested as a dynamic condition feature. Known at baseline."
        elif col == 'Risk_Profile':
            reason = "A synthetic label generated to verify data health. Would cause target leakage if used in X."
        else:
            reason = "Not specified in the feature requirements."
        print(f"- {col}: {reason}")
        
    print("\nFirst 5 rows of X (Features matrix):")
    print(X_features.head(5).to_string())

    print("\nTime-Awareness Note:")
    print("Because this is a forecasting problem predicting Final_Cost and Final_Duration, ")
    print("a future phase must implement a strictly sequential or grouped train/test split ")
    print("(e.g., splitting by Project_ID) to prevent future data leakage from the same project.")
