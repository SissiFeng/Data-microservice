from fastapi import APIRouter, HTTPException, BackgroundTasks, Response
from typing import List, Optional, Dict
import uuid
from datetime import datetime
import pandas as pd
import numpy as np
import json
import os
import io

from app.schemas.etl import (
    ProcessingRequest,
    ProcessingResponse,
    ProcessingResultList,
    ProcessingStatus,
    ProcessingType
)
from app.etl.processors import rolling_mean, peak_detection, data_quality
from app.api.endpoints.data import data_files  # Using in-memory storage for demo
from app.core.config import settings

router = APIRouter()

# In-memory storage for processing results
processing_results = {}

def process_data_background(
    processing_id: str,
    data_file_id: str,
    processing_type: ProcessingType,
    parameters: Dict
):
    """Background task to process data"""
    try:
        # Update status to processing
        processing_results[processing_id]["status"] = ProcessingStatus.PROCESSING
        processing_results[processing_id]["updated_at"] = datetime.now()

        # Get the data file
        if data_file_id not in data_files:
            raise Exception("Data file not found")

        file_path = data_files[data_file_id]["filepath"]

        # Read the data
        df = pd.read_csv(file_path)

        # Process based on type
        result_data = {}
        if processing_type == ProcessingType.ROLLING_MEAN:
            result_df = rolling_mean.process(df, parameters)
            result_data = {
                "original_columns": df.columns.tolist(),
                "processed_columns": result_df.columns.tolist(),
                "sample_data": result_df.head(10).to_dict(orient="records")
            }

        elif processing_type == ProcessingType.PEAK_DETECTION:
            peaks, properties = peak_detection.process(df, parameters)
            result_data = {
                "peaks": peaks.tolist() if isinstance(peaks, np.ndarray) else peaks,
                "properties": {k: v.tolist() if isinstance(v, np.ndarray) else v
                              for k, v in properties.items()} if properties else {}
            }

        elif processing_type == ProcessingType.DATA_QUALITY:
            quality_metrics = data_quality.process(df, parameters)
            result_data = quality_metrics

        else:
            raise Exception(f"Unsupported processing type: {processing_type}")

        # Save processed data
        result_dir = os.path.join(settings.DATA_DIR, "processed")
        os.makedirs(result_dir, exist_ok=True)

        result_file = os.path.join(
            result_dir,
            f"{data_file_id}_{processing_type}_{processing_id}.json"
        )

        with open(result_file, "w") as f:
            json.dump(result_data, f)

        # Update processing result
        processing_results[processing_id].update({
            "status": ProcessingStatus.COMPLETED,
            "result_file": result_file,
            "result_data": result_data,
            "updated_at": datetime.now()
        })

    except Exception as e:
        # Update with error status
        processing_results[processing_id].update({
            "status": ProcessingStatus.FAILED,
            "result_data": {"error": str(e)},
            "updated_at": datetime.now()
        })

@router.post("/process", response_model=ProcessingResponse)
async def process_data(
    request: ProcessingRequest,
    background_tasks: BackgroundTasks
):
    """
    Process a data file with specified algorithm and parameters
    """
    # Validate data file exists
    if request.data_file_id not in data_files:
        raise HTTPException(status_code=404, detail="Data file not found")

    # Create processing record
    processing_id = str(uuid.uuid4())

    processing_result = {
        "data_file_id": request.data_file_id,
        "processing_type": request.processing_type,
        "parameters": request.parameters.dict() if request.parameters else {},
        "status": ProcessingStatus.PENDING,
        "created_at": datetime.now(),
        "updated_at": datetime.now()
    }

    # Store in memory
    processing_results[processing_id] = processing_result

    # Start background processing
    background_tasks.add_task(
        process_data_background,
        processing_id,
        request.data_file_id,
        request.processing_type,
        processing_result["parameters"]
    )

    return {**processing_result, "id": processing_id}

@router.get("/results", response_model=ProcessingResultList)
async def list_processing_results(
    data_file_id: Optional[str] = None,
    processing_type: Optional[ProcessingType] = None,
    status: Optional[ProcessingStatus] = None,
    skip: int = 0,
    limit: int = 100
):
    """
    List processing results with optional filtering
    """
    filtered_results = []

    for id, result in processing_results.items():
        if data_file_id and result["data_file_id"] != data_file_id:
            continue
        if processing_type and result["processing_type"] != processing_type:
            continue
        if status and result["status"] != status:
            continue

        filtered_results.append({**result, "id": id})

    # Sort by created_at descending
    filtered_results.sort(key=lambda x: x["created_at"], reverse=True)

    # Apply pagination
    paginated_results = filtered_results[skip:skip+limit]

    return {
        "total": len(filtered_results),
        "items": paginated_results
    }

@router.get("/results/{processing_id}", response_model=ProcessingResponse)
async def get_processing_result(processing_id: str):
    """
    Get a specific processing result by ID
    """
    if processing_id not in processing_results:
        raise HTTPException(status_code=404, detail="Processing result not found")

    return {**processing_results[processing_id], "id": processing_id}

@router.get("/results/{processing_id}/export")
async def export_processing_result(processing_id: str, format: str = "csv"):
    """
    Export a processing result in CSV or JSON format
    """
    if processing_id not in processing_results:
        raise HTTPException(status_code=404, detail="Processing result not found")

    result = processing_results[processing_id]

    # Check if processing is complete
    if result["status"] != ProcessingStatus.COMPLETED:
        raise HTTPException(status_code=400, detail="Processing is not complete")

    # Get the data file
    data_file_id = result["data_file_id"]
    if data_file_id not in data_files:
        raise HTTPException(status_code=404, detail="Data file not found")

    file_path = data_files[data_file_id]["filepath"]

    # Read the original data
    df = pd.read_csv(file_path)

    # Apply the processing based on type
    processed_df = None

    if result["processing_type"] == ProcessingType.ROLLING_MEAN:
        processed_df = rolling_mean.process(df, result["parameters"])

    elif result["processing_type"] == ProcessingType.PEAK_DETECTION:
        # For peak detection, we'll add a column indicating peaks
        processed_df = df.copy()
        peaks = result["result_data"]["peaks"]
        processed_df["is_peak"] = 0
        for peak in peaks:
            if peak < len(processed_df):
                processed_df.loc[peak, "is_peak"] = 1

    elif result["processing_type"] == ProcessingType.DATA_QUALITY:
        # For data quality, we'll return the original data with quality metrics as metadata
        processed_df = df.copy()

    else:
        raise HTTPException(status_code=400, detail=f"Export not supported for {result['processing_type']}")

    # Export in the requested format
    if format.lower() == "csv":
        output = io.StringIO()
        processed_df.to_csv(output, index=False)

        filename = f"{data_files[data_file_id]['filename'].split('.')[0]}_{result['processing_type']}.csv"

        return Response(
            content=output.getvalue(),
            media_type="text/csv",
            headers={
                "Content-Disposition": f"attachment; filename={filename}"
            }
        )

    elif format.lower() == "json":
        output = processed_df.to_json(orient="records")

        filename = f"{data_files[data_file_id]['filename'].split('.')[0]}_{result['processing_type']}.json"

        return Response(
            content=output,
            media_type="application/json",
            headers={
                "Content-Disposition": f"attachment; filename={filename}"
            }
        )

    else:
        raise HTTPException(status_code=400, detail=f"Unsupported export format: {format}")
