from typing import List, Optional, Dict, Any, Union
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum

class AnnotationType(str, Enum):
    VALID = "valid"
    INVALID = "invalid"
    PEAK_CORRECTION = "peak_correction"
    EXPERIMENT_FAILED = "experiment_failed"
    OUTLIER = "outlier"
    BASELINE_SHIFT = "baseline_shift"
    NOISE = "noise"
    CUSTOM = "custom"

class Annotation(BaseModel):
    id: str
    data_file_id: str
    processing_result_id: Optional[str] = None
    annotation_type: AnnotationType
    annotation_data: Dict[str, Any] = {}
    notes: Optional[str] = None
    created_by: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

class AnnotationCreate(BaseModel):
    data_file_id: str
    processing_result_id: Optional[str] = None
    annotation_type: AnnotationType
    annotation_data: Dict[str, Any] = {}
    notes: Optional[str] = None

class AnnotationUpdate(BaseModel):
    annotation_type: Optional[AnnotationType] = None
    annotation_data: Optional[Dict[str, Any]] = None
    notes: Optional[str] = None

class AnnotationResponse(Annotation):
    pass

class AnnotationList(BaseModel):
    total: int
    items: List[AnnotationResponse]
