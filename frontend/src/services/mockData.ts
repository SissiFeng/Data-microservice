import { DataFile, DataStatus, ProcessingResult, AnnotationType } from '../types';
import { v4 as uuidv4 } from 'uuid';

// Mock data files
export const mockFiles: DataFile[] = [
  {
    id: '1',
    filename: 'sample_data_1.csv',
    filepath: '/uploads/sample_data_1.csv',
    status: DataStatus.PROCESSED,
    created_at: new Date(Date.now() - 3600000).toISOString(),
    updated_at: new Date(Date.now() - 3500000).toISOString(),
    metadata: {
      experiment_id: 'EXP-2023-001',
      operator: 'John Doe',
      material: 'Silicon Wafer',
      timestamp: new Date(Date.now() - 3600000).toISOString(),
      source: 'upload' as any,
      additional_metadata: {
        notes: 'First test run with new parameters'
      }
    },
    // Non-standard fields for mock data
    _data: [
      { time: 0, value: 0 },
      { time: 1, value: 10 },
      { time: 2, value: 20 },
      { time: 3, value: 30 },
      { time: 4, value: 25 },
      { time: 5, value: 40 },
      { time: 6, value: 35 },
      { time: 7, value: 50 },
      { time: 8, value: 45 },
      { time: 9, value: 60 }
    ]
  },
  {
    id: '2',
    filename: 'sample_data_2.csv',
    filepath: '/uploads/sample_data_2.csv',
    status: DataStatus.ANNOTATED,
    created_at: new Date(Date.now() - 7200000).toISOString(),
    updated_at: new Date(Date.now() - 7000000).toISOString(),
    metadata: {
      experiment_id: 'EXP-2023-002',
      operator: 'Jane Smith',
      material: 'Aluminum Alloy',
      timestamp: new Date(Date.now() - 7200000).toISOString(),
      source: 'upload' as any,
      additional_metadata: {
        notes: 'Second test with modified cooling rate'
      }
    },
    // Non-standard fields for mock data
    _data: [
      { time: 0, value: 5 },
      { time: 1, value: 15 },
      { time: 2, value: 25 },
      { time: 3, value: 35 },
      { time: 4, value: 30 },
      { time: 5, value: 45 },
      { time: 6, value: 40 },
      { time: 7, value: 55 },
      { time: 8, value: 50 },
      { time: 9, value: 65 }
    ],
    _annotations: [
      {
        id: 'a1',
        data_file_id: '2',
        annotation_type: AnnotationType.VALID,
        annotation_data: { range: [2, 7] },
        notes: 'Good data range',
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString()
      },
      {
        id: 'a2',
        data_file_id: '2',
        annotation_type: AnnotationType.INVALID,
        annotation_data: { range: [0, 1] },
        notes: 'Calibration period',
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString()
      }
    ]
  },
  {
    id: '3',
    filename: 'sample_data_3.csv',
    filepath: '/uploads/sample_data_3.csv',
    status: DataStatus.PENDING,
    created_at: new Date(Date.now() - 10800000).toISOString(),
    updated_at: new Date(Date.now() - 10700000).toISOString(),
    metadata: {
      experiment_id: 'EXP-2023-003',
      operator: 'Robert Johnson',
      material: 'Carbon Fiber',
      timestamp: new Date(Date.now() - 10800000).toISOString(),
      source: 'upload' as any,
      additional_metadata: {
        notes: 'Initial test of new material'
      }
    }
  }
];

// Mock processing result
export const mockProcessingResult: ProcessingResult = {
  id: 'pr1',
  data_file_id: '1',
  processing_type: 'rolling_mean' as any,
  parameters: {
    window_size: 3
  },
  status: 'completed' as any,
  created_at: new Date().toISOString(),
  updated_at: new Date().toISOString(),
  result_data: {
    rolling_average: [
      { time: 0, value: 0 },
      { time: 1, value: 5 },
      { time: 2, value: 10 },
      { time: 3, value: 20 },
      { time: 4, value: 25 },
      { time: 5, value: 30 },
      { time: 6, value: 33.33 },
      { time: 7, value: 41.67 },
      { time: 8, value: 43.33 },
      { time: 9, value: 51.67 }
    ],
    peaks: [
      { time: 5, value: 40 },
      { time: 9, value: 60 }
    ]
  }
};

// Mock file upload function
export const mockUploadFile = async (file: File, metadata: any): Promise<DataFile> => {
  // Simulate network delay
  await new Promise(resolve => setTimeout(resolve, 1000));

  const now = new Date().toISOString();
  const id = uuidv4();

  const newFile: DataFile = {
    id: id,
    filename: file.name,
    filepath: `/uploads/${id}/${file.name}`,
    status: DataStatus.PENDING,
    created_at: now,
    updated_at: now,
    metadata: {
      experiment_id: metadata.experiment_id || '',
      operator: metadata.operator || '',
      material: metadata.material || '',
      timestamp: now,
      source: 'upload' as any,
      additional_metadata: {
        notes: metadata.notes || ''
      }
    }
  };

  return newFile;
};

// Mock get files function
export const mockGetFiles = async (params?: any): Promise<{ items: DataFile[], total: number }> => {
  // Simulate network delay
  await new Promise(resolve => setTimeout(resolve, 500));

  return {
    items: mockFiles,
    total: mockFiles.length
  };
};

// Mock process file function
export const mockProcessFile = async (fileId: string, params: any): Promise<ProcessingResult> => {
  // Simulate network delay
  await new Promise(resolve => setTimeout(resolve, 1500));

  return {
    ...mockProcessingResult,
    data_file_id: fileId
  };
};

// Mock add annotation function
export const mockAddAnnotation = async (fileId: string, annotation: any): Promise<any> => {
  // Simulate network delay
  await new Promise(resolve => setTimeout(resolve, 500));

  return {
    id: uuidv4(),
    ...annotation
  };
};

// Mock export data function
export const mockExportData = async (fileId: string, format: string): Promise<Blob> => {
  // Simulate network delay
  await new Promise(resolve => setTimeout(resolve, 1000));

  // Create a mock CSV or JSON blob
  const content = format === 'csv'
    ? 'time,value\n0,0\n1,10\n2,20\n3,30\n4,25\n5,40\n6,35\n7,50\n8,45\n9,60'
    : JSON.stringify({ data: [
        { time: 0, value: 0 },
        { time: 1, value: 10 },
        { time: 2, value: 20 },
        { time: 3, value: 30 },
        { time: 4, value: 25 },
        { time: 5, value: 40 },
        { time: 6, value: 35 },
        { time: 7, value: 50 },
        { time: 8, value: 45 },
        { time: 9, value: 60 }
      ]}, null, 2);

  const type = format === 'csv' ? 'text/csv' : 'application/json';
  return new Blob([content], { type });
};
