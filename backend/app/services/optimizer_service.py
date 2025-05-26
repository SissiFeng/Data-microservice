import asyncio
import uuid
from datetime import datetime
from typing import Optional

from sqlmodel.ext.asyncio.session import AsyncSession

from app.db.models import DBOptimizationResult, DBProcessingResult # ORM Models
from app.schemas.optimizer import OptimizerRequest # Pydantic schema for request

async def run_optimization(
    session: AsyncSession, 
    request: OptimizerRequest, 
    processing_result: DBProcessingResult # The fetched ProcessingResult ORM instance
) -> DBOptimizationResult:
    """
    Creates an optimization run record, simulates processing, and updates the record.
    """
    # Create DBOptimizationResult instance
    db_optimization_run = DBOptimizationResult(
        processing_result_id=processing_result.id,
        optimizer_params=request.optimizer_params,
        status="PENDING",
        # started_at is default_factory
    )

    session.add(db_optimization_run)
    await session.commit()
    await session.refresh(db_optimization_run)

    # Simulate optimization: Update status to RUNNING
    db_optimization_run.status = "RUNNING"
    session.add(db_optimization_run)
    await session.commit()
    await session.refresh(db_optimization_run)

    # Placeholder for actual optimization logic
    await asyncio.sleep(1) # Simulate work being done

    # Update status to COMPLETED and set results
    db_optimization_run.status = "COMPLETED"
    db_optimization_run.results = {
        "simulated_output": f"Optimization completed successfully for ProcessingResult ID: {processing_result.id}",
        "input_params_received": request.optimizer_params
    }
    db_optimization_run.completed_at = datetime.utcnow()
    
    session.add(db_optimization_run)
    await session.commit()
    await session.refresh(db_optimization_run)
    
    return db_optimization_run
