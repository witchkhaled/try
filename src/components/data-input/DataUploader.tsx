import React, { useState, useCallback, useRef } from 'react';
import { useForm, useFieldArray } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import Papa from 'papaparse';
import { Upload, FileText, X, Download, AlertCircle, CheckCircle } from 'lucide-react';
import { ExperimentalPoint } from '../../types';
import { experimentalPointSchema, ExperimentalPointInput } from '../../utils/validation';
import { parseCSV, parseJSON, exportToCSV, exportToJSON } from '../../utils/data-transform';

interface DataUploaderProps {
  onDataLoaded: (data: ExperimentalPoint[]) => void;
}

interface ManualEntryForm {
  points: Array<{
    T_C: number;
    P_bar: number;
    t_min: number;
    C_exp: number;
    replicate: number;
  }>;
}

export const DataUploader: React.FC<DataUploaderProps> = ({ onDataLoaded }) => {
  const [isDragging, setIsDragging] = useState(false);
  const [parseErrors, setParseErrors] = useState<string[]>([]);
  const [validationErrors, setValidationErrors] = useState<Array<{ row: number; error: string }>>([]);
  const [parsedData, setParsedData] = useState<ExperimentalPoint[]>([]);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const { register, handleSubmit, control, setValue, reset, formState: { errors } } = useForm<ManualEntryForm>({
    resolver: zodResolver(
      experimentalPointSchema.omit({ id: true }).array().min(1, 'At least one point required')
    ),
    defaultValues: {
      points: [{ T_C: 25, P_bar: 1, t_min: 10, C_exp: 0.5, replicate: 1 }]
    }
  });

  const { fields, append, remove } = useFieldArray({
    control,
    name: 'points'
  });

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  }, []);

  const processFile = useCallback((file: File) => {
    const reader = new FileReader();
    const extension = file.name.split('.').pop()?.toLowerCase();

    reader.onload = (event) => {
      const content = event.target?.result as string;
      setParseErrors([]);
      setValidationErrors([]);

      let result: { success: boolean; data?: ExperimentalPoint[]; errors?: string[] };

      if (extension === 'csv') {
        result = parseCSV(content);
      } else if (extension === 'json') {
        result = parseJSON(content);
      } else {
        setParseErrors(['Unsupported file format. Please upload CSV or JSON.']);
        return;
      }

      if (!result.success || !result.data) {
        setParseErrors(result.errors || ['Failed to parse file']);
        return;
      }

      // Validate each point
      const validationResults: Array<{ row: number; error: string }> = [];
      const validPoints: ExperimentalPoint[] = [];

      result.data.forEach((point, index) => {
        const validated = experimentalPointSchema.safeParse(point);
        if (validated.success) {
          validPoints.push(validated.data);
        } else {
          const errorMsg = validated.error.errors.map(e => `${e.path.join('.')}: ${e.message}`).join(', ');
          validationResults.push({ row: index + 1, error: errorMsg });
        }
      });

      if (validationResults.length > 0) {
        setValidationErrors(validationResults);
      }

      if (validPoints.length > 0) {
        setParsedData(validPoints);
      }
    };

    reader.readAsText(file);
  }, []);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);

    const files = e.dataTransfer.files;
    if (files.length > 0) {
      processFile(files[0]);
    }
  }, [processFile]);

  const handleFileSelect = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (files && files.length > 0) {
      processFile(files[0]);
    }
  }, [processFile]);

  const handleManualSubmit = handleSubmit((data) => {
    const pointsWithIds: ExperimentalPoint[] = data.points.map((p, i) => ({
      id: `manual-${Date.now()}-${i}`,
      ...p
    }));
    setParsedData(pointsWithIds);
    setValidationErrors([]);
    setParseErrors([]);
  });

  const handleLoadData = () => {
    if (parsedData.length > 0) {
      onDataLoaded(parsedData);
    }
  };

  const handleExportCSV = () => {
    if (parsedData.length === 0) return;
    const csv = exportToCSV(parsedData);
    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    link.href = URL.createObjectURL(blob);
    link.download = 'experimental_data.csv';
    link.click();
  };

  const handleExportJSON = () => {
    if (parsedData.length === 0) return;
    const json = exportToJSON(parsedData);
    const blob = new Blob([json], { type: 'application/json' });
    const link = document.createElement('a');
    link.href = URL.createObjectURL(blob);
    link.download = 'experimental_data.json';
    link.click();
  };

  const handleClearAll = () => {
    setParsedData([]);
    setParseErrors([]);
    setValidationErrors([]);
    reset();
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  return (
    <div className="space-y-6">
      {/* Drag & Drop Area */}
      <div
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        onClick={() => fileInputRef.current?.click()}
        className={`border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-colors ${
          isDragging
            ? 'border-blue-500 bg-blue-50'
            : 'border-gray-300 hover:border-gray-400 hover:bg-gray-50'
        }`}
      >
        <input
          ref={fileInputRef}
          type="file"
          accept=".csv,.json"
          onChange={handleFileSelect}
          className="hidden"
        />
        <Upload className="mx-auto h-12 w-12 text-gray-400" />
        <p className="mt-2 text-sm text-gray-600">
          Drag & drop a CSV or JSON file here, or click to select
        </p>
        <p className="mt-1 text-xs text-gray-500">
          Expected columns: T_C, P_bar, t_min, C_exp, replicate
        </p>
      </div>

      {/* Parse Errors */}
      {parseErrors.length > 0 && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <div className="flex items-center gap-2 text-red-700 font-medium">
            <AlertCircle className="h-5 w-5" />
            <span>Parse Errors</span>
          </div>
          <ul className="mt-2 text-sm text-red-600 list-disc list-inside">
            {parseErrors.map((error, i) => (
              <li key={i}>{error}</li>
            ))}
          </ul>
        </div>
      )}

      {/* Validation Errors */}
      {validationErrors.length > 0 && (
        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
          <div className="flex items-center gap-2 text-yellow-700 font-medium">
            <AlertCircle className="h-5 w-5" />
            <span>Validation Warnings ({validationErrors.length} rows)</span>
          </div>
          <ul className="mt-2 text-sm text-yellow-600 list-disc list-inside max-h-40 overflow-y-auto">
            {validationErrors.slice(0, 10).map((err, i) => (
              <li key={i}>Row {err.row}: {err.error}</li>
            ))}
            {validationErrors.length > 10 && (
              <li className="text-gray-500">... and {validationErrors.length - 10} more</li>
            )}
          </ul>
        </div>
      )}

      {/* Parsed Data Summary */}
      {parsedData.length > 0 && (
        <div className="bg-green-50 border border-green-200 rounded-lg p-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2 text-green-700 font-medium">
              <CheckCircle className="h-5 w-5" />
              <span>{parsedData.length} valid data points loaded</span>
            </div>
            <div className="flex gap-2">
              <button
                onClick={handleExportCSV}
                className="flex items-center gap-1 px-3 py-1.5 text-sm bg-white border border-gray-300 rounded hover:bg-gray-50"
              >
                <Download className="h-4 w-4" />
                CSV
              </button>
              <button
                onClick={handleExportJSON}
                className="flex items-center gap-1 px-3 py-1.5 text-sm bg-white border border-gray-300 rounded hover:bg-gray-50"
              >
                <Download className="h-4 w-4" />
                JSON
              </button>
              <button
                onClick={handleLoadData}
                className="px-3 py-1.5 text-sm bg-blue-600 text-white rounded hover:bg-blue-700"
              >
                Load to Dashboard
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Manual Entry Form */}
      <div className="border rounded-lg p-6 bg-white">
        <div className="flex items-center justify-between mb-4">
          <h3 className="font-semibold text-gray-900 flex items-center gap-2">
            <FileText className="h-5 w-5" />
            Manual Data Entry
          </h3>
          <button
            onClick={() => append({ T_C: 25, P_bar: 1, t_min: 10, C_exp: 0.5, replicate: 1 })}
            className="text-sm text-blue-600 hover:text-blue-700"
          >
            + Add Row
          </button>
        </div>

        <form onSubmit={handleManualSubmit}>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b">
                  <th className="text-left py-2 px-3 font-medium text-gray-700">T (°C)</th>
                  <th className="text-left py-2 px-3 font-medium text-gray-700">P (bar)</th>
                  <th className="text-left py-2 px-3 font-medium text-gray-700">t (min)</th>
                  <th className="text-left py-2 px-3 font-medium text-gray-700">C_exp</th>
                  <th className="text-left py-2 px-3 font-medium text-gray-700">Replicate</th>
                  <th className="w-10"></th>
                </tr>
              </thead>
              <tbody>
                {fields.map((field, index) => (
                  <tr key={field.id} className="border-b hover:bg-gray-50">
                    <td className="py-2 px-3">
                      <input
                        type="number"
                        step="0.1"
                        {...register(`points.${index}.T_C` as const, { valueAsNumber: true })}
                        className="w-full border rounded px-2 py-1 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                      />
                      {errors.points?.[index]?.T_C && (
                        <span className="text-xs text-red-500">{errors.points[index].T_C?.message}</span>
                      )}
                    </td>
                    <td className="py-2 px-3">
                      <input
                        type="number"
                        step="0.1"
                        {...register(`points.${index}.P_bar` as const, { valueAsNumber: true })}
                        className="w-full border rounded px-2 py-1 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                      />
                      {errors.points?.[index]?.P_bar && (
                        <span className="text-xs text-red-500">{errors.points[index].P_bar?.message}</span>
                      )}
                    </td>
                    <td className="py-2 px-3">
                      <input
                        type="number"
                        step="0.1"
                        {...register(`points.${index}.t_min` as const, { valueAsNumber: true })}
                        className="w-full border rounded px-2 py-1 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                      />
                      {errors.points?.[index]?.t_min && (
                        <span className="text-xs text-red-500">{errors.points[index].t_min?.message}</span>
                      )}
                    </td>
                    <td className="py-2 px-3">
                      <input
                        type="number"
                        step="0.001"
                        {...register(`points.${index}.C_exp` as const, { valueAsNumber: true })}
                        className="w-full border rounded px-2 py-1 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                      />
                      {errors.points?.[index]?.C_exp && (
                        <span className="text-xs text-red-500">{errors.points[index].C_exp?.message}</span>
                      )}
                    </td>
                    <td className="py-2 px-3">
                      <input
                        type="number"
                        step="1"
                        min="1"
                        max="5"
                        {...register(`points.${index}.replicate` as const, { valueAsNumber: true })}
                        className="w-full border rounded px-2 py-1 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                      />
                      {errors.points?.[index]?.replicate && (
                        <span className="text-xs text-red-500">{errors.points[index].replicate?.message}</span>
                      )}
                    </td>
                    <td className="py-2 px-3">
                      {fields.length > 1 && (
                        <button
                          type="button"
                          onClick={() => remove(index)}
                          className="text-gray-400 hover:text-red-500"
                        >
                          <X className="h-4 w-4" />
                        </button>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <div className="mt-4 flex gap-3">
            <button
              type="submit"
              className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
            >
              Validate & Preview
            </button>
            <button
              type="button"
              onClick={handleClearAll}
              className="px-4 py-2 bg-gray-200 text-gray-700 rounded hover:bg-gray-300"
            >
              Clear All
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
