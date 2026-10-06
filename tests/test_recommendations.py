import pytest
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.recommendations import generate_recommendations, load_recommendation_rules

@pytest.fixture
def baseline_data():
    return {
        'Scope_Change_Percentage': 0.0,
        'Resource_Utilization': 0.8,
        'Defect_Rate': 0.01,
        'Rework_Rate': 0.01,
        'Dependency_Delays': 0,
        'Delay_Severity': 0.0,
        'CPI': 1.0,
        'SPI': 1.0,
        'Requirement_Volatility': 0.01,
        'Task_Completion_Rate': 0.1
    }

@pytest.fixture
def baseline_risk():
    return {'overall_risk': 'LOW'}

def test_no_recommendation_when_healthy(baseline_data, baseline_risk):
    recs = generate_recommendations(baseline_data, baseline_risk)
    assert len(recs) == 0

def test_high_scope_change_trigger(baseline_data, baseline_risk):
    data = baseline_data.copy()
    data['Scope_Change_Percentage'] = 0.15
    recs = generate_recommendations(data, baseline_risk)
    assert len(recs) == 1
    assert recs[0]['risk_factor'] == 'HIGH SCOPE CHANGE'
    assert recs[0]['priority'] == 'HIGH'
    assert 'change-control approval' in recs[0]['recommendation']

def test_high_resource_utilization_trigger(baseline_data, baseline_risk):
    data = baseline_data.copy()
    data['Resource_Utilization'] = 1.2
    recs = generate_recommendations(data, baseline_risk)
    assert any(r['risk_factor'] == 'HIGH RESOURCE UTILIZATION' for r in recs)

def test_high_defect_rate_trigger(baseline_data, baseline_risk):
    data = baseline_data.copy()
    data['Defect_Rate'] = 0.08
    recs = generate_recommendations(data, baseline_risk)
    assert any(r['risk_factor'] == 'HIGH DEFECT RATE' for r in recs)

def test_high_rework_rate_trigger(baseline_data, baseline_risk):
    data = baseline_data.copy()
    data['Rework_Rate'] = 0.15
    recs = generate_recommendations(data, baseline_risk)
    assert any(r['risk_factor'] == 'HIGH REWORK RATE' for r in recs)

def test_dependency_delays_trigger(baseline_data, baseline_risk):
    data = baseline_data.copy()
    data['Dependency_Delays'] = 4
    recs = generate_recommendations(data, baseline_risk)
    assert any(r['risk_factor'] == 'HIGH DEPENDENCY DELAYS' for r in recs)

def test_low_cpi_trigger(baseline_data, baseline_risk):
    data = baseline_data.copy()
    data['CPI'] = 0.8  # critical
    recs = generate_recommendations(data, baseline_risk)
    assert any(r['risk_factor'] == 'LOW CPI' and r['priority'] == 'HIGH' for r in recs)

def test_low_spi_trigger(baseline_data, baseline_risk):
    data = baseline_data.copy()
    data['SPI'] = 0.9  # warning
    recs = generate_recommendations(data, baseline_risk)
    assert any(r['risk_factor'] == 'LOW SPI' and r['priority'] == 'MEDIUM' for r in recs)

def test_multiple_factors(baseline_data, baseline_risk):
    data = baseline_data.copy()
    data['SPI'] = 0.8  # HIGH priority
    data['CPI'] = 0.9  # MEDIUM priority
    recs = generate_recommendations(data, baseline_risk)
    assert len(recs) == 2
    
def test_recommendation_priority_sorting(baseline_data, baseline_risk):
    data = baseline_data.copy()
    data['SPI'] = 0.8  # critical -> HIGH
    data['CPI'] = 0.9  # warning -> MEDIUM
    recs = generate_recommendations(data, baseline_risk)
    assert recs[0]['priority'] == 'HIGH'
    assert recs[1]['priority'] == 'MEDIUM'

def test_high_overall_risk_trigger(baseline_data):
    risk = {'overall_risk': 'HIGH'}
    recs = generate_recommendations(baseline_data, risk)
    assert any(r['risk_factor'] == 'HIGH OVERALL RISK' for r in recs)

