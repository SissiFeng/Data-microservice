import pytest
import pandas as pd
import numpy as np
from app.etl.processors import data_quality

def test_data_quality_basic_stats():
    """Test basic statistics calculation."""
    data = {'col1': [1, 2, 3, 4, 5], 'col2': [np.nan, 10, 20, 30, 40]}
    df = pd.DataFrame(data)
    params = {} # No specific parameters for this processor usually
    
    metrics = data_quality.process(df, params)
    
    assert 'col1' in metrics
    assert 'col2' in metrics
    
    # Test col1 metrics
    assert metrics['col1']['missing_values'] == 0
    assert metrics['col1']['missing_percentage'] == 0.0
    assert metrics['col1']['unique_values'] == 5
    assert metrics['col1']['mean'] == 3.0
    assert metrics['col1']['median'] == 3.0
    assert metrics['col1']['std_dev'] == pytest.approx(np.std([1,2,3,4,5])) # np.std for population std
    assert metrics['col1']['min_value'] == 1
    assert metrics['col1']['max_value'] == 5
    
    # Test col2 metrics
    assert metrics['col2']['missing_values'] == 1
    assert metrics['col2']['missing_percentage'] == 20.0 # 1 out of 5
    assert metrics['col2']['unique_values'] == 4 # 10, 20, 30, 40
    assert metrics['col2']['mean'] == np.mean([10,20,30,40]) # Mean of non-NaN
    assert metrics['col2']['median'] == np.median([10,20,30,40]) # Median of non-NaN

def test_data_quality_all_nan_column():
    """Test a column with all NaN values."""
    data = {'col1': [1, 2, 3], 'all_nan': [np.nan, np.nan, np.nan]}
    df = pd.DataFrame(data)
    params = {}
    
    metrics = data_quality.process(df, params)
    
    assert 'all_nan' in metrics
    assert metrics['all_nan']['missing_values'] == 3
    assert metrics['all_nan']['missing_percentage'] == 100.0
    assert metrics['all_nan']['unique_values'] == 0
    assert np.isnan(metrics['all_nan']['mean']) # Check for NaN, not a specific value
    assert np.isnan(metrics['all_nan']['median'])
    assert np.isnan(metrics['all_nan']['std_dev'])
    assert np.isnan(metrics['all_nan']['min_value'])
    assert np.isnan(metrics['all_nan']['max_value'])

def test_data_quality_non_numeric_column():
    """Test a non-numeric column."""
    data = {'text_col': ['apple', 'banana', 'apple', 'orange'], 'numeric_col': [1,2,3,4]}
    df = pd.DataFrame(data)
    params = {}
    
    metrics = data_quality.process(df, params)
    
    assert 'text_col' in metrics
    assert metrics['text_col']['missing_values'] == 0
    assert metrics['text_col']['unique_values'] == 3 # apple, banana, orange
    assert metrics['text_col']['most_frequent'] == 'apple' # Based on current processor logic
    # Numeric stats should not be present for non-numeric columns, or be NaN/None
    assert 'mean' not in metrics['text_col'] or np.isnan(metrics['text_col']['mean'])
    
    assert 'numeric_col' in metrics # Ensure numeric col is still processed

def test_data_quality_empty_dataframe():
    """Test with an empty DataFrame."""
    df = pd.DataFrame()
    params = {}
    
    metrics = data_quality.process(df, params)
    assert len(metrics) == 0 # No columns to process

def test_data_quality_with_duplicate_rows():
    """Test if duplicate row count is calculated (if processor supports it)."""
    # The current data_quality processor focuses on per-column stats,
    # not general DataFrame stats like duplicate rows.
    # This test can be adapted if that functionality is added.
    data = {'col1': [1, 1, 2, 3], 'col2': ['a', 'a', 'b', 'c']}
    df = pd.DataFrame(data)
    params = {}
    
    metrics = data_quality.process(df, params)
    
    # Example: if duplicate_rows metric was added to the top level of returned dict:
    # assert 'duplicate_rows' in metrics
    # assert metrics['duplicate_rows'] == 1 
    # For now, just ensure it processes columns correctly
    assert 'col1' in metrics
    assert metrics['col1']['unique_values'] == 3

def test_data_quality_specific_column_selection():
    """Test when 'columns' parameter is used."""
    data = {'col1': [1,2,3], 'col2': [10,20,30], 'col3': ['a','b','c']}
    df = pd.DataFrame(data)
    params = {'columns': ['col1', 'col3']} # Only process these
    
    metrics = data_quality.process(df, params)
    
    assert 'col1' in metrics
    assert 'col3' in metrics
    assert 'col2' not in metrics # col2 should not be processed

def test_data_quality_numeric_column_as_object():
    """Test a numeric column that is of object dtype (e.g., read as string)."""
    data = {'num_as_object': ['1', '2', '3', '2', '1', np.nan, '5']}
    df = pd.DataFrame(data)
    params = {}
    
    metrics = data_quality.process(df, params)
    
    assert 'num_as_object' in metrics
    # The processor attempts to convert to numeric.
    # '1', '2', '3', '2', '1', np.nan, '5' -> 1,2,3,2,1,nan,5
    assert metrics['num_as_object']['missing_values'] == 1
    assert metrics['num_as_object']['unique_values'] == 4 # 1, 2, 3, 5
    assert metrics['num_as_object']['mean'] == pytest.approx((1+2+3+2+1+5)/6)
    
    # Check if it correctly identifies it as numeric after conversion attempt
    assert metrics['num_as_object']['data_type_original'] == 'object'
    assert metrics['num_as_object']['data_type_inferred'] == 'float64' # or int64 if no NaNs after conversion

def test_data_quality_mixed_type_object_column():
    """Test an object column with truly mixed types that cannot be fully numeric."""
    data = {'mixed_col': ['1', 'apple', '3.0', 'banana', '5']}
    df = pd.DataFrame(data)
    params = {}
    
    metrics = data_quality.process(df, params)
    
    assert 'mixed_col' in metrics
    # After attempting conversion, 'apple' and 'banana' would remain as non-numeric.
    # The processor's to_numeric(errors='coerce') would turn them into NaN.
    # So, '1', NaN, '3.0', NaN, '5' -> 1, NaN, 3, NaN, 5
    assert metrics['mixed_col']['missing_values'] == 2 # apple, banana become NaN
    assert metrics['mixed_col']['unique_values'] == 3 # 1, 3, 5 (after coercion)
    assert metrics['mixed_col']['data_type_original'] == 'object'
    assert metrics['mixed_col']['data_type_inferred'] == 'float64' # Due to NaNs
    assert metrics['mixed_col']['mean'] == pytest.approx((1+3+5)/3)
    assert 'most_frequent' not in metrics['mixed_col'] # Should be treated as numeric after coercion for stats part

# Ensure that the global 'row_count' is present in the output.
def test_data_quality_global_row_count():
    data = {'col1': [1, 2, 3], 'col2': [4, 5, 6]}
    df = pd.DataFrame(data)
    params = {}
    
    metrics = data_quality.process(df, params)
    
    assert 'overall_summary' in metrics
    assert metrics['overall_summary']['row_count'] == 3
    assert metrics['overall_summary']['column_count'] == 2
