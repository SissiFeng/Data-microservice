from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends, Query
from fastapi.responses import JSONResponse
from typing import List, Optional
import uuid
import os
import json
import shutil
from datetime import datetime
import pandas as pd

from app.core.config import settings
from app.schemas.data import (
    DataFileCreate, 
    DataFileResponse, 
    DataFileList, 
    DataStatus,
    DataMetadata,
    DataSource
)
from app.services import s3_service

router = APIRouter()

# In-memory storage for demo purposes
# In production, use a database
data_files = {}

@router.post("/upload", response_model=DataFileResponse)
async def upload_data_file(
    file: UploadFile = File(...),
    metadata: Optional[str] = Form(None)
):
    """
    Upload a data file (CSV, etc.) with optional metadata
    """
    # Create a unique ID for the file
    file_id = str(uuid.uuid4())
    
    # Parse metadata if provided
    file_metadata = None
    if metadata:
        try:
            metadata_dict = json.loads(metadata)
            file_metadata = DataMetadata(**metadata_dict)
        except json.JSONDecodeError:
            raise HTTPException(status_code=400, detail="Invalid metadata format")
    
    if file_metadata is None:
        file_metadata = DataMetadata(source=DataSource.UPLOAD)
    
    # Ensure data directory exists
    os.makedirs(settings.DATA_DIR, exist_ok=True)
    
    # Save file locally
    file_path = os.path.join(settings.DATA_DIR, f"{file_id}_{file.filename}")
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    # Create data file record
    data_file = {
        "id": file_id,
        "filename": file.filename,
        "filepath": file_path,
        "s3_key": None,  # Will be set if uploaded to S3
        "metadata": file_metadata.dict(),
        "status": DataStatus.PENDING,
        "created_at": datetime.now(),
        "updated_at": datetime.now()
    }
    
    # Store in memory (replace with database in production)
    data_files[file_id] = data_file
    
    # Upload to S3 if configured
    if settings.AWS_ACCESS_KEY_ID and settings.AWS_SECRET_ACCESS_KEY:
        try:
            s3_key = f"raw/{file_id}/{file.filename}"
            s3_service.upload_file(file_path, s3_key)
            data_files[file_id]["s3_key"] = s3_key
        except Exception as e:
            # Log the error but continue
            print(f"Error uploading to S3: {str(e)}")
    
    return data_file

@router.get("/files", response_model=DataFileList)
async def list_data_files(
    skip: int = 0,
    limit: int = 100,
    status: Optional[DataStatus] = None
):
    """
    List all data files with optional filtering
    """
    filtered_files = list(data_files.values())
    
    if status:
        filtered_files = [f for f in filtered_files if f["status"] == status]
    
    # Sort by created_at descending
    filtered_files.sort(key=lambda x: x["created_at"], reverse=True)
    
    # Apply pagination
    paginated_files = filtered_files[skip:skip+limit]
    
    return {
        "total": len(filtered_files),
        "items": paginated_files
    }

@router.get("/files/{file_id}", response_model=DataFileResponse)
async def get_data_file(file_id: str):
    """
    Get a specific data file by ID
    """
    if file_id not in data_files:
        raise HTTPException(status_code=404, detail="Data file not found")
    
    return data_files[file_id]

@router.get("/files/{file_id}/preview")
async def preview_data_file(file_id: str, rows: int = 10):
    """
    Preview the contents of a data file
    """
    if file_id not in data_files:
        raise HTTPException(status_code=404, detail="Data file not found")
    
    file_path = data_files[file_id]["filepath"]
    
    try:
        # Try to read as CSV
        df = pd.read_csv(file_path)
        preview = df.head(rows).to_dict(orient="records")
        columns = df.columns.tolist()
        
        return {
            "columns": columns,
            "data": preview,
            "total_rows": len(df)
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error reading file: {str(e)}")

@router.delete("/files/{file_id}")
async def delete_data_file(file_id: str):
    """
    Delete a data file
    """
    if file_id not in data_files:
        raise HTTPException(status_code=404, detail="Data file not found")
    
    # Delete local file
    file_path = data_files[file_id]["filepath"]
    if os.path.exists(file_path):
        os.remove(file_path)
    
    # Delete from S3 if applicable
    if data_files[file_id]["s3_key"]:
        try:
            s3_service.delete_file(data_files[file_id]["s3_key"])
        except Exception as e:
            # Log the error but continue
            print(f"Error deleting from S3: {str(e)}")
    
    # Remove from in-memory storage
    del data_files[file_id]
    
    return {"message": "Data file deleted successfully"}
