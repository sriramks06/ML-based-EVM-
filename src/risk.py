# Configuration Thresholds for Risk Classification
# (Percentage overrun thresholds)
COST_RISK_THRESHOLDS = {
    'LOW': 5.0,    # <= 5%
    'MEDIUM': 15.0 # > 5% and <= 15%. Above 15% is HIGH.
}

SCHEDULE_RISK_THRESHOLDS = {
    'LOW': 5.0,
    'MEDIUM': 15.0
}

def calculate_overrun_percentage(predicted, baseline):
    """Calculates the percentage difference between predicted and baseline."""
    if baseline == 0:
        return 0.0
    return ((predicted - baseline) / baseline) * 100.0

def assess_risk_level(overrun_percentage, thresholds):
    """Classifies risk into LOW, MEDIUM, or HIGH based on thresholds."""
    if overrun_percentage <= thresholds['LOW']:
        return "LOW"
    elif overrun_percentage <= thresholds['MEDIUM']:
        return "MEDIUM"
    else:
        return "HIGH"

def assess_overall_risk(cost_risk, schedule_risk):
    """
    Deterministic overall risk rule:
    - HIGH if either is HIGH
    - MEDIUM if neither is HIGH but at least one is MEDIUM
    - LOW otherwise
    """
    if cost_risk == "HIGH" or schedule_risk == "HIGH":
        return "HIGH"
    elif cost_risk == "MEDIUM" or schedule_risk == "MEDIUM":
        return "MEDIUM"
    else:
        return "LOW"

def generate_risk_assessment(predicted_cost, bac, predicted_duration, planned_duration):
    """Computes full risk profile for a prediction."""
    cost_overrun_pct = calculate_overrun_percentage(predicted_cost, bac)
    schedule_overrun_pct = calculate_overrun_percentage(predicted_duration, planned_duration)
    
    cost_risk = assess_risk_level(cost_overrun_pct, COST_RISK_THRESHOLDS)
    schedule_risk = assess_risk_level(schedule_overrun_pct, SCHEDULE_RISK_THRESHOLDS)
    
    overall_risk = assess_overall_risk(cost_risk, schedule_risk)
    
    return {
        'cost_overrun_percentage': cost_overrun_pct,
        'schedule_overrun_percentage': schedule_overrun_pct,
        'cost_risk': cost_risk,
        'schedule_risk': schedule_risk,
        'overall_risk': overall_risk
    }
