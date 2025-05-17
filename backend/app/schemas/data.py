from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum

class DataStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    PROCESSED = "processed"
    FAILED = "failed"
    ANNOTATED = "annotated"

class DataSource(str, Enum):
    UPLOAD = "upload"
    WATCH = "watch"
    S3 = "s3"

class DataMetadata(BaseModel):
    experiment_id: Optional[str] = None
    operator: Optional[str] = None
    material: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.now)
    source: DataSource = DataSource.UPLOAD
    additional_metadata: Optional[Dict[str, Any]] = None

class DataFile(BaseModel):
    id: str
    filename: str
    filepath: str
    s3_key: Optional[str] = None
    metadata: DataMetadata
    status: DataStatus = DataStatus.PENDING
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

class DataFileCreate(BaseModel):
    filename: str
    metadata: Optional[DataMetadata] = None

class DataFileUpdate(BaseModel):
    metadata: Optional[DataMetadata] = None
    status: Optional[DataStatus] = None

class DataFileResponse(DataFile):
    pass

class DataFileList(BaseModel):
    total: int
    items: List[DataFileResponse]
