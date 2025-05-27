import uuid
from typing import Optional

from litestar import Router, post # Replaced APIRouter with Router and post
from litestar.exceptions import HTTPException # Replaced FastAPI's HTTPException
from sqlmodel.ext.asyncio.session import AsyncSession

# get_session is no longer needed here, will be injected by app
from app.schemas.optimizer import OptimizerRequest, OptimizerResponse
from app.db.models import ProcessingResult as DBProcessingResult
from app.db.models import DBOptimizationResult # Import the new ORM model
from app.services.optimizer_service import run_optimization # Import the service function

@post("/run")
async def run_optimizer_handler( # Renamed function
    data: OptimizerRequest, # Changed request to data
    session: AsyncSession # Depends(get_session) removed
) -> OptimizerResponse:
    """
    Accepts an optimization request, initiates an optimization run via optimizer_service,
    and returns the outcome.
    """
    # Verify that the processing_result_id from the data exists
    db_processing_result = await session.get(DBProcessingResult, data.processing_result_id)
    if not db_processing_result:
        raise HTTPException(
            status_code=404,
            detail=f"ProcessingResult with id {data.processing_result_id} not found."
        )

    # Call the optimizer service
    db_optimization_run = await run_optimization(
        session=session, 
        request=data, # Pass data (OptimizerRequest) as request to the service
        processing_result=db_processing_result
    )

    return OptimizerResponse(
        optimizer_run_id=db_optimization_run.id,
        status=db_optimization_run.status,
        input_processing_result_id=db_optimization_run.processing_result_id,
        results=db_optimization_run.results,
        message=f"Optimization run {db_optimization_run.id} status: {db_optimization_run.status}"
    )

optimizer_router = Router(path="/optimizer", route_handlers=[run_optimizer_handler])
