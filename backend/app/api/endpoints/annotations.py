from fastapi import APIRouter, HTTPException
from typing import List, Optional
import uuid
from datetime import datetime

from app.schemas.annotations import (
    AnnotationCreate,
    AnnotationUpdate,
    AnnotationResponse,
    AnnotationList,
    AnnotationType
)
from app.api.endpoints.data import data_files
from app.api.endpoints.etl import processing_results

router = APIRouter()

# In-memory storage for annotations
annotations = {}

@router.post("/", response_model=AnnotationResponse)
async def create_annotation(annotation: AnnotationCreate):
    """
    Create a new annotation for a data file or processing result
    """
    # Validate data file exists
    if annotation.data_file_id not in data_files:
        raise HTTPException(status_code=404, detail="Data file not found")
    
    # Validate processing result if provided
    if annotation.processing_result_id and annotation.processing_result_id not in processing_results:
        raise HTTPException(status_code=404, detail="Processing result not found")
    
    # Create annotation
    annotation_id = str(uuid.uuid4())
    
    new_annotation = {
        "id": annotation_id,
        "data_file_id": annotation.data_file_id,
        "processing_result_id": annotation.processing_result_id,
        "annotation_type": annotation.annotation_type,
        "annotation_data": annotation.annotation_data,
        "notes": annotation.notes,
        "created_by": "user",  # Replace with actual user ID in production
        "created_at": datetime.now(),
        "updated_at": datetime.now()
    }
    
    # Store in memory
    annotations[annotation_id] = new_annotation
    
    return new_annotation

@router.get("/", response_model=AnnotationList)
async def list_annotations(
    data_file_id: Optional[str] = None,
    processing_result_id: Optional[str] = None,
    annotation_type: Optional[AnnotationType] = None,
    skip: int = 0,
    limit: int = 100
):
    """
    List annotations with optional filtering
    """
    filtered_annotations = list(annotations.values())
    
    if data_file_id:
        filtered_annotations = [a for a in filtered_annotations if a["data_file_id"] == data_file_id]
    
    if processing_result_id:
        filtered_annotations = [a for a in filtered_annotations if a["processing_result_id"] == processing_result_id]
    
    if annotation_type:
        filtered_annotations = [a for a in filtered_annotations if a["annotation_type"] == annotation_type]
    
    # Sort by created_at descending
    filtered_annotations.sort(key=lambda x: x["created_at"], reverse=True)
    
    # Apply pagination
    paginated_annotations = filtered_annotations[skip:skip+limit]
    
    return {
        "total": len(filtered_annotations),
        "items": paginated_annotations
    }

@router.get("/{annotation_id}", response_model=AnnotationResponse)
async def get_annotation(annotation_id: str):
    """
    Get a specific annotation by ID
    """
    if annotation_id not in annotations:
        raise HTTPException(status_code=404, detail="Annotation not found")
    
    return annotations[annotation_id]

@router.put("/{annotation_id}", response_model=AnnotationResponse)
async def update_annotation(annotation_id: str, update: AnnotationUpdate):
    """
    Update an existing annotation
    """
    if annotation_id not in annotations:
        raise HTTPException(status_code=404, detail="Annotation not found")
    
    # Update fields
    if update.annotation_type is not None:
        annotations[annotation_id]["annotation_type"] = update.annotation_type
    
    if update.annotation_data is not None:
        annotations[annotation_id]["annotation_data"] = update.annotation_data
    
    if update.notes is not None:
        annotations[annotation_id]["notes"] = update.notes
    
    annotations[annotation_id]["updated_at"] = datetime.now()
    
    return annotations[annotation_id]

@router.delete("/{annotation_id}")
async def delete_annotation(annotation_id: str):
    """
    Delete an annotation
    """
    if annotation_id not in annotations:
        raise HTTPException(status_code=404, detail="Annotation not found")
    
    del annotations[annotation_id]
    
    return {"message": "Annotation deleted successfully"}
