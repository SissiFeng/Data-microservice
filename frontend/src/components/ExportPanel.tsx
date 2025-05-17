import { useState } from 'react';
import { etlApi } from '../services/api';
import { ProcessingStatus } from '../types';
import type { ProcessingResult } from '../types';
import { ArrowDownTrayIcon } from '@heroicons/react/24/outline';

interface ExportPanelProps {
  processingResult: ProcessingResult | null;
}

const ExportPanel: React.FC<ExportPanelProps> = ({ processingResult }) => {
  const [isExporting, setIsExporting] = useState(false);

  const handleExport = async (format: 'csv' | 'json') => {
    if (!processingResult) return;

    setIsExporting(true);
    try {
      await etlApi.exportResult(processingResult.id, format);
    } catch (err) {
      console.error('Error exporting data:', err);
    } finally {
      setIsExporting(false);
    }
  };

  if (!processingResult || processingResult.status !== ProcessingStatus.COMPLETED) {
    return null;
  }

  return (
    <div className="bg-white shadow rounded-lg p-6">
      <h2 className="text-xl font-semibold mb-4">Export Data</h2>

      <p className="text-sm text-gray-600 mb-4">
        Export the processed data in your preferred format
      </p>

      <div className="flex space-x-2">
        <button
          onClick={() => handleExport('csv')}
          disabled={isExporting}
          className="inline-flex items-center justify-center py-2 px-4 border border-transparent
                    shadow-sm text-sm font-medium rounded-md text-white bg-green-600
                    hover:bg-green-700 focus:outline-none focus:ring-2
                    focus:ring-offset-2 focus:ring-green-500 disabled:opacity-50"
        >
          <ArrowDownTrayIcon className="h-5 w-5 mr-2" />
          Export as CSV
        </button>

        <button
          onClick={() => handleExport('json')}
          disabled={isExporting}
          className="inline-flex items-center justify-center py-2 px-4 border border-transparent
                    shadow-sm text-sm font-medium rounded-md text-white bg-blue-600
                    hover:bg-blue-700 focus:outline-none focus:ring-2
                    focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50"
        >
          <ArrowDownTrayIcon className="h-5 w-5 mr-2" />
          Export as JSON
        </button>
      </div>
    </div>
  );
};

export default ExportPanel;
