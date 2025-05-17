import { useState } from 'react';
import { dataApi } from '../services/api';
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from './ui/card';
import { Input } from './ui/input';
import { Label } from './ui/label';
import { Button } from './ui/button';
import { Textarea } from './ui/textarea';
import { UploadCloud, FileText, AlertCircle, X } from 'lucide-react';

interface FileUploadProps {
  onUploadSuccess?: (data: any) => void;
  onUploadError?: (error: any) => void;
}

const EnhancedFileUpload: React.FC<FileUploadProps> = ({
  onUploadSuccess,
  onUploadError,
}) => {
  const [file, setFile] = useState<File | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [metadata, setMetadata] = useState({
    experiment_id: '',
    operator: '',
    material: '',
    notes: '',
  });

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      setFile(e.target.files[0]);
      setError(null);
    }
  };

  const handleMetadataChange = (
    e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>
  ) => {
    const { name, value } = e.target;
    setMetadata((prev) => ({
      ...prev,
      [name]: value,
    }));
  };

  const handleRemoveFile = () => {
    setFile(null);
  };

  const [isMockMode, setIsMockMode] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!file) {
      setError('Please select a file to upload');
      return;
    }

    setIsUploading(true);
    setError(null);

    try {
      const result = await dataApi.uploadFile(file, metadata);

      // Check if we're in mock mode by looking at console logs
      if (result && !result.id.includes('-')) {
        // Real IDs from the backend are UUIDs with hyphens
        setIsMockMode(true);
      }

      setFile(null);
      setMetadata({
        experiment_id: '',
        operator: '',
        material: '',
        notes: '',
      });
      onUploadSuccess?.(result);
    } catch (error: any) {
      console.error('Error uploading file:', error);

      // Provide more specific error messages based on the error type
      if (error.message && error.message.includes('Network Error')) {
        setError('Connection error: Unable to connect to the server. Please check if the backend service is running.');
        // We'll likely switch to mock mode after this error
      } else if (error.response) {
        // The request was made and the server responded with a status code
        // that falls out of the range of 2xx
        const statusCode = error.response.status;
        const errorMessage = error.response.data?.detail || error.response.data?.message || 'Unknown server error';

        if (statusCode === 400) {
          setError(`Invalid request: ${errorMessage}`);
        } else if (statusCode === 413) {
          setError('File too large: The server rejected the file because it exceeds the maximum allowed size.');
        } else if (statusCode >= 500) {
          setError(`Server error (${statusCode}): ${errorMessage}`);
        } else {
          setError(`Upload failed (${statusCode}): ${errorMessage}`);
        }
      } else if (error.request) {
        // The request was made but no response was received
        setError('No response from server: The request was sent but received no response. Please check your network connection.');
      } else {
        // Something happened in setting up the request that triggered an Error
        setError(`Failed to upload file: ${error.message || 'Unknown error occurred'}`);
      }

      onUploadError?.(error);
    } finally {
      setIsUploading(false);
    }
  };

  return (
    <Card className="w-full shadow-md">
      <CardHeader className="space-y-1">
        <CardTitle className="text-2xl font-bold">Upload Data File</CardTitle>
        <CardDescription>Upload CSV file and fill in experiment information</CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* Mock mode indicator */}
        {isMockMode && (
          <div className="mb-4 p-3 bg-amber-50 border border-amber-200 rounded-md text-sm">
            <div className="flex items-center gap-2">
              <AlertCircle className="h-4 w-4 text-amber-500" />
              <p className="text-amber-800 font-medium">Mock Mode Active</p>
            </div>
            <p className="mt-1 text-amber-700 text-xs">
              You are using simulated data because the backend service is unavailable.
              Files uploaded in this mode will not be saved permanently.
            </p>
          </div>
        )}

        {/* File upload area */}
        <div className="space-y-2">
          <Label htmlFor="file-upload">CSV File</Label>
          <div className="relative">
            <div className="border-2 border-dashed border-gray-300 dark:border-gray-700 rounded-lg p-8 transition-all hover:bg-gray-50 dark:hover:bg-gray-800/50 cursor-pointer group">
              <input
                type="file"
                id="file-upload"
                className="absolute inset-0 w-full h-full opacity-0 cursor-pointer z-10"
                accept=".csv,.xlsx,.xls,.txt"
                onChange={handleFileChange}
              />
              <div className="flex flex-col items-center justify-center gap-3 text-center">
                <div className="p-3 rounded-full bg-primary/10 text-primary">
                  <UploadCloud className="h-10 w-10" />
                </div>
                <div className="space-y-1">
                  <p className="text-sm font-medium">Drag and drop file here or click to upload</p>
                  <p className="text-xs text-muted-foreground">Supports CSV, Excel, and text formats (max 10MB)</p>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Selected file display - show only when a file is selected */}
        {file && (
          <div className="flex items-center justify-between p-3 border rounded-lg bg-muted/50">
            <div className="flex items-center gap-2">
              <div className="p-2 rounded-md bg-primary/10">
                <FileText className="h-5 w-5 text-primary" />
              </div>
              <div>
                <p className="text-sm font-medium">{file.name}</p>
                <p className="text-xs text-muted-foreground">{(file.size / 1024 / 1024).toFixed(2)} MB</p>
              </div>
            </div>
            <Button variant="ghost" size="icon" className="h-8 w-8 rounded-full" onClick={handleRemoveFile}>
              <X className="h-4 w-4" />
              <span className="sr-only">Remove file</span>
            </Button>
          </div>
        )}

        {/* Metadata form */}
        <div className="grid gap-6 md:grid-cols-2">
          <div className="space-y-2">
            <Label htmlFor="experiment_id">Experiment ID</Label>
            <Input
              id="experiment_id"
              name="experiment_id"
              value={metadata.experiment_id}
              onChange={handleMetadataChange}
              placeholder="e.g., EXP-2023-001"
              className="w-full"
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="operator">Operator</Label>
            <Input
              id="operator"
              name="operator"
              value={metadata.operator}
              onChange={handleMetadataChange}
              placeholder="Enter operator name"
              className="w-full"
            />
          </div>
          <div className="space-y-2 md:col-span-2">
            <Label htmlFor="material">Material</Label>
            <Input
              id="material"
              name="material"
              value={metadata.material}
              onChange={handleMetadataChange}
              placeholder="Enter experiment material"
              className="w-full"
            />
          </div>
          <div className="space-y-2 md:col-span-2">
            <Label htmlFor="notes">Notes</Label>
            <Textarea
              id="notes"
              name="notes"
              value={metadata.notes}
              onChange={handleMetadataChange}
              placeholder="Enter experiment notes (optional)"
              className="min-h-[100px]"
            />
          </div>
        </div>

        {/* Error message - show only when there's an error */}
        {error && (
          <div className="flex items-start gap-2 p-4 text-sm border rounded-lg bg-destructive/10 text-destructive border-destructive/20">
            <AlertCircle className="h-5 w-5 flex-shrink-0 mt-0.5" />
            <div>
              <p className="font-medium mb-1">Upload Failed</p>
              <p className="leading-relaxed">{error}</p>
              {typeof error === 'string' && error.includes('Connection error') && (
                <div className="mt-2 text-xs space-y-1 text-muted-foreground">
                  <p>Troubleshooting steps:</p>
                  <ul className="list-disc pl-4 space-y-1">
                    <li>Make sure Docker is running</li>
                    <li>Check if the backend service is started with <code className="bg-muted px-1 py-0.5 rounded">docker-compose up -d</code></li>
                    <li>Verify the API endpoint is accessible at <code className="bg-muted px-1 py-0.5 rounded">http://localhost:8000/api</code></li>
                  </ul>
                </div>
              )}
            </div>
          </div>
        )}
      </CardContent>
      <CardFooter className="flex justify-end gap-2 pt-2">
        <Button
          variant="outline"
          onClick={handleRemoveFile}
          disabled={!file || isUploading}
        >
          Cancel
        </Button>
        <Button
          className="px-8 transition-all hover:bg-primary/90 hover:shadow-md"
          onClick={handleSubmit}
          disabled={!file || isUploading}
        >
          {isUploading ? 'Uploading...' : 'Upload Data'}
        </Button>
      </CardFooter>
    </Card>
  );
};

export default EnhancedFileUpload;
