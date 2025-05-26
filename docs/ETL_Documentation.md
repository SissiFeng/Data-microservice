# ETL Components in Data Microservice

## Overview

The Extract, Transform, Load (ETL) components form the core data processing pipeline of the Data Microservice. These components are responsible for extracting information from raw data, transforming it into useful formats, and loading it into the system for analysis and visualization.

**Key Architectural Change**: ETL processing is now primarily asynchronous using Celery. When an ETL process is initiated via the API, a task is dispatched to a Celery worker queue. The worker then executes the processing in the background. This allows the API to remain responsive and enables handling of potentially long-running ETL tasks. Clients can be notified of completion or status changes via WebSockets.

## Backend ETL Components

### `backend/app/tasks.py` (`process_data_task`)
**Purpose**: This Celery task is the main entry point for all asynchronous ETL processing.
**Key Functions**:
- Fetches `DataFile` and `ProcessingResult` records from the database.
- Updates `ProcessingResult` status (e.g., `PROCESSING`, `COMPLETED`, `FAILED`).
- Downloads data from S3 (if applicable).
- Calls the appropriate processing function based on `processing_type` (e.g., rolling mean, peak detection, custom script).
- Stores results back into the `ProcessingResult` record.
- Sends WebSocket notifications upon completion or failure.

### Standard Processors (`backend/app/etl/processors/`)
- **`rolling_mean.py`**: Calculates rolling mean.
- **`peak_detection.py`**: Detects peaks in data.
- **`data_quality.py`**: Assesses data quality.

### Custom Processors (`backend/app/etl/processors/custom/`)
- User-defined Python scripts for specialized ETL tasks. See "Custom Processing Workflows" section below.

### API Endpoints (`backend/app/api/endpoints/etl.py`)
**Purpose**: Provides REST API interfaces for initiating and managing ETL tasks.
**Key Endpoints**:
- `POST /api/etl/process`: Receives processing requests, creates a `ProcessingResult` record in the database with a 'PENDING' status, and dispatches a task to the Celery queue (e.g., `process_data_task`). Returns the initial `ProcessingResult` including its ID and the Celery task ID.
- `GET /api/etl/results`: Retrieves a list of processing results from the database.
- `GET /api/etl/results/{result_id}`: Gets detailed information for a specific processing result, including its current status and any result data.
- `DELETE /api/etl/results/{result_id}`: Deletes a processing result record.
- `GET /api/etl/results/{result_id}/export`: Exports processing results (primarily from the `result_data` field of the `ProcessingResult` record).

**Example Request (Standard Processor)**:
```json
POST /api/etl/process
{
  "data_file_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
  "processing_type": "peak_detection",
  "parameters": {
    "min_peak_height": 0.1,
    "distance": 5
  }
}
```

### Database Models (`backend/app/db/models.py`)
**Purpose**: Defines SQLModel ORM data models.
**Key Models (relevant to ETL)**:
- `DataFile`: Stores metadata about uploaded data files.
- `ProcessingResult`: Stores metadata, parameters, status (`task_id`, `status`, `result_data`, etc.) for each ETL operation, linked to a `DataFile`.

**Example Model (ProcessingResult snippet)**:
```python
class ProcessingResult(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True, index=True)
    task_id: Optional[str] = Field(default=None, index=True) # Celery task ID
    data_file_id: uuid.UUID = Field(foreign_key="datafile.id")
    processing_type: str
    parameters: Optional[Dict[str, Any]] = Field(default=None, sa_column=Column(JSON))
    status: str = Field(default=ProcessingStatus.PENDING.value)
    result_data: Optional[Dict[str, Any]] = Field(default=None, sa_column=Column(JSON))
    # ... other fields like created_at, updated_at
```
*(Note: The actual model in `backend/app/db/models.py` should be referenced for full details.)*

## New Section: Custom Processing Workflows

The system now supports custom ETL processing scripts. This allows users to define their own Python scripts for specialized data transformations and analyses.

### Creating a Custom Processing Script
1.  **Location**: Place your Python script in the `backend/app/etl/processors/custom/` directory.
2.  **File Naming**: The filename (without `.py`) will be used as the `custom_script_name`. For example, `my_custom_analysis.py` would be referenced as `my_custom_analysis`.
3.  **Function Signature**: Each script must contain a function named `process` with the following signature:
    ```python
    import pandas as pd
    from typing import Dict, Any

    def process(df: pd.DataFrame, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Processes the input DataFrame based on the provided parameters.
        
        Args:
            df (pd.DataFrame): The input data.
            params (Dict[str, Any]): Custom parameters for this script, 
                                     passed from the API request.
                                     
        Returns:
            Dict[str, Any]: A dictionary containing the results of the processing.
                            This dictionary will be stored as JSON in the 
                            ProcessingResult.result_data field.
        """
        # Your custom processing logic here
        results = {"message": "Custom script executed!", "processed_rows": len(df)}
        if 'my_param' in params:
            results['my_param_value_seen'] = params['my_param']
        return results
    ```
    The returned dictionary must be JSON serializable.

### Triggering a Custom Workflow
To trigger a custom workflow via the API:
1.  Set `processing_type` to `"custom"`.
2.  In the `parameters` object:
    *   Provide `custom_script_name` with the name of your script (e.g., `"example_custom_processor"`).
    *   Provide any other parameters your script needs under the `custom_params` key, or directly if your script expects them at the top level of `params`. The current backend implementation passes the entire `parameters` object from the request to the custom script, after extracting `custom_script_name`. It's good practice to nest script-specific params under `custom_params`.

**Example API Request (Custom Processor)**:
```json
POST /api/etl/process
{
  "data_file_id": "some-uuid-goes-here",
  "processing_type": "custom",
  "parameters": {
    "custom_script_name": "example_custom_processor", 
    "custom_params": { 
      "target_column": "voltage", 
      "multiplier": 2.5 
    }
  }
}
```
The `example_custom_processor.py` (created in a previous step) expects `target_column` and `multiplier` directly within the `params` argument it receives. The backend currently extracts `custom_script_name` and passes the rest of the `parameters` field (from `ProcessingRequest`) to the custom script. If `ProcessingParameters.custom_params` is used in the request, those will be nested. Ensure your script and request align on parameter structure.

## Data Flow (with Celery)

1.  User uploads a data file through the frontend.
2.  User selects a processing type (standard or "Custom") and configures parameters in the `ProcessingPanel`.
    *   If "Custom", user provides "Custom Script Name" and JSON parameters.
3.  Frontend sends a processing request to the `POST /api/etl/process` endpoint.
4.  The API endpoint:
    *   Validates the request (e.g., checks if `DataFile` exists).
    *   Creates a `ProcessingResult` record in the database with status `PENDING` and the request parameters.
    *   Dispatches an asynchronous task (e.g., `process_data_task`) to the Celery queue, including the `ProcessingResult` ID, `DataFile` ID, processing type, and parameters.
    *   Returns an immediate response to the client, including the `ProcessingResult` ID and the Celery `task_id`.
5.  A Celery worker picks up the task from the queue.
6.  The `process_data_task` in `backend/app/tasks.py`:
    *   Updates the `ProcessingResult` status to `PROCESSING`.
    *   Downloads the data file from S3.
    *   Executes the relevant processing logic (standard processor or dynamically loaded custom script).
    *   Updates the `ProcessingResult` with the results (in `result_data`) and status (`COMPLETED` or `FAILED`).
    *   Sends a WebSocket notification (`etl_update`) to connected clients about the status change.
7.  Frontend receives the WebSocket notification and updates the UI (e.g., refreshes the `DataVisualization` or processing status display). Clients can also poll the `GET /api/etl/results/{result_id}` endpoint using the `ProcessingResult` ID.
8.  User can view/export the results.

## Extending ETL Functionality (Standard Processors)
To add a new *standard* processing type (not a dynamic custom script):
1.  Add the new type to the `ProcessingType` enum in `backend/app/schemas/etl.py` and relevant frontend type definitions.
2.  Implement the processing algorithm in a new Python file under `backend/app/etl/processors/`.
3.  Update the `process_data_task` in `backend/app/tasks.py` to include a condition for the new processing type, calling your new processor function.
4.  Update the `ProcessingPanel` component in the frontend to support the new processing type and its specific parameters.
5.  Implement visualization for the new processing results in `DataVisualization` if needed.
6.  Add mock implementation in `frontend/src/services/mockData.js` for frontend development.

These components and workflows provide a robust and extensible ETL system.
```
