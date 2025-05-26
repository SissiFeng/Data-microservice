import uuid
from datetime import datetime
from typing import List, Optional, Any # Removed Dict

from sqlmodel import Field, Relationship, SQLModel, Column, JSON # Added Column, JSON


class DataFileBase(SQLModel):
    filename: str = Field(index=True)
    upload_date: datetime = Field(default_factory=datetime.utcnow)
    s3_path: Optional[str] = None  # Or local_path depending on storage strategy
    file_metadata: Optional[Any] = Field(default=None, sa_column=Column(JSON)) # Renamed metadata to file_metadata


class DataFile(DataFileBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True, index=True, nullable=False)

    # Relationships
    annotations: List["Annotation"] = Relationship(back_populates="data_file")
    processing_results: List["ProcessingResult"] = Relationship(back_populates="data_file")


class AnnotationBase(SQLModel):
    timestamp_start: float
    timestamp_end: float
    annotation_type: str
    label: str
    description: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Foreign Key
    data_file_id: uuid.UUID = Field(foreign_key="datafile.id", index=True)


class Annotation(AnnotationBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True, index=True, nullable=False)

    # Relationship back to DataFile
    data_file: Optional[DataFile] = Relationship(back_populates="annotations")


class ProcessingResultBase(SQLModel):
    processing_type: str
    parameters: Optional[Any] = Field(default=None, sa_column=Column(JSON))
    status: str = Field(default="pending") # e.g., pending, success, failed
    result_data: Optional[Any] = Field(default=None, sa_column=Column(JSON))
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow) # Consider onupdate in the DB

    # Foreign Key
    data_file_id: uuid.UUID = Field(foreign_key="datafile.id", index=True)


class ProcessingResult(ProcessingResultBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True, index=True, nullable=False)

    # Relationship back to DataFile
    data_file: Optional[DataFile] = Relationship(back_populates="processing_results")
    # Relationship to OptimizationResult
    optimization_runs: List["DBOptimizationResult"] = Relationship(back_populates="processing_result")


class DBOptimizationResultBase(SQLModel):
    processing_result_id: uuid.UUID = Field(foreign_key="processingresult.id", index=True) # Corrected FK to 'processingresult.id'
    optimizer_params: Optional[Any] = Field(default=None, sa_column=Column(JSON))
    status: str = Field(default="PENDING", index=True) # e.g., PENDING, RUNNING, COMPLETED, FAILED
    results: Optional[Any] = Field(default=None, sa_column=Column(JSON))
    started_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = Field(default=None)


class DBOptimizationResult(DBOptimizationResultBase, table=True):
    __tablename__ = "dboptimizationresult" # Explicit table name
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True, index=True, nullable=False)

    processing_result: Optional["ProcessingResult"] = Relationship(back_populates="optimization_runs")
