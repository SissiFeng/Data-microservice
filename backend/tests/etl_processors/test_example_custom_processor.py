import pytest
import pandas as pd
import numpy as np
from app.etl.processors.custom import example_custom_processor

def test_custom_processor_basic_run():
    """Test basic execution without specific calculation parameters."""
    data = {'col_a': [1, 2, 3], 'col_b': [4, 5, 6]}
    df = pd.DataFrame(data)
    params = {} # No target_column or multiplier
    
    result = example_custom_processor.process(df, params)
    
    assert result["message"] == "Example custom processor executed successfully."
    assert result["input_rows"] == 3
    assert result["input_cols"] == 2
    assert "info" in result
    assert result["info"] == "No target_column specified in parameters for custom calculation."
    assert "error" not in result
    assert "custom_calculation_details" not in result

def test_custom_processor_with_valid_target_column_and_multiplier():
    """Test with a valid target column and multiplier."""
    data = {'col_a': [10, 20, 30], 'col_b': ['x', 'y', 'z']}
    df = pd.DataFrame(data)
    params = {'target_column': 'col_a', 'multiplier': 2.5}
    
    result = example_custom_processor.process(df, params)
    
    assert result["message"] == "Example custom processor executed successfully."
    assert result["input_rows"] == 3
    assert result["input_cols"] == 2
    assert "custom_calculation_details" in result
    details = result["custom_calculation_details"]
    assert details["target_column"] == 'col_a'
    assert details["multiplier_used"] == 2.5
    assert details["new_column_name_preview"] == 'col_a_multiplied_by_2.5'
    
    expected_sample = {'0': 25.0, '1': 50.0, '2': 75.0} # Assuming head(3) for sample
    # The current script logic uses .head() which defaults to 5.
    # If df has 3 rows, head() returns all 3.
    assert details["sample_custom_calculation_result"] == expected_sample
    assert "error" not in result

def test_custom_processor_default_multiplier():
    """Test when multiplier is not provided (should default to 1)."""
    data = {'col_a': [10, 20, 30]}
    df = pd.DataFrame(data)
    params = {'target_column': 'col_a'} # No multiplier
    
    result = example_custom_processor.process(df, params)
    
    assert result["message"] == "Example custom processor executed successfully."
    assert "custom_calculation_details" in result
    details = result["custom_calculation_details"]
    assert details["multiplier_used"] == 1.0
    expected_sample = {'0': 10.0, '1': 20.0, '2': 30.0}
    assert details["sample_custom_calculation_result"] == expected_sample

def test_custom_processor_invalid_multiplier_string():
    """Test when multiplier is an invalid string (should default to 1)."""
    data = {'col_a': [10, 20, 30]}
    df = pd.DataFrame(data)
    params = {'target_column': 'col_a', 'multiplier': 'not_a_number'}
    
    result = example_custom_processor.process(df, params)
    
    assert "custom_calculation_details" in result
    details = result["custom_calculation_details"]
    assert details["multiplier_used"] == 1.0 # Defaults to 1.0
    expected_sample = {'0': 10.0, '1': 20.0, '2': 30.0}
    assert details["sample_custom_calculation_result"] == expected_sample

def test_custom_processor_target_column_not_found():
    """Test when the specified target_column does not exist in DataFrame."""
    data = {'col_a': [1, 2, 3]}
    df = pd.DataFrame(data)
    params = {'target_column': 'non_existent_col', 'multiplier': 2}
    
    result = example_custom_processor.process(df, params)
    
    assert result["message"] == "Example custom processor failed due to missing target column."
    assert "error" in result
    assert result["error"] == "Target column 'non_existent_col' not found in DataFrame."
    assert "custom_calculation_details" not in result

def test_custom_processor_target_column_not_numeric():
    """Test when target_column is not numeric."""
    data = {'col_a': ['text1', 'text2', 'text3'], 'col_b': [1,2,3]}
    df = pd.DataFrame(data)
    params = {'target_column': 'col_a', 'multiplier': 2}
    
    result = example_custom_processor.process(df, params)
    
    assert result["message"] == "Example custom processor failed due to non-numeric target column."
    assert "error" in result
    assert result["error"] == "Target column 'col_a' is not numeric and cannot be multiplied."
    assert "custom_calculation_details" not in result

def test_custom_processor_empty_dataframe():
    """Test with an empty DataFrame."""
    df = pd.DataFrame({'col_a': pd.Series(dtype='float')})
    params = {'target_column': 'col_a', 'multiplier': 2}
    
    result = example_custom_processor.process(df, params)
    
    assert result["message"] == "Example custom processor executed successfully."
    assert result["input_rows"] == 0
    assert result["input_cols"] == 1 # Still has one column definition
    assert "custom_calculation_details" in result # It will try to process
    details = result["custom_calculation_details"]
    assert details["sample_custom_calculation_result"] == {} # Empty series to_dict is {}
    assert "error" not in result

def test_custom_processor_multiplier_as_float_string():
    """Test when multiplier is a string that can be converted to float."""
    data = {'col_a': [10, 20, 30]}
    df = pd.DataFrame(data)
    params = {'target_column': 'col_a', 'multiplier': '3.0'}
    
    result = example_custom_processor.process(df, params)
    
    assert "custom_calculation_details" in result
    details = result["custom_calculation_details"]
    assert details["multiplier_used"] == 3.0
    expected_sample = {'0': 30.0, '1': 60.0, '2': 90.0}
    assert details["sample_custom_calculation_result"] == expected_sample

def test_custom_processor_input_df_not_modified():
    """Test that the input DataFrame is not modified by the processor."""
    data = {'col_a': [10, 20, 30]}
    df_original = pd.DataFrame(data)
    df_copy = df_original.copy() # Keep a copy for comparison
    params = {'target_column': 'col_a', 'multiplier': 2}
    
    example_custom_processor.process(df_original, params)
    
    pd.testing.assert_frame_equal(df_original, df_copy)
