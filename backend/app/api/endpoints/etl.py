from fastapi import APIRouter, HTTPException, BackgroundTasks, Response, Depends, Query
from typing import List, Optional, Dict
import uuid
from datetime import datetime
import pandas as pd
import numpy as np
import json
import os
import io
from sqlmodel import select, func

from app.schemas.etl import (
    ProcessingRequest,
    ProcessingResponse,
    ProcessingResultList,
    ProcessingStatus,
    ProcessingType
)
# ETL processors are now called within the Celery task
# from app.etl.processors import rolling_mean, peak_detection, data_quality 
# from app.services import s3_service # s3_service is used within the Celery task
from app.core.config import settings
from app.db.session import get_session, AsyncSession
from app.db.models import ProcessingResult as DBProcessingResult
from app.db.models import DataFile as DBDataFile
from app.tasks import process_data_task # Import the Celery task

router = APIRouter()

# The old process_data_background_db function is removed as its logic is now in app.tasks.process_data_task

@router.post("/process", response_model=ProcessingResponse)
async def process_data(
    request: ProcessingRequest,
    # background_tasks: BackgroundTasks, # Removed BackgroundTasks
    session: AsyncSession = Depends(get_session)
):
    """
    Initiates data processing by creating a DBProcessingResult record 
    and dispatching a Celery task.
    """
    db_data_file = await session.get(DBDataFile, request.data_file_id)
    if not db_data_file:
        raise HTTPException(status_code=404, detail=f"DataFile with ID {request.data_file_id} not found.")

    db_processing_result = DBProcessingResult(
        data_file_id=request.data_file_id,
        processing_type=request.processing_type.value,
        parameters=request.parameters.dict(exclude_none=True) if request.parameters else {}, # Ensure exclude_none
        status=ProcessingStatus.PENDING.value,
    )
    session.add(db_processing_result)
    await session.commit()
    await session.refresh(db_processing_result)

    # Dispatch Celery task
    task = process_data_task.delay(
        processing_id=db_processing_result.id,
        data_file_id=request.data_file_id,
        processing_type_value=request.processing_type.value, # Pass enum value
        parameters=db_processing_result.parameters
    )

    # Update the DB record with the task_id
    db_processing_result.task_id = task.id
    session.add(db_processing_result)
    await session.commit()
    await session.refresh(db_processing_result)
    
    # Return the ProcessingResponse, which now includes task_id
    # The schema ProcessingResponse should already include all fields from DBProcessingResult
    # or be able to serialize it correctly (e.g. if it's a SQLModel itself with from_orm=True)
    return db_processing_result


@router.get("/results", response_model=ProcessingResultList)
async def list_processing_results(
    data_file_id: Optional[uuid.UUID] = Query(None, description="Filter by DataFile ID"),
    processing_type: Optional[ProcessingType] = Query(None, description="Filter by Processing Type"),
    status: Optional[ProcessingStatus] = Query(None, description="Filter by Status"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    session: AsyncSession = Depends(get_session)
):
    """
    List processing results from the database with optional filtering.
    """
    statement = select(DBProcessingResult)
    count_statement = select(func.count(DBProcessingResult.id))

    if data_file_id:
        statement = statement.where(DBProcessingResult.data_file_id == data_file_id)
        count_statement = count_statement.where(DBProcessingResult.data_file_id == data_file_id)
    if processing_type:
        statement = statement.where(DBProcessingResult.processing_type == processing_type.value)
        count_statement = count_statement.where(DBProcessingResult.processing_type == processing_type.value)
    if status:
        statement = statement.where(DBProcessingResult.status == status.value)
        count_statement = count_statement.where(DBProcessingResult.status == status.value)

    total_count_result = await session.exec(count_statement)
    total_count = total_count_result.one_or_none()
    if total_count is None: total_count = 0
        
    statement = statement.offset(skip).limit(limit).order_by(DBProcessingResult.created_at.desc())
    results = await session.exec(statement)
    items = results.scalars().all()
    
    return {"total": total_count, "items": items}

@router.get("/results/{processing_id}", response_model=ProcessingResponse)
async def get_processing_result(
    processing_id: uuid.UUID, # Path parameter is UUID
    session: AsyncSession = Depends(get_session)
):
    """
    Get a specific processing result by ID from the database.
    """
    db_processing_result = await session.get(DBProcessingResult, processing_id)
    if not db_processing_result:
        raise HTTPException(status_code=404, detail="Processing result not found")
    return db_processing_result

@router.delete("/results/{processing_id}", status_code=204)
async def delete_processing_result(
    processing_id: uuid.UUID,
    session: AsyncSession = Depends(get_session)
):
    """
    Delete a processing result by ID.
    (Note: This does not delete associated files from S3 or local disk if any result_data pointed to them)
    """
    db_processing_result = await session.get(DBProcessingResult, processing_id)
    if not db_processing_result:
        raise HTTPException(status_code=404, detail="Processing result not found")

    # If result_data contains paths to files that need cleanup, that logic would go here.
    # For example, if result_data = {"result_file_path": "path/to/file.json"}
    # if db_processing_result.result_data and "result_file_path" in db_processing_result.result_data:
    #     file_to_delete = db_processing_result.result_data["result_file_path"]
    #     if os.path.exists(file_to_delete): # Or s3_service.delete_file if it's an S3 key
    #         os.remove(file_to_delete) # Or s3_service.delete_file

    await session.delete(db_processing_result)
    await session.commit()
    return None


# The /results/{processing_id}/export endpoint is more complex as it involves
# re-running or interpreting stored results to generate an exportable file.
# This typically requires knowledge of the original data and processing steps.
# Given the current DBProcessingResult model stores `result_data` as JSON,
# exporting might mean formatting this JSON or, if it's summary data,
# the export might not be a direct re-creation of a processed DataFrame.
# For this refactor, I will simplify or remove the export endpoint if it's too complex
# to adapt without significant changes to ETL processors or data storage strategy.
# The original export logic heavily relied on in-memory structures and local file paths.
# Re-implementing it to work with S3-stored original files and JSON results in DB
# would require significant changes.
# I will provide a placeholder for the export endpoint, noting it needs more work.

@router.get("/results/{processing_id}/export")
async def export_processing_result(
    processing_id: uuid.UUID,
    format: str = Query("json", description="Export format: 'json' or 'csv' (csv might be limited by stored data)"),
    session: AsyncSession = Depends(get_session)
):
    """
    Export a processing result.
    JSON export will return the 'result_data' field.
    CSV export is more complex and might only be feasible if 'result_data' is tabular.
    """
    db_processing_result = await session.get(DBProcessingResult, processing_id)
    if not db_processing_result:
        raise HTTPException(status_code=404, detail="Processing result not found")

    if db_processing_result.status != ProcessingStatus.COMPLETED.value:
        raise HTTPException(status_code=400, detail=f"Processing not complete. Status: {db_processing_result.status}")

    if not db_processing_result.result_data:
        raise HTTPException(status_code=404, detail="No result data available for export.")

    db_data_file = await session.get(DBDataFile, db_processing_result.data_file_id)
    original_filename_base = "export"
    if db_data_file and db_data_file.filename:
        original_filename_base = os.path.splitext(db_data_file.filename)[0]
    
    export_filename = f"{original_filename_base}_{db_processing_result.processing_type}_{processing_id}.{format.lower()}"

    if format.lower() == "json":
        return Response(
            content=json.dumps(db_processing_result.result_data, indent=2),
            media_type="application/json",
            headers={"Content-Disposition": f"attachment; filename={export_filename}"}
        )
    
    elif format.lower() == "csv":
        # CSV export is only meaningful if result_data is a list of dicts (tabular)
        # or can be converted to a pandas DataFrame.
        # This is a simplified example; more robust conversion might be needed.
        if isinstance(db_processing_result.result_data, list) and \
           all(isinstance(item, dict) for item in db_processing_result.result_data):
            try:
                df_to_export = pd.DataFrame(db_processing_result.result_data)
                output = io.StringIO()
                df_to_export.to_csv(output, index=False)
                return Response(
                    content=output.getvalue(),
                    media_type="text/csv",
                    headers={"Content-Disposition": f"attachment; filename={export_filename}"}
                )
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Failed to convert result_data to CSV: {str(e)}")
        elif isinstance(db_processing_result.result_data, dict) and "sample_data" in db_processing_result.result_data and isinstance(db_processing_result.result_data["sample_data"], list) :
             try: # Attempt to export sample_data if main result_data is not directly tabular
                df_to_export = pd.DataFrame(db_processing_result.result_data["sample_data"])
                output = io.StringIO()
                df_to_export.to_csv(output, index=False)
                return Response(
                    content=output.getvalue(),
                    media_type="text/csv",
                    headers={"Content-Disposition": f"attachment; filename=sample_{export_filename}"}
                )
             except Exception as e:
                raise HTTPException(status_code=500, detail=f"Failed to convert sample_data to CSV: {str(e)}")
        else:
            raise HTTPException(status_code=400, detail="CSV export not suitable for the format of result_data.")
            
    else:
        raise HTTPException(status_code=400, detail=f"Unsupported export format: {format}. Try 'json' or 'csv'.")
