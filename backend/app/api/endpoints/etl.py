from litestar import Router, post, get, delete, Response, Parameter
from litestar.exceptions import HTTPException
from typing import Optional # Removed List, Dict as they are not directly used in type hints here
import uuid
# from datetime import datetime # Not directly used
import pandas as pd
# import numpy as np # Not directly used
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
# from app.core.config import settings # Not directly used in this file
from app.db.session import AsyncSession # get_session will be provided by dependency injection
from app.db.models import ProcessingResult as DBProcessingResult
from app.db.models import DataFile as DBDataFile
from app.tasks import process_data_task

@post("/process")
async def process_data_handler(
    data: ProcessingRequest, # Changed 'request' to 'data' as per Litestar convention for request body
    session: AsyncSession
) -> ProcessingResponse:
    """
    Initiates data processing by creating a DBProcessingResult record 
    and dispatching a Celery task.
    """
    db_data_file = await session.get(DBDataFile, data.data_file_id)
    if not db_data_file:
        raise HTTPException(status_code=404, detail=f"DataFile with ID {data.data_file_id} not found.")

    db_processing_result = DBProcessingResult(
        data_file_id=data.data_file_id,
        processing_type=data.processing_type.value,
        parameters=data.parameters.model_dump(exclude_none=True) if data.parameters else {}, # Use model_dump
        status=ProcessingStatus.PENDING.value,
    )
    session.add(db_processing_result)
    await session.commit()
    await session.refresh(db_processing_result)

    task = process_data_task.delay(
        processing_id=db_processing_result.id,
        data_file_id=data.data_file_id,
        processing_type_value=data.processing_type.value,
        parameters=db_processing_result.parameters
    )

    db_processing_result.task_id = task.id
    session.add(db_processing_result)
    await session.commit()
    await session.refresh(db_processing_result)
    
    return ProcessingResponse.model_validate(db_processing_result)


@get("/results")
async def list_processing_results_handler(
    session: AsyncSession,
    data_file_id: Optional[uuid.UUID] = Parameter(default=None, query="data_file_id", required=False, description="Filter by DataFile ID"),
    processing_type: Optional[ProcessingType] = Parameter(default=None, query="processing_type", required=False, description="Filter by Processing Type"),
    status: Optional[ProcessingStatus] = Parameter(default=None, query="status", required=False, description="Filter by Status"),
    skip: int = Parameter(default=0, query="skip", ge=0),
    limit: int = Parameter(default=100, query="limit", ge=1, le=500)
) -> ProcessingResultList:
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
    results_exec = await session.exec(statement)
    items_db = results_exec.scalars().all()

    items_response = [ProcessingResponse.model_validate(item) for item in items_db]
    
    return ProcessingResultList(total=total_count, items=items_response)

@get("/{processing_id:uuid}")
async def get_processing_result_handler(
    processing_id: uuid.UUID,
    session: AsyncSession
) -> ProcessingResponse:
    """
    Get a specific processing result by ID from the database.
    """
    db_processing_result = await session.get(DBProcessingResult, processing_id)
    if not db_processing_result:
        raise HTTPException(status_code=404, detail="Processing result not found")
    return ProcessingResponse.model_validate(db_processing_result)

@delete("/{processing_id:uuid}", status_code=204)
async def delete_processing_result_handler(
    processing_id: uuid.UUID,
    session: AsyncSession
) -> None:
    """
    Delete a processing result by ID.
    """
    db_processing_result = await session.get(DBProcessingResult, processing_id)
    if not db_processing_result:
        raise HTTPException(status_code=404, detail="Processing result not found")

    await session.delete(db_processing_result)
    await session.commit()
    return None


@get("/{processing_id:uuid}/export")
async def export_processing_result_handler(
    processing_id: uuid.UUID,
    session: AsyncSession,
    format: str = Parameter(default="json", query="format", description="Export format: 'json' or 'csv'")
) -> Response:
    """
    Export a processing result.
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
        content = json.dumps(db_processing_result.result_data, indent=2)
        return Response(
            content=content,
            media_type="application/json",
            headers={"Content-Disposition": f"attachment; filename={export_filename}"}
        )
    
    elif format.lower() == "csv":
        result_data = db_processing_result.result_data
        data_to_export = None

        if isinstance(result_data, list) and all(isinstance(item, dict) for item in result_data):
            data_to_export = result_data
        elif isinstance(result_data, dict) and "sample_data" in result_data and isinstance(result_data["sample_data"], list):
            data_to_export = result_data["sample_data"]
            export_filename = f"sample_{export_filename}" # Prepend sample to filename

        if data_to_export is not None:
            try:
                df_to_export = pd.DataFrame(data_to_export)
                output = io.StringIO()
                df_to_export.to_csv(output, index=False)
                csv_content = output.getvalue()
                return Response(
                    content=csv_content,
                    media_type="text/csv",
                    headers={"Content-Disposition": f"attachment; filename={export_filename}"}
                )
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Failed to convert result_data to CSV: {str(e)}")
        else:
            raise HTTPException(status_code=400, detail="CSV export not suitable for the format of result_data.")
            
    else:
        raise HTTPException(status_code=400, detail=f"Unsupported export format: {format}. Try 'json' or 'csv'.")

etl_router = Router(
    path="/etl", 
    route_handlers=[
        process_data_handler,
        list_processing_results_handler,
        get_processing_result_handler,
        delete_processing_result_handler,
        export_processing_result_handler,
    ]
)
