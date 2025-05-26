import uuid
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field

class OptimizerRequest(BaseModel):
    processing_result_id: uuid.UUID = Field(..., description="ID of the ProcessingResult to be optimized.")
    optimizer_params: Optional[Dict[str, Any]] = Field(None, description="Specific parameters for the optimizer.")

class OptimizerResponse(BaseModel):
    optimizer_run_id: uuid.UUID = Field(..., default_factory=uuid.uuid4, description="A new ID for this optimization run.")
    status: str = Field(..., description="Status of the optimization run (e.g., pending, completed, failed).")
    input_processing_result_id: uuid.UUID = Field(..., description="ID of the ProcessingResult that was input to the optimizer.")
    results: Optional[Dict[str, Any]] = Field(None, description="The actual optimization output.")
    message: Optional[str] = Field(None, description="Optional message regarding the optimization run.")

    class Config:
        orm_mode = True # For potential future use if returning ORM models directly
        # For Pydantic v2, orm_mode is now from_attributes = True
        # However, this schema is for response, not directly mapping an ORM model yet.
        # If using Pydantic v2 and wanting to ensure compatibility for models that might be ORM-based:
        # from_attributes = True
        # For now, orm_mode is fine for Pydantic v1 compatibility if underlying models use it.
        # Given we are creating this from scratch, being explicit about Pydantic V2 is better if applicable.
        # Let's assume Pydantic V1 context based on existing project files, or be neutral.
        # The `default_factory=uuid.uuid4` for optimizer_run_id means it will be generated upon model creation.
