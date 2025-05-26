import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel.ext.asyncio.session import AsyncSession

from app.db.session import get_session
from app.schemas.optimizer import OptimizerRequest, OptimizerResponse
from app.db.models import ProcessingResult as DBProcessingResult
from app.db.models import DBOptimizationResult # Import the new ORM model
from app.services.optimizer_service import run_optimization # Import the service function

router = APIRouter()

@router.post("/run", response_model=OptimizerResponse)
async def run_optimizer_endpoint( # Renamed function to avoid clash with imported service
    request: OptimizerRequest,
    session: AsyncSession = Depends(get_session)
):
    """
    Accepts an optimization request, initiates an optimization run via optimizer_service,
    and returns the outcome.
    """
    # Verify that the processing_result_id from the request exists
    db_processing_result = await session.get(DBProcessingResult, request.processing_result_id)
    if not db_processing_result:
        raise HTTPException(
            status_code=404,
            detail=f"ProcessingResult with id {request.processing_result_id} not found."
        )

    # Call the optimizer service
    db_optimization_run = await run_optimization(
        session=session, 
        request=request, 
        processing_result=db_processing_result
    )

    return OptimizerResponse(
        optimizer_run_id=db_optimization_run.id,
        status=db_optimization_run.status,
        input_processing_result_id=db_optimization_run.processing_result_id,
        results=db_optimization_run.results,
        message=f"Optimization run {db_optimization_run.id} status: {db_optimization_run.status}"
    )
