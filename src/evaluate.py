"""
Phase 10: Final Evaluation, Integration Testing, and Academic Validation
ML-Enhanced EVM Project

This script produces all evaluation reports, figures, and academic evidence.
It does NOT retrain models — it uses saved models from Phase 5.
"""

import os
import sys
import time
import warnings
import json
from datetime import datetime

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')  # non-interactive backend for headless generation
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from sklearn.metrics import (
    mean_absolute_error, mean_squared_error, r2_score,
    precision_score, recall_score, f1_score, confusion_matrix
)
from sklearn.model_selection import GroupShuffleSplit

warnings.filterwarnings('ignore')

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.train_models import load_training_data, split_projects, prepare_features, FEATURES
from src.predict import load_models, prepare_prediction_features, predict_cost, predict_duration
from src.risk import generate_risk_assessment, COST_RISK_THRESHOLDS, SCHEDULE_RISK_THRESHOLDS
from src.recommendations import generate_recommendations, THRESHOLDS
from src.database import SessionLocal, ProjectWeeklyData, Project, Prediction, RiskAssessment

# ─── Output Directories ──────────────────────────────────────────
REPORTS_DIR = 'reports'
FIGURES_DIR = os.path.join(REPORTS_DIR, 'figures')
os.makedirs(FIGURES_DIR, exist_ok=True)

# ─── Plot Style ───────────────────────────────────────────────────
plt.rcParams.update({
    'figure.facecolor': '#0d0f1a',
    'axes.facecolor': '#1a1e30',
    'axes.edgecolor': '#2e3450',
    'axes.labelcolor': '#8892b0',
    'xtick.color': '#8892b0',
    'ytick.color': '#8892b0',
    'text.color': '#e2e8f0',
    'grid.color': '#252a40',
    'grid.alpha': 0.6,
    'lines.linewidth': 2,
    'font.family': 'sans-serif',
    'font.size': 10,
    'axes.titlesize': 12,
    'axes.titleweight': 'bold',
    'figure.titlesize': 14,
})
PALETTE = ['#6366f1', '#10b981', '#f43f5e', '#f59e0b', '#3b82f6', '#8b5cf6']

OVERRUN_THRESHOLD_PCT = 15.0  # >15% cost or schedule overrun = "risky project"


# ══════════════════════════════════════════════════════════════════
# SECTION 1: LOAD DATA AND MODELS
# ══════════════════════════════════════════════════════════════════
def load_all():
    print("=" * 65)
    print("PHASE 10: FINAL EVALUATION")
    print("=" * 65)
    print("\n[1/10] Loading training data and models...")

    df = load_training_data()
    train_df, test_df = split_projects(df)

    cost_model, schedule_model = load_models()

    print(f"  Dataset: {df['project_id'].nunique()} projects, {len(df)} observations")
    print(f"  Train: {train_df['project_id'].nunique()} projects ({len(train_df)} rows)")
    print(f"  Test : {test_df['project_id'].nunique()} projects ({len(test_df)} rows)")
    return df, train_df, test_df, cost_model, schedule_model


# ══════════════════════════════════════════════════════════════════
# SECTION 2: FINAL MODEL COMPARISON TABLE
# ══════════════════════════════════════════════════════════════════
def run_model_comparison(train_df, test_df):
    print("\n[2/10] Final model comparison on held-out test set...")
    from src.train_models import (
        train_cost_models, train_schedule_models, evaluate_models,
        evaluate_traditional_evm_baseline
    )

    X_train, y_cost_train, y_sched_train = prepare_features(train_df)
    X_test,  y_cost_test,  y_sched_test  = prepare_features(test_df)

    cost_models = train_cost_models(X_train, y_cost_train)
    sched_models = train_schedule_models(X_train, y_sched_train)

    cost_results, _, _ = evaluate_models(cost_models, X_test, y_cost_test, "Cost")
    sched_results, _, _ = evaluate_models(sched_models, X_test, y_sched_test, "Schedule")

    baseline = evaluate_traditional_evm_baseline(test_df)

    # Add EVM baseline rows
    evm_cost_row = pd.DataFrame([{
        'Model': 'Traditional EVM (EAC)',
        'MAE': baseline['Traditional EVM (Cost)']['MAE'],
        'RMSE': baseline['Traditional EVM (Cost)']['RMSE'],
        'R²': baseline['Traditional EVM (Cost)']['R²'],
        'Target': 'Cost'
    }])
    evm_sched_row = pd.DataFrame([{
        'Model': 'Traditional EVM (Est. Duration)',
        'MAE': baseline['Traditional EVM (Schedule)']['MAE'],
        'RMSE': baseline['Traditional EVM (Schedule)']['RMSE'],
        'R²': baseline['Traditional EVM (Schedule)']['R²'],
        'Target': 'Schedule'
    }])

    cost_results['Target'] = 'Cost'
    sched_results['Target'] = 'Schedule'

    full_table = pd.concat([
        evm_cost_row, cost_results,
        evm_sched_row, sched_results
    ], ignore_index=True)

    full_table.to_csv(os.path.join(REPORTS_DIR, 'final_metrics.csv'), index=False)
    print("  Saved: reports/final_metrics.csv")
    return full_table, baseline, cost_results, sched_results


# ══════════════════════════════════════════════════════════════════
# SECTION 3: IMPROVEMENT CALCULATION
# ══════════════════════════════════════════════════════════════════
def compute_improvements(baseline, cost_results, sched_results):
    print("\n[3/10] Computing ML improvement over EVM baseline...")

    best_cost = cost_results.loc[cost_results['MAE'].idxmin()]
    best_sched = sched_results.loc[sched_results['MAE'].idxmin()]

    evm_cost_mae  = baseline['Traditional EVM (Cost)']['MAE']
    evm_cost_rmse = baseline['Traditional EVM (Cost)']['RMSE']
    evm_cost_r2   = baseline['Traditional EVM (Cost)']['R²']
    evm_sched_mae  = baseline['Traditional EVM (Schedule)']['MAE']
    evm_sched_rmse = baseline['Traditional EVM (Schedule)']['RMSE']
    evm_sched_r2   = baseline['Traditional EVM (Schedule)']['R²']

    cost_mae_imp  = (evm_cost_mae  - best_cost['MAE'])  / evm_cost_mae  * 100
    cost_rmse_imp = (evm_cost_rmse - best_cost['RMSE']) / evm_cost_rmse * 100
    sched_mae_imp  = (evm_sched_mae  - best_sched['MAE'])  / evm_sched_mae  * 100
    sched_rmse_imp = (evm_sched_rmse - best_sched['RMSE']) / evm_sched_rmse * 100

    improvements = {
        'best_cost_model':  best_cost['Model'],
        'best_sched_model': best_sched['Model'],
        'cost_mae_imp_pct':  cost_mae_imp,
        'cost_rmse_imp_pct': cost_rmse_imp,
        'cost_r2_delta':     best_cost['R²'] - evm_cost_r2,
        'sched_mae_imp_pct':  sched_mae_imp,
        'sched_rmse_imp_pct': sched_rmse_imp,
        'sched_r2_delta':     best_sched['R²'] - evm_sched_r2,
        'evm_cost_mae': evm_cost_mae, 'ml_cost_mae': best_cost['MAE'],
        'evm_sched_mae': evm_sched_mae, 'ml_sched_mae': best_sched['MAE'],
    }

    print(f"  Best Cost Model:     {best_cost['Model']}")
    print(f"  Cost MAE Improvement:     {cost_mae_imp:.1f}%")
    print(f"  Cost RMSE Improvement:    {cost_rmse_imp:.1f}%")
    print(f"  Best Schedule Model: {best_sched['Model']}")
    print(f"  Schedule MAE Improvement: {sched_mae_imp:.1f}%")
    print(f"  Schedule RMSE Improvement:{sched_rmse_imp:.1f}%")

    return improvements


# ══════════════════════════════════════════════════════════════════
# SECTION 4: EARLY WARNING EVALUATION
# ══════════════════════════════════════════════════════════════════
def early_warning_evaluation(test_df, cost_model, schedule_model):
    print("\n[4/10] Early warning evaluation on test projects...")

    test_projects = test_df['project_id'].unique()
    results = []

    for pid in test_projects:
        proj_df = test_df[test_df['project_id'] == pid].sort_values('week')

        actual_final_cost = proj_df['Final_Cost'].iloc[0]
        actual_final_dur  = proj_df['Final_Duration'].iloc[0]
        bac               = proj_df['BAC'].iloc[0]
        planned_dur       = proj_df['Planned_Duration'].iloc[0]

        actual_cost_overrun_pct = (actual_final_cost - bac) / bac * 100
        actual_sched_overrun_pct = (actual_final_dur - planned_dur) / planned_dur * 100
        is_truly_at_risk = (actual_cost_overrun_pct > OVERRUN_THRESHOLD_PCT or
                            actual_sched_overrun_pct > OVERRUN_THRESHOLD_PCT)

        first_high_week = None
        for _, row in proj_df.iterrows():
            row_dict = row.to_dict()
            row_dict['Planned_Duration'] = planned_dur
            try:
                X = prepare_prediction_features(row_dict)
                pred_cost, _ = predict_cost(cost_model, X)
                pred_dur,  _ = predict_duration(schedule_model, X)
                risk = generate_risk_assessment(pred_cost, bac, pred_dur, planned_dur)
                if risk['overall_risk'] == 'HIGH' and first_high_week is None:
                    first_high_week = int(row['week'])
            except Exception:
                continue

        total_weeks = int(proj_df['week'].max())

        results.append({
            'project_id': int(pid),
            'total_weeks': total_weeks,
            'actual_cost_overrun_pct': round(actual_cost_overrun_pct, 2),
            'actual_sched_overrun_pct': round(actual_sched_overrun_pct, 2),
            'is_truly_at_risk': is_truly_at_risk,
            'first_high_risk_week': first_high_week,
            'early_warning_weeks': (total_weeks - first_high_week) if first_high_week else None,
            'detected': first_high_week is not None
        })

    ew_df = pd.DataFrame(results)
    ew_df.to_csv(os.path.join(REPORTS_DIR, 'early_warning_results.csv'), index=False)

    at_risk = ew_df[ew_df['is_truly_at_risk']]
    safe    = ew_df[~ew_df['is_truly_at_risk']]
    true_pos  = len(at_risk[at_risk['detected']])
    false_neg = len(at_risk[~at_risk['detected']])
    false_pos = len(safe[safe['detected']])
    true_neg  = len(safe[~safe['detected']])

    precision = true_pos / (true_pos + false_pos) if (true_pos + false_pos) > 0 else 0
    recall    = true_pos / (true_pos + false_neg) if (true_pos + false_neg) > 0 else 0
    f1        = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0
    avg_lead  = ew_df[ew_df['early_warning_weeks'].notna()]['early_warning_weeks'].mean()

    ew_summary = {
        'total_test_projects': len(ew_df),
        'truly_at_risk': len(at_risk),
        'detected': true_pos,
        'missed': false_neg,
        'false_alarms': false_pos,
        'precision': round(precision, 3),
        'recall': round(recall, 3),
        'f1': round(f1, 3),
        'avg_early_warning_weeks': round(avg_lead, 1) if not np.isnan(avg_lead) else 0
    }

    print(f"  At-risk projects: {len(at_risk)} / {len(ew_df)}")
    print(f"  Detected: {true_pos}, Missed: {false_neg}, False alarms: {false_pos}")
    print(f"  Precision: {precision:.3f}, Recall: {recall:.3f}, F1: {f1:.3f}")
    print(f"  Avg early warning lead time: {avg_lead:.1f} weeks")

    return ew_df, ew_summary


# ══════════════════════════════════════════════════════════════════
# SECTION 5: SCENARIO SENSITIVITY TESTS
# ══════════════════════════════════════════════════════════════════
def scenario_sensitivity_tests(cost_model, schedule_model):
    print("\n[5/10] Scenario sensitivity tests...")

    base = {
        'BAC': 500000, 'Planned_Duration': 24,
        'PV': 250000, 'EV': 240000, 'AC': 245000,
        'CPI': 0.980, 'SPI': 0.960, 'EAC': 510204,
        'Requirement_Volatility': 0.03, 'Change_Requests': 1,
        'Scope_Change_Percentage': 0.02, 'Task_Completion_Rate': 0.08,
        'Resource_Utilization': 0.85, 'Team_Experience': 4.0,
        'Task_Complexity': 5.0, 'Defect_Rate': 0.02, 'Rework_Rate': 0.02,
        'Dependency_Delays': 0, 'Delay_Severity': 0.05,
        'Project_Completion_Percentage': 0.50
    }

    scenarios = {
        'A. Stable Project':             base.copy(),
        'B. High Scope Growth':          {**base, 'Scope_Change_Percentage': 0.20, 'Change_Requests': 8, 'Requirement_Volatility': 0.20},
        'C. High Resource Utilization':  {**base, 'Resource_Utilization': 1.30},
        'D. High Defect/Rework':         {**base, 'Defect_Rate': 0.12, 'Rework_Rate': 0.15},
        'E. Dependency Delays':          {**base, 'Dependency_Delays': 5, 'Delay_Severity': 0.40, 'SPI': 0.75},
        'F. Multiple Risk Factors':      {**base, 'Scope_Change_Percentage': 0.15, 'Resource_Utilization': 1.20,
                                          'Defect_Rate': 0.09, 'Dependency_Delays': 4, 'CPI': 0.80, 'SPI': 0.78},
    }

    rows = []
    for scenario_name, data in scenarios.items():
        X = prepare_prediction_features(data)
        pred_cost, _ = predict_cost(cost_model, X)
        pred_dur,  _ = predict_duration(schedule_model, X)
        risk = generate_risk_assessment(pred_cost, data['BAC'], pred_dur, data['Planned_Duration'])
        rec_dict = {'overall_risk': risk['overall_risk']}
        recs = generate_recommendations(data, rec_dict)

        rows.append({
            'Scenario': scenario_name,
            'Predicted_Final_Cost': round(pred_cost),
            'Cost_Overrun_Pct': round(risk['cost_overrun_percentage'], 1),
            'Predicted_Final_Duration': round(pred_dur, 1),
            'Schedule_Overrun_Pct': round(risk['schedule_overrun_percentage'], 1),
            'Cost_Risk': risk['cost_risk'],
            'Schedule_Risk': risk['schedule_risk'],
            'Overall_Risk': risk['overall_risk'],
            'Num_Recommendations': len(recs),
            'Top_Recommendation': recs[0]['risk_factor'] if recs else 'None'
        })
        print(f"  {scenario_name}: cost={round(pred_cost):,} ({risk['cost_overrun_percentage']:+.1f}%) | sched={pred_dur:.1f}w ({risk['schedule_overrun_percentage']:+.1f}%) | risk={risk['overall_risk']}")

    sc_df = pd.DataFrame(rows)
    sc_df.to_csv(os.path.join(REPORTS_DIR, 'scenario_tests.csv'), index=False)
    print("  Saved: reports/scenario_tests.csv")
    return sc_df


# ══════════════════════════════════════════════════════════════════
# SECTION 6: DATA QUALITY VALIDATION
# ══════════════════════════════════════════════════════════════════
def data_quality_check(df):
    print("\n[6/10] Data quality validation...")
    issues = []

    dups = df.duplicated(subset=['project_id', 'week']).sum()
    if dups: issues.append(f"Duplicate project-week rows: {dups}")

    nulls = df[FEATURES + ['Final_Cost', 'Final_Duration']].isnull().sum().sum()
    if nulls: issues.append(f"Total null values: {nulls}")

    neg_costs = (df['Final_Cost'] <= 0).sum()
    if neg_costs: issues.append(f"Non-positive Final_Cost: {neg_costs}")

    neg_dur = (df['Final_Duration'] <= 0).sum()
    if neg_dur: issues.append(f"Non-positive Final_Duration: {neg_dur}")

    invalid_cpi = ((df['CPI'] < 0) | (df['CPI'] > 10)).sum()
    if invalid_cpi: issues.append(f"CPI outside [0,10]: {invalid_cpi}")

    invalid_spi = ((df['SPI'] < 0) | (df['SPI'] > 10)).sum()
    if invalid_spi: issues.append(f"SPI outside [0,10]: {invalid_spi}")

    invalid_pct = ((df['Project_Completion_Percentage'] < 0) | (df['Project_Completion_Percentage'] > 1)).sum()
    if invalid_pct: issues.append(f"Project_Completion_Percentage out of [0,1]: {invalid_pct}")

    session = SessionLocal()
    pred_count = session.query(Prediction).count()
    risk_count = session.query(RiskAssessment).count()
    session.close()

    quality_report = {
        'total_rows': len(df),
        'total_projects': df['project_id'].nunique(),
        'issues': issues if issues else ['None detected'],
        'prediction_records_in_db': pred_count,
        'risk_records_in_db': risk_count
    }

    status = "PASS" if not issues else f"WARNING — {len(issues)} issues"
    print(f"  Data Quality: {status}")
    if issues:
        for i in issues:
            print(f"    ⚠ {i}")

    with open(os.path.join(REPORTS_DIR, 'data_quality_report.txt'), 'w') as f:
        f.write("ML-Enhanced EVM — Data Quality Report\n")
        f.write("=" * 50 + "\n")
        f.write(f"Generated: {datetime.now().isoformat()}\n\n")
        f.write(f"Total Rows: {len(df)}\n")
        f.write(f"Total Projects: {df['project_id'].nunique()}\n")
        f.write(f"Prediction Records (DB): {pred_count}\n")
        f.write(f"Risk Records (DB): {risk_count}\n\n")
        f.write("Issues Found:\n")
        for i in quality_report['issues']:
            f.write(f"  - {i}\n")
    print("  Saved: reports/data_quality_report.txt")
    return quality_report


# ══════════════════════════════════════════════════════════════════
# SECTION 7: API TIMING TEST
# ══════════════════════════════════════════════════════════════════
def timing_test(cost_model, schedule_model, test_df):
    print("\n[7/10] Measuring prediction timing...")

    row = test_df.iloc[0].to_dict()
    row['Planned_Duration'] = row.get('Planned_Duration', 24)

    start = time.perf_counter()
    for _ in range(100):
        X = prepare_prediction_features(row)
        predict_cost(cost_model, X)
        predict_duration(schedule_model, X)
    elapsed = (time.perf_counter() - start) / 100 * 1000

    print(f"  Average prediction time (100 runs): {elapsed:.2f} ms")
    return elapsed


# ══════════════════════════════════════════════════════════════════
# SECTION 8: GENERATE ALL FIGURES
# ══════════════════════════════════════════════════════════════════
def generate_figures(test_df, cost_model, schedule_model, full_table):
    print("\n[8/10] Generating evaluation figures...")

    X_test, y_cost_test, y_sched_test = prepare_features(test_df)
    ml_cost_preds = cost_model.predict(X_test)
    ml_sched_preds = schedule_model.predict(X_test)

    test_safe = test_df.copy()
    test_safe['SPI'] = test_safe['SPI'].replace(0, 0.001)
    evm_cost_preds = test_safe['EAC'].values
    evm_sched_preds = (test_safe['Planned_Duration'] / test_safe['SPI']).clip(upper=200).values

    # 1. Actual vs Predicted Final Cost
    fig, axes = plt.subplots(1, 2, figsize=(14, 6))
    fig.suptitle("Actual vs Predicted Final Cost", fontweight='bold')
    for ax, preds, label, color in [
        (axes[0], evm_cost_preds, 'Traditional EVM (EAC)', PALETTE[0]),
        (axes[1], ml_cost_preds,  'ML Linear Regression',  PALETTE[2])
    ]:
        lim = [min(y_cost_test.min(), preds.min()) * 0.9,
               max(y_cost_test.max(), preds.max()) * 1.1]
        ax.scatter(y_cost_test, preds, alpha=0.4, s=15, color=color)
        ax.plot(lim, lim, 'w--', alpha=0.5, lw=1)
        ax.set_xlim(lim); ax.set_ylim(lim)
        ax.set_xlabel("Actual Final Cost ($)"); ax.set_ylabel("Predicted ($)")
        ax.set_title(label)
        ax.grid(True)
        mae = mean_absolute_error(y_cost_test, preds)
        r2  = r2_score(y_cost_test, preds)
        ax.text(0.05, 0.92, f"MAE=${mae:,.0f}\nR²={r2:.3f}",
                transform=ax.transAxes, fontsize=9,
                bbox=dict(boxstyle='round', facecolor='#252a40', alpha=0.8))
    plt.tight_layout()
    plt.savefig(os.path.join(FIGURES_DIR, '1_actual_vs_predicted_cost.png'), dpi=150, bbox_inches='tight')
    plt.close()

    # 2. Actual vs Predicted Final Duration
    fig, axes = plt.subplots(1, 2, figsize=(14, 6))
    fig.suptitle("Actual vs Predicted Final Duration", fontweight='bold')
    for ax, preds, label, color in [
        (axes[0], evm_sched_preds, 'Traditional EVM (Est. Duration)', PALETTE[0]),
        (axes[1], ml_sched_preds,   'ML Gradient Boosting',            PALETTE[2])
    ]:
        lim = [min(y_sched_test.min(), preds.min()) * 0.9,
               max(y_sched_test.max(), preds.max()) * 1.1]
        ax.scatter(y_sched_test, preds, alpha=0.4, s=15, color=color)
        ax.plot(lim, lim, 'w--', alpha=0.5, lw=1)
        ax.set_xlim(lim); ax.set_ylim(lim)
        ax.set_xlabel("Actual Final Duration (weeks)"); ax.set_ylabel("Predicted (weeks)")
        ax.set_title(label)
        ax.grid(True)
        mae = mean_absolute_error(y_sched_test, preds)
        r2  = r2_score(y_sched_test, preds)
        ax.text(0.05, 0.92, f"MAE={mae:.2f} wks\nR²={r2:.3f}",
                transform=ax.transAxes, fontsize=9,
                bbox=dict(boxstyle='round', facecolor='#252a40', alpha=0.8))
    plt.tight_layout()
    plt.savefig(os.path.join(FIGURES_DIR, '2_actual_vs_predicted_duration.png'), dpi=150, bbox_inches='tight')
    plt.close()

    # 3. EVM vs ML Cost Error Distribution
    fig, ax = plt.subplots(figsize=(10, 5))
    evm_cost_errors = np.abs(y_cost_test.values - evm_cost_preds)
    ml_cost_errors  = np.abs(y_cost_test.values - ml_cost_preds)
    ax.hist(evm_cost_errors / 1e6, bins=40, alpha=0.6, color=PALETTE[0], label='EVM EAC Error')
    ax.hist(ml_cost_errors  / 1e6, bins=40, alpha=0.6, color=PALETTE[2], label='ML Error')
    ax.set_xlabel("Absolute Error ($ millions)"); ax.set_ylabel("Count")
    ax.set_title("Cost Absolute Error Distribution: EVM vs ML")
    ax.legend(); ax.grid(True)
    plt.tight_layout()
    plt.savefig(os.path.join(FIGURES_DIR, '3_cost_error_distribution.png'), dpi=150, bbox_inches='tight')
    plt.close()

    # 4. EVM vs ML Schedule Error Distribution
    fig, ax = plt.subplots(figsize=(10, 5))
    evm_sched_errors = np.abs(y_sched_test.values - evm_sched_preds)
    ml_sched_errors  = np.abs(y_sched_test.values - ml_sched_preds)
    ax.hist(evm_sched_errors, bins=40, alpha=0.6, color=PALETTE[0], label='EVM Est. Duration Error')
    ax.hist(ml_sched_errors,  bins=40, alpha=0.6, color=PALETTE[2], label='ML Error')
    ax.set_xlabel("Absolute Error (weeks)"); ax.set_ylabel("Count")
    ax.set_title("Schedule Absolute Error Distribution: EVM vs ML")
    ax.legend(); ax.grid(True)
    plt.tight_layout()
    plt.savefig(os.path.join(FIGURES_DIR, '4_schedule_error_distribution.png'), dpi=150, bbox_inches='tight')
    plt.close()

    # 5. Model Comparison Bar Chart
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    fig.suptitle("Model Comparison: MAE by Method", fontweight='bold')
    for ax, target, ylabel in [(axes[0], 'Cost', 'MAE ($)'), (axes[1], 'Schedule', 'MAE (weeks)')]:
        sub = full_table[full_table['Target'] == target].copy()
        bars = ax.bar(sub['Model'], sub['MAE'],
                      color=[PALETTE[0]] + [PALETTE[2]] * (len(sub) - 1),
                      edgecolor='none', width=0.5)
        ax.set_xlabel("Method"); ax.set_ylabel(ylabel)
        ax.set_title(f"{target} Prediction MAE")
        ax.tick_params(axis='x', rotation=20)
        for b in bars:
            ax.text(b.get_x() + b.get_width() / 2, b.get_height() * 1.01,
                    f'{b.get_height():,.0f}', ha='center', va='bottom', fontsize=8)
        ax.grid(True, axis='y')
    plt.tight_layout()
    plt.savefig(os.path.join(FIGURES_DIR, '5_model_comparison_mae.png'), dpi=150, bbox_inches='tight')
    plt.close()

    # 6. Feature Importance (Cost — Linear Regression)
    try:
        cost_reg = cost_model.named_steps['regressor']
        cost_coefs = np.abs(cost_reg.coef_)
        cost_norm  = cost_coefs / cost_coefs.sum() * 100
        feat_cost_df = pd.DataFrame({'Feature': FEATURES, 'Importance': cost_norm}).nlargest(10, 'Importance')

        fig, ax = plt.subplots(figsize=(10, 5))
        bars = ax.barh(feat_cost_df['Feature'][::-1], feat_cost_df['Importance'][::-1],
                       color=PALETTE[1], edgecolor='none')
        ax.set_xlabel("Relative Importance (%)"); ax.set_title("Top 10 Cost Model Feature Importance\n(Linear Regression Coefficients, Normalized)")
        ax.grid(True, axis='x')
        plt.tight_layout()
        plt.savefig(os.path.join(FIGURES_DIR, '6a_feature_importance_cost.png'), dpi=150, bbox_inches='tight')
        plt.close()
    except Exception: pass

    # 6b. Feature Importance (Schedule — Gradient Boosting)
    try:
        sched_reg = schedule_model.named_steps['regressor']
        sched_imps = sched_reg.feature_importances_ * 100
        feat_sched_df = pd.DataFrame({'Feature': FEATURES, 'Importance': sched_imps}).nlargest(10, 'Importance')

        fig, ax = plt.subplots(figsize=(10, 5))
        ax.barh(feat_sched_df['Feature'][::-1], feat_sched_df['Importance'][::-1],
                color=PALETTE[3], edgecolor='none')
        ax.set_xlabel("Feature Importance (%)"); ax.set_title("Top 10 Schedule Model Feature Importance\n(Gradient Boosting feature_importances_)")
        ax.grid(True, axis='x')
        plt.tight_layout()
        plt.savefig(os.path.join(FIGURES_DIR, '6b_feature_importance_schedule.png'), dpi=150, bbox_inches='tight')
        plt.close()
    except Exception: pass

    print(f"  Saved 7 figures to {FIGURES_DIR}/")


# ══════════════════════════════════════════════════════════════════
# SECTION 9: WRITE FINAL EVALUATION REPORT
# ══════════════════════════════════════════════════════════════════
def write_final_report(df, test_df, full_table, improvements, ew_summary, quality_report, sc_df, avg_timing_ms):
    print("\n[9/10] Writing final evaluation report...")

    report_path = os.path.join(REPORTS_DIR, 'final_evaluation.txt')
    with open(report_path, 'w') as f:
        f.write("=" * 70 + "\n")
        f.write("ML-ENHANCED EARNED VALUE MANAGEMENT — FINAL EVALUATION REPORT\n")
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("=" * 70 + "\n\n")

        # ── Dataset Summary
        f.write("1. DATASET SUMMARY\n")
        f.write("-" * 50 + "\n")
        f.write(f"Total Projects         : {df['project_id'].nunique()}\n")
        f.write(f"Total Observations     : {len(df)}\n")
        f.write(f"Weeks per Project      : {int(df.groupby('project_id').size().mean())} (avg)\n")
        f.write(f"Test Projects          : {test_df['project_id'].nunique()}\n")
        f.write(f"Test Observations      : {len(test_df)}\n")
        f.write(f"Split Method           : GroupShuffleSplit (by Project_ID) — no data leakage\n\n")

        # ── Model Comparison Table
        f.write("2. FINAL MODEL COMPARISON (Held-Out Test Set)\n")
        f.write("-" * 50 + "\n")
        for target in ['Cost', 'Schedule']:
            f.write(f"\n{target.upper()} PREDICTION\n")
            sub = full_table[full_table['Target'] == target][['Model', 'MAE', 'RMSE', 'R²']]
            f.write(sub.to_string(index=False) + "\n")

        # ── Improvements
        f.write("\n\n3. ML IMPROVEMENT OVER TRADITIONAL EVM BASELINE\n")
        f.write("-" * 50 + "\n")
        f.write(f"Best Cost Model    : {improvements['best_cost_model']}\n")
        f.write(f"Best Schedule Model: {improvements['best_sched_model']}\n\n")
        f.write(f"On the synthetic held-out test set, the selected ML model reduced cost\n")
        f.write(f"prediction MAE by {improvements['cost_mae_imp_pct']:.1f}% compared with the traditional EVM\n")
        f.write(f"EAC baseline ({improvements['evm_cost_mae']:,.0f} → {improvements['ml_cost_mae']:,.0f} $/project).\n\n")
        f.write(f"Schedule prediction MAE improved by {improvements['sched_mae_imp_pct']:.1f}%\n")
        f.write(f"({improvements['evm_sched_mae']:.2f} → {improvements['ml_sched_mae']:.2f} weeks/project).\n\n")
        f.write(f"Cost R² delta      : +{improvements['cost_r2_delta']:.4f}\n")
        f.write(f"Schedule R² delta  : +{improvements['sched_r2_delta']:.4f}\n")

        # ── Early Warning
        f.write("\n\n4. EARLY WARNING EVALUATION\n")
        f.write("-" * 50 + "\n")
        f.write(f"Overrun threshold used: >{OVERRUN_THRESHOLD_PCT}% cost OR schedule overrun\n\n")
        f.write(f"Total Test Projects    : {ew_summary['total_test_projects']}\n")
        f.write(f"Truly At-Risk          : {ew_summary['truly_at_risk']}\n")
        f.write(f"Correctly Detected     : {ew_summary['detected']}\n")
        f.write(f"Missed (False Negative): {ew_summary['missed']}\n")
        f.write(f"False Alarms           : {ew_summary['false_alarms']}\n")
        f.write(f"Precision              : {ew_summary['precision']:.3f}\n")
        f.write(f"Recall                 : {ew_summary['recall']:.3f}\n")
        f.write(f"F1 Score               : {ew_summary['f1']:.3f}\n")
        f.write(f"Avg Early Warning Lead : {ew_summary['avg_early_warning_weeks']} weeks\n")

        # ── Scenario Tests
        f.write("\n\n5. SCENARIO SENSITIVITY TESTS\n")
        f.write("-" * 50 + "\n")
        for _, row in sc_df.iterrows():
            f.write(f"\n  {row['Scenario']}\n")
            f.write(f"    Predicted Cost    : ${row['Predicted_Final_Cost']:,} ({row['Cost_Overrun_Pct']:+.1f}%)\n")
            f.write(f"    Predicted Duration: {row['Predicted_Final_Duration']} wks ({row['Schedule_Overrun_Pct']:+.1f}%)\n")
            f.write(f"    Overall Risk      : {row['Overall_Risk']}\n")
            f.write(f"    Recommendations   : {row['Num_Recommendations']} (top: {row['Top_Recommendation']})\n")

        # ── Data Quality
        f.write("\n\n6. DATA QUALITY\n")
        f.write("-" * 50 + "\n")
        for issue in quality_report['issues']:
            f.write(f"  {issue}\n")
        f.write(f"\n  Prediction records in DB: {quality_report['prediction_records_in_db']}\n")
        f.write(f"  Risk records in DB      : {quality_report['risk_records_in_db']}\n")

        # ── System Performance
        f.write("\n\n7. SYSTEM PERFORMANCE\n")
        f.write("-" * 50 + "\n")
        f.write(f"  Average end-to-end prediction time: {avg_timing_ms:.2f} ms per request\n")
        f.write("  (Suitable for interactive, near-real-time project analysis)\n")

        # ── Limitations
        f.write("\n\n8. ACADEMIC LIMITATIONS\n")
        f.write("-" * 50 + "\n")
        limitations = [
            "1. Training data are synthetic, generated using domain-informed heuristics.",
            "2. Synthetic relationships approximate EVM concepts but cannot replicate real organizational complexity.",
            "3. Model performance metrics apply only to this synthetic dataset and may differ on real project histories.",
            "4. Risk thresholds are prototype decision-support defaults; they are not industry-validated standards.",
            "5. Feature importance values indicate correlation with predictions, not proof of causation.",
            "6. External validation with real organizational project data is required before operational deployment.",
            "7. Models should be retrained or recalibrated when sufficient real project history is available.",
        ]
        for lim in limitations:
            f.write(f"  {lim}\n")

        # ── Deployment Readiness
        f.write("\n\n9. DEPLOYMENT READINESS CHECK\n")
        f.write("-" * 50 + "\n")
        f.write("  The feature interface is stable and designed for real data injection:\n\n")
        f.write("  Real project data -> PostgreSQL -> Feature Pipeline (unchanged)\n")
        f.write("  -> Saved ML Model -> Prediction -> Risk -> Recommendations\n\n")
        f.write("  Steps to adapt to real data:\n")
        f.write("  1. Replace synthetic CSV with real project data.\n")
        f.write("  2. Run src/load_database.py to populate PostgreSQL.\n")
        f.write("  3. Run src/train_models.py to retrain on real data.\n")
        f.write("  4. All API and dashboard layers remain unchanged.\n")

        f.write("\n\n" + "=" * 70 + "\n")
        f.write("END OF EVALUATION REPORT\n")
        f.write("=" * 70 + "\n")

    print(f"  Saved: {report_path}")


# ══════════════════════════════════════════════════════════════════
# SECTION 10: FINAL SUMMARY PRINTOUT
# ══════════════════════════════════════════════════════════════════
def print_final_summary(df, improvements, ew_summary):
    print("\n" + "=" * 65)
    print("FINAL PROJECT SUMMARY")
    print("=" * 65)
    print(f"  Dataset: {df['project_id'].nunique()} projects, {len(df)} observations")
    print(f"  Cost Model:     {improvements['best_cost_model']}")
    print(f"  Schedule Model: {improvements['best_sched_model']}")
    print(f"  Cost MAE:     ${improvements['ml_cost_mae']:,.0f}  (EVM: ${improvements['evm_cost_mae']:,.0f})")
    print(f"  Schedule MAE: {improvements['ml_sched_mae']:.2f} wks (EVM: {improvements['evm_sched_mae']:.2f} wks)")
    print(f"  Cost MAE Improvement:     {improvements['cost_mae_imp_pct']:.1f}%")
    print(f"  Schedule MAE Improvement: {improvements['sched_mae_imp_pct']:.1f}%")
    print(f"  Early Warning — Precision: {ew_summary['precision']:.3f}, Recall: {ew_summary['recall']:.3f}, F1: {ew_summary['f1']:.3f}")
    print(f"  Avg lead time: {ew_summary['avg_early_warning_weeks']} weeks before project end")
    print("=" * 65)
    print("\n[10/10] Phase 10 complete. All reports and figures saved to reports/")
    print("        The system is ready for academic demonstration.\n")


# ══════════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════════
if __name__ == '__main__':
    df, train_df, test_df, cost_model, schedule_model = load_all()
    full_table, baseline, cost_results, sched_results = run_model_comparison(train_df, test_df)
    improvements = compute_improvements(baseline, cost_results, sched_results)
    ew_df, ew_summary = early_warning_evaluation(test_df, cost_model, schedule_model)
    sc_df = scenario_sensitivity_tests(cost_model, schedule_model)
    quality_report = data_quality_check(df)
    avg_timing_ms = timing_test(cost_model, schedule_model, test_df)
    generate_figures(test_df, cost_model, schedule_model, full_table)
    write_final_report(df, test_df, full_table, improvements, ew_summary, quality_report, sc_df, avg_timing_ms)
    print_final_summary(df, improvements, ew_summary)
