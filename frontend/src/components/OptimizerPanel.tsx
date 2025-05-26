import React, { useState } from 'react';
import { optimizerApi } from '../services/api';
import { OptimizerResponse, OptimizerRequest } from '../types';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Textarea } from './ui/textarea';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from './ui/card';
import { Label } from './ui/label';

interface OptimizerPanelProps {
  // Initially, we might not pass any props if it's self-contained with input fields.
  // If integrated more deeply, selectedProcessingResultId could be a prop.
  initialProcessingResultId?: string; 
}

export const OptimizerPanel: React.FC<OptimizerPanelProps> = ({ initialProcessingResultId }) => {
  const [processingResultId, setProcessingResultId] = useState<string>(initialProcessingResultId || '');
  const [optimizerParamsStr, setOptimizerParamsStr] = useState<string>('{}'); // Default to empty JSON object
  const [optimizationRun, setOptimizationRun] = useState<OptimizerResponse | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const handleRunOptimizer = async () => {
    if (!processingResultId) {
      setError('Processing Result ID is required.');
      return;
    }

    setIsLoading(true);
    setError(null);
    setOptimizationRun(null);

    let params: Record<string, any> | undefined;
    try {
      if (optimizerParamsStr.trim()) {
        params = JSON.parse(optimizerParamsStr);
      }
    } catch (e) {
      setError('Invalid JSON format for Optimizer Parameters.');
      setIsLoading(false);
      return;
    }

    const request: OptimizerRequest = {
      processing_result_id: processingResultId,
      optimizer_params: params,
    };

    try {
      const response = await optimizerApi.runOptimizer(request);
      setOptimizationRun(response);
    } catch (err: any) {
      setError(err.message || 'Failed to run optimizer.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle>Optimizer Panel</CardTitle>
        <CardDescription>Run optimization on a processing result.</CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="space-y-2">
          <Label htmlFor="processingResultId">Processing Result ID</Label>
          <Input
            id="processingResultId"
            placeholder="Enter Processing Result ID (UUID)"
            value={processingResultId}
            onChange={(e) => setProcessingResultId(e.target.value)}
            disabled={isLoading}
          />
        </div>
        <div className="space-y-2">
          <Label htmlFor="optimizerParams">Optimizer Parameters (JSON)</Label>
          <Textarea
            id="optimizerParams"
            placeholder='Enter optimizer parameters as JSON, e.g., {"alpha": 0.5, "iterations": 100}'
            value={optimizerParamsStr}
            onChange={(e) => setOptimizerParamsStr(e.target.value)}
            rows={3}
            disabled={isLoading}
          />
        </div>
        <Button onClick={handleRunOptimizer} disabled={isLoading}>
          {isLoading ? 'Optimizing...' : 'Run Optimizer'}
        </Button>
      </CardContent>
      <CardFooter className="flex-col items-start space-y-2">
        {error && <p className="text-red-500">Error: {error}</p>}
        {optimizationRun && (
          <div className="space-y-2 w-full">
            <h4 className="font-semibold">Optimization Run Details:</h4>
            <p><strong>Run ID:</strong> {optimizationRun.optimizer_run_id}</p>
            <p><strong>Status:</strong> {optimizationRun.status}</p>
            <p><strong>Input Processing Result ID:</strong> {optimizationRun.input_processing_result_id}</p>
            {optimizationRun.message && <p><strong>Message:</strong> {optimizationRun.message}</p>}
            {optimizationRun.results && (
              <div>
                <strong>Results:</strong>
                <pre className="bg-gray-100 p-2 rounded-md text-sm overflow-x-auto">
                  {JSON.stringify(optimizationRun.results, null, 2)}
                </pre>
              </div>
            )}
          </div>
        )}
      </CardFooter>
    </Card>
  );
};
