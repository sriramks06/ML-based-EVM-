import pandas as pd
import numpy as np
import os

def calculate_cpi(ev, ac):
    if isinstance(ev, pd.Series):
        return np.where(ac == 0, np.where(ev == 0, 1.0, float('inf')), ev / ac)
    else:
        if ac == 0:
            return 1.0 if ev == 0 else float('inf')
        return ev / ac

def calculate_spi(ev, pv):
    if isinstance(ev, pd.Series):
        return np.where(pv == 0, np.where(ev == 0, 1.0, float('inf')), ev / pv)
    else:
        if pv == 0:
            return 1.0 if ev == 0 else float('inf')
        return ev / pv

def calculate_eac(bac, cpi):
    if isinstance(bac, pd.Series):
        return np.where(cpi == 0, float('inf'), bac / cpi)
    else:
        if cpi == 0:
            return float('inf')
        return bac / cpi

def calculate_tcpi(bac, ev, ac):
    # TCPI = (BAC - EV) / (BAC - AC)
    if isinstance(bac, pd.Series):
        return np.where((bac - ac) == 0, float('inf'), (bac - ev) / (bac - ac))
    else:
        if (bac - ac) == 0:
            return float('inf')
        return (bac - ev) / (bac - ac)

def calculate_evm_metrics(df):
    df_out = df.copy()
    df_out['CPI'] = calculate_cpi(df_out['EV'], df_out['AC'])
    df_out['SPI'] = calculate_spi(df_out['EV'], df_out['PV'])
    df_out['EAC'] = calculate_eac(df_out['BAC'], df_out['CPI'])
    df_out['TCPI'] = calculate_tcpi(df_out['BAC'], df_out['EV'], df_out['AC'])
    return df_out

def interpret_cpi(cpi):
    if cpi > 1.0:
        return 'under budget / favorable'
    elif cpi < 1.0:
        return 'over budget / unfavorable'
    else:
        return 'on budget'

def interpret_spi(spi):
    if spi > 1.0:
        return 'ahead of schedule / favorable'
    elif spi < 1.0:
        return 'behind schedule / unfavorable'
    else:
        return 'on schedule'
        
if __name__ == "__main__":
    os.makedirs('data/processed', exist_ok=True)
    
    input_path = 'data/raw/project_data.csv'
    output_path = 'data/processed/evm_dataset.csv'
    
    df = pd.read_csv(input_path)
    df_evm = calculate_evm_metrics(df)
    df_evm.to_csv(output_path, index=False)
    
    print(f"Processed {len(df_evm)} rows.")
    print("First 5 rows (selected columns):")
    cols = ['Project_ID', 'Week', 'PV', 'EV', 'AC', 'CPI', 'SPI', 'EAC']
    print(df_evm[cols].head(5).to_string())
