import { useState, useEffect } from 'react';
import EnhancedFileUpload from '../components/EnhancedFileUpload';
import FileList from '../components/FileList';
import DataVisualization from '../components/DataVisualization';
import ProcessingPanel from '../components/ProcessingPanel';
import AnnotationPanel from '../components/AnnotationPanel';
import ExportPanel from '../components/ExportPanel';
import type { DataFile, ProcessingResult } from '../types';
import useWebSocket from '../services/websocket';
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
        // Refresh file list when new data is available
        handleRefresh();
      } else if (latestMessage.type === 'processing_complete') {
        // Update processing result if it matches the current file
        if (selectedFile && latestMessage.data.data_file_id === selectedFile.id) {
          setProcessingResult(latestMessage.data);
        }
      }
    }
  }, [messages, selectedFile]);

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
