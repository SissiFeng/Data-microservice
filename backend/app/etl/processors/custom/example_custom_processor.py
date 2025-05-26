import pandas as pd
from typing import Dict, Any
import logging

# Configure logging for this module (optional, but good practice)
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

def process(df: pd.DataFrame, params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Example custom processor that performs a simple operation based on parameters.
    """
    logger.info(f"Executing example_custom_processor with parameters: {params}")

    input_rows = len(df)
    input_cols = len(df.columns)

    results = {
        "message": "Example custom processor executed successfully.",
        "input_rows": input_rows,
        "input_cols": input_cols,
    }

    target_column = params.get('target_column')
    multiplier = params.get('multiplier', 1) # Default multiplier to 1 if not provided

    if target_column:
        if target_column not in df.columns:
            error_message = f"Target column '{target_column}' not found in DataFrame."
            logger.error(error_message)
            # Return error in results or raise an exception, depending on desired handling
            results["error"] = error_message
            results["message"] = "Example custom processor failed due to missing target column."
        else:
            try:
                # Ensure multiplier is a number, default to 1 if conversion fails
                multiplier_val = float(multiplier)
            except (ValueError, TypeError):
                logger.warning(f"Invalid multiplier '{multiplier}', defaulting to 1.")
                multiplier_val = 1.0
            
            # Perform a custom calculation: multiply target column by multiplier
            # Ensure the target column is numeric for multiplication
            if pd.api.types.is_numeric_dtype(df[target_column]):
                custom_column_name = f"{target_column}_multiplied_by_{multiplier_val}"
                # Create a new series for the result to avoid modifying original df if not intended
                processed_series = df[target_column] * multiplier_val
                results["custom_calculation_details"] = {
                    "target_column": target_column,
                    "multiplier_used": multiplier_val,
                    "new_column_name_preview": custom_column_name,
                    # Return a sample of the calculated data (e.g., first 5 rows)
                    "sample_custom_calculation_result": processed_series.head().to_dict()
                }
                # Note: This processor returns a dictionary. If the expectation is to return a DataFrame
                # (like other processors such as rolling_mean), this function signature and the calling
                # code in etl.py (process_data_background_db) would need to be adjusted.
                # For now, it returns a Dict as specified by "Return a dictionary with results".
            else:
                error_message = f"Target column '{target_column}' is not numeric and cannot be multiplied."
                logger.error(error_message)
                results["error"] = error_message
                results["message"] = "Example custom processor failed due to non-numeric target column."
    else:
        results["info"] = "No target_column specified in parameters for custom calculation."

    logger.info(f"Example custom processor results: {results}")
    return results
