import asyncio
import uuid
from datetime import datetime
from typing import Dict, Any
import os
import pandas as pd
import importlib # For dynamic custom script loading

from app.celery_worker import celery_app
from app.core.config import settings
from app.db.models import ProcessingResult as DBProcessingResult, DataFile as DBDataFile
from app.schemas.etl import ProcessingStatus, ProcessingType # Enums

# Import ETL processors
from app.etl.processors import rolling_mean, peak_detection, data_quality
from app.services import s3_service # Assuming s3_service is correctly set up

# Database session setup for tasks
from sqlalchemy.ext.asyncio import create_async_engine
from sqlmodel.ext.asyncio.session import AsyncSession as TaskAsyncSession
from sqlalchemy.orm import sessionmaker

from app.api.endpoints.websocket import notify_clients # Added for WebSocket notifications

# Create a new engine instance for tasks
# Note: echo=False is usually preferred for background tasks to reduce log noise
task_engine = create_async_engine(settings.DATABASE_URL, echo=False, future=True)
TaskAsyncSessionLocal = sessionmaker(task_engine, class_=TaskAsyncSession, expire_on_commit=False)


@celery_app.task(bind=True, name="process_data_task")
async def process_data_task(
    self, # Task instance, thanks to bind=True
    processing_id: uuid.UUID, 
    data_file_id: uuid.UUID, 
    processing_type_value: str, # Pass enum value
    parameters: Dict[str, Any]
):
    """
    Celery task to process data asynchronously.
    """
    async with TaskAsyncSessionLocal() as session:
        temp_local_path = None # Initialize for finally block
        try:
            # 1. Fetch ProcessingResult record
            db_processing_result = await session.get(DBProcessingResult, processing_id)
            if not db_processing_result:
                # Log error or handle as appropriate if record not found
                # This might indicate a race condition or an issue with DB state
                print(f"Error: ProcessingResult {processing_id} not found in task.")
                # Optionally, update task state if possible, though without a DB record, it's tricky
                # self.update_state(state='FAILURE', meta={'error': 'ProcessingResult record not found'})
                return {"status": "failed", "processing_id": str(processing_id), "error": "ProcessingResult record not found"}

            # 2. Update status to PROCESSING
            db_processing_result.status = ProcessingStatus.PROCESSING.value
            db_processing_result.updated_at = datetime.utcnow()
            session.add(db_processing_result)
            await session.commit()
            await session.refresh(db_processing_result)

            # 3. Fetch DataFile record
            db_data_file = await session.get(DBDataFile, data_file_id)
            if not db_data_file:
                raise Exception(f"DataFile {data_file_id} not found.")
            
            if not db_data_file.s3_path:
                raise Exception(f"DataFile {data_file_id} has no s3_path for processing.")

            # 4. Download data from S3 to a temporary local file
            # Ensure DATA_DIR is accessible by the Celery worker
            os.makedirs(settings.DATA_DIR, exist_ok=True) 
            temp_local_path = os.path.join(settings.DATA_DIR, f"celery_processing_{uuid.uuid4()}_{db_data_file.filename}")
            s3_service.download_file(db_data_file.s3_path, temp_local_path)

            if not os.path.exists(temp_local_path):
                 raise Exception(f"Failed to download {db_data_file.s3_path} from S3 to {temp_local_path}.")

            # 5. Perform actual processing
            # Assuming CSV for now, can be extended
            df = pd.read_csv(temp_local_path) 
            processed_data_for_db = {}

            # Convert processing_type_value back to ProcessingType enum for comparison
            current_processing_type = ProcessingType(processing_type_value)

            if current_processing_type == ProcessingType.ROLLING_MEAN:
                result_df = rolling_mean.process(df, parameters)
                processed_data_for_db = {
                    "original_columns": df.columns.tolist(),
                    "processed_columns": result_df.columns.tolist(),
                    "sample_data": result_df.head(10).to_dict(orient="records")
                }
            elif current_processing_type == ProcessingType.PEAK_DETECTION:
                peaks, properties = peak_detection.process(df, parameters)
                processed_data_for_db = {
                    "peaks": peaks.tolist() if isinstance(peaks, (list, pd.Series, np.ndarray)) else peaks,
                    "properties": {k: v.tolist() if isinstance(v, (list, pd.Series, np.ndarray)) else v
                                  for k, v in properties.items()} if properties else {}
                }
            elif current_processing_type == ProcessingType.DATA_QUALITY:
                quality_metrics = data_quality.process(df, parameters)
                processed_data_for_db = quality_metrics
            elif current_processing_type == ProcessingType.CUSTOM:
                custom_script_name = parameters.get("custom_script_name")
                if not custom_script_name:
                    raise Exception("Custom processing type selected, but 'custom_script_name' not provided.")
                
                try:
                    module_path = f"app.etl.processors.custom.{custom_script_name}"
                    custom_module = importlib.import_module(module_path)
                    custom_params = {k: v for k, v in parameters.items() if k != "custom_script_name"}
                    processed_data_for_db = custom_module.process(df, custom_params)
                except ImportError:
                    raise Exception(f"Custom script '{custom_script_name}.py' not found or module error.")
                except AttributeError:
                    raise Exception(f"'process' function not found in custom script '{custom_script_name}.py'.")
                except Exception as e_custom:
                    raise Exception(f"Error executing custom script '{custom_script_name}.py': {str(e_custom)}")
            else:
                raise Exception(f"Unsupported processing type value: {processing_type_value}")

            # 6. Update ProcessingResult record with COMPLETED status and results
            db_processing_result.status = ProcessingStatus.COMPLETED.value
            db_processing_result.result_data = processed_data_for_db
            db_processing_result.updated_at = datetime.utcnow()
            session.add(db_processing_result)
            await session.commit()

            return {"status": "completed", "processing_id": str(processing_id), "result_sample": str(processed_data_for_db)[:200]}

        except Exception as e:
            # Log error and update ProcessingResult record with FAILED status
            print(f"Error during Celery task processing {processing_id}: {str(e)}")
            if 'db_processing_result' in locals() and db_processing_result: # Check if fetched
                db_processing_result.status = ProcessingStatus.FAILED.value
                db_processing_result.result_data = {"error": str(e)}
                db_processing_result.updated_at = datetime.utcnow()
                session.add(db_processing_result)
                await session.commit()
            await session.refresh(db_processing_result) # Refresh to get latest state for notification
            # Send WebSocket notification for failure
            await notify_clients(
                event_type="etl_update", 
                data={
                    "processing_result_id": str(db_processing_result.id), 
                    "data_file_id": str(db_processing_result.data_file_id), 
                    "status": db_processing_result.status
                }
            )
            # Update Celery task state to FAILURE
            self.update_state(state='FAILURE', meta={'error': str(e), 'processing_id': str(processing_id)})
            return {"status": "failed", "processing_id": str(processing_id), "error": str(e)}
        finally:
            # 7. Clean up temporary local file
            if temp_local_path and os.path.exists(temp_local_path):
                try:
                    os.remove(temp_local_path)
                except Exception as e_clean:
                    print(f"Error cleaning up temp file {temp_local_path}: {e_clean}")
        
        # Ensure notification is sent on successful completion as well
        if 'db_processing_result' in locals() and db_processing_result and db_processing_result.status == ProcessingStatus.COMPLETED.value:
            await notify_clients(
                event_type="etl_update", 
                data={
                    "processing_result_id": str(db_processing_result.id), 
                    "data_file_id": str(db_processing_result.data_file_id), 
                    "status": db_processing_result.status
                }
            )
