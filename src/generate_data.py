import os
import numpy as np
import pandas as pd

def generate_data(num_projects=150, seed=42):
    np.random.seed(seed)
    
    data = []
    
    for pid in range(1, num_projects + 1):
        planned_duration = np.random.randint(20, 31)
        bac = np.random.uniform(100000, 1000000)
        
        team_experience = np.random.uniform(1, 10)
        task_complexity = np.random.uniform(1, 10)
        
        # Risk profiles - probability influenced by complexity and experience
        risk_prob = 0.4 + (task_complexity - 5.0) * 0.04 - (team_experience - 5.0) * 0.04
        risk_prob = np.clip(risk_prob, 0.1, 0.9)
        is_risky = np.random.rand() < risk_prob
        
        has_cost_risk = is_risky and np.random.rand() < 0.7
        has_schedule_risk = is_risky and np.random.rand() < 0.7
        if is_risky and not has_cost_risk and not has_schedule_risk:
            has_cost_risk = True # Ensure at least one if risky
        
        week = 1
        project_completion = 0.0
        
        ac_cumulative = 0.0
        ev_cumulative = 0.0
        
        # Initial conditions
        req_volatility = np.random.uniform(0, 0.05)
        change_requests = 0
        scope_change_pct = 0.0
        resource_utilization = np.random.uniform(0.7, 0.9)
        defect_rate = np.random.uniform(0, 0.02)
        rework_rate = np.random.uniform(0, 0.02)
        dependency_delays = 0
        delay_severity = 0.0
        
        project_rows = []
        
        while project_completion < 1.0 and week < 100: # cap at 100 weeks to avoid infinite loop
            # Drift for risky projects (with added stochastic noise)
            if has_cost_risk:
                resource_utilization += max(0, np.random.normal(0.015, 0.02))
                defect_rate += max(0, np.random.normal(0.003, 0.005))
                rework_rate += max(0, np.random.normal(0.003, 0.005))
                req_volatility += max(0, np.random.normal(0.003, 0.005))
                
            if has_schedule_risk:
                if np.random.rand() < 0.15:
                    change_requests += np.random.poisson(0.5)
                    scope_change_pct += np.random.uniform(0.0, 0.04)
                if np.random.rand() < 0.15:
                    dependency_delays += np.random.poisson(0.5)
                    delay_severity += np.random.uniform(0.0, 0.08)
            
            # Clip variables to reasonable limits
            resource_utilization = min(resource_utilization, 2.0)
            defect_rate = min(defect_rate, 1.0)
            rework_rate = min(rework_rate, 1.0)
            req_volatility = min(req_volatility, 1.0)
            scope_change_pct = min(scope_change_pct, 1.0)
            delay_severity = min(delay_severity, 1.0)
            
            # Compute SPI and CPI based on features
            # Introduce non-linear interaction with complexity/experience
            complexity_factor = 1.0 + (task_complexity - 5.0) * 0.05
            experience_factor = max(0.5, 1.0 - (team_experience - 5.0) * 0.05)
            
            # Base penalties (reduced determinism)
            spi_penalty = (change_requests * 0.03 + scope_change_pct * 0.6 + 
                           dependency_delays * 0.06 + delay_severity * 0.3) * complexity_factor * experience_factor
            
            cpi_penalty = (max(0, resource_utilization - 1.0) * 0.6 + 
                           defect_rate * 3.0 + rework_rate * 3.0 + 
                           req_volatility * 0.6) * complexity_factor * experience_factor
            
            # Add direct effects of complexity and experience
            spi_penalty += (task_complexity - 5.0) * 0.015 - (team_experience - 5.0) * 0.015
            cpi_penalty += (task_complexity - 5.0) * 0.015 - (team_experience - 5.0) * 0.015
            
            # Add an optimistic baseline (1.1) so stable projects finish under-budget
            # Increased random noise to prevent near-perfect correlations
            spi = max(0.1, 1.1 - spi_penalty + np.random.normal(0, 0.08))
            cpi = max(0.1, 1.1 - cpi_penalty + np.random.normal(0, 0.08))
            
            # Progress calculation
            base_completion_rate = 1.0 / planned_duration
            task_completion_rate = base_completion_rate * spi
            task_completion_rate = max(0.001, task_completion_rate) # Ensure it always moves forward
            
            project_completion += task_completion_rate
            project_completion = min(1.0, project_completion)
            
            # EVM core values
            pv = min(bac, bac * (week / planned_duration))
            ev = bac * project_completion
            
            # AC is determined by the work actually done (EV added) and how efficiently it was done (CPI)
            ev_added = ev - ev_cumulative
            ac_added = ev_added / cpi
            
            ac_cumulative += ac_added
            ev_cumulative = ev
            
            row = {
                'Project_ID': pid,
                'Week': week,
                'Planned_Duration': planned_duration,
                'BAC': bac,
                'PV': pv,
                'EV': ev,
                'AC': ac_cumulative,
                'Requirement_Volatility': req_volatility,
                'Change_Requests': change_requests,
                'Scope_Change_Percentage': scope_change_pct,
                'Task_Completion_Rate': task_completion_rate,
                'Resource_Utilization': resource_utilization,
                'Team_Experience': team_experience,
                'Task_Complexity': task_complexity,
                'Defect_Rate': defect_rate,
                'Rework_Rate': rework_rate,
                'Dependency_Delays': dependency_delays,
                'Delay_Severity': delay_severity,
                'Project_Completion_Percentage': project_completion,
                'Risk_Profile': 'Both' if (has_cost_risk and has_schedule_risk) else ('Cost' if has_cost_risk else ('Schedule' if has_schedule_risk else 'Stable'))
            }
            project_rows.append(row)
            week += 1
            
        # At the end of the project, backfill Final Cost and Final Duration
        final_cost = ac_cumulative
        final_duration = week - 1
        
        for r in project_rows:
            r['Final_Cost'] = final_cost
            r['Final_Duration'] = final_duration
            
        data.extend(project_rows)
        
    df = pd.DataFrame(data)
    return df

def validate_data(df):
    errors = []
    
    # 1. No negative cost values
    if (df['AC'] < 0).any() or (df['Final_Cost'] < 0).any():
        errors.append("Negative cost values found.")
        
    # 2. Percentages in reasonable ranges
    pct_cols = ['Requirement_Volatility', 'Scope_Change_Percentage', 'Task_Completion_Rate', 
                'Defect_Rate', 'Rework_Rate', 'Project_Completion_Percentage']
    for col in pct_cols:
        if (df[col] < 0).any():
            errors.append(f"{col} has negative values.")
        if col == 'Project_Completion_Percentage' and (df[col] > 1.01).any():
            errors.append(f"{col} out of range [0, 1]. Max is {df[col].max()}")
            
    # 3. Resource utilization realistic
    if (df['Resource_Utilization'] < 0).any() or (df['Resource_Utilization'] > 3.0).any():
        errors.append("Resource Utilization outside [0, 3.0].")
        
    # 4. Multiple weeks per project
    weeks_per_project = df.groupby('Project_ID').size()
    if (weeks_per_project < 2).any():
        errors.append("Some projects have less than 2 weeks.")
        
    # 5. Project completion generally increases
    for pid, group in df.groupby('Project_ID'):
        if not group['Project_Completion_Percentage'].is_monotonic_increasing:
            errors.append(f"Project_Completion_Percentage not monotonic increasing for Project {pid}.")
            break
            
    # 6. PV follows schedule
    for pid, group in df.groupby('Project_ID'):
        if not group['PV'].is_monotonic_increasing:
            errors.append(f"PV not monotonic increasing for Project {pid}.")
            break
            
    # 7. Final_Cost is constant per project
    if df.groupby('Project_ID')['Final_Cost'].nunique().max() > 1:
        errors.append("Final_Cost is not constant per project.")
        
    # 8. Final_Duration is constant per project
    if df.groupby('Project_ID')['Final_Duration'].nunique().max() > 1:
        errors.append("Final_Duration is not constant per project.")
        
    # 9. Riskier projects generally have worse final outcomes
    cpi_stable = (df[df['Risk_Profile'] == 'Stable'].groupby('Project_ID').last()['BAC'] / df[df['Risk_Profile'] == 'Stable'].groupby('Project_ID').last()['Final_Cost']).mean()
    cpi_risky = (df[df['Risk_Profile'].isin(['Cost', 'Both'])].groupby('Project_ID').last()['BAC'] / df[df['Risk_Profile'].isin(['Cost', 'Both'])].groupby('Project_ID').last()['Final_Cost']).mean()
    
    if cpi_risky > cpi_stable:
         errors.append("Cost Risk projects do not have worse outcomes on average than Stable projects.")
         
    # 10. Both successful and unsuccessful projects
    cpis = df.groupby('Project_ID').last()['BAC'] / df.groupby('Project_ID').last()['Final_Cost']
    if not ((cpis > 1.05).any() and (cpis < 0.95).any()):
        errors.append("Dataset does not contain both under-budget and over-budget projects.")
        
    return errors

if __name__ == "__main__":
    os.makedirs('data/raw', exist_ok=True)
    df = generate_data(num_projects=150)
    df.to_csv('data/raw/project_data.csv', index=False)
    
    errors = validate_data(df)
    if errors:
        print("Validation FAILURES:")
        for e in errors:
            print(f"- {e}")
    else:
        print("Validation PASSED!")
        
    print("\nDataset Statistics:")
    print(f"Number of projects: {df['Project_ID'].nunique()}")
    print(f"Number of rows: {len(df)}")
    print(f"Number of columns: {len(df.columns)}")
    print(f"Dataset shape: {df.shape}")
    
    print("\nFirst 10 rows:")
    print(df.head(10).to_string())
    
    print("\nDescriptive statistics:")
    print(df.describe().to_string())
    
    print("\nDistribution of project risk types (by row):")
    print(df['Risk_Profile'].value_counts().to_string())
    
    print("\nDistribution of project risk types (by project):")
    print(df.groupby('Project_ID')['Risk_Profile'].first().value_counts().to_string())
    
    print("\nCorrelations with Target Variables (normalized by BAC / Planned_Duration):")
    corr_cols = ['Requirement_Volatility', 'Change_Requests', 'Scope_Change_Percentage',
                 'Resource_Utilization', 'Team_Experience', 'Task_Complexity', 'Defect_Rate',
                 'Rework_Rate', 'Dependency_Delays', 'Delay_Severity']
                 
    # Take the final row of each project for correlation to avoid week-by-week confounding
    final_rows = df.groupby('Project_ID').last().copy()
    final_rows['Cost_Overrun_Ratio'] = final_rows['Final_Cost'] / final_rows['BAC']
    final_rows['Schedule_Overrun_Ratio'] = final_rows['Final_Duration'] / final_rows['Planned_Duration']
    
    print("\nCorrelation with Cost_Overrun_Ratio (Final_Cost / BAC):")
    print("(Positive values indicate the factor increases cost overruns)")
    cost_corrs = {col: final_rows[col].corr(final_rows['Cost_Overrun_Ratio']) for col in corr_cols}
    for col, corr in cost_corrs.items():
        print(f"  {col}: {corr:.4f}")
        
    print("\nTop 5 Strongest Correlations with Cost Overrun:")
    for col, corr in sorted(cost_corrs.items(), key=lambda item: abs(item[1]), reverse=True)[:5]:
        print(f"  {col}: {corr:.4f}")
        
    print("\nCorrelation with Schedule_Overrun_Ratio (Final_Duration / Planned_Duration):")
    print("(Positive values indicate the factor increases schedule delays)")
    sched_corrs = {col: final_rows[col].corr(final_rows['Schedule_Overrun_Ratio']) for col in corr_cols}
    for col, corr in sched_corrs.items():
        print(f"  {col}: {corr:.4f}")
        
    print("\nTop 5 Strongest Correlations with Schedule Overrun:")
    for col, corr in sorted(sched_corrs.items(), key=lambda item: abs(item[1]), reverse=True)[:5]:
        print(f"  {col}: {corr:.4f}")
