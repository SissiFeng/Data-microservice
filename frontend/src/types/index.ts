// Data types
export enum DataStatus {
  PENDING = 'pending',
  PROCESSING = 'processing',
  PROCESSED = 'processed',
  FAILED = 'failed',
  ANNOTATED = 'annotated',
}

export enum DataSource {
  UPLOAD = 'upload',
  WATCH = 'watch',
  S3 = 's3',
}

export interface DataMetadata {
  experiment_id?: string;
  operator?: string;
  material?: string;
  timestamp: string;
  source: DataSource;
  additional_metadata?: Record<string, any>;
}

export interface DataFile {
  id: string;
  filename: string;
  filepath: string;
  s3_key?: string;
  metadata: DataMetadata;
  status: DataStatus;
  created_at: string;
  updated_at: string;
}

export interface DataFileList {
  total: number;
  items: DataFile[];
}

// ETL types
export enum ProcessingType {
  ROLLING_MEAN = 'rolling_mean',
  PEAK_DETECTION = 'peak_detection',
  DATA_QUALITY = 'data_quality',
  CUSTOM = 'custom',
}

export enum ProcessingStatus {
  PENDING = 'pending',
  PROCESSING = 'processing',
  COMPLETED = 'completed',
  FAILED = 'failed',
}

export interface ProcessingParameters {
  window_size?: number;
  min_peak_height?: number;
  distance?: number;
  prominence?: number;
  width?: number;
  custom_params?: Record<string, any>;
  custom_script_name?: string; // Added for custom processing type
}

export interface ProcessingResult {
  id: string;
  data_file_id: string;
  processing_type: ProcessingType;
  parameters: ProcessingParameters;
  result_file?: string;
  result_data?: Record<string, any>;
  status: ProcessingStatus;
  created_at: string;
  updated_at: string;
  task_id?: string; // Added for Celery task ID
}

export interface ProcessingResultList {
  total: number;
  items: ProcessingResult[];
}

// Annotation types
export enum AnnotationType {
  VALID = 'valid',
  INVALID = 'invalid',
  PEAK_CORRECTION = 'peak_correction',
  EXPERIMENT_FAILED = 'experiment_failed',
  OUTLIER = 'outlier',
  BASELINE_SHIFT = 'baseline_shift',
  NOISE = 'noise',
  CUSTOM = 'custom',
}

// Optimizer Interface Types
export interface OptimizerRequest {
  processing_result_id: string; // UUID
  optimizer_params?: Record<string, any>;
}

export interface OptimizerResponse {
  optimizer_run_id: string; // UUID
  status: string;
  input_processing_result_id: string; // UUID
  results?: Record<string, any>;
  message?: string;
}

export interface Annotation {
  id: string;
  data_file_id: string;
  processing_result_id?: string;
  annotation_type: AnnotationType;
  annotation_data: Record<string, any>;
  notes?: string;
  created_by?: string;
  created_at: string;
  updated_at: string;
}

export interface AnnotationList {
  total: number;
  items: Annotation[];
}
