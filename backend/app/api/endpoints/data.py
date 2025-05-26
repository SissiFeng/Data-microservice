from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends, Query
from fastapi.responses import JSONResponse
from typing import List, Optional
import uuid
import os
import json
import shutil
from datetime import datetime
import pandas as pd # Keep for preview, though preview logic will change
from sqlmodel import select, func # Added select and func for DB queries

from app.core.config import settings
from app.schemas.data import (
    # DataFileCreate, # Not used directly in these endpoints after upload refactor
    DataFileResponse, 
    DataFileList, 
    DataStatus,      # Will be used if/when status field is added to DB model
    DataMetadata,    # Used for parsing input metadata in upload
    DataSource       # Used for default metadata source in upload
)
from app.services import s3_service
from app.db.session import get_session, AsyncSession
from app.db.models import DataFile as DBDataFile

router = APIRouter()

# In-memory 'data_files' dictionary is now removed.

@router.post("/upload", response_model=DataFileResponse)
async def upload_data_file(
    file: UploadFile = File(...),
    metadata: Optional[str] = Form(None),
    session: AsyncSession = Depends(get_session)
):
    """
    Upload a data file (CSV, etc.) with optional metadata and save its record to the DB.
    (This endpoint was refactored in the previous subtask)
    """
    parsed_metadata_as_dict = None
    if metadata:
        try:
            loaded_json = json.loads(metadata)
            validated_metadata_model = DataMetadata(**loaded_json)
            parsed_metadata_as_dict = validated_metadata_model.dict()
        except json.JSONDecodeError:
            raise HTTPException(status_code=400, detail="Invalid metadata format. Must be valid JSON.")
        except Exception as e: 
            raise HTTPException(status_code=400, detail=f"Invalid metadata content: {str(e)}")

    if parsed_metadata_as_dict is None:
        default_metadata_model = DataMetadata(source=DataSource.UPLOAD)
        parsed_metadata_as_dict = default_metadata_model.dict()
    
    os.makedirs(settings.DATA_DIR, exist_ok=True)
    temp_file_id_prefix = str(uuid.uuid4())
    local_file_path = os.path.join(settings.DATA_DIR, f"{temp_file_id_prefix}_{file.filename}")
    
    try:
        with open(local_file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        s3_path_for_db = None
        if settings.AWS_ACCESS_KEY_ID and settings.AWS_SECRET_ACCESS_KEY:
            try:
                s3_object_name = f"raw/{temp_file_id_prefix}/{file.filename}"
                s3_service.upload_file(local_file_path, s3_object_name)
                s3_path_for_db = s3_object_name
            except Exception as e:
                print(f"Error uploading to S3: {str(e)}")
                raise HTTPException(status_code=500, detail=f"Failed to upload file to S3: {str(e)}")

        db_datafile_instance = DBDataFile(
            filename=file.filename,
            s3_path=s3_path_for_db,
            file_metadata=parsed_metadata_as_dict
        )
        session.add(db_datafile_instance)
        await session.commit()
        await session.refresh(db_datafile_instance)
        return db_datafile_instance
    finally:
        if os.path.exists(local_file_path):
            try:
                os.remove(local_file_path)
            except Exception as e:
                print(f"Error deleting temporary local file {local_file_path}: {str(e)}")

@router.get("/files", response_model=DataFileList)
async def list_data_files(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    # status: Optional[DataStatus] = None, # Status field not in DBDataFile model yet
    session: AsyncSession = Depends(get_session)
):
    """
    List all data files from the database.
    """
    count_statement = select(func.count(DBDataFile.id))
    total_count_result = await session.exec(count_statement)
    total_count = total_count_result.one_or_none() # Should be 'one()' if table not empty
    if total_count is None:
        total_count = 0

    statement = select(DBDataFile).offset(skip).limit(limit).order_by(DBDataFile.upload_date.desc())
    # if status: # Add this when/if status field is added to DBDataFile model
    #     statement = statement.where(DBDataFile.status == status.value) # Assuming status is an enum
    
    result = await session.exec(statement)
    files = result.scalars().all()
    
    return {
        "total": total_count,
        "items": files
    }

@router.get("/files/{file_id}", response_model=DataFileResponse)
async def get_data_file(
    file_id: uuid.UUID, # Changed to uuid.UUID for direct use with session.get
    session: AsyncSession = Depends(get_session)
):
    """
    Get a specific data file by ID from the database.
    """
    db_datafile = await session.get(DBDataFile, file_id)
    if not db_datafile:
        raise HTTPException(status_code=404, detail="Data file not found")
    return db_datafile

@router.get("/files/{file_id}/preview")
async def preview_data_file(
    file_id: uuid.UUID, 
    rows: int = Query(10, ge=1, le=100),
    session: AsyncSession = Depends(get_session)
):
    """
    Preview the contents of a data file.
    This implementation requires the file to be accessible, preferably from S3.
    """
    db_datafile = await session.get(DBDataFile, file_id)
    if not db_datafile:
        raise HTTPException(status_code=404, detail="Data file not found")

    if not db_datafile.s3_path:
        raise HTTPException(status_code=404, detail="File not found in S3 or path is missing.")

    temp_preview_path = None
    try:
        # Download from S3 to a temporary local file for preview
        base_name = os.path.basename(db_datafile.s3_path) # Or use db_datafile.filename
        temp_preview_path = os.path.join(settings.DATA_DIR, f"preview_{uuid.uuid4()}_{base_name}")
        os.makedirs(settings.DATA_DIR, exist_ok=True) # Ensure dir exists

        s3_service.download_file(db_datafile.s3_path, temp_preview_path)
        
        if not os.path.exists(temp_preview_path) or os.path.getsize(temp_preview_path) == 0:
             raise HTTPException(status_code=500, detail="Failed to download file from S3 for preview or file is empty.")

        # Try to read as CSV (can be extended for other types)
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
        # Catch any other errors (e.g., file format not CSV, S3 access issues if not caught by service)
        raise HTTPException(status_code=500, detail=f"Error reading or previewing file: {str(e)}")
    finally:
        # Clean up the temporary downloaded file
        if temp_preview_path and os.path.exists(temp_preview_path):
            try:
                os.remove(temp_preview_path)
            except Exception as e:
                print(f"Error deleting temporary preview file {temp_preview_path}: {str(e)}")


@router.delete("/files/{file_id}", status_code=204) # Return 204 No Content on success
async def delete_data_file(
    file_id: uuid.UUID,
    session: AsyncSession = Depends(get_session)
):
    """
    Delete a data file record from the database and its corresponding file from S3.
    """
    db_datafile = await session.get(DBDataFile, file_id)
    if not db_datafile:
        raise HTTPException(status_code=404, detail="Data file not found")

    # Delete from S3 if s3_path exists
    if db_datafile.s3_path:
        try:
            s3_service.delete_file(db_datafile.s3_path)
        except Exception as e:
            # Log the error but proceed to delete the DB record.
            # Depending on policy, you might want to handle this more strictly.
            print(f"Error deleting file {db_datafile.s3_path} from S3: {str(e)}")
            # Optionally, raise an error if S3 deletion is critical to fail here
            # raise HTTPException(status_code=500, detail=f"Failed to delete file from S3: {str(e)}")

    await session.delete(db_datafile)
    await session.commit()
    
    return None # FastAPI will return 204 No Content
