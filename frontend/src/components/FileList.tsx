import { useState, useEffect } from 'react';
import { dataApi } from '../services/api';
import { DataStatus } from '../types';
import type { DataFile } from '../types';
import { AlertCircle } from 'lucide-react';

interface FileListProps {
  onFileSelect?: (file: DataFile) => void;
  onRefresh?: () => void;
}

const FileList: React.FC<FileListProps> = ({ onFileSelect, onRefresh }) => {
  const [files, setFiles] = useState<DataFile[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedStatus, setSelectedStatus] = useState<DataStatus | 'all'>('all');
  const [isMockMode, setIsMockMode] = useState(false);

  const fetchFiles = async () => {
    setIsLoading(true);
    setError(null);

    try {
      const params: any = { limit: 100 };
      if (selectedStatus !== 'all') {
        params.status = selectedStatus;
      }

      // Set up a listener for console logs to detect mock mode
      const originalConsoleLog = console.log;
      console.log = function(...args) {
        if (args[0] === 'Using mock data for file listing') {
          setIsMockMode(true);
        }
        originalConsoleLog.apply(console, args);
      };

      const response = await dataApi.getFiles(params);

      // Restore original console.log
      console.log = originalConsoleLog;

      setFiles(response.items);
    } catch (err: any) {
      console.error('Error fetching files:', err);

      if (err.message && err.message.includes('Network Error')) {
        setError('Connection error: Unable to connect to the server. Please check if the backend service is running.');
      } else if (err.response) {
        const statusCode = err.response.status;
        const errorMessage = err.response.data?.detail || err.response.data?.message || 'Unknown server error';
        setError(`Server error (${statusCode}): ${errorMessage}`);
      } else if (err.request) {
        setError('No response from server: The request was sent but received no response.');
      } else {
        setError(`Failed to load files: ${err.message || 'Unknown error occurred'}`);
      }
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchFiles();
  }, [selectedStatus]);

  const handleStatusChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    setSelectedStatus(e.target.value as DataStatus | 'all');
  };

  const handleRefresh = () => {
    fetchFiles();
    onRefresh?.();
  };

  const handleDelete = async (fileId: string, e: React.MouseEvent) => {
    e.stopPropagation();

    if (!confirm('Are you sure you want to delete this file?')) {
      return;
    }

    try {
      await dataApi.deleteFile(fileId);
      setFiles((prev) => prev.filter((file) => file.id !== fileId));
    } catch (err) {
      console.error('Error deleting file:', err);
      alert('Failed to delete file. Please try again.');
    }
  };

  const getStatusBadgeClass = (status: DataStatus) => {
    switch (status) {
      case DataStatus.PENDING:
        return 'bg-amber-100 text-amber-800 dark:bg-amber-900/30 dark:text-amber-500';
      case DataStatus.PROCESSING:
        return 'bg-primary/10 text-primary dark:bg-primary/20';
      case DataStatus.PROCESSED:
        return 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-500';
      case DataStatus.FAILED:
        return 'bg-destructive/10 text-destructive dark:bg-destructive/20';
      case DataStatus.ANNOTATED:
        return 'bg-secondary/50 text-secondary-foreground dark:bg-secondary/20';
      default:
        return 'bg-muted text-muted-foreground';
    }
  };

  return (
    <div className="bg-card shadow-sm rounded-lg border">
      <div className="flex justify-between items-center p-6 border-b">
        <div>
          <h2 className="text-xl font-semibold text-card-foreground">Data Files</h2>
          {isMockMode && (
            <div className="mt-1 flex items-center gap-1.5">
              <span className="w-2 h-2 rounded-full bg-amber-500 animate-pulse"></span>
              <span className="text-xs text-amber-600 font-medium">Mock Data Mode</span>
            </div>
          )}
        </div>

        <div className="flex space-x-2">
          <select
            value={selectedStatus}
            onChange={handleStatusChange}
            className="h-9 rounded-md border border-input bg-background px-3 py-1 text-sm shadow-sm transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring"
          >
            <option value="all">All Status</option>
            {Object.values(DataStatus).map((status) => (
              <option key={status} value={status}>
                {status.charAt(0).toUpperCase() + status.slice(1)}
              </option>
            ))}
          </select>

          <button
            onClick={handleRefresh}
            className="inline-flex items-center justify-center rounded-md text-sm font-medium transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring h-9 px-4 py-2 bg-primary text-primary-foreground shadow hover:bg-primary/90"
          >
            Refresh
          </button>
        </div>
      </div>

      {isLoading ? (
        <div className="flex justify-center items-center py-8">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
          <span className="ml-3 text-sm text-muted-foreground">Loading files...</span>
        </div>
      ) : error ? (
        <div className="p-6 text-center">
          <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-destructive/10 mb-4">
            <AlertCircle className="h-8 w-8 text-destructive" />
          </div>
          <h3 className="text-lg font-medium text-foreground mb-2">Failed to load files</h3>
          <p className="text-sm text-muted-foreground mb-4 max-w-md mx-auto">{error}</p>
          <button
            onClick={handleRefresh}
            className="inline-flex items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-primary hover:bg-primary/90 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary"
          >
            Try Again
          </button>
        </div>
      ) : files.length === 0 ? (
        <div className="text-center py-8 text-muted-foreground">
          <p className="mb-2">No files found</p>
          <p className="text-sm">Upload a file to get started</p>
        </div>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-muted/50">
              <tr>
                <th className="h-10 px-4 text-left align-middle text-xs font-medium text-muted-foreground uppercase tracking-wider">
                  Filename
                </th>
                <th className="h-10 px-4 text-left align-middle text-xs font-medium text-muted-foreground uppercase tracking-wider">
                  Status
                </th>
                <th className="h-10 px-4 text-left align-middle text-xs font-medium text-muted-foreground uppercase tracking-wider">
                  Metadata
                </th>
                <th className="h-10 px-4 text-left align-middle text-xs font-medium text-muted-foreground uppercase tracking-wider">
                  Created
                </th>
                <th className="h-10 px-4 text-left align-middle text-xs font-medium text-muted-foreground uppercase tracking-wider">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border">
              {files.map((file) => (
                <tr
                  key={file.id}
                  onClick={() => onFileSelect?.(file)}
                  className="hover:bg-muted/50 cursor-pointer transition-colors"
                >
                  <td className="p-4 align-middle text-sm font-medium">
                    {file.filename}
                  </td>
                  <td className="p-4 align-middle text-sm">
                    <span className={`px-2 py-1 inline-flex text-xs leading-5 font-semibold rounded-full ${getStatusBadgeClass(file.status)}`}>
                      {file.status}
                    </span>
                  </td>
                  <td className="p-4 align-middle text-sm text-muted-foreground">
                    {file.metadata.experiment_id && (
                      <div>Exp: {file.metadata.experiment_id}</div>
                    )}
                    {file.metadata.operator && (
                      <div>Op: {file.metadata.operator}</div>
                    )}
                  </td>
                  <td className="p-4 align-middle text-sm text-muted-foreground">
                    {new Date(file.created_at).toLocaleString()}
                  </td>
                  <td className="p-4 align-middle text-sm">
                    <button
                      onClick={(e) => handleDelete(file.id, e)}
                      className="text-destructive hover:text-destructive/80 font-medium transition-colors"
                    >
                      Delete
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
};

export default FileList;
