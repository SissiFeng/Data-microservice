import pandas as pd
import numpy as np
from typing import Dict, Any, List

def process(
    df: pd.DataFrame, 
    params: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Assess data quality of the dataframe
    
    Parameters:
    -----------
    df : pd.DataFrame
        Input dataframe
    params : Dict[str, Any]
        Parameters for data quality assessment
        - columns: List[str], columns to assess (if None, assess all columns)
    
    Returns:
    --------
    Dict[str, Any]
        Data quality metrics
    """
    # Get parameters
    columns = params.get("columns", None)
    
    # If columns not specified, use all columns
    if columns is None:
        columns = df.columns.tolist()
    else:
        # Filter to only include columns that exist in the dataframe
        columns = [col for col in columns if col in df.columns]
    
    # Initialize results
    results = {
        "row_count": len(df),
        "column_count": len(columns),
        "columns": {}
    }
    
    # Calculate metrics for each column
    for col in columns:
        col_data = df[col]
        col_metrics = {
            "dtype": str(df[col].dtype),
            "missing_count": col_data.isna().sum(),
            "missing_percentage": round(col_data.isna().mean() * 100, 2)
        }
        
        # Add numeric metrics if applicable
        if pd.api.types.is_numeric_dtype(col_data):
            col_metrics.update({
                "min": col_data.min() if not col_data.empty else None,
                "max": col_data.max() if not col_data.empty else None,
                "mean": col_data.mean() if not col_data.empty else None,
                "median": col_data.median() if not col_data.empty else None,
                "std": col_data.std() if not col_data.empty else None,
                "zeros_count": (col_data == 0).sum(),
                "zeros_percentage": round((col_data == 0).mean() * 100, 2),
                "negative_count": (col_data < 0).sum() if not col_data.empty else 0,
                "negative_percentage": round((col_data < 0).mean() * 100, 2) if not col_data.empty else 0
            })
        
        # Add categorical metrics if applicable
        if pd.api.types.is_object_dtype(col_data) or pd.api.types.is_categorical_dtype(col_data):
            value_counts = col_data.value_counts()
            col_metrics.update({
                "unique_count": col_data.nunique(),
                "top_values": value_counts.head(5).to_dict() if not value_counts.empty else {}
            })
        
        results["columns"][col] = col_metrics
    
    # Overall data quality score (simple example)
    missing_percentages = [results["columns"][col]["missing_percentage"] for col in columns]
    results["overall_missing_percentage"] = round(sum(missing_percentages) / len(columns), 2) if columns else 0
    
    # Data quality score (0-100, higher is better)
    results["quality_score"] = round(100 - results["overall_missing_percentage"], 2)
    
    return results
