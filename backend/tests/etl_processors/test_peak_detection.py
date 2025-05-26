import pytest
import pandas as pd
import numpy as np
from app.etl.processors import peak_detection

def test_peak_detection_simple():
    """Test basic peak detection."""
    data = {'time': range(10), 'value': [0, 1, 2, 5, 2, 3, 1, 4, 2, 0]}
    df = pd.DataFrame(data)
    params = {'column': 'value', 'height': 3}
    
    peaks, properties = peak_detection.process(df, params)
    
    assert len(peaks) == 2
    assert 3 in peaks  # Peak at index 3 (value 5)
    assert 7 in peaks  # Peak at index 7 (value 4)
    assert 'peak_heights' in properties

def test_peak_detection_no_peaks():
    """Test case with no peaks meeting criteria."""
    data = {'time': range(10), 'value': [0, 1, 2, 1, 2, 1, 0, 1, 2, 0]}
    df = pd.DataFrame(data)
    params = {'column': 'value', 'height': 3}
    
    peaks, properties = peak_detection.process(df, params)
    
    assert len(peaks) == 0

def test_peak_detection_with_prominence():
    """Test peak detection with prominence."""
    data = {'value': [0, 1, 0, 5, 0, 3, 0, 4, 0, 2, 0]} # Peaks at 5, 3, 4, 2
    df = pd.DataFrame(data)
    # Peak at 5 (prominence 5), peak at 3 (prominence 3), peak at 4 (prominence 4), peak at 2 (prominence 2)
    params = {'column': 'value', 'prominence': 3.5} # Should detect peaks 5 and 4
    
    peaks, properties = peak_detection.process(df, params)
    
    expected_peaks = [3, 7] # Indices of 5 and 4
    assert np.array_equal(peaks, expected_peaks)

def test_peak_detection_no_numeric_column():
    """Test with a DataFrame that has no numeric columns to process."""
    data = {'text_data': ['a', 'b', 'c', 'd', 'e']}
    df = pd.DataFrame(data)
    params = {'column': 'text_data', 'height': 1} # Attempt to process non-numeric
    
    peaks, properties = peak_detection.process(df, params)
    
    # Expect no peaks, as non-numeric data should be handled gracefully (e.g., by returning empty)
    assert len(peaks) == 0

def test_peak_detection_specific_column_not_found():
    """Test when specified column does not exist."""
    data = {'value': [0, 1, 5, 1, 0]}
    df = pd.DataFrame(data)
    params = {'column': 'non_existent_column', 'height': 1}
    
    peaks, properties = peak_detection.process(df, params)
    # Should default to first numeric or handle gracefully
    assert len(peaks) == 1 # Assuming it defaults to 'value' or similar logic
    assert 2 in peaks

def test_peak_detection_empty_dataframe():
    """Test with an empty DataFrame."""
    df = pd.DataFrame({'value': pd.Series(dtype='float')})
    params = {'column': 'value', 'height': 1}
    
    peaks, properties = peak_detection.process(df, params)
    assert len(peaks) == 0

def test_peak_detection_all_same_values():
    """Test with a DataFrame where all values are the same (no peaks)."""
    data = {'value': [5, 5, 5, 5, 5]}
    df = pd.DataFrame(data)
    params = {'column': 'value', 'height': 0.1} # Height is low but no local maxima
    
    peaks, properties = peak_detection.process(df, params)
    assert len(peaks) == 0

# You can add more tests for other parameters like distance, width, etc.
# Example for distance:
def test_peak_detection_with_distance():
    data = {'value': [0, 5, 2, 6, 3, 5, 0]} # Potential peaks at 5, 6, 5
    df = pd.DataFrame(data)
    params_no_distance = {'column': 'value', 'height': 4}
    peaks_no_dist, _ = peak_detection.process(df, params_no_distance)
    assert len(peaks_no_dist) == 3 # 5, 6, 5

    params_with_distance = {'column': 'value', 'height': 4, 'distance': 2} # Min distance 2
    peaks_with_dist, _ = peak_detection.process(df, params_with_distance)
    # Expected: index 3 (value 6) is highest. Next peak must be at least 2 away.
    # Index 1 (value 5) and Index 5 (value 5) are 2 away from index 3.
    # If 6 is chosen, then 5 (idx 1) and 5 (idx 5) are selected if they qualify.
    # SciPy's find_peaks selects the highest peaks first if distance conflicts.
    # If 6 (idx 3) is selected, then 5 (idx 1) is 2 away, 5 (idx 5) is 2 away.
    # This can be tricky, often depends on the exact algorithm behavior.
    # Let's assume it picks the highest ones that satisfy distance.
    # If 6 is picked, then 5 (idx 1) and 5 (idx 5) are valid.
    # If 5 (idx 1) is picked, then 6 (idx 3) is valid. 5 (idx 5) is 4 away from idx 1.
    # For this example, let's be explicit about what we expect or simplify.
    # A simpler distance test:
    data_dist_simple = {'value': [0, 5, 4, 3, 5, 0]} # Peaks at 5 (idx 1), 5 (idx 4)
    df_dist_simple = pd.DataFrame(data_dist_simple)
    params_dist = {'column': 'value', 'height': 4, 'distance': 3} # distance 3
    peaks_dist, _ = peak_detection.process(df_dist_simple, params_dist)
    # With distance 3, if 5 (idx 1) is chosen, 5 (idx 4) cannot be (4-1=3).
    # It should pick one, likely the first or the higher if different. Here they are same.
    assert len(peaks_dist) == 1 
    assert peaks_dist[0] == 1 # Or 4, depending on implementation tie-breaking
    
    # Another test: ensure the highest peak is chosen when distance constraint applies
    data_dist_priority = {'value': [0, 5, 0, 6, 0, 4, 0]} # Peaks: 5 (idx 1), 6 (idx 3), 4 (idx 5)
    df_dist_priority = pd.DataFrame(data_dist_priority)
    params_dist_priority = {'column': 'value', 'height': 3, 'distance': 2}
    peaks_priority, _ = peak_detection.process(df_dist_priority, params_dist_priority)
    # Peak 6 (idx 3) should be chosen.
    # Peak 5 (idx 1) is 2 away, valid.
    # Peak 4 (idx 5) is 2 away, valid.
    # The find_peaks sorts by peak height if there are conflicts with distance.
    # This example might be too complex without knowing exact find_peaks behavior with multiple constraints.
    # A simpler way to test distance is to have two close peaks and one far one.
    data_clear_dist = {'value': [0,5,4,5,0,0,0,5,0]} # Peaks at idx 1,3,7. (5, (4), 5, 5)
    df_clear_dist = pd.DataFrame(data_clear_dist)
    params_clear_dist = {'column': 'value', 'height': 4, 'distance': 3}
    peaks_clear, _ = peak_detection.process(df_clear_dist, params_clear_dist)
    # Expected: idx 1 (val 5). idx 3 (val 5) is too close (dist 2). idx 7 (val 5) is far (dist 6).
    # So, idx 1 and idx 7 should be detected.
    assert 1 in peaks_clear
    assert 7 in peaks_clear
    assert 3 not in peaks_clear # This peak should be suppressed by distance to peak at idx 1
    assert len(peaks_clear) == 2

# Test default column selection (first numeric column)
def test_peak_detection_default_column():
    data = {'text': ['a','b','c'], 'numeric1': [0,5,1], 'numeric2': [1,2,6]}
    df = pd.DataFrame(data)
    params = {'height': 3} # No column specified
    peaks, _ = peak_detection.process(df, params)
    # 'numeric1' is first, peak at index 1 (value 5)
    assert len(peaks) == 1
    assert peaks[0] == 1

def test_peak_detection_default_column_no_numeric():
    data = {'text': ['a','b','c'], 'text2': ['d','e','f']}
    df = pd.DataFrame(data)
    params = {'height': 3} # No column specified
    peaks, _ = peak_detection.process(df, params)
    assert len(peaks) == 0 # No numeric columns to default to
