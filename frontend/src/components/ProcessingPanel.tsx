import { useState } from 'react';
import { etlApi } from '../services/api';
import { ProcessingType, ProcessingStatus } from '../types';
import type { DataFile, ProcessingResult } from '../types';

interface ProcessingPanelProps {
  dataFile: DataFile | null;
  onProcessingComplete?: (result: ProcessingResult) => void;
}

const ProcessingPanel: React.FC<ProcessingPanelProps> = ({
  dataFile,
  onProcessingComplete,
}) => {
  const [processingType, setProcessingType] = useState<ProcessingType>(ProcessingType.ROLLING_MEAN);
  const [parameters, setParameters] = useState({
    window_size: 5,
    column: '', // General purpose column, might be used by custom scripts too
    min_peak_height: 0,
    distance: 1,
    prominence: 1,
    width: 1,
    custom_script_name: '', // Added for custom script name
    custom_params_json: '{}', // Added for custom parameters as JSON string
  });
  });
  const [isProcessing, setIsProcessing] = useState(false); // Used for initial submission and polling
  const [error, setError] = useState<string | null>(null);
  const [pollingIntervalId, setPollingIntervalId] = useState<NodeJS.Timeout | null>(null);
  const [currentProcessingStatus, setCurrentProcessingStatus] = useState<ProcessingStatus | null>(null);
  const [currentTaskId, setCurrentTaskId] = useState<string | null>(null); // Added to store task_id

  // Effect for cleaning up interval on component unmount
  useEffect(() => {
    return () => {
      if (pollingIntervalId) {
        clearInterval(pollingIntervalId);
      }
    };
  }, [pollingIntervalId]);

  const handleProcessingTypeChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    setProcessingType(e.target.value as ProcessingType);
  };

  const handleParameterChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => { // Added HTMLTextAreaElement
    const { name, value } = e.target;
    setParameters((prev) => ({
      ...prev,
      // Keep numeric conversion for specific known fields, others as string
      [name]: (name === 'window_size' || name === 'min_peak_height' || name === 'distance' || name === 'prominence' || name === 'width') && value !== '' ? Number(value) : value,
    }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!dataFile) {
      setError('No data file selected');
      return;
    }

    setIsProcessing(true);
    setError(null);

    try {
      // Prepare parameters based on processing type
      const processParams: any = {};

      if (processingType === ProcessingType.ROLLING_MEAN) {
        processParams.window_size = parameters.window_size;
        if (parameters.column) {
          processParams.columns = [parameters.column];
        }
      } else if (processingType === ProcessingType.PEAK_DETECTION) {
        if (parameters.column) {
          processParams.column = parameters.column;
        }
        processParams.height = parameters.min_peak_height;
        processParams.distance = parameters.distance;
        processParams.prominence = parameters.prominence;
        processParams.width = parameters.width;
      } else if (processingType === ProcessingType.CUSTOM) {
        if (!parameters.custom_script_name) {
          setError('Custom Script Name is required for Custom processing type.');
          setIsProcessing(false);
          return;
        }
        processParams.custom_script_name = parameters.custom_script_name;
        try {
          // Merge JSON params with other specific params like 'column' if applicable
          const customJsonParams = JSON.parse(parameters.custom_params_json || '{}');
          processParams.custom_params = { ...customJsonParams }; 
          // Add other relevant general params if your custom scripts expect them, e.g. 'column'
          if (parameters.column) {
            processParams.custom_params.target_column = parameters.column; // Example: pass 'column' as 'target_column'
          }
        } catch (jsonError) {
          setError('Invalid JSON format for Custom Parameters.');
          setIsProcessing(false);
          return;
        }
      }

      const result = await etlApi.processData({
        data_file_id: dataFile.id,
        processing_type: processingType,
        parameters: processParams, // This now includes custom_script_name and parsed custom_params
      });

      // The backend now immediately returns a PENDING status with a task_id.
      // The actual processing happens via Celery. We need to poll using the result.id.
      setCurrentProcessingStatus(result.status);
      setCurrentTaskId(result.task_id || null); // Store the task_id from the initial response
      if (result.status === ProcessingStatus.PENDING || result.status === ProcessingStatus.PROCESSING) {
        // Start polling using the ProcessingResult ID (result.id)
        startPolling(result.id);
      } else { // Should not happen if backend adheres to PENDING first
        onProcessingComplete?.(result);
        setIsProcessing(false); // Stop loading state if completed/failed immediately
      }
    } catch (err) {
      console.error('Error processing data:', err);
      setError((err as Error).message || 'Failed to process data. Please try again.');
      setIsProcessing(false); // Stop loading on error
    }
    // No finally block for setIsProcessing(false) here, as polling will handle it
  };

  const startPolling = (processingResultId: string) => {
    if (pollingIntervalId) {
      clearInterval(pollingIntervalId); // Clear any existing interval
    }

    setIsProcessing(true); // Keep processing indicator active
    setCurrentProcessingStatus(ProcessingStatus.PENDING); // Initial status display

    const intervalId = setInterval(async () => {
      try {
        const currentResult = await etlApi.getResult(processingResultId);
        setCurrentProcessingStatus(currentResult.status);

        if (currentResult.status === ProcessingStatus.COMPLETED || currentResult.status === ProcessingStatus.FAILED) {
          clearInterval(intervalId);
          setPollingIntervalId(null);
          onProcessingComplete?.(currentResult);
          setIsProcessing(false); // Stop processing indicator
          if (currentResult.status === ProcessingStatus.FAILED) {
            setError(currentResult.result_data?.error || 'Processing failed without specific error.');
          }
        }
      } catch (err) {
        console.error('Error polling processing result:', err);
        setError('Failed to get processing status. Polling stopped.');
        clearInterval(intervalId);
        setPollingIntervalId(null);
        setIsProcessing(false); // Stop processing indicator on polling error
      }
    }, 2000); // Poll every 2 seconds

    setPollingIntervalId(intervalId);
  };


  if (!dataFile) {
    return (
      <div className="bg-white shadow rounded-lg p-6">
        <div className="text-center py-4 text-gray-500">
          Select a data file to process
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white shadow rounded-lg p-6">
      <h2 className="text-xl font-semibold mb-4">Process Data</h2>

      {error && (
        <div className="mb-4 p-2 bg-red-100 text-red-700 rounded">
          {error}
        </div>
      )}
      {isProcessing && currentProcessingStatus && (
        <div className="mb-4 p-2 bg-blue-100 text-blue-700 rounded">
          Processing... Status: {currentProcessingStatus} 
          {currentTaskId && ` (Task ID: ${currentTaskId})`}
        </div>
      )}

      <form onSubmit={handleSubmit}>
        <div className="mb-4">
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Processing Type
          </label>
          <select
            value={processingType}
            onChange={handleProcessingTypeChange}
            className="mt-1 block w-full rounded-md border-gray-300 shadow-sm
                      focus:border-blue-500 focus:ring-blue-500 sm:text-sm
                      p-2 border"
          >
            {Object.values(ProcessingType).map((type) => (
              <option key={type} value={type}>
                {type.split('_').map(word => word.charAt(0).toUpperCase() + word.slice(1)).join(' ')}
              </option>
            ))}
          </select>
        </div>

        <div className="mb-4">
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Column (optional)
          </label>
          <input
            type="text"
            name="column"
            value={parameters.column}
            onChange={handleParameterChange}
            className="mt-1 block w-full rounded-md border-gray-300 shadow-sm
                      focus:border-blue-500 focus:ring-blue-500 sm:text-sm
                      p-2 border"
            placeholder="Leave empty to use first numeric column"
          />
        </div>

        {/* Standard Processing Type Parameters */}
        {processingType === ProcessingType.ROLLING_MEAN && (
          <div className="mb-4">
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Window Size
            </label>
            <input
              type="number"
              name="window_size"
              value={parameters.window_size}
              onChange={handleParameterChange}
              min="2"
              className="mt-1 block w-full rounded-md border-gray-300 shadow-sm
                        focus:border-blue-500 focus:ring-blue-500 sm:text-sm
                        p-2 border"
            />
          </div>
        )}

        {processingType === ProcessingType.PEAK_DETECTION && (
          <>
            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Minimum Peak Height
              </label>
              <input
                type="number"
                name="min_peak_height"
                value={parameters.min_peak_height}
                onChange={handleParameterChange}
                min="0"
                step="0.1"
                className="mt-1 block w-full rounded-md border-gray-300 shadow-sm
                          focus:border-blue-500 focus:ring-blue-500 sm:text-sm
                          p-2 border"
              />
            </div>

            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Minimum Distance Between Peaks
              </label>
              <input
                type="number"
                name="distance"
                value={parameters.distance}
                onChange={handleParameterChange}
                min="1"
                className="mt-1 block w-full rounded-md border-gray-300 shadow-sm
                          focus:border-blue-500 focus:ring-blue-500 sm:text-sm
                          p-2 border"
              />
            </div>

            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Prominence
              </label>
              <input
                type="number"
                name="prominence"
                value={parameters.prominence}
                onChange={handleParameterChange}
                min="0"
                step="0.1"
                className="mt-1 block w-full rounded-md border-gray-300 shadow-sm
                          focus:border-blue-500 focus:ring-blue-500 sm:text-sm
                          p-2 border"
              />
            </div>

            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Width
              </label>
              <input
                type="number"
                name="width"
                value={parameters.width}
                onChange={handleParameterChange}
                min="1"
                className="mt-1 block w-full rounded-md border-gray-300 shadow-sm
                          focus:border-blue-500 focus:ring-blue-500 sm:text-sm
                          p-2 border"
              />
            </div>
          </>
        )}

        {/* Custom Processing Type Parameters */}
        {processingType === ProcessingType.CUSTOM && (
          <>
            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Custom Script Name
              </label>
              <input
                type="text"
                name="custom_script_name"
                value={parameters.custom_script_name}
                onChange={handleParameterChange}
                className="mt-1 block w-full rounded-md border-gray-300 shadow-sm
                          focus:border-blue-500 focus:ring-blue-500 sm:text-sm
                          p-2 border"
                placeholder="e.g., example_custom_processor"
              />
            </div>
            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Custom Parameters (JSON)
              </label>
              <textarea
                name="custom_params_json"
                value={parameters.custom_params_json}
                onChange={handleParameterChange}
                rows={4}
                className="mt-1 block w-full rounded-md border-gray-300 shadow-sm
                          focus:border-blue-500 focus:ring-blue-500 sm:text-sm
                          p-2 border"
                placeholder='e.g., {"alpha": 0.5, "iterations": 100}'
              />
            </div>
          </>
        )}

        <div className="flex justify-end">
          <button
            type="submit"
            disabled={isProcessing}
            className="inline-flex justify-center py-2 px-4 border border-transparent
                      shadow-sm text-sm font-medium rounded-md text-white bg-blue-600
                      hover:bg-blue-700 focus:outline-none focus:ring-2
                      focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50"
          >
            {isProcessing ? 'Processing...' : 'Process Data'}
          </button>
        </div>
      </form>
    </div>
  );
};

export default ProcessingPanel;
