import pytest
import pandas as pd
import numpy as np
from app.etl.processors import rolling_mean

def test_rolling_mean_simple():
    """Test basic rolling mean calculation."""
    data = {'value': [1, 2, 3, 4, 5, 6]}
    df = pd.DataFrame(data)
    params = {'window_size': 3, 'columns': ['value']}
    
    result_df = rolling_mean.process(df, params)
    
    assert 'value_rolling_mean_3' in result_df.columns
    expected_means = [np.nan, 2.0, 3.0, 4.0, 5.0, np.nan] # Default center=False
    # SciPy's rolling_mean (if that's what's used) or pandas.rolling might have different defaults
    # Pandas default for rolling(window=3).mean() is right-aligned, so first two are NaN
    # If center=True, then first and last are NaN.
    # Assuming pandas default: .rolling(window=3).mean() -> [nan, nan, 2.0, 3.0, 4.0, 5.0]
    # The processor might be implementing a centered mean or a specific library.
    # The current processor in app.etl.processors.rolling_mean.py uses df[col].rolling(window=window_size, center=True, min_periods=1).mean()
    
    # Based on center=True, min_periods=1 in rolling_mean.py
    expected_means_center_true = [1.5, 2.0, 3.0, 4.0, 5.0, 5.5] 
    pd.testing.assert_series_equal(result_df['value_rolling_mean_3'], pd.Series(expected_means_center_true), check_dtype=False)

def test_rolling_mean_multiple_columns():
    """Test rolling mean on multiple specified columns."""
    data = {'col1': [1, 2, 3, 4, 5], 'col2': [10, 20, 30, 40, 50], 'text': ['a','b','c','d','e']}
    df = pd.DataFrame(data)
    params = {'window_size': 3, 'columns': ['col1', 'col2']}
    
    result_df = rolling_mean.process(df, params)
    
    assert 'col1_rolling_mean_3' in result_df.columns
    assert 'col2_rolling_mean_3' in result_df.columns
    assert 'text' in result_df.columns # Non-processed columns should remain
    
    # Expected for col1 with center=True, min_periods=1
    expected_col1_means = [1.5, 2.0, 3.0, 4.0, 4.5]
    pd.testing.assert_series_equal(result_df['col1_rolling_mean_3'], pd.Series(expected_col1_means), check_dtype=False)
    
    # Expected for col2 with center=True, min_periods=1
    expected_col2_means = [15.0, 20.0, 30.0, 40.0, 45.0]
    pd.testing.assert_series_equal(result_df['col2_rolling_mean_3'], pd.Series(expected_col2_means), check_dtype=False)

def test_rolling_mean_default_column_selection():
    """Test rolling mean when no columns are specified (defaults to all numeric)."""
    data = {'numeric1': [1, 2, 3], 'text': ['a', 'b', 'c'], 'numeric2': [10, 20, 30]}
    df = pd.DataFrame(data)
    params = {'window_size': 2} # No 'columns' specified
    
    result_df = rolling_mean.process(df, params)
    
    assert 'numeric1_rolling_mean_2' in result_df.columns
    assert 'numeric2_rolling_mean_2' in result_df.columns
    assert 'text' in result_df.columns # Non-numeric column should remain
    
    # Expected for numeric1 (center=True, min_periods=1, window=2) -> ( (1), (1+2)/2, (2+3)/2, (3) ) -> [1.0, 1.5, 2.5, 3.0]
    # Pandas rolling(2, center=True, min_periods=1) for [1,2,3] -> [1*0.5+2*0.5, 1*0.5+2*0.5, 2*0.5+3*0.5] -> [1.5, 1.5, 2.5] if we consider how it aligns
    # df[col].rolling(window=window_size, center=True, min_periods=1).mean()
    # For [1,2,3], window 2, center=True:
    # Index 0: window [1,2] -> mean 1.5. ( considers index 0 and index 1 for its window, centered at 0.5)
    # Index 1: window [1,2,3] -> mean 2.0 (if window can expand due to min_periods) OR window [2,3] -> 2.5
    # Let's trace:
    # For val 1 (idx 0): window is [1,2] (idx 0,1), centered result for idx 0. mean = 1.5
    # For val 2 (idx 1): window is [1,2,3] (idx 0,1,2) for center=True, window size 2. This is tricky.
    # Pandas .rolling(window=2, center=True) means the window is of size 2.
    # For idx 0, window is effectively [NaN, value_at_0, value_at_1, ...], label is at idx 0.
    # If center=True, the label is in the center of the window.
    # Window [1,2] -> result at index 0 for value 1 (1.5)
    # Window [2,3] -> result at index 1 for value 2 (2.5)
    # Window [3,NaN] -> result at index 2 for value 3 (3.0)
    # With min_periods=1:
    # idx 0: values [1], result 1.0. (window centered at 0, takes values from -0.5 to 0.5, effectively [0])
    # No, this is not how it works. `min_periods=1` means if window has at least 1 non-NA, compute.
    # `center=True` means the label of the window is the center.
    # For [1,2,3] window 2 center=True:
    # idx 0: val 1. Window is [0,1]. Mean(1,2) = 1.5
    # idx 1: val 2. Window is [1,2]. Mean(2,3) = 2.5
    # idx 2: val 3. Window is [2,NaN]. If it's only [3], mean is 3.
    # Let's use pandas directly to verify:
    # s = pd.Series([1,2,3])
    # s.rolling(window=2, center=True, min_periods=1).mean() -> 0: 1.5, 1: 2.5, 2: 3.0
    expected_numeric1 = [1.5, 2.5, 3.0] 
    expected_numeric2 = [15.0, 25.0, 30.0]
    pd.testing.assert_series_equal(result_df['numeric1_rolling_mean_2'], pd.Series(expected_numeric1), check_dtype=False)
    pd.testing.assert_series_equal(result_df['numeric2_rolling_mean_2'], pd.Series(expected_numeric2), check_dtype=False)


def test_rolling_mean_window_larger_than_data():
    """Test when window size is larger than the DataFrame length."""
    data = {'value': [1, 2, 3]}
    df = pd.DataFrame(data)
    params = {'window_size': 5, 'columns': ['value']}
    
    result_df = rolling_mean.process(df, params)
    assert 'value_rolling_mean_5' in result_df.columns
    # With min_periods=1 and center=True:
    # idx 0: window [1,2,3], mean(1,2,3)=2
    # idx 1: window [1,2,3], mean(1,2,3)=2
    # idx 2: window [1,2,3], mean(1,2,3)=2
    expected_means = [2.0, 2.0, 2.0]
    pd.testing.assert_series_equal(result_df['value_rolling_mean_5'], pd.Series(expected_means), check_dtype=False)

def test_rolling_mean_empty_dataframe():
    """Test with an empty DataFrame."""
    df = pd.DataFrame({'value': pd.Series(dtype='float')})
    params = {'window_size': 3, 'columns': ['value']}
    
    result_df = rolling_mean.process(df, params)
    assert 'value_rolling_mean_3' in result_df.columns
    assert len(result_df['value_rolling_mean_3']) == 0

def test_rolling_mean_non_numeric_column_specified():
    """Test when a non-numeric column is specified."""
    data = {'text': ['a', 'b', 'c'], 'value': [1,2,3]}
    df = pd.DataFrame(data)
    params = {'window_size': 2, 'columns': ['text', 'value']} # 'text' is non-numeric
    
    result_df = rolling_mean.process(df, params)
    
    assert 'text' in result_df.columns # Original non-numeric column should remain
    assert 'text_rolling_mean_2' not in result_df.columns # No rolling mean for text
    assert 'value_rolling_mean_2' in result_df.columns # Numeric column should be processed
    expected_value_means = [1.5, 2.5, 3.0]
    pd.testing.assert_series_equal(result_df['value_rolling_mean_2'], pd.Series(expected_value_means), check_dtype=False)

def test_rolling_mean_no_numeric_data_at_all():
    """Test with DataFrame containing no numeric data."""
    data = {'text1': ['a', 'b', 'c'], 'text2': ['x', 'y', 'z']}
    df = pd.DataFrame(data)
    params = {'window_size': 2} # No columns specified, should find no numeric ones
    
    result_df = rolling_mean.process(df, params)
    assert 'text1' in result_df.columns
    assert 'text2' in result_df.columns
    assert len(df.columns) == len(result_df.columns) # No new columns added

def test_rolling_mean_with_nan_values():
    """Test rolling mean with NaN values in the input."""
    data = {'value': [1, np.nan, 3, 4, np.nan, 6]}
    df = pd.DataFrame(data)
    params = {'window_size': 3, 'columns': ['value']}
    
    result_df = rolling_mean.process(df, params)
    # s = pd.Series([1, np.nan, 3, 4, np.nan, 6])
    # s.rolling(window=3, center=True, min_periods=1).mean()
    # idx 0: [1, nan] -> 1.0
    # idx 1: [1, nan, 3] -> 2.0
    # idx 2: [nan, 3, 4] -> 3.5
    # idx 3: [3, 4, nan] -> 3.5
    # idx 4: [4, nan, 6] -> 5.0
    # idx 5: [nan, 6] -> 6.0
    expected_means = [1.0, 2.0, 3.5, 3.5, 5.0, 6.0]
    pd.testing.assert_series_equal(result_df['value_rolling_mean_3'], pd.Series(expected_means), check_dtype=False)

def test_rolling_mean_invalid_window_size():
    """Test with invalid window size (e.g., less than 1). Processor should handle it."""
    data = {'value': [1, 2, 3, 4, 5]}
    df = pd.DataFrame(data)
    params = {'window_size': 0, 'columns': ['value']} 
    
    # The pandas rolling window must be > 0.
    # The processor code has: window_size = max(1, int(params.get("window_size", 1)))
    # So, window_size 0 becomes 1.
    # rolling(window=1) means each value is its own mean.
    result_df = rolling_mean.process(df, params)
    expected_means = [1.0, 2.0, 3.0, 4.0, 5.0]
    pd.testing.assert_series_equal(result_df['value_rolling_mean_1'], pd.Series(expected_means), check_dtype=False)

    params_negative = {'window_size': -2, 'columns': ['value']}
    result_df_neg = rolling_mean.process(df, params_negative)
    pd.testing.assert_series_equal(result_df_neg['value_rolling_mean_1'], pd.Series(expected_means), check_dtype=False)

def test_rolling_mean_column_not_found_graceful():
    """Test when specified column is not found, should process other valid columns or do nothing."""
    data = {'col1': [1,2,3], 'col2': [4,5,6]}
    df = pd.DataFrame(data)
    params = {'window_size': 2, 'columns': ['col_not_exist', 'col1']}
    result_df = rolling_mean.process(df, params)

    assert 'col_not_exist_rolling_mean_2' not in result_df.columns
    assert 'col1_rolling_mean_2' in result_df.columns
    expected_col1_means = [1.5, 2.5, 3.0]
    pd.testing.assert_series_equal(result_df['col1_rolling_mean_2'], pd.Series(expected_col1_means), check_dtype=False)
    assert 'col2' in result_df.columns and 'col2_rolling_mean_2' not in result_df.columns # col2 not specified

# Test if original DataFrame is not modified
def test_rolling_mean_original_df_unmodified():
    data = {'value': [1, 2, 3, 4, 5]}
    df_original = pd.DataFrame(data)
    df_copy = df_original.copy() # Keep a copy for comparison
    params = {'window_size': 3, 'columns': ['value']}
    
    rolling_mean.process(df_original, params) # Process the original df
    
    # Check if df_original is still the same as df_copy
    pd.testing.assert_frame_equal(df_original, df_copy)
