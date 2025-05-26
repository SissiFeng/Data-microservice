from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Optional
import uuid
from datetime import datetime
from sqlmodel import select, func # Added select and func

from app.schemas.annotations import (
    AnnotationCreate,
    AnnotationUpdate,
    AnnotationResponse, # Assuming this is the read schema
    AnnotationList    # For listing multiple annotations
    # AnnotationType # This was used for filtering, can be added if field exists in DB model
)
# Removed imports for data_files and processing_results from other endpoints
from app.db.session import get_session, AsyncSession
from app.db.models import Annotation as DBAnnotation # Renamed to DBAnnotation
from app.db.models import DataFile as DBDataFile     # To validate data_file_id
from app.api.endpoints.websocket import notify_clients # Added for WebSocket notifications

router = APIRouter()

# In-memory 'annotations' dictionary is now removed.

@router.post("/", response_model=AnnotationResponse)
async def create_annotation(
    annotation_create: AnnotationCreate, 
    session: AsyncSession = Depends(get_session)
):
    """
    Create a new annotation for a data file.
    """
    # Validate data file exists
    db_data_file = await session.get(DBDataFile, annotation_create.data_file_id)
    if not db_data_file:
        raise HTTPException(status_code=404, detail=f"DataFile with id {annotation_create.data_file_id} not found")

    # The DBAnnotation model (previously defined in models.py) has fields:
    # id, data_file_id, timestamp_start, timestamp_end, annotation_type, label, description, created_at
    # AnnotationCreate schema has:
    # data_file_id, timestamp_start, timestamp_end, annotation_type, label, description (Optional)

    db_annotation = DBAnnotation(
        data_file_id=annotation_create.data_file_id,
        timestamp_start=annotation_create.timestamp_start,
        timestamp_end=annotation_create.timestamp_end,
        annotation_type=annotation_create.annotation_type,
        label=annotation_create.label,
        description=annotation_create.description
        # id and created_at are set by default by the model/DB
    )
    
    session.add(db_annotation)
    await session.commit()
    await session.refresh(db_annotation)
    
    # Notify clients
    await notify_clients(
        event_type="annotation_update", 
        data={
            "data_file_id": str(db_annotation.data_file_id), 
            "annotation_id": str(db_annotation.id),
            "action": "created"
        }
    )
    
    return db_annotation

@router.get("/", response_model=AnnotationList)
async def list_annotations(
    data_file_id: Optional[uuid.UUID] = Query(None, description="Filter annotations by DataFile ID"),
    # processing_result_id: Optional[str] = None, # ProcessingResult not part of DBAnnotation model yet
    # annotation_type: Optional[AnnotationType] = None, # AnnotationType enum not used directly here yet
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    session: AsyncSession = Depends(get_session)
):
    """
    List annotations with optional filtering by data_file_id.
    """
    statement = select(DBAnnotation)
    count_statement = select(func.count(DBAnnotation.id))

    if data_file_id:
        statement = statement.where(DBAnnotation.data_file_id == data_file_id)
        count_statement = count_statement.where(DBAnnotation.data_file_id == data_file_id)
    
    # if annotation_type: # Add if 'annotation_type' string field needs filtering
    #     statement = statement.where(DBAnnotation.annotation_type == annotation_type.value)
    #     count_statement = count_statement.where(DBAnnotation.annotation_type == annotation_type.value)

    total_count_result = await session.exec(count_statement)
    total_count = total_count_result.one_or_none()
    if total_count is None:
        total_count = 0
        
    statement = statement.offset(skip).limit(limit).order_by(DBAnnotation.created_at.desc())
    
    results = await session.exec(statement)
    annotations_list = results.scalars().all()
    
    return {
        "total": total_count,
        "items": annotations_list
    }

@router.get("/{annotation_id}", response_model=AnnotationResponse)
async def get_annotation(
    annotation_id: uuid.UUID, # Path parameter is UUID
    session: AsyncSession = Depends(get_session)
):
    """
    Get a specific annotation by ID.
    """
    db_annotation = await session.get(DBAnnotation, annotation_id)
    if not db_annotation:
        raise HTTPException(status_code=404, detail="Annotation not found")
    return db_annotation

@router.put("/{annotation_id}", response_model=AnnotationResponse)
async def update_annotation(
    annotation_id: uuid.UUID,
    annotation_update: AnnotationUpdate,
    session: AsyncSession = Depends(get_session)
):
    """
    Update an existing annotation.
    """
    db_annotation = await session.get(DBAnnotation, annotation_id)
    if not db_annotation:
        raise HTTPException(status_code=404, detail="Annotation not found")
    
    update_data = annotation_update.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_annotation, key, value)
    
    # The DBAnnotation model does not have 'updated_at' automatically updated by SQLModel/SQLAlchemy
    # on every update unless a DB-level trigger or specific event listener is set.
    # For application-level timestamp, set it manually:
    db_annotation.updated_at = datetime.utcnow() # Assuming DBAnnotation model has an 'updated_at' field.
                                                # The current DBAnnotation model in previous steps did not have updated_at.
                                                # If it's required, it should be added to the model.
                                                # For now, I'll assume it's NOT in the model as per earlier definition.

    session.add(db_annotation)
    await session.commit()
    await session.refresh(db_annotation)
    
    # Notify clients
    await notify_clients(
        event_type="annotation_update", 
        data={
            "data_file_id": str(db_annotation.data_file_id), 
            "annotation_id": str(db_annotation.id),
            "action": "updated"
        }
    )
    
    return db_annotation

@router.delete("/{annotation_id}", status_code=204) # Return 204 No Content on success
async def delete_annotation(
    annotation_id: uuid.UUID,
    session: AsyncSession = Depends(get_session)
):
    """
    Delete an annotation by ID.
    """
    db_annotation = await session.get(DBAnnotation, annotation_id)
    if not db_annotation:
        raise HTTPException(status_code=404, detail="Annotation not found")
    
    # Store data_file_id before deleting for notification
    data_file_id_for_notification = str(db_annotation.data_file_id)
    annotation_id_for_notification = str(db_annotation.id)

    await session.delete(db_annotation)
    await session.commit()
    
    # Notify clients
    await notify_clients(
        event_type="annotation_update", 
        data={
            "data_file_id": data_file_id_for_notification, 
            "annotation_id": annotation_id_for_notification,
            "action": "deleted",
            "deleted": True 
        }
    )
    
    return None # FastAPI returns 204 No Content
