export interface GasProperty {
  name: string;
  molarMass: number;
  kH: number;
  Tc: number;
  Pc: number;
}

export interface ExperimentalPoint {
  id: string;
  T_C: number;
  P_bar: number;
  t_min: number;
  C_exp: number;
  replicate: number;
}

export interface AnalysisResult {
  T_C: number;
  P_bar: number;
  C_exp: number;
  C_ideal: number;
  C_real: number;
  deviation_abs: number;
  deviation_pct: number;
  uncertainty_expanded: number;
  ci_95_lower: number;
  ci_95_upper: number;
}
