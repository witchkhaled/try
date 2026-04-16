/**
 * Gas Absorption Analysis Library
 * Compatible with Node.js and Modern Browsers (ES Modules)
 */

// --- Constants ---
const R = 0.08314; // L·bar/(mol·K)

// --- Data Structures & Validation ---

export function validateTemperature(temp) {
    if (temp === null || temp === undefined) return { valid: false, error: "Missing value" };
    if (temp < -50 || temp > 500) return { valid: false, error: "Out of range (-50 to 500°C)" };
    return { valid: true };
}

export function validatePressure(pressure) {
    if (pressure === null || pressure === undefined) return { valid: false, error: "Missing value" };
    if (pressure < 0.1 || pressure > 100) return { valid: false, error: "Out of range (0.1 to 100 bar)" };
    return { valid: true };
}

export function detectOutliersIQR(data) {
    if (data.length < 4) return [];
    const sorted = [...data].sort((a, b) => a - b);
    const q1 = sorted[Math.floor(sorted.length / 4)];
    const q3 = sorted[Math.ceil(sorted.length * 3 / 4)];
    const iqr = q3 - q1;
    const lower = q1 - 1.5 * iqr;
    const upper = q3 + 1.5 * iqr;
    return data.map(val => val < lower || val > upper);
}

export class DataValidator {
    static validateExperiment(experiment) {
        const errors = [];
        const warnings = [];
        const temps = experiment.dataPoints.map(d => d.temperature);
        const pressures = experiment.dataPoints.map(d => d.pressure);

        experiment.dataPoints.forEach((point, index) => {
            const tempVal = validateTemperature(point.temperature);
            if (!tempVal.valid) errors.push(`Point ${index}: ${tempVal.error}`);
            
            const pressVal = validatePressure(point.pressure);
            if (!pressVal.valid) errors.push(`Point ${index}: ${pressVal.error}`);
            
            if (point.absorption_capacity === null) warnings.push(`Point ${index}: Missing absorption data`);
        });

        const outliers = detectOutliersIQR(temps);
        if (outliers.some(x => x)) warnings.push("Temperature outliers detected via IQR");

        return {
            isValid: errors.length === 0,
            errors,
            warnings,
            outlierFlags: outliers
        };
    }
}

// --- Thermodynamic Calculations ---

export class Thermodynamics {
    static celsiusToKelvin(t) { return t + 273.15; }
    
    static idealGasLaw(P, V, T) {
        // P in bar, V in L, T in °C
        const TK = this.celsiusToKelvin(T);
        return (P * V) / (R * TK); // moles
    }

    static henrysLaw(kH, P) {
        return kH * P;
    }

    static vanDerWaalsPressure(n, T, V, a, b) {
        const TK = this.celsiusToKelvin(T);
        const term1 = (n * R * TK) / (V - n * b);
        const term2 = (a * n * n) / (V * V);
        return term1 - term2;
    }

    static pengRobinsonAlpha(Tc, Tr, w) {
        const kappa = 0.37464 + 1.54226 * w - 0.26992 * w * w;
        return Math.pow(1 + kappa * (1 - Math.sqrt(Tr)), 2);
    }

    static compressibilityFactorZ(P, T, Tc, Pc) {
        const Pr = P / Pc;
        const Tr = this.celsiusToKelvin(T) / Tc;
        // Simplified Pitzer correlation for Z
        const B0 = 0.083 - 0.422 / Math.pow(Tr, 1.6);
        const B1 = 0.139 - 0.172 / Math.pow(Tr, 4.2);
        // Assuming w=0.1 for generic gas if not provided
        const w = 0.1; 
        const Z = 1 + (B0 + w * B1) * Pr / Tr;
        return Z;
    }

    static arrheniusRate(k0, Ea, T) {
        const TK = this.celsiusToKelvin(T);
        return k0 * Math.exp(-Ea / (8.314 * TK));
    }

    static antoineVaporPressure(A, B, C, T) {
        // Returns mmHg
        return Math.pow(10, A - B / (T + C));
    }
}

// --- Statistical Analysis ---

export class Statistics {
    static mean(data) {
        if (data.length === 0) return 0;
        return data.reduce((a, b) => a + b, 0) / data.length;
    }

    static stdDev(data) {
        if (data.length < 2) return 0;
        const m = this.mean(data);
        const variance = data.reduce((acc, val) => acc + Math.pow(val - m, 2), 0) / (data.length - 1);
        return Math.sqrt(variance);
    }

    static linearRegression(x, y) {
        const n = x.length;
        const sumX = x.reduce((a, b) => a + b, 0);
        const sumY = y.reduce((a, b) => a + b, 0);
        const sumXY = x.reduce((acc, xi, i) => acc + xi * y[i], 0);
        const sumXX = x.reduce((acc, xi) => acc + xi * xi, 0);

        const slope = (n * sumXY - sumX * sumY) / (n * sumXX - sumX * sumX);
        const intercept = (sumY - slope * sumX) / n;
        
        return { slope, intercept };
    }

    static uncertaintyTypeA(data) {
        return this.stdDev(data) / Math.sqrt(data.length);
    }

    static combinedUncertainty(uA, uB) {
        return Math.sqrt(uA * uA + uB * uB);
    }

    static expandedUncertainty(uc, k = 2) {
        return uc * k;
    }
}

// --- Deviation Analysis ---

export class DeviationAnalysis {
    static calculateRMSE(exp, ideal) {
        const n = exp.length;
        const sumSq = exp.reduce((acc, val, i) => acc + Math.pow(val - ideal[i], 2), 0);
        return Math.sqrt(sumSq / n);
    }

    static calculateMAPE(exp, ideal) {
        const n = exp.length;
        const sumPercent = exp.reduce((acc, val, i) => {
            if (ideal[i] === 0) return acc;
            return acc + Math.abs((val - ideal[i]) / ideal[i]);
        }, 0);
        return (sumPercent / n) * 100;
    }

    static rSquared(exp, ideal) {
        const meanExp = Statistics.mean(exp);
        const ssTot = exp.reduce((acc, val) => acc + Math.pow(val - meanExp, 2), 0);
        const ssRes = exp.reduce((acc, val, i) => acc + Math.pow(val - ideal[i], 2), 0);
        return 1 - (ssRes / ssTot);
    }
}

// --- Dashboard Data Generator ---

export class DashboardGenerator {
    static generateSurfaceData(dataPoints) {
        // Grid generation for 3D plot
        const temps = [...new Set(dataPoints.map(d => d.temperature))].sort((a,b)=>a-b);
        const pressures = [...new Set(dataPoints.map(d => d.pressure))].sort((a,b)=>a-b);
        
        const zExp = [];
        const zIdeal = [];

        temps.forEach(t => {
            const rowExp = [];
            const rowIdeal = [];
            pressures.forEach(p => {
                const point = dataPoints.find(d => d.temperature === t && d.pressure === p);
                const expVal = point ? point.absorption_capacity : null;
                // Calculate Ideal using Henry's law approximation for demo
                const idealVal = point ? Thermodynamics.henrysLaw(0.5, p) * (1 - (t-25)*0.01) : null; 
                
                rowExp.push(expVal);
                rowIdeal.push(idealVal);
            });
            zExp.push(rowExp);
            zIdeal.push(rowIdeal);
        });

        return { temps, pressures, zExp, zIdeal };
    }

    static generateKPIs(dataPoints) {
        const absValues = dataPoints.map(d => d.absorption_capacity).filter(v => v !== null);
        const avgAbs = Statistics.mean(absValues);
        const maxDev = Math.max(...absValues) - Math.min(...absValues);
        return { avgAbs, maxDev };
    }
}

// --- Export Utilities ---

export class ExportUtils {
    static exportToCSV(dataPoints, filename = "data.csv") {
        const headers = ["Temperature", "Pressure", "Absorption", "Time"];
        const csvContent = [
            headers.join(","),
            ...dataPoints.map(d => 
                `${d.temperature},${d.pressure},${d.absorption_capacity},${d.time}`
            )
        ].join("\n");
        
        const blob = new Blob([csvContent], { type: "text/csv" });
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = filename;
        a.click();
    }

    static exportReport(results, filename = "report.json") {
        const json = JSON.stringify(results, null, 2);
        const blob = new Blob([json], { type: "application/json" });
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = filename;
        a.click();
    }
}
