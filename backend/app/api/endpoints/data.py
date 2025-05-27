from litestar import Router, post, get, delete, Parameter
from litestar.datastructures import UploadFile
from litestar.exceptions import HTTPException
# from litestar.di import Provide # Will be used at app level for dependencies
from typing import Optional, Any # Added Any for preview return type
import uuid
import os
import json
import shutil
# from datetime import datetime # Not directly used in this file after refactor
import pandas as pd
from sqlmodel import select, func

from app.core.config import settings
from app.schemas.data import (
    DataFileResponse, 
    DataFileList, 
    # DataStatus, # Not used currently
    DataMetadata,
    DataSource
)
from app.services import s3_service
from app.db.session import AsyncSession # get_session will be provided by dependency injection
from app.db.models import DataFile as DBDataFile


@post("/upload")
async def upload_data_file_handler(
    file: UploadFile,
    session: AsyncSession, # Depends(get_session) removed, to be handled by Provide
    metadata: Optional[str] = None,
) -> DataFileResponse:
    """
    Upload a data file (CSV, etc.) with optional metadata and save its record to the DB.
    """
    parsed_metadata_as_dict = None
    if metadata:
        try:
            loaded_json = json.loads(metadata)
            validated_metadata_model = DataMetadata(**loaded_json)
            parsed_metadata_as_dict = validated_metadata_model.model_dump() # Use model_dump for Pydantic v2
        except json.JSONDecodeError:
            raise HTTPException(status_code=400, detail="Invalid metadata format. Must be valid JSON.")
        except Exception as e: 
            raise HTTPException(status_code=400, detail=f"Invalid metadata content: {str(e)}")

    if parsed_metadata_as_dict is None:
        default_metadata_model = DataMetadata(source=DataSource.UPLOAD)
        parsed_metadata_as_dict = default_metadata_model.model_dump() # Use model_dump for Pydantic v2
    
    os.makedirs(settings.DATA_DIR, exist_ok=True)
    # Ensure file.filename is not None and is a string
    filename = file.filename if file.filename is not None else "unknown_file"
    temp_file_id_prefix = str(uuid.uuid4())
    local_file_path = os.path.join(settings.DATA_DIR, f"{temp_file_id_prefix}_{filename}")
    
    try:
        # Use file.read() and write to buffer, as Litestar's UploadFile might behave differently
        content = await file.read()
        with open(local_file_path, "wb") as buffer:
            buffer.write(content) # shutil.copyfileobj(file.file, buffer) might not work directly
        
        s3_path_for_db = None
        if settings.AWS_ACCESS_KEY_ID and settings.AWS_SECRET_ACCESS_KEY:
            try:
                s3_object_name = f"raw/{temp_file_id_prefix}/{filename}"
                s3_service.upload_file(local_file_path, s3_object_name)
                s3_path_for_db = s3_object_name
            except Exception as e:
                print(f"Error uploading to S3: {str(e)}")
                raise HTTPException(status_code=500, detail=f"Failed to upload file to S3: {str(e)}")

        db_datafile_instance = DBDataFile(
            filename=filename,
            s3_path=s3_path_for_db,
            file_metadata=parsed_metadata_as_dict
        )
        session.add(db_datafile_instance)
        await session.commit()
        await session.refresh(db_datafile_instance)
        # Manually construct the response if direct return of DBModel isn't auto-serializing as expected
        # For now, assume Litestar handles Pydantic model conversion from DBModel attributes
        return DataFileResponse.model_validate(db_datafile_instance)
    finally:
        if os.path.exists(local_file_path):
            try:
                os.remove(local_file_path)
            except Exception as e:
                print(f"Error deleting temporary local file {local_file_path}: {str(e)}")

@get("/files")
async def list_data_files_handler(
    session: AsyncSession, # Depends(get_session) removed
    skip: int = Parameter(default=0, query="skip", ge=0),
    limit: int = Parameter(default=100, query="limit", ge=1, le=500),
    # status: Optional[DataStatus] = None, # Status field not in DBDataFile model yet
) -> DataFileList:
    """
    List all data files from the database.
    """
    count_statement = select(func.count(DBDataFile.id))
    total_count_result = await session.exec(count_statement)
    total_count = total_count_result.one_or_none()
    if total_count is None:
        total_count = 0

    statement = select(DBDataFile).offset(skip).limit(limit).order_by(DBDataFile.upload_date.desc())
    # if status:
    #     statement = statement.where(DBDataFile.status == status.value)
    
    result = await session.exec(statement)
    files_db = result.scalars().all()
    
    # Convert DB models to Pydantic models for the response
    files_response = [DataFileResponse.model_validate(f) for f in files_db]

    return DataFileList(
        total=total_count,
        items=files_response
    )

@get("/{file_id:uuid}")
async def get_data_file_handler(
    file_id: uuid.UUID,
    session: AsyncSession, # Depends(get_session) removed
) -> DataFileResponse:
    """
    Get a specific data file by ID from the database.
    """
    db_datafile = await session.get(DBDataFile, file_id)
    if not db_datafile:
        raise HTTPException(status_code=404, detail="Data file not found")
    return DataFileResponse.model_validate(db_datafile)

@get("/{file_id:uuid}/preview")
async def preview_data_file_handler(
    file_id: uuid.UUID, 
    session: AsyncSession, # Depends(get_session) removed
    rows: int = Parameter(default=10, query="rows", ge=1, le=100),
) -> dict[str, Any]: # Changed return type to dict[str, Any] as per original logic
    """
    Preview the contents of a data file.
    """
    db_datafile = await session.get(DBDataFile, file_id)
    if not db_datafile:
        raise HTTPException(status_code=404, detail="Data file not found")

    if not db_datafile.s3_path:
        raise HTTPException(status_code=404, detail="File not found in S3 or path is missing.")

    temp_preview_path = None
    try:
        base_name = os.path.basename(db_datafile.s3_path) if db_datafile.s3_path else db_datafile.filename
        temp_preview_path = os.path.join(settings.DATA_DIR, f"preview_{uuid.uuid4()}_{base_name}")
        os.makedirs(settings.DATA_DIR, exist_ok=True)

        s3_service.download_file(db_datafile.s3_path, temp_preview_path)
        
        if not os.path.exists(temp_preview_path) or os.path.getsize(temp_preview_path) == 0:
             raise HTTPException(status_code=500, detail="Failed to download file from S3 for preview or file is empty.")

        df = pd.read_csv(temp_preview_path)
        preview_data = df.head(rows).to_dict(orient="records")
        columns = df.columns.tolist()
        
        return {
            "filename": db_datafile.filename,
            "columns": columns,
            "data": preview_data,
            "total_rows_in_file": len(df),
            "preview_rows_shown": len(preview_data)
        }
    except pd.errors.EmptyDataError:
        raise HTTPException(status_code=400, detail="The file is empty or not a valid CSV.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reading or previewing file: {str(e)}")
    finally:
        if temp_preview_path and os.path.exists(temp_preview_path):
            try:
                os.remove(temp_preview_path)
            except Exception as e:
                print(f"Error deleting temporary preview file {temp_preview_path}: {str(e)}")

@delete("/{file_id:uuid}", status_code=204)
async def delete_data_file_handler(
    file_id: uuid.UUID,
    session: AsyncSession, # Depends(get_session) removed
) -> None: # Return None for 204 No Content
    """
    Delete a data file record from the database and its corresponding file from S3.
    """
    db_datafile = await session.get(DBDataFile, file_id)
    if not db_datafile:
        raise HTTPException(status_code=404, detail="Data file not found")

    if db_datafile.s3_path:
        try:
            s3_service.delete_file(db_datafile.s3_path)
        except Exception as e:
            print(f"Error deleting file {db_datafile.s3_path} from S3: {str(e)}")
            # Consider if this error should be raised or just logged
            # raise HTTPException(status_code=500, detail=f"Failed to delete file from S3: {str(e)}")

    await session.delete(db_datafile)
    await session.commit()
    
    return None

router = Router(
    path="/data", 
    route_handlers=[
        upload_data_file_handler,
        list_data_files_handler,
        get_data_file_handler,
        preview_data_file_handler,
        delete_data_file_handler,
    ]
)
