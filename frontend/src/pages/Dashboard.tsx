import { useState, useEffect } from 'react';
import EnhancedFileUpload from '../components/EnhancedFileUpload';
import FileList from '../components/FileList';
import DataVisualization from '../components/DataVisualization';
import ProcessingPanel from '../components/ProcessingPanel';
import AnnotationPanel from '../components/AnnotationPanel';
import ExportPanel from '../components/ExportPanel';
import { OptimizerPanel } from '../components/OptimizerPanel';
import type { DataFile, ProcessingResult } from '../types';
import useWebSocket from '../services/websocket';
import { etlApi } from '../services/api'; // Added etlApi for fetching results
import { v4 as uuidv4 } from 'uuid';

const Dashboard: React.FC = () => {
  const [selectedFile, setSelectedFile] = useState<DataFile | null>(null);
  const [processingResult, setProcessingResult] = useState<ProcessingResult | null>(null);

  // Generate a client ID for WebSocket
  const clientId = useState(() => uuidv4())[0];

  // Connect to WebSocket
  const { isConnected, messages } = useWebSocket(clientId);

  // Handle WebSocket messages
  useEffect(() => {
    if (messages.length > 0) {
      const latestMessage = messages[messages.length - 1];

      if (latestMessage.type === 'new_data') {
        console.log('WebSocket: new_data received', latestMessage.data);
        handleRefresh(); // Placeholder for actual file list refresh
      } else if (latestMessage.type === 'etl_update') {
        console.log('WebSocket: etl_update received', latestMessage.data);
        const { data_file_id, processing_result_id, status } = latestMessage.data;
        // If this update is for the currently selected file and there's a processing result ID
        if (selectedFile && data_file_id === selectedFile.id && processing_result_id) {
          // If the current processingResult matches or if we want to update to this new one.
          // Also, ensure we don't re-set if the status is already final (COMPLETED/FAILED) unless it's a new result.
          if (processingResult?.id !== processing_result_id || 
              (processingResult?.id === processing_result_id && 
               processingResult?.status !== 'COMPLETED' && 
               processingResult?.status !== 'FAILED')) {
            
            etlApi.getResult(processing_result_id)
              .then(updatedProcessingResult => {
                setProcessingResult(updatedProcessingResult);
                console.log('Processing result updated from etl_update:', updatedProcessingResult);
              })
              .catch(error => {
                console.error('Error fetching updated processing result:', error);
              });
          }
        }
      } else if (latestMessage.type === 'annotation_update') {
        console.log('WebSocket: annotation_update received', latestMessage.data);
        const { data_file_id, annotation_id, action } = latestMessage.data;
        if (selectedFile && data_file_id === selectedFile.id) {
          // Annotation updates would typically trigger a refresh of the AnnotationPanel.
          // This might involve AnnotationPanel having its own useEffect to refetch annotations
          // when a 'refreshAnnotations' prop changes, or by directly calling a refetch function.
          // For now, just logging. A simple way is to change a key on AnnotationPanel to force re-mount.
          console.log(`Annotation ${action} for annotation_id: ${annotation_id} on data_file_id: ${data_file_id}`);
          // Example: setAnnotationRefreshKey(prevKey => prevKey + 1); // if AnnotationPanel takes such a key
        }
      }
      // Note: The old 'processing_complete' message type might be redundant if 'etl_update' covers it.
      // If 'processing_complete' is still used by some backend parts (e.g. older websocket implementation), keep its handler or merge logic.
    }
  }, [messages, selectedFile, processingResult]); // Added processingResult to dependencies

  const handleFileSelect = (file: DataFile) => {
    setSelectedFile(file);
    setProcessingResult(null);
  };

  const handleUploadSuccess = () => {
    handleRefresh();
  };

  const handleProcessingComplete = (result: ProcessingResult) => {
    setProcessingResult(result);
  };

  const handleRefresh = () => {
    // Trigger a refresh by forcing a re-render
    // This is a placeholder for actual refresh logic
    console.log("Refreshing file list...");
  };

  return (
    <div className="min-h-screen bg-background">
      <header className="bg-card shadow-sm border-b">
        <div className="max-w-7xl mx-auto py-6 px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-foreground">
                Data Processing Microservice
              </h1>
              <p className="mt-1 text-sm text-muted-foreground">
                Upload, process, visualize, and annotate experimental data
              </p>
            </div>
            {isConnected && (
              <span className="inline-flex items-center px-3 py-1 rounded-full text-xs font-medium bg-primary/10 text-primary">
                Realtime Connected
              </span>
            )}
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto py-8 px-4 sm:px-6 lg:px-8">
        {/* Upper Section: File Upload and File List */}
        <div className="grid grid-cols-1 gap-8 lg:grid-cols-3 mb-8">
          <div className="lg:col-span-1">
            <EnhancedFileUpload onUploadSuccess={handleUploadSuccess} />
          </div>
          <div className="lg:col-span-2">
            <div className="grid grid-cols-1 gap-8 md:grid-cols-2">
              <div className="md:col-span-1">
                <FileList
                  onFileSelect={handleFileSelect}
                  onRefresh={handleRefresh}
                />
              </div>
              <div className="md:col-span-1">
                <AnnotationPanel
                  dataFile={selectedFile}
                  processingResult={processingResult}
                />
              </div>
            </div>
          </div>
        </div>

        {/* Lower Section: Processing Panel and Data Visualization */}
        <div className="grid grid-cols-1 gap-8 lg:grid-cols-3">
          {/* Left Column - Processing Controls */}
          <div className="lg:col-span-1 space-y-8">
            <ProcessingPanel
              dataFile={selectedFile}
              onProcessingComplete={handleProcessingComplete}
            />
            {processingResult && ( // Conditionally render OptimizerPanel if a processingResult is available
              <OptimizerPanel
                key={processingResult.id} // Add key to re-mount if processingResult changes
                initialProcessingResultId={processingResult.id}
              />
            )}
            <ExportPanel processingResult={processingResult} />
          </div>

          {/* Right Column - Data Visualization */}
          <div className="lg:col-span-2">
            <DataVisualization
              dataFile={selectedFile}
              processingResult={processingResult}
            />
          </div>
        </div>
      </main>
    </div>
  );
};

export default Dashboard;
