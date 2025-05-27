from litestar import Router, post, get, put, delete, Parameter
from litestar.exceptions import HTTPException
from typing import Optional # Removed List as it's not directly used in type hints
import uuid
from datetime import datetime # Keep for potential use, though updated_at is removed for now
from sqlmodel import select, func

from app.schemas.annotations import (
    AnnotationCreate,
    AnnotationUpdate,
    AnnotationResponse,
    AnnotationList
    # AnnotationType
)
from app.db.session import AsyncSession # get_session will be provided by dependency injection
from app.db.models import Annotation as DBAnnotation
from app.db.models import DataFile as DBDataFile
from app.api.endpoints.websocket import notify_clients

@post("/")
async def create_annotation_handler(
    data: AnnotationCreate, 
    session: AsyncSession
) -> AnnotationResponse:
    """
    Create a new annotation for a data file.
    """
    db_data_file = await session.get(DBDataFile, data.data_file_id)
    if not db_data_file:
        raise HTTPException(status_code=404, detail=f"DataFile with id {data.data_file_id} not found")

    db_annotation = DBAnnotation(
        data_file_id=data.data_file_id,
        timestamp_start=data.timestamp_start,
        timestamp_end=data.timestamp_end,
        annotation_type=data.annotation_type,
        label=data.label,
        description=data.description
    )
    
    session.add(db_annotation)
    await session.commit()
    await session.refresh(db_annotation)
    
    await notify_clients(
        event_type="annotation_update", 
        data={
            "data_file_id": str(db_annotation.data_file_id), 
            "annotation_id": str(db_annotation.id),
            "action": "created"
        }
    )
    
    return AnnotationResponse.model_validate(db_annotation)

@get("/")
async def list_annotations_handler(
    session: AsyncSession,
    data_file_id: Optional[uuid.UUID] = Parameter(default=None, query="data_file_id", required=False, description="Filter annotations by DataFile ID"),
    # annotation_type: Optional[AnnotationType] = Parameter(default=None, query="annotation_type", required=False), # If filtering by type is needed
    skip: int = Parameter(default=0, query="skip", ge=0),
    limit: int = Parameter(default=100, query="limit", ge=1, le=500)
) -> AnnotationList:
    """
    List annotations with optional filtering by data_file_id.
    """
    statement = select(DBAnnotation)
    count_statement = select(func.count(DBAnnotation.id))

    if data_file_id:
        statement = statement.where(DBAnnotation.data_file_id == data_file_id)
        count_statement = count_statement.where(DBAnnotation.data_file_id == data_file_id)
    
    # if annotation_type:
    #     statement = statement.where(DBAnnotation.annotation_type == annotation_type.value)
    #     count_statement = count_statement.where(DBAnnotation.annotation_type == annotation_type.value)

    total_count_result = await session.exec(count_statement)
    total_count = total_count_result.one_or_none()
    if total_count is None:
        total_count = 0
        
    statement = statement.offset(skip).limit(limit).order_by(DBAnnotation.created_at.desc())
    
    results_exec = await session.exec(statement)
    annotations_db = results_exec.scalars().all()
    
    items_response = [AnnotationResponse.model_validate(ann) for ann in annotations_db]
    
    return AnnotationList(
        total=total_count,
        items=items_response
    )

@get("/{annotation_id:uuid}")
async def get_annotation_handler(
    annotation_id: uuid.UUID,
    session: AsyncSession
) -> AnnotationResponse:
    """
    Get a specific annotation by ID.
    """
    db_annotation = await session.get(DBAnnotation, annotation_id)
    if not db_annotation:
        raise HTTPException(status_code=404, detail="Annotation not found")
    return AnnotationResponse.model_validate(db_annotation)

@put("/{annotation_id:uuid}")
async def update_annotation_handler(
    annotation_id: uuid.UUID,
    data: AnnotationUpdate,
    session: AsyncSession
) -> AnnotationResponse:
    """
    Update an existing annotation.
    """
    db_annotation = await session.get(DBAnnotation, annotation_id)
    if not db_annotation:
        raise HTTPException(status_code=404, detail="Annotation not found")
    
    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_annotation, key, value)
    
    # Removed: db_annotation.updated_at = datetime.utcnow() as per instructions

    session.add(db_annotation)
    await session.commit()
    await session.refresh(db_annotation)
    
    await notify_clients(
        event_type="annotation_update", 
        data={
            "data_file_id": str(db_annotation.data_file_id), 
            "annotation_id": str(db_annotation.id),
            "action": "updated"
        }
    )
    
    return AnnotationResponse.model_validate(db_annotation)

@delete("/{annotation_id:uuid}", status_code=204)
async def delete_annotation_handler(
    annotation_id: uuid.UUID,
    session: AsyncSession
) -> None:
    """
    Delete an annotation by ID.
    """
    db_annotation = await session.get(DBAnnotation, annotation_id)
    if not db_annotation:
        raise HTTPException(status_code=404, detail="Annotation not found")
    
    data_file_id_for_notification = str(db_annotation.data_file_id)
    annotation_id_for_notification = str(db_annotation.id)

    await session.delete(db_annotation)
    await session.commit()
    
    await notify_clients(
        event_type="annotation_update", 
        data={
            "data_file_id": data_file_id_for_notification, 
            "annotation_id": annotation_id_for_notification,
            "action": "deleted",
            "deleted": True 
        }
    )
    
    return None

annotations_router = Router(
    path="/annotations", 
    route_handlers=[
        create_annotation_handler,
        list_annotations_handler,
        get_annotation_handler,
        update_annotation_handler,
        delete_annotation_handler,
    ]
)
