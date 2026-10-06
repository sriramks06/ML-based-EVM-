import pytest
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.risk import (
    calculate_overrun_percentage, assess_risk_level, 
    assess_overall_risk, generate_risk_assessment,
    COST_RISK_THRESHOLDS
)

def test_overrun_calculation():
    # 20% overrun
    assert calculate_overrun_percentage(120, 100) == 20.0
    # On budget
    assert calculate_overrun_percentage(100, 100) == 0.0
    # Under budget
    assert calculate_overrun_percentage(80, 100) == -20.0
    # Zero baseline defense
    assert calculate_overrun_percentage(100, 0) == 0.0

def test_risk_level_classification():
    # LOW (<= 5)
    assert assess_risk_level(-10.0, COST_RISK_THRESHOLDS) == "LOW"
    assert assess_risk_level(0.0, COST_RISK_THRESHOLDS) == "LOW"
    assert assess_risk_level(5.0, COST_RISK_THRESHOLDS) == "LOW"
    
    # MEDIUM (> 5 and <= 15)
    assert assess_risk_level(5.1, COST_RISK_THRESHOLDS) == "MEDIUM"
    assert assess_risk_level(15.0, COST_RISK_THRESHOLDS) == "MEDIUM"
    
    # HIGH (> 15)
    assert assess_risk_level(15.1, COST_RISK_THRESHOLDS) == "HIGH"
    assert assess_risk_level(50.0, COST_RISK_THRESHOLDS) == "HIGH"

def test_overall_risk_rule():
    # High if either is high
    assert assess_overall_risk("HIGH", "LOW") == "HIGH"
    assert assess_overall_risk("LOW", "HIGH") == "HIGH"
    assert assess_overall_risk("HIGH", "HIGH") == "HIGH"
    
    # Medium if neither high but one is medium
    assert assess_overall_risk("MEDIUM", "LOW") == "MEDIUM"
    assert assess_overall_risk("LOW", "MEDIUM") == "MEDIUM"
    assert assess_overall_risk("MEDIUM", "MEDIUM") == "MEDIUM"
    
    # Low otherwise
    assert assess_overall_risk("LOW", "LOW") == "LOW"

def test_full_risk_assessment():
    res = generate_risk_assessment(
        predicted_cost=110, bac=100,           # 10% overrun -> MEDIUM
        predicted_duration=120, planned_duration=100 # 20% overrun -> HIGH
    )
    
    assert res['cost_overrun_percentage'] == 10.0
    assert res['schedule_overrun_percentage'] == 20.0
    assert res['cost_risk'] == "MEDIUM"
    assert res['schedule_risk'] == "HIGH"
    assert res['overall_risk'] == "HIGH"
