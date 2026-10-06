import pytest
import pandas as pd
import numpy as np
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.evm import calculate_cpi, calculate_spi, calculate_eac, calculate_evm_metrics

def test_normal_cpi():
    assert pytest.approx(calculate_cpi(100, 80)) == 1.25

def test_normal_spi():
    assert pytest.approx(calculate_spi(100, 120)) == 0.8333333333333334

def test_normal_eac():
    assert pytest.approx(calculate_eac(1000, 0.8)) == 1250.0

def test_zero_ac():
    assert calculate_cpi(100, 0) == float('inf')
    assert calculate_cpi(0, 0) == 1.0

def test_zero_pv():
    assert calculate_spi(100, 0) == float('inf')
    assert calculate_spi(0, 0) == 1.0

def test_zero_cpi():
    assert calculate_eac(1000, 0) == float('inf')

def test_known_manual_example():
    bac = 1000000
    pv = 500000
    ev = 450000
    ac = 550000
    
    cpi = calculate_cpi(ev, ac)
    spi = calculate_spi(ev, pv)
    eac = calculate_eac(bac, cpi)
    
    assert pytest.approx(cpi, 0.0001) == 0.81818
    assert pytest.approx(spi, 0.0001) == 0.90000
    assert pytest.approx(eac, 0.01) == 1222222.22

def test_dataframe_calculations():
    df = pd.DataFrame({
        'Project_ID': [1, 1, 2],
        'Week': [1, 2, 1],
        'BAC': [1000.0, 1000.0, 2000.0],
        'PV': [100.0, 200.0, 0.0],
        'EV': [90.0, 180.0, 0.0],
        'AC': [110.0, 220.0, 0.0]
    })
    
    df_out = calculate_evm_metrics(df)
    
    # Check row 1
    assert pytest.approx(df_out.loc[0, 'CPI']) == 90 / 110
    assert pytest.approx(df_out.loc[0, 'SPI']) == 90 / 100
    assert pytest.approx(df_out.loc[0, 'EAC']) == 1000 / (90 / 110)
    
    # Check row 3 (zeroes)
    assert df_out.loc[2, 'CPI'] == 1.0
    assert df_out.loc[2, 'SPI'] == 1.0
    assert df_out.loc[2, 'EAC'] == 2000.0
    
    # Validate mathematical relationships for non-zero cases
    mask = (df_out['AC'] > 0) & (df_out['PV'] > 0) & (df_out['CPI'] > 0)
    assert np.allclose(df_out.loc[mask, 'CPI'], df_out.loc[mask, 'EV'] / df_out.loc[mask, 'AC'])
    assert np.allclose(df_out.loc[mask, 'SPI'], df_out.loc[mask, 'EV'] / df_out.loc[mask, 'PV'])
    assert np.allclose(df_out.loc[mask, 'EAC'], df_out.loc[mask, 'BAC'] / df_out.loc[mask, 'CPI'])
