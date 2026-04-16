import { z } from 'zod';

export const experimentalPointSchema = z.object({
  id: z.string(),
  T_C: z.number().min(-50).max(500, "Temperature must be between -50 and 500°C"),
  P_bar: z.number().min(0.1).max(100, "Pressure must be between 0.1 and 100 bar"),
  t_min: z.number().positive("Time must be positive"),
  C_exp: z.number().positive("Concentration must be positive"),
  replicate: z.number().int().min(1).max(5, "Replicate must be between 1 and 5")
});

export type ExperimentalPointInput = z.infer<typeof experimentalPointSchema>;

export const validateExperimentalPoint = (data: unknown) => {
  return experimentalPointSchema.safeParse(data);
};

export const validateBatchPoints = (data: Array<Record<string, unknown>>) => {
  const results: Array<{ valid: true; data: ExperimentalPointInput } | { valid: false; error: string; row: number }> = [];
  
  data.forEach((row, index) => {
    const parsed = experimentalPointSchema.safeParse(row);
    if (parsed.success) {
      results.push({ valid: true, data: parsed.data });
    } else {
      const errorMessage = parsed.error.errors.map(e => `${e.path.join('.')}: ${e.message}`).join(', ');
      results.push({ valid: false, error: errorMessage, row: index + 1 });
    }
  });
  
  return results;
};
