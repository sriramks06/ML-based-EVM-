import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from src.database import Recommendation

# Configurable prototype thresholds for decision support
THRESHOLDS = {
    'scope_change': {
        'high': 0.10,
        'medium': 0.05
    },
    'resource_utilization': {
        'high': 1.10,
        'medium': 0.95
    },
    'defect_rate': {
        'high': 0.06,
        'medium': 0.03
    },
    'rework_rate': {
        'high': 0.10,
        'medium': 0.05
    },
    'dependency_delays': {
        'high': 3,
        'medium': 1
    },
    'cpi': {
        'warning': 0.95,
        'critical': 0.85
    },
    'spi': {
        'warning': 0.95,
        'critical': 0.85
    },
    'requirement_volatility': {
        'high': 0.15,
        'medium': 0.08
    },
    'task_completion_rate': {
        'warning': 0.05,
        'critical': 0.02
    },
    'delay_severity': {
        'high': 0.3,
        'medium': 0.1
    }
}

def load_recommendation_rules():
    """Returns the rule definitions and thresholds."""
    return THRESHOLDS

def evaluate_risk_factors(project_data, risk_assessment):
    """
    Evaluates raw project data and computed risk assessment against configurable thresholds.
    Returns a list of dicts with triggered rules.
    """
    rules = load_recommendation_rules()
    triggered = []

    # Scope Change
    scope = project_data.get('Scope_Change_Percentage', 0)
    if scope > rules['scope_change']['high']:
        triggered.append({
            'risk_factor': 'HIGH SCOPE CHANGE',
            'priority': 'HIGH',
            'triggered_value': scope,
            'threshold': rules['scope_change']['high'],
            'explanation': 'Scope change is above the critical threshold.',
            'recommendation': 'Review and control additional scope. Consider change-control approval before accepting further requirements.'
        })
        
    # Resource Utilization
    utilization = project_data.get('Resource_Utilization', 0)
    if utilization > rules['resource_utilization']['high']:
        triggered.append({
            'risk_factor': 'HIGH RESOURCE UTILIZATION',
            'priority': 'HIGH',
            'triggered_value': utilization,
            'threshold': rules['resource_utilization']['high'],
            'explanation': 'Resource utilization is critically excessive.',
            'recommendation': 'Rebalance workload across available resources. Consider adding or reallocating resources.'
        })

    # Defect Rate
    defect = project_data.get('Defect_Rate', 0)
    if defect > rules['defect_rate']['high']:
        triggered.append({
            'risk_factor': 'HIGH DEFECT RATE',
            'priority': 'HIGH',
            'triggered_value': defect,
            'threshold': rules['defect_rate']['high'],
            'explanation': 'Defect rate is critically high.',
            'recommendation': 'Strengthen quality assurance and testing. Investigate recurring defect sources.'
        })

    # Rework Rate
    rework = project_data.get('Rework_Rate', 0)
    if rework > rules['rework_rate']['high']:
        triggered.append({
            'risk_factor': 'HIGH REWORK RATE',
            'priority': 'HIGH',
            'triggered_value': rework,
            'threshold': rules['rework_rate']['high'],
            'explanation': 'Rework rate is critically high.',
            'recommendation': 'Perform root-cause analysis on repeated work. Improve review and quality-control activities.'
        })

    # Dependency Delays
    delays = project_data.get('Dependency_Delays', 0)
    if delays > rules['dependency_delays']['high']:
        triggered.append({
            'risk_factor': 'HIGH DEPENDENCY DELAYS',
            'priority': 'HIGH',
            'triggered_value': delays,
            'threshold': rules['dependency_delays']['high'],
            'explanation': 'Multiple dependencies are delayed.',
            'recommendation': 'Escalate delayed dependencies. Establish revised dependency commitments.'
        })
        
    # Delay Severity
    severity = project_data.get('Delay_Severity', 0)
    if severity > rules['delay_severity']['high']:
        triggered.append({
            'risk_factor': 'HIGH DELAY SEVERITY',
            'priority': 'HIGH',
            'triggered_value': severity,
            'threshold': rules['delay_severity']['high'],
            'explanation': 'Delay severity indicates critical path impact.',
            'recommendation': 'Reassess the project schedule and critical activities. Prioritize delayed tasks.'
        })

    # CPI
    cpi = project_data.get('CPI', 1.0)
    if cpi < rules['cpi']['critical']:
        triggered.append({
            'risk_factor': 'LOW CPI',
            'priority': 'HIGH',
            'triggered_value': cpi,
            'threshold': rules['cpi']['critical'],
            'explanation': 'Cost Performance Index is critically low.',
            'recommendation': 'Review cost drivers and resource consumption. Investigate activities contributing to cost inefficiency.'
        })
    elif cpi < rules['cpi']['warning']:
        triggered.append({
            'risk_factor': 'LOW CPI',
            'priority': 'MEDIUM',
            'triggered_value': cpi,
            'threshold': rules['cpi']['warning'],
            'explanation': 'Cost Performance Index is below the warning threshold.',
            'recommendation': 'Monitor cost drivers and resource consumption.'
        })

    # SPI
    spi = project_data.get('SPI', 1.0)
    if spi < rules['spi']['critical']:
        triggered.append({
            'risk_factor': 'LOW SPI',
            'priority': 'HIGH',
            'triggered_value': spi,
            'threshold': rules['spi']['critical'],
            'explanation': 'Schedule Performance Index is critically low.',
            'recommendation': 'Review schedule performance and delayed work. Reassess critical-path activities.'
        })
    elif spi < rules['spi']['warning']:
        triggered.append({
            'risk_factor': 'LOW SPI',
            'priority': 'MEDIUM',
            'triggered_value': spi,
            'threshold': rules['spi']['warning'],
            'explanation': 'Schedule Performance Index is below the warning threshold.',
            'recommendation': 'Review delayed activities and critical-path tasks.'
        })

    # Requirement Volatility
    req_vol = project_data.get('Requirement_Volatility', 0)
    if req_vol > rules['requirement_volatility']['high']:
        triggered.append({
            'risk_factor': 'HIGH REQUIREMENT VOLATILITY',
            'priority': 'HIGH',
            'triggered_value': req_vol,
            'threshold': rules['requirement_volatility']['high'],
            'explanation': 'Requirements are changing rapidly.',
            'recommendation': 'Establish stronger requirements/change control. Prioritize and baseline requirements.'
        })

    # Task Completion Rate
    completion_rate = project_data.get('Task_Completion_Rate', 1.0)
    if completion_rate < rules['task_completion_rate']['critical']:
        triggered.append({
            'risk_factor': 'LOW TASK COMPLETION RATE',
            'priority': 'HIGH',
            'triggered_value': completion_rate,
            'threshold': rules['task_completion_rate']['critical'],
            'explanation': 'Tasks are not being completed at the expected rate.',
            'recommendation': 'Reassess workload and task allocation. Identify blocked or underperforming activities.'
        })

    # Overall Risk (from ML risk assessment module)
    overall_risk = risk_assessment.get('overall_risk', 'LOW')
    if overall_risk == 'HIGH':
        triggered.append({
            'risk_factor': 'HIGH OVERALL RISK',
            'priority': 'HIGH',
            'triggered_value': 1,
            'threshold': 1,
            'explanation': 'Aggregated risk factors forecast a high probability of significant overrun.',
            'recommendation': 'Conduct a project-level risk review. Revisit cost and schedule assumptions.'
        })

    return triggered

def sort_recommendations(recommendations):
    """Sorts recommendations based on priority (HIGH -> MEDIUM -> LOW)."""
    priority_map = {'HIGH': 1, 'MEDIUM': 2, 'LOW': 3}
    return sorted(recommendations, key=lambda x: priority_map.get(x['priority'], 4))

def generate_recommendations(project_data, risk_assessment):
    """Main entrypoint to generate and sort recommendations."""
    triggered = evaluate_risk_factors(project_data, risk_assessment)
    sorted_recs = sort_recommendations(triggered)
    return sorted_recs

def save_recommendations(session, project_id, week, recommendations):
    """Saves generated recommendations to the PostgreSQL database, avoiding duplicates."""
    try:
        # Delete existing recommendations for this project-week to prevent duplicates on rerun
        session.query(Recommendation).filter_by(project_id=project_id, week=week).delete()
        
        for rec in recommendations:
            db_rec = Recommendation(
                project_id=project_id,
                week=week,
                risk_factor=rec['risk_factor'],
                recommendation=rec['recommendation'],
                priority=rec['priority']
            )
            session.add(db_rec)
        
        session.commit()
        return True
    except Exception as e:
        session.rollback()
        print(f"Failed to save recommendations: {e}")
        return False
