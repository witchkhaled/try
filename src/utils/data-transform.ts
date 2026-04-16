import Papa from 'papaparse';
import { ExperimentalPoint } from '../types';

export interface ParseResult {
  success: boolean;
  data?: ExperimentalPoint[];
  errors?: string[];
}

// Simple UUID v4 generator without external dependency
const generateUUID = (): string => {
  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, (c) => {
    const r = Math.random() * 16 | 0;
    const v = c === 'x' ? r : (r & 0x3 | 0x8);
    return v.toString(16);
  });
};

export const parseCSV = (csvContent: string): ParseResult => {
  const errors: string[] = [];
  
  const result = Papa.parse<Record<string, string>>(csvContent, {
    header: true,
    skipEmptyLines: true,
    dynamicTyping: true
  });

  if (result.errors.length > 0) {
    result.errors.forEach(err => {
      errors.push(`Row ${err.row}: ${err.message}`);
    });
  }

  const mappedData: ExperimentalPoint[] = result.data.map((row, index) => {
    const point: ExperimentalPoint = {
      id: generateUUID(),
      T_C: Number(row['T_C'] ?? row['t_c'] ?? row['temperature'] ?? 0),
      P_bar: Number(row['P_bar'] ?? row['p_bar'] ?? row['pressure'] ?? 0),
      t_min: Number(row['t_min'] ?? row['time'] ?? 0),
      C_exp: Number(row['C_exp'] ?? row['c_exp'] ?? row['concentration'] ?? 0),
      replicate: Number(row['replicate'] ?? row['rep'] ?? 1)
    };
    return point;
  });

  return {
    success: errors.length === 0,
    data: mappedData,
    errors: errors.length > 0 ? errors : undefined
  };
};

export const parseJSON = (jsonContent: string): ParseResult => {
  try {
    const parsed = JSON.parse(jsonContent);
    
    if (!Array.isArray(parsed)) {
      return {
        success: false,
        errors: ['JSON must be an array of experimental points']
      };
    }

    const mappedData: ExperimentalPoint[] = parsed.map((item: Record<string, unknown>) => ({
      id: (item.id as string) || generateUUID(),
      T_C: Number(item.T_C ?? item.t_c ?? item.temperature ?? 0),
      P_bar: Number(item.P_bar ?? item.p_bar ?? item.pressure ?? 0),
      t_min: Number(item.t_min ?? item.time ?? 0),
      C_exp: Number(item.C_exp ?? item.c_exp ?? item.concentration ?? 0),
      replicate: Number(item.replicate ?? item.rep ?? 1)
    }));

    return {
      success: true,
      data: mappedData
    };
  } catch (error) {
    return {
      success: false,
      errors: [`JSON parse error: ${(error as Error).message}`]
    };
  }
};

export const exportToCSV = (data: ExperimentalPoint[]): string => {
  const csv = Papa.unparse(data.map(({ id, ...rest }) => rest));
  return csv;
};

export const exportToJSON = (data: ExperimentalPoint[]): string => {
  return JSON.stringify(data.map(({ id, ...rest }) => rest), null, 2);
};
