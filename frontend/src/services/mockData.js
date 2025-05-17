import { v4 as uuidv4 } from 'uuid';

// Mock data status
const DataStatus = {
  PENDING: 'pending',
  PROCESSING: 'processing',
  PROCESSED: 'processed',
  FAILED: 'failed',
  ANNOTATED: 'annotated',
};

// Mock annotation types
const AnnotationType = {
  VALID: 'valid',
  INVALID: 'invalid',
  PEAK_CORRECTION: 'peak_correction',
  EXPERIMENT_FAILED: 'experiment_failed',
  OUTLIER: 'outlier',
  BASELINE_SHIFT: 'baseline_shift',
  NOISE: 'noise',
  CUSTOM: 'custom',
};

// Mock data files
export const mockFiles = [
  {
    id: '1',
    filename: 'test.csv',
    filepath: '/uploads/test.csv',
    status: DataStatus.PROCESSED,
    created_at: new Date(Date.now() - 3600000).toISOString(),
    updated_at: new Date(Date.now() - 3500000).toISOString(),
    metadata: {
      experiment_id: 'TEST-2023-001',
      operator: 'Test User',
      material: 'Test Material',
      timestamp: new Date(Date.now() - 3600000).toISOString(),
      source: 'upload',
      additional_metadata: {
        notes: 'Test CSV data from user'
      }
    },
    // Non-standard fields for mock data - sample from test.csv
    _data: [
      { index: 0, time: 0, voltage: null, current: null, cycle: 0, exp: 0, ref: 0.09711 },
      { index: 1, time: 5000, voltage: null, current: null, cycle: 0, exp: 0, ref: 0.09691 },
      { index: 2, time: 10000, voltage: 0.09413, current: 0.000187, cycle: 0, exp: 0, ref: 0.09671 },
      { index: 3, time: 15000, voltage: 0.09366, current: 0.000140, cycle: 0, exp: 0, ref: 0.09651 },
      { index: 4, time: 20000, voltage: 0.09319, current: 0.000094, cycle: 0, exp: 0, ref: 0.09631 },
      { index: 5, time: 25000, voltage: 0.09272, current: 0.000047, cycle: 0, exp: 0, ref: 0.09611 },
      { index: 6, time: 30000, voltage: 0.09225, current: 0.000000, cycle: 0, exp: 0, ref: 0.09591 },
      { index: 7, time: 35000, voltage: 0.09178, current: -0.000047, cycle: 0, exp: 0, ref: 0.09571 },
      { index: 8, time: 40000, voltage: 0.09131, current: -0.000094, cycle: 0, exp: 0, ref: 0.09551 },
      { index: 9, time: 45000, voltage: 0.09084, current: -0.000140, cycle: 0, exp: 0, ref: 0.09531 },
      { index: 10, time: 50000, voltage: 0.09037, current: -0.000187, cycle: 0, exp: 0, ref: 0.09511 },
      { index: 11, time: 55000, voltage: 0.08990, current: -0.000234, cycle: 0, exp: 0, ref: 0.09491 },
      { index: 12, time: 60000, voltage: 0.08943, current: -0.000281, cycle: 0, exp: 0, ref: 0.09471 },
      { index: 13, time: 65000, voltage: 0.08896, current: -0.000327, cycle: 0, exp: 0, ref: 0.09451 },
      { index: 14, time: 70000, voltage: 0.08849, current: -0.000374, cycle: 0, exp: 0, ref: 0.09431 },
      { index: 15, time: 75000, voltage: 0.08802, current: -0.000421, cycle: 0, exp: 0, ref: 0.09411 },
      { index: 16, time: 80000, voltage: 0.08755, current: -0.000468, cycle: 0, exp: 0, ref: 0.09391 },
      { index: 17, time: 85000, voltage: 0.08708, current: -0.000514, cycle: 0, exp: 0, ref: 0.09371 },
      { index: 18, time: 90000, voltage: 0.08661, current: -0.000561, cycle: 0, exp: 0, ref: 0.09351 },
      { index: 19, time: 95000, voltage: 0.08614, current: -0.000608, cycle: 0, exp: 0, ref: 0.09331 },
      { index: 20, time: 100000, voltage: 0.08567, current: -0.000655, cycle: 0, exp: 0, ref: 0.09311 },
      { index: 21, time: 105000, voltage: 0.08520, current: -0.000701, cycle: 0, exp: 0, ref: 0.09291 },
      { index: 22, time: 110000, voltage: 0.08473, current: -0.000748, cycle: 0, exp: 0, ref: 0.09271 },
      { index: 23, time: 115000, voltage: 0.08426, current: -0.000795, cycle: 0, exp: 0, ref: 0.09251 },
      { index: 24, time: 120000, voltage: 0.08379, current: -0.000842, cycle: 0, exp: 0, ref: 0.09231 },
      { index: 25, time: 125000, voltage: 0.08332, current: -0.000888, cycle: 0, exp: 0, ref: 0.09211 },
      { index: 26, time: 130000, voltage: 0.08285, current: -0.000935, cycle: 0, exp: 0, ref: 0.09191 },
      { index: 27, time: 135000, voltage: 0.08238, current: -0.000982, cycle: 0, exp: 0, ref: 0.09171 },
      { index: 28, time: 140000, voltage: 0.08191, current: -0.001029, cycle: 0, exp: 0, ref: 0.09151 },
      { index: 29, time: 145000, voltage: 0.08144, current: -0.001075, cycle: 0, exp: 0, ref: 0.09131 },
      { index: 30, time: 150000, voltage: 0.08097, current: -0.001122, cycle: 0, exp: 0, ref: 0.09111 }
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
      source: 'upload',
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
        comment: 'Calibration period',
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
      source: 'upload',
      additional_metadata: {
        notes: 'Initial test of new material'
      }
    }
  }
];

// Mock processing result
export const mockProcessingResult = {
  id: 'pr1',
  data_file_id: '1',
  processing_type: 'rolling_mean',
  parameters: {
    window_size: 3
  },
  status: 'completed',
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
export const mockUploadFile = async (file, metadata) => {
  // Simulate network delay
  await new Promise(resolve => setTimeout(resolve, 1000));

  const now = new Date().toISOString();
  const id = uuidv4();

  const newFile = {
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
      source: 'upload',
      additional_metadata: {
        notes: metadata.notes || ''
      }
    }
  };

  return newFile;
};

// Mock get files function
export const mockGetFiles = async (params) => {
  // Simulate network delay
  await new Promise(resolve => setTimeout(resolve, 500));

  return {
    items: mockFiles,
    total: mockFiles.length
  };
};

// Mock process file function
export const mockProcessFile = async (fileId, params) => {
  // Simulate network delay
  await new Promise(resolve => setTimeout(resolve, 1500));

  // Find the file data
  const file = mockFiles.find(f => f.id === fileId);
  const fileData = file ? file._data || [] : [];

  // Create a result based on the processing type
  if (params.processing_type === 'peak_detection') {
    // For peak detection, identify some peaks in the data
    const peaks = [];
    if (fileData.length > 0) {
      // Find the value field (assuming it's the second field after time)
      const valueField = Object.keys(fileData[0])[1] || 'value';

      // Simple peak detection algorithm
      for (let i = 1; i < fileData.length - 1; i++) {
        const prev = fileData[i-1][valueField];
        const current = fileData[i][valueField];
        const next = fileData[i+1][valueField];

        // If current value is higher than neighbors, it's a peak
        if (current > prev && current > next && current > (params.parameters?.min_peak_height || 0)) {
          peaks.push(i);
        }
      }
    }

    return {
      id: 'pr-' + Math.random().toString(36).substr(2, 9),
      data_file_id: fileId,
      processing_type: 'peak_detection',
      parameters: params.parameters || {},
      status: 'completed',
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
      result_data: {
        peaks: peaks
      }
    };
  }
  else if (params.processing_type === 'rolling_mean') {
    // For rolling mean, calculate moving average
    const windowSize = params.parameters?.window_size || 3;
    const rollingMeanData = [];

    if (fileData.length > 0) {
      // Find the value field
      const valueField = Object.keys(fileData[0])[1] || 'value';

      // Calculate rolling mean
      for (let i = 0; i < fileData.length; i++) {
        let sum = 0;
        let count = 0;

        // Look back windowSize/2 and forward windowSize/2
        for (let j = Math.max(0, i - Math.floor(windowSize/2));
             j <= Math.min(fileData.length - 1, i + Math.floor(windowSize/2));
             j++) {
          sum += fileData[j][valueField];
          count++;
        }

        const mean = count > 0 ? sum / count : 0;
        rollingMeanData.push({
          ...fileData[i],
          [`${valueField}_rolling_mean`]: mean
        });
      }
    }

    return {
      id: 'pr-' + Math.random().toString(36).substr(2, 9),
      data_file_id: fileId,
      processing_type: 'rolling_mean',
      parameters: params.parameters || { window_size: windowSize },
      status: 'completed',
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
      result_data: {
        sample_data: rollingMeanData
      }
    };
  }

  // Default fallback
  return {
    ...mockProcessingResult,
    data_file_id: fileId
  };
};

// Mock add annotation function
export const mockAddAnnotation = async (fileId, annotation) => {
  // Simulate network delay
  await new Promise(resolve => setTimeout(resolve, 500));

  return {
    id: uuidv4(),
    ...annotation
  };
};

// Mock export data function
export const mockExportData = async (fileId, format) => {
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
