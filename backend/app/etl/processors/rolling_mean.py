import pandas as pd
import numpy as np
from typing import Dict, Any, List, Union

def process(
    df: pd.DataFrame, 
    params: Dict[str, Any]
) -> pd.DataFrame:
    """
    Apply rolling mean to the dataframe
    
    Parameters:
    -----------
    df : pd.DataFrame
        Input dataframe
    params : Dict[str, Any]
        Parameters for rolling mean
        - window_size: int, window size for rolling mean
        - columns: List[str], columns to apply rolling mean (if None, apply to all numeric columns)
    
    Returns:
    --------
    pd.DataFrame
        Dataframe with rolling mean applied
    """
    # Get parameters
    window_size = params.get("window_size", 5)
    columns = params.get("columns", None)
    
    # Make a copy of the dataframe
    result_df = df.copy()
    
    # If columns not specified, use all numeric columns
    if columns is None:
        columns = df.select_dtypes(include=[np.number]).columns.tolist()
    
    # Apply rolling mean to specified columns
    for col in columns:
        if col in df.columns and pd.api.types.is_numeric_dtype(df[col]):
            result_df[f"{col}_rolling_mean"] = df[col].rolling(window=window_size).mean()
    
    return result_df
