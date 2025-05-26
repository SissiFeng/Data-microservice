import axios from 'axios';
import {
  mockUploadFile,
  mockGetFiles,
  mockProcessFile,
  mockAddAnnotation,
  mockExportData,
  mockRunOptimizer // Added for mock mode
} from './mockData.js';
import { OptimizerRequest, OptimizerResponse } from '../types'; // Added

// Flag to enable mock mode when backend is unavailable
let useMockData = true; // Always use mock data for now

// Create axios instance
const api = axios.create({
  baseURL: 'http://localhost:8000/api',
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add response interceptor to detect backend unavailability
api.interceptors.response.use(
  response => response,
  error => {
    // Check if error is due to network issues (backend unavailable)
    if (error.message && (
        error.message.includes('Network Error') ||
        !error.response ||
        error.code === 'ECONNABORTED'
      )) {
      console.warn('Backend unavailable, switching to mock data mode');
      useMockData = true;
    }
    return Promise.reject(error);
  }
);

// Data API
export const dataApi = {
  uploadFile: async (file: File, metadata?: any) => {
    try {
      if (useMockData) {
        console.log('Using mock data for file upload');
        return await mockUploadFile(file, metadata);
      }

      const formData = new FormData();
      formData.append('file', file);

      if (metadata) {
        formData.append('metadata', JSON.stringify(metadata));
      }

      const response = await api.post('/data/upload', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });

      return response.data;
    } catch (error) {
      if (!useMockData && error.message && error.message.includes('Network Error')) {
        console.log('Switching to mock mode after failed upload attempt');
        useMockData = true;
        return await mockUploadFile(file, metadata);
      }
      throw error;
    }
  },

  getFiles: async (params?: { skip?: number; limit?: number; status?: string }) => {
    try {
      if (useMockData) {
        console.log('Using mock data for file listing');
        return await mockGetFiles(params);
      }

      const response = await api.get('/data/files', { params });
      return response.data;
    } catch (error) {
      if (!useMockData && error.message && error.message.includes('Network Error')) {
        console.log('Switching to mock mode after failed files fetch');
        useMockData = true;
        return await mockGetFiles(params);
      }
      throw error;
    }
  },

  getFile: async (fileId: string) => {
    if (useMockData) {
      console.log('Using mock data for file details');
      const { items } = await mockGetFiles();
      const file = items.find(f => f.id === fileId);
      if (!file) throw new Error('File not found');
      return file;
    }

    const response = await api.get(`/data/files/${fileId}`);
    return response.data;
  },

  previewFile: async (fileId: string, rows: number = 10) => {
    if (useMockData) {
      console.log('Using mock data for file preview');
      const { items } = await mockGetFiles();
      const file = items.find(f => f.id === fileId);
      if (!file) throw new Error('File not found');

      // Use _data field for mock data (non-standard field)
      const mockData = (file as any)._data || [];

      // Add index to each data point and extract columns
      const dataWithIndex = mockData.map((point, index) => ({
        index,
        ...point
      }));

      // Extract column names from the first data point
      const columns = mockData.length > 0 ? Object.keys(mockData[0]) : [];

      return {
        data: dataWithIndex.slice(0, rows),
        columns: ['index', ...columns]
      };
    }

    const response = await api.get(`/data/files/${fileId}/preview`, {
      params: { rows },
    });
    return response.data;
  },

  deleteFile: async (fileId: string) => {
    if (useMockData) {
      console.log('Using mock data for file deletion');
      await new Promise(resolve => setTimeout(resolve, 500));
      return { success: true, message: 'File deleted (mock)' };
    }

    const response = await api.delete(`/data/files/${fileId}`);
    return response.data;
  },
};

// ETL API
export const etlApi = {
  processData: async (data: {
    data_file_id: string;
    processing_type: string;
    parameters?: any;
  }) => {
    if (useMockData) {
      console.log('Using mock data for processing');
      return await mockProcessFile(data.data_file_id, data);
    }

    try {
      const response = await api.post('/etl/process', data);
      return response.data;
    } catch (error) {
      if (!useMockData && error.message && error.message.includes('Network Error')) {
        console.log('Switching to mock mode for processing');
        useMockData = true;
        return await mockProcessFile(data.data_file_id, data);
      }
      throw error;
    }
  },

  getResults: async (params?: {
    data_file_id?: string;
    processing_type?: string;
    status?: string;
    skip?: number;
    limit?: number;
  }) => {
    if (useMockData) {
      console.log('Using mock data for processing results');
      await new Promise(resolve => setTimeout(resolve, 500));
      return {
        items: [mockProcessFile(params?.data_file_id || '1', {})],
        total: 1
      };
    }

    const response = await api.get('/etl/results', { params });
    return response.data;
  },

  getResult: async (resultId: string) => {
    if (useMockData) {
      console.log('Using mock data for processing result details');
      return mockProcessFile('1', {});
    }

    const response = await api.get(`/etl/results/${resultId}`);
    return response.data;
  },

  exportResult: async (resultId: string, format: 'csv' | 'json') => {
    if (useMockData) {
      console.log('Using mock data for export');
      const blob = await mockExportData('1', format);
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `export-${resultId}.${format}`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
      return;
    }

    // Use window.open for direct download
    window.open(`${api.defaults.baseURL}/etl/results/${resultId}/export?format=${format}`);
  },
};

// Annotations API
export const annotationsApi = {
  createAnnotation: async (data: {
    data_file_id: string;
    processing_result_id?: string;
    annotation_type: string;
    annotation_data?: any;
    notes?: string;
  }) => {
    if (useMockData) {
      console.log('Using mock data for annotation creation');
      return await mockAddAnnotation(data.data_file_id, data);
    }

    try {
      const response = await api.post('/annotations', data);
      return response.data;
    } catch (error) {
      if (!useMockData && error.message && error.message.includes('Network Error')) {
        console.log('Switching to mock mode for annotation creation');
        useMockData = true;
        return await mockAddAnnotation(data.data_file_id, data);
      }
      throw error;
    }
  },

  getAnnotations: async (params?: {
    data_file_id?: string;
    processing_result_id?: string;
    annotation_type?: string;
    skip?: number;
    limit?: number;
  }) => {
    if (useMockData) {
      console.log('Using mock data for annotations');
      await new Promise(resolve => setTimeout(resolve, 500));

      // Return mock annotations if we have them for the file
      const { items } = await mockGetFiles();
      const file = items.find(f => f.id === params?.data_file_id);

      if (file && (file as any)._annotations) {
        return { items: (file as any)._annotations, total: (file as any)._annotations.length };
      }

      return { items: [], total: 0 };
    }

    const response = await api.get('/annotations', { params });
    return response.data;
  },

  getAnnotation: async (annotationId: string) => {
    if (useMockData) {
      console.log('Using mock data for annotation details');
      const { items } = await mockGetFiles();

      // Find the annotation in any of our mock files
      for (const file of items) {
        if ((file as any)._annotations) {
          const annotation = (file as any)._annotations.find((a: any) => a.id === annotationId);
          if (annotation) return annotation;
        }
      }

      throw new Error('Annotation not found');
    }

    const response = await api.get(`/annotations/${annotationId}`);
    return response.data;
  },

  updateAnnotation: async (
    annotationId: string,
    data: {
      annotation_type?: string;
      annotation_data?: any;
      notes?: string;
    }
  ) => {
    if (useMockData) {
      console.log('Using mock data for annotation update');
      await new Promise(resolve => setTimeout(resolve, 500));
      return { id: annotationId, ...data };
    }

    const response = await api.put(`/annotations/${annotationId}`, data);
    return response.data;
  },

  deleteAnnotation: async (annotationId: string) => {
    if (useMockData) {
      console.log('Using mock data for annotation deletion');
      await new Promise(resolve => setTimeout(resolve, 500));
      return { success: true };
    }

    const response = await api.delete(`/annotations/${annotationId}`);
    return response.data;
  },
};

// Optimizer API
export const optimizerApi = {
  runOptimizer: async (request: OptimizerRequest): Promise<OptimizerResponse> => {
    if (useMockData) {
      console.log('Using mock data for optimizer run');
      return await mockRunOptimizer(request);
    }
    try {
      const response = await api.post('/optimizer/run', request);
      return response.data;
    } catch (error) {
      if (!useMockData && error.message && error.message.includes('Network Error')) {
        console.log('Switching to mock mode for optimizer run');
        useMockData = true; // Switch to mock data if backend fails
        return await mockRunOptimizer(request);
      }
      throw error; // Re-throw other errors
    }
  },
  // getOptimizationRun: async (runId: string): Promise<OptimizerResponse> => { ... } // Optional
};

export default api;
