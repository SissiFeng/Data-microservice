import { useState } from 'react';
import { dataApi } from '../services/api';

interface FileUploadProps {
  onUploadSuccess?: (data: any) => void;
  onUploadError?: (error: any) => void;
}

const FileUpload: React.FC<FileUploadProps> = ({
  onUploadSuccess,
  onUploadError,
}) => {
  const [file, setFile] = useState<File | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [metadata, setMetadata] = useState({
    experiment_id: '',
    operator: '',
    material: '',
  });

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      setFile(e.target.files[0]);
    }
  };

  const handleMetadataChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setMetadata((prev) => ({
      ...prev,
      [name]: value,
    }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!file) {
      return;
    }
    
    setIsUploading(true);
    
    try {
      const result = await dataApi.uploadFile(file, metadata);
      setFile(null);
      setMetadata({
        experiment_id: '',
        operator: '',
        material: '',
      });
      onUploadSuccess?.(result);
    } catch (error) {
      console.error('Error uploading file:', error);
      onUploadError?.(error);
    } finally {
      setIsUploading(false);
    }
  };

  return (
    <div className="bg-white shadow rounded-lg p-6">
      <h2 className="text-xl font-semibold mb-4">Upload Data File</h2>
      
      <form onSubmit={handleSubmit}>
        <div className="mb-4">
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Data File (CSV)
          </label>
          <input
            type="file"
            accept=".csv,.xlsx,.xls,.txt"
            onChange={handleFileChange}
            className="block w-full text-sm text-gray-500
                      file:mr-4 file:py-2 file:px-4
                      file:rounded-md file:border-0
                      file:text-sm file:font-semibold
                      file:bg-blue-50 file:text-blue-700
                      hover:file:bg-blue-100"
            required
          />
        </div>
        
        <div className="mb-4">
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Experiment ID
          </label>
          <input
            type="text"
            name="experiment_id"
            value={metadata.experiment_id}
            onChange={handleMetadataChange}
            className="mt-1 block w-full rounded-md border-gray-300 shadow-sm
                      focus:border-blue-500 focus:ring-blue-500 sm:text-sm
                      p-2 border"
            placeholder="Experiment identifier"
          />
        </div>
        
        <div className="mb-4">
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Operator
          </label>
          <input
            type="text"
            name="operator"
            value={metadata.operator}
            onChange={handleMetadataChange}
            className="mt-1 block w-full rounded-md border-gray-300 shadow-sm
                      focus:border-blue-500 focus:ring-blue-500 sm:text-sm
                      p-2 border"
            placeholder="Operator name"
          />
        </div>
        
        <div className="mb-4">
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Material
          </label>
          <input
            type="text"
            name="material"
            value={metadata.material}
            onChange={handleMetadataChange}
            className="mt-1 block w-full rounded-md border-gray-300 shadow-sm
                      focus:border-blue-500 focus:ring-blue-500 sm:text-sm
                      p-2 border"
            placeholder="Material type"
          />
        </div>
        
        <div className="flex justify-end">
          <button
            type="submit"
            disabled={!file || isUploading}
            className="inline-flex justify-center py-2 px-4 border border-transparent
                      shadow-sm text-sm font-medium rounded-md text-white bg-blue-600
                      hover:bg-blue-700 focus:outline-none focus:ring-2
                      focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50"
          >
            {isUploading ? 'Uploading...' : 'Upload'}
          </button>
        </div>
      </form>
    </div>
  );
};

export default FileUpload;
