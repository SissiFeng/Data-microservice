# ETL Components in Data Microservice

## Overview

The Extract, Transform, Load (ETL) components form the core data processing pipeline of the Data Microservice. These components are responsible for extracting information from raw data, transforming it into useful formats, and loading it into the system for analysis and visualization.

This document provides an overview of the ETL-related files in the Data Microservice, their purposes, and how they interact to form a complete data processing workflow.

## Backend ETL Components

### data_process.py
**Purpose**: Core data processing engine that implements various data transformation and analysis algorithms.

**Key Functions**:
- Rolling mean calculation
- Peak detection algorithms
- Data quality assessment
- Support for custom processing workflows

**Usage**:
```python
# Example of using the peak detection function
from data_process import detect_peaks

peaks = detect_peaks(data, height=0.1, distance=5, prominence=0.2, width=1)
```

### api.py (ETL-related endpoints)
**Purpose**: Provides REST API interfaces for ETL functionality.

**Key Endpoints**:
- `/api/etl/process`: Receives processing requests and calls the appropriate processing functions
- `/api/etl/results`: Retrieves processing results
- `/api/etl/results/{result_id}`: Gets detailed information for a specific processing result
- `/api/etl/results/{result_id}/export`: Exports processing results

**Example Request**:
```json
POST /api/etl/process
{
  "data_file_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
  "processing_type": "peak_detection",
  "parameters": {
    "height": 0.1,
    "distance": 5,
    "prominence": 0.2,
    "width": 1
  }
}
```

### sqlalchemy_models.py (ETL-related models)
**Purpose**: Defines data models for ETL processing results.

**Key Models**:
- `ProcessingResult`: Stores metadata and result data for processing operations
- `ProcessingType`: Defines supported processing types (enum)
- `ProcessingStatus`: Defines processing statuses (enum)

**Example Model**:
```python
class ProcessingResult(Base):
    __tablename__ = "processing_results"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    data_file_id = Column(String, ForeignKey("data_files.id"), nullable=False)
    processing_type = Column(String, nullable=False)
    parameters = Column(JSON, nullable=True)
    result_file = Column(String, nullable=True)
    result_data = Column(JSON, nullable=True)
    status = Column(String, nullable=False, default="pending")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
```

## Frontend ETL Components

### frontend/src/services/api.ts (ETL-related functions)
**Purpose**: Frontend API client for communicating with the backend ETL services.

**Key Functions**:
- `etlApi.processData`: Sends data processing requests
- `etlApi.getResults`: Retrieves list of processing results
- `etlApi.getResult`: Gets a specific processing result
- `etlApi.exportResult`: Exports processing results

**Example Usage**:
```typescript
// Process a data file
const result = await etlApi.processData({
  data_file_id: selectedFile.id,
  processing_type: ProcessingType.PEAK_DETECTION,
  parameters: {
    height: 0.1,
    distance: 5,
    prominence: 0.2,
    width: 1
  }
});
```

### frontend/src/components/ProcessingPanel.tsx
**Purpose**: Provides a user interface for selecting processing types and parameters.

**Key Features**:
- Processing type selection (rolling mean, peak detection, etc.)
- Processing parameter configuration (window size, peak height, etc.)
- Submission of processing requests and handling of results

**Component Structure**:
- Processing type dropdown
- Parameter input fields (dynamically shown based on selected processing type)
- Process button to submit the request

### frontend/src/components/DataVisualization.tsx
**Purpose**: Visualizes raw data and processing results.

**Key Features**:
- Display of raw data charts
- Visualization of processing results (e.g., rolling mean lines, detected peaks)
- Interactive data exploration

**Visualization Types**:
- Line charts for time series data
- Scatter plots for peak detection
- Reference lines for important thresholds

### frontend/src/services/mockData.js (ETL-related functions)
**Purpose**: Provides mock ETL processing functionality for frontend development and testing.

**Key Functions**:
- `mockProcessFile`: Simulates data processing, returning different results based on processing type
- Mock implementations of peak detection and rolling mean calculations

**Example**:
```javascript
// Mock processing function
export const mockProcessFile = async (fileId, params) => {
  // Simulate network delay
  await new Promise(resolve => setTimeout(resolve, 1500));
  
  // Create result based on processing type
  if (params.processing_type === 'peak_detection') {
    // Mock peak detection logic
    // ...
  } else if (params.processing_type === 'rolling_mean') {
    // Mock rolling mean calculation
    // ...
  }
  
  return {
    id: 'mock-result-id',
    data_file_id: fileId,
    processing_type: params.processing_type,
    parameters: params.parameters,
    status: 'completed',
    // ...
  };
};
```

### frontend/src/types/index.ts (ETL-related types)
**Purpose**: Defines TypeScript types for ETL-related components.

**Key Types**:
- `ProcessingType`: Processing type enum
- `ProcessingStatus`: Processing status enum
- `ProcessingParameters`: Processing parameters interface
- `ProcessingResult`: Processing result interface

**Example**:
```typescript
export enum ProcessingType {
  ROLLING_MEAN = 'rolling_mean',
  PEAK_DETECTION = 'peak_detection',
  DATA_QUALITY = 'data_quality',
  CUSTOM = 'custom',
}

export interface ProcessingResult {
  id: string;
  data_file_id: string;
  processing_type: ProcessingType;
  parameters: ProcessingParameters;
  result_file?: string;
  result_data?: Record<string, any>;
  status: ProcessingStatus;
  created_at: string;
  updated_at: string;
}
```

### frontend/src/components/ExportPanel.tsx
**Purpose**: Provides a user interface for exporting processing results.

**Key Features**:
- Export to CSV or JSON format
- Handling of export requests and file downloads

## Data Flow

The ETL workflow in the Data Microservice follows these steps:

1. User uploads a data file (CSV, etc.) through the frontend
2. User selects processing type and parameters in the ProcessingPanel
3. Frontend sends a processing request to the backend via etlApi
4. Backend api.py receives the request and calls the appropriate function in data_process.py
5. Processing results are stored in the database (using models defined in sqlalchemy_models.py)
6. Frontend retrieves the processing results and displays them in the DataVisualization component
7. User can export the processing results via the ExportPanel

## Best Practices for ETL Development

When extending or modifying the ETL components, consider the following best practices:

1. **Modularity**: Keep processing algorithms modular and focused on a single task
2. **Error Handling**: Implement robust error handling for data processing functions
3. **Performance**: Consider performance implications for large datasets
4. **Testing**: Write unit tests for processing algorithms to ensure correctness
5. **Documentation**: Document parameters and expected outputs for all processing functions
6. **Validation**: Validate input parameters before processing
7. **Asynchronous Processing**: Use asynchronous processing for long-running tasks

## Extending ETL Functionality

To add a new processing type:

1. Add the new type to the `ProcessingType` enum in both backend and frontend
2. Implement the processing algorithm in data_process.py
3. Add the appropriate API endpoint in api.py
4. Update the ProcessingPanel component to support the new processing type
5. Implement visualization for the new processing results in DataVisualization
6. Add mock implementation in mockData.js for frontend development

These components collectively form the ETL functionality of the Data Microservice, enabling the system to extract valuable information from raw data and provide it to users in visualized and exportable formats.
