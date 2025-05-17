import pandas as pd
import numpy as np
from typing import Dict, Any, List, Tuple, Union
from scipy.signal import find_peaks

def process(
    df: pd.DataFrame, 
    params: Dict[str, Any]
) -> Tuple[np.ndarray, Dict[str, np.ndarray]]:
    """
    Detect peaks in the dataframe
    
    Parameters:
    -----------
    df : pd.DataFrame
        Input dataframe
    params : Dict[str, Any]
        Parameters for peak detection
        - column: str, column to detect peaks
        - height: float, required height of peaks
        - threshold: float, required threshold of peaks
        - distance: int, required minimal horizontal distance between peaks
        - prominence: float, required prominence of peaks
        - width: float, required width of peaks
    
    Returns:
    --------
    Tuple[np.ndarray, Dict[str, np.ndarray]]
        Peaks indices and properties
    """
    # Get parameters
    column = params.get("column")
    if column is None:
        # Use the first numeric column if not specified
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        if not numeric_cols:
            raise ValueError("No numeric columns found in the dataframe")
        column = numeric_cols[0]
    
    # Check if column exists
    if column not in df.columns:
        raise ValueError(f"Column '{column}' not found in the dataframe")
    
    # Extract data
    y = df[column].values
    
    # Extract peak detection parameters
    height = params.get("height", None)
    threshold = params.get("threshold", None)
    distance = params.get("distance", None)
    prominence = params.get("prominence", None)
    width = params.get("width", None)
    
    # Detect peaks
    peaks, properties = find_peaks(
        y,
        height=height,
        threshold=threshold,
        distance=distance,
        prominence=prominence,
        width=width
    )
    
    return peaks, properties
