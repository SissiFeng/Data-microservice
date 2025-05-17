from typing import List, Optional, Dict, Any, Union
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum

class ProcessingType(str, Enum):
    ROLLING_MEAN = "rolling_mean"
    PEAK_DETECTION = "peak_detection"
    DATA_QUALITY = "data_quality"
    CUSTOM = "custom"

class ProcessingStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

class ProcessingParameters(BaseModel):
    window_size: Optional[int] = None
    min_peak_height: Optional[float] = None
    distance: Optional[int] = None
    prominence: Optional[float] = None
    width: Optional[int] = None
    custom_params: Optional[Dict[str, Any]] = None

class ProcessingResult(BaseModel):
    data_file_id: str
    processing_type: ProcessingType
    parameters: ProcessingParameters
    result_file: Optional[str] = None
    result_data: Optional[Dict[str, Any]] = None
    status: ProcessingStatus = ProcessingStatus.PENDING
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

class ProcessingRequest(BaseModel):
    data_file_id: str
    processing_type: ProcessingType
    parameters: Optional[ProcessingParameters] = None

class ProcessingResponse(ProcessingResult):
    pass

class ProcessingResultList(BaseModel):
    total: int
    items: List[ProcessingResponse]
