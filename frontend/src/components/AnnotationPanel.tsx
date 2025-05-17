import { useState, useEffect } from 'react';
import { annotationsApi } from '../services/api';
import { AnnotationType } from '../types';
import type { DataFile, ProcessingResult, Annotation } from '../types';
import { ExclamationCircleIcon, CheckCircleIcon, XCircleIcon } from '@heroicons/react/24/solid';

interface AnnotationPanelProps {
  dataFile: DataFile | null;
  processingResult: ProcessingResult | null;
  onAnnotationCreated?: (annotation: Annotation) => void;
}

const AnnotationPanel: React.FC<AnnotationPanelProps> = ({
  dataFile,
  processingResult,
  onAnnotationCreated,
}) => {
  const [annotationType, setAnnotationType] = useState<AnnotationType>(AnnotationType.VALID);
  const [notes, setNotes] = useState('');
  const [annotationData, setAnnotationData] = useState<Record<string, any>>({});
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [existingAnnotations, setExistingAnnotations] = useState<Annotation[]>([]);

  useEffect(() => {
    if (dataFile) {
      fetchExistingAnnotations();
    } else {
      setExistingAnnotations([]);
    }
  }, [dataFile]);

  const fetchExistingAnnotations = async () => {
    if (!dataFile) return;

    try {
      const response = await annotationsApi.getAnnotations({
        data_file_id: dataFile.id,
        processing_result_id: processingResult?.id,
      });

      setExistingAnnotations(response.items);
    } catch (err) {
      console.error('Error fetching annotations:', err);
    }
  };

  const handleNotesChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setNotes(e.target.value);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!dataFile) {
      setError('No data file selected');
      return;
    }

    setIsSubmitting(true);
    setError(null);

    try {
      // Prepare annotation data based on type
      let finalAnnotationData = { ...annotationData };

      if (annotationType === AnnotationType.PEAK_CORRECTION) {
        // Ensure we have the required peak correction data
        if (!annotationData.corrected_peaks || !Array.isArray(annotationData.corrected_peaks)) {
          finalAnnotationData.corrected_peaks = [];
        }
      }

      const result = await annotationsApi.createAnnotation({
        data_file_id: dataFile.id,
        processing_result_id: processingResult?.id,
        annotation_type: annotationType,
        annotation_data: finalAnnotationData,
        notes: notes,
      });

      // Reset form
      setNotes('');
      setAnnotationData({});

      // Refresh annotations
      fetchExistingAnnotations();

      // Notify parent
      onAnnotationCreated?.(result);
    } catch (err) {
      console.error('Error creating annotation:', err);
      setError('Failed to create annotation. Please try again.');
    } finally {
      setIsSubmitting(false);
    }
  };

  if (!dataFile) {
    return (
      <div className="bg-white shadow rounded-lg p-6">
        <div className="text-center py-4 text-gray-500">
          Select a data file to annotate
        </div>
      </div>
    );
  }

  // Helper function to get icon for annotation type
  const getAnnotationIcon = (type: AnnotationType) => {
    switch (type) {
      case AnnotationType.VALID:
        return <CheckCircleIcon className="h-5 w-5 text-green-500" />;
      case AnnotationType.INVALID:
      case AnnotationType.EXPERIMENT_FAILED:
        return <XCircleIcon className="h-5 w-5 text-red-500" />;
      default:
        return <ExclamationCircleIcon className="h-5 w-5 text-yellow-500" />;
    }
  };

  // Helper function to get color for annotation type
  const getAnnotationColor = (type: AnnotationType) => {
    switch (type) {
      case AnnotationType.VALID:
        return 'bg-green-50 border-green-200';
      case AnnotationType.INVALID:
      case AnnotationType.EXPERIMENT_FAILED:
        return 'bg-red-50 border-red-200';
      case AnnotationType.OUTLIER:
      case AnnotationType.NOISE:
        return 'bg-yellow-50 border-yellow-200';
      case AnnotationType.BASELINE_SHIFT:
        return 'bg-blue-50 border-blue-200';
      default:
        return 'bg-gray-50 border-gray-200';
    }
  };

  return (
    <div className="bg-white shadow rounded-lg p-6">
      <h2 className="text-xl font-semibold mb-4">Annotations</h2>

      {existingAnnotations.length > 0 && (
        <div className="mb-6">
          <h3 className="text-lg font-medium mb-2">Existing Annotations</h3>
          <div className="space-y-2">
            {existingAnnotations.map((annotation) => (
              <div
                key={annotation.id}
                className={`p-3 rounded border ${getAnnotationColor(annotation.annotation_type as AnnotationType)}`}
              >
                <div className="flex justify-between items-center">
                  <div className="flex items-center">
                    {getAnnotationIcon(annotation.annotation_type as AnnotationType)}
                    <span className="font-medium ml-2">
                      {annotation.annotation_type.split('_').map(word =>
                        word.charAt(0).toUpperCase() + word.slice(1)
                      ).join(' ')}
                    </span>
                  </div>
                  <span className="text-sm text-gray-500">
                    {new Date(annotation.created_at).toLocaleString()}
                  </span>
                </div>
                {annotation.notes && (
                  <div className="mt-2 text-sm">{annotation.notes}</div>
                )}
                {Object.keys(annotation.annotation_data).length > 0 && (
                  <div className="mt-2 text-sm text-gray-700 bg-white p-2 rounded">
                    {annotation.annotation_type === AnnotationType.PEAK_CORRECTION && (
                      <div>
                        <span className="font-medium">Corrected Peaks: </span>
                        {annotation.annotation_data.corrected_peaks?.join(', ')}
                      </div>
                    )}
                    {annotation.annotation_type === AnnotationType.OUTLIER && (
                      <div>
                        <span className="font-medium">Outlier Points: </span>
                        {annotation.annotation_data.outlier_points?.join(', ')}
                      </div>
                    )}
                    {annotation.annotation_type === AnnotationType.CUSTOM && (
                      <pre className="whitespace-pre-wrap">
                        {JSON.stringify(annotation.annotation_data, null, 2)}
                      </pre>
                    )}
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {error && (
        <div className="mb-4 p-2 bg-red-100 text-red-700 rounded">
          {error}
        </div>
      )}

      <form onSubmit={handleSubmit}>
        <div className="mb-4">
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Annotation Type
          </label>
          <div className="grid grid-cols-2 gap-2 mb-2">
            {Object.values(AnnotationType).map((type) => (
              <div
                key={type}
                onClick={() => setAnnotationType(type)}
                className={`p-2 rounded border cursor-pointer flex items-center
                          ${annotationType === type
                            ? 'border-blue-500 bg-blue-50 ring-2 ring-blue-200'
                            : 'border-gray-200 hover:bg-gray-50'}`}
              >
                {getAnnotationIcon(type)}
                <span className="ml-2 text-sm">
                  {type.split('_').map(word => word.charAt(0).toUpperCase() + word.slice(1)).join(' ')}
                </span>
              </div>
            ))}
          </div>
        </div>

        {annotationType === AnnotationType.PEAK_CORRECTION && (
          <div className="mb-4">
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Corrected Peak Indices (comma-separated)
            </label>
            <input
              type="text"
              name="corrected_peaks"
              value={annotationData.corrected_peaks || ''}
              onChange={(e) => {
                const peakValues = e.target.value.split(',')
                  .map(v => parseInt(v.trim()))
                  .filter(v => !isNaN(v));
                setAnnotationData(prev => ({
                  ...prev,
                  corrected_peaks: peakValues
                }));
              }}
              className="mt-1 block w-full rounded-md border-gray-300 shadow-sm
                        focus:border-blue-500 focus:ring-blue-500 sm:text-sm
                        p-2 border"
              placeholder="e.g. 10, 25, 42"
            />
          </div>
        )}

        {annotationType === AnnotationType.OUTLIER && (
          <div className="mb-4">
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Outlier Points (comma-separated)
            </label>
            <input
              type="text"
              name="outlier_points"
              value={annotationData.outlier_points || ''}
              onChange={(e) => {
                const pointValues = e.target.value.split(',')
                  .map(v => parseInt(v.trim()))
                  .filter(v => !isNaN(v));
                setAnnotationData(prev => ({
                  ...prev,
                  outlier_points: pointValues
                }));
              }}
              className="mt-1 block w-full rounded-md border-gray-300 shadow-sm
                        focus:border-blue-500 focus:ring-blue-500 sm:text-sm
                        p-2 border"
              placeholder="e.g. 15, 32, 47"
            />
          </div>
        )}

        {annotationType === AnnotationType.BASELINE_SHIFT && (
          <div className="mb-4">
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Baseline Shift Range
            </label>
            <div className="grid grid-cols-2 gap-2">
              <div>
                <label className="block text-xs text-gray-500">Start Index</label>
                <input
                  type="number"
                  name="shift_start"
                  value={annotationData.shift_start || ''}
                  onChange={(e) => {
                    setAnnotationData(prev => ({
                      ...prev,
                      shift_start: parseInt(e.target.value)
                    }));
                  }}
                  className="mt-1 block w-full rounded-md border-gray-300 shadow-sm
                            focus:border-blue-500 focus:ring-blue-500 sm:text-sm
                            p-2 border"
                />
              </div>
              <div>
                <label className="block text-xs text-gray-500">End Index</label>
                <input
                  type="number"
                  name="shift_end"
                  value={annotationData.shift_end || ''}
                  onChange={(e) => {
                    setAnnotationData(prev => ({
                      ...prev,
                      shift_end: parseInt(e.target.value)
                    }));
                  }}
                  className="mt-1 block w-full rounded-md border-gray-300 shadow-sm
                            focus:border-blue-500 focus:ring-blue-500 sm:text-sm
                            p-2 border"
                />
              </div>
            </div>
          </div>
        )}

        <div className="mb-4">
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Notes
          </label>
          <textarea
            value={notes}
            onChange={handleNotesChange}
            rows={4}
            className="mt-1 block w-full rounded-md border-gray-300 shadow-sm
                      focus:border-blue-500 focus:ring-blue-500 sm:text-sm
                      p-2 border"
            placeholder="Add any notes or observations..."
          />
        </div>

        <div className="flex justify-end">
          <button
            type="submit"
            disabled={isSubmitting}
            className="inline-flex justify-center py-2 px-4 border border-transparent
                      shadow-sm text-sm font-medium rounded-md text-white bg-blue-600
                      hover:bg-blue-700 focus:outline-none focus:ring-2
                      focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50"
          >
            {isSubmitting ? 'Saving...' : 'Save Annotation'}
          </button>
        </div>
      </form>
    </div>
  );
};

export default AnnotationPanel;
