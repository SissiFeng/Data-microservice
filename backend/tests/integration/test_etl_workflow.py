import pytest
import asyncio
import uuid
from httpx import AsyncClient  # TestClient uses AsyncClient
from fastapi import status  # For status codes
from app.db.session import AsyncSession

from app.schemas.etl import ProcessingStatus, ProcessingType
from app.db.models import DataFile as DBDataFile, ProcessingResult as DBProcessingResult

# Mark all tests in this file as asyncio
pytestmark = pytest.mark.asyncio

async def test_upload_trigger_etl_and_get_result(
    test_client: AsyncClient,
    db_session: AsyncSession,
    sample_csv_file: tuple[str, bytes],
):
    """
    Integration test for the full ETL workflow:
    1. Upload a data file.
    2. Trigger an ETL processing task on it.
    3. Poll for the processing result until completion.
    4. Verify the result.
    """
    filename, file_content = sample_csv_file

    # 1. Upload Data File
    upload_response = await test_client.post(
        "/api/data/upload",
        files={"file": (filename, file_content, "text/csv")},
        data={"metadata": '{"experiment_id": "integration_test_001", "source": "upload"}'} # Basic metadata
    )
    assert upload_response.status_code == status.HTTP_200_OK # Assuming 200 OK from current impl
    upload_data = upload_response.json()
    data_file_id = upload_data["id"]
    assert uuid.UUID(data_file_id) # Check if it's a valid UUID

    # Verify DataFile record in DB (optional, but good for sanity)
    
    # Re-fetch from DB to ensure it's committed
    # db_datafile_record = await db_session.get(DBDataFile, uuid.UUID(data_file_id))
    # assert db_datafile_record is not None
    # assert db_datafile_record.filename == filename

    # 2. Trigger ETL Processing
    etl_request_payload = {
        "data_file_id": data_file_id,
        "processing_type": ProcessingType.ROLLING_MEAN.value,
        "parameters": {"window_size": 3, "columns": ["value1"]} # Match sample_csv_file columns
    }
    etl_response = await test_client.post("/api/etl/process", json=etl_request_payload)
    assert etl_response.status_code == status.HTTP_200_OK
    etl_data = etl_response.json()
    processing_result_id = etl_data["id"]
    task_id = etl_data.get("task_id") # task_id should be in the response
    
    assert uuid.UUID(processing_result_id)
    assert task_id is not None
    assert etl_data["status"] == ProcessingStatus.PENDING.value

    # 3. Verify Celery Task Execution and Result (Polling)
    max_retries = 20  # Max 20 retries (e.g., 20 * 2s = 40s timeout)
    retry_delay = 2  # Seconds
    final_status = None

    for attempt in range(max_retries):
        await asyncio.sleep(retry_delay)
        result_response = await test_client.get(f"/api/etl/results/{processing_result_id}")
        
        if result_response.status_code == status.HTTP_200_OK:
            result_data = result_response.json()
            final_status = result_data["status"]
            if final_status == ProcessingStatus.COMPLETED.value:
                break
            elif final_status == ProcessingStatus.FAILED.value:
                pytest.fail(f"ETL processing failed: {result_data.get('result_data', {}).get('error', 'Unknown error')}")
        else:
            # Handle cases where the result endpoint might itself fail temporarily
            print(f"Polling attempt {attempt + 1}: Failed to fetch result, status {result_response.status_code}")

    assert final_status == ProcessingStatus.COMPLETED.value, f"ETL task did not complete. Final status: {final_status}"

    # 4. Verify the result_data (basic check)
    assert "result_data" in result_data
    assert result_data["result_data"] is not None
    
    # Example check for rolling mean output structure (depends on your processor's output)
    # The current rolling_mean processor returns:
    # { "original_columns": [...], "processed_columns": [...], "sample_data": [...] }
    assert "original_columns" in result_data["result_data"]
    assert "processed_columns" in result_data["result_data"]
    assert "sample_data" in result_data["result_data"]
    
    processed_columns = result_data["result_data"]["processed_columns"]
    # 'value1_rolling_mean_3' should be in processed_columns if 'value1' was processed with window 3
    assert any("value1_rolling_mean_3" in col for col in processed_columns)

    # Further checks could involve looking at the actual data in result_data["sample_data"]
    # For example, if sample_data is a list of dicts:
    sample_output = result_data["result_data"]["sample_data"]
    assert isinstance(sample_output, list)
    if sample_output: # If not empty
        assert "value1_rolling_mean_3" in sample_output[0] # Check first row for the new column
        # Based on input [1,2,3,4,5] and window 3, center=True, min_periods=1:
        # Expected means: [1.5, 2.0, 3.0, 4.0, 4.5]
        # The sample_csv_file has value1: [1,2,3,4,5]
        # Expected sample_data[0]['value1_rolling_mean_3'] could be 1.5 (if it's the first output point)
        # This depends on how the processor aligns and handles edges.
        # The current rolling_mean.py uses center=True, min_periods=1
        # For [1,2,3,4,5], window=3:
        # idx 0 (val 1): mean(1,2) = 1.5
        # idx 1 (val 2): mean(1,2,3) = 2.0
        # idx 2 (val 3): mean(2,3,4) = 3.0
        # idx 3 (val 4): mean(3,4,5) = 4.0
        # idx 4 (val 5): mean(4,5) = 4.5
        # Assuming sample_data contains these results:
        assert len(sample_output) > 0 # Ensure there is data to check
        # Check a specific value if the output format is known and stable
        # For example, if the first row of sample_data corresponds to the first input row's processing:
        # assert sample_output[0]['value1_rolling_mean_3'] == 1.5 # (or approx)
        # Given that sample_data is result_df.head(10), this should hold.
        if len(sample_output) >= 1:
             assert sample_output[0]['value1_rolling_mean_3'] == pytest.approx(1.5)
        if len(sample_output) >= 2:
             assert sample_output[1]['value1_rolling_mean_3'] == pytest.approx(2.0)

    # Confirm persisted result in the database
    db_processing_result = await db_session.get(DBProcessingResult, uuid.UUID(processing_result_id))
    assert db_processing_result is not None
    assert db_processing_result.status == ProcessingStatus.COMPLETED.value
    assert db_processing_result.result_data is not None

    print(
        f"Successfully tested ETL workflow for data_file_id: {data_file_id}, processing_result_id: {processing_result_id}"
    )
