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
    column: '',
    min_peak_height: 0,
    distance: 1,
    prominence: 1,
    width: 1,
  });
  const [isProcessing, setIsProcessing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleProcessingTypeChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    setProcessingType(e.target.value as ProcessingType);
  };

  const handleParameterChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setParameters((prev) => ({
      ...prev,
      [name]: name === 'column' ? value : Number(value),
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
      }

      const result = await etlApi.processData({
        data_file_id: dataFile.id,
        processing_type: processingType,
        parameters: processParams,
      });

      // Poll for completion if needed
      if (result.status === ProcessingStatus.PENDING || result.status === ProcessingStatus.PROCESSING) {
        await pollProcessingResult(result.id);
      } else {
        onProcessingComplete?.(result);
      }
    } catch (err) {
      console.error('Error processing data:', err);
      setError('Failed to process data. Please try again.');
    } finally {
      setIsProcessing(false);
    }
  };

  const pollProcessingResult = async (resultId: string) => {
    let attempts = 0;
    const maxAttempts = 30; // 30 seconds max

    const poll = async () => {
      attempts++;

      try {
        const result = await etlApi.getResult(resultId);

        if (result.status === ProcessingStatus.COMPLETED || result.status === ProcessingStatus.FAILED) {
          onProcessingComplete?.(result);
          return;
        }

        if (attempts >= maxAttempts) {
          setError('Processing is taking longer than expected. Check results later.');
          return;
        }

        // Continue polling
        setTimeout(poll, 1000);
      } catch (err) {
        console.error('Error polling processing result:', err);
        setError('Failed to get processing status');
      }
    };

    await poll();
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
