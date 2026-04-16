/**
 * Experimental Gas Absorption Data Analysis System
 * 
 * A comprehensive JavaScript module for processing experimental gas absorption data,
 * performing thermodynamic calculations, statistical analysis, and generating reports.
 * 
 * Designed for Node.js environments. For browser usage, replace 'fs' imports with
 * file input handlers and use native DOM manipulation for exports.
 */

// ============================================================================
// SECTION 1: DATA STRUCTURES & VALIDATION
// ============================================================================

/**
 * Validates temperature range (-50°C to 500°C)
 */
function validateTemperature(temp) {
    if (temp === null || temp === undefined) return { valid: false, error: "Missing temperature" };
    if (temp < -50 || temp > 500) return { valid: false, error: `Temperature ${temp}°C out of range [-50, 500]` };
    return { valid: true };
}

/**
 * Validates pressure range (0.1 to 100 bar)
 */
function validatePressure(pressure) {
    if (pressure === null || pressure === undefined) return { valid: false, error: "Missing pressure" };
    if (pressure < 0.1 || pressure > 100) return { valid: false, error: `Pressure ${pressure} bar out of range [0.1, 100]` };
    return { valid: true };
}

/**
 * Detects outliers using the Interquartile Range (IQR) method
 */
function detectOutliersIQR(dataArray) {
    if (!dataArray || dataArray.length < 4) return { outliers: [], indices: [] };
    
    const sorted = [...dataArray].sort((a, b) => a - b);
    const q1Index = Math.floor(sorted.length / 4);
    const q3Index = Math.ceil(3 * sorted.length / 4);
    
    const q1 = sorted[q1Index];
    const q3 = sorted[q3Index];
    const iqr = q3 - q1;
    
    const lowerBound = q1 - 1.5 * iqr;
    const upperBound = q3 + 1.5 * iqr;
    
    const outliers = [];
    const indices = [];
    
    dataArray.forEach((val, idx) => {
        if (val < lowerBound || val > upperBound) {
            outliers.push(val);
            indices.push(idx);
        }
    });
    
    return { outliers, indices, bounds: { lower: lowerBound, upper: upperBound } };
}

/**
 * Main Validation Class
 */
class DataValidator {
    constructor() {
        this.errors = [];
        this.warnings = [];
        this.flaggedPoints = [];
    }

    validatePoint(point, index) {
        const issues = [];
        
        // Check missing data
        if (point.temperature === null || point.pressure === null || point.absorption_capacity === null) {
            issues.push("Missing critical data fields");
        }

        // Validate ranges
        const tempCheck = validateTemperature(point.temperature);
        if (!tempCheck.valid) issues.push(tempCheck.error);

        const presCheck = validatePressure(point.pressure);
        if (!presCheck.valid) issues.push(presCheck.error);

        if (issues.length > 0) {
            this.flaggedPoints.push({ index, issues });
            return false;
        }
        return true;
    }

    validateDataset(dataPoints) {
        this.errors = [];
        this.warnings = [];
        this.flaggedPoints = [];

        // Point-by-point validation
        dataPoints.forEach((pt, idx) => this.validatePoint(pt, idx));

        // Outlier detection on absorption capacity
        const capacities = dataPoints.map(p => p.absorption_capacity).filter(v => v !== null);
        const outlierResult = detectOutliersIQR(capacities);
        
        if (outlierResult.indices.length > 0) {
            this.warnings.push(`Detected ${outlierResult.indices.length} statistical outliers in absorption capacity`);
            outlierResult.indices.forEach(idx => {
                this.flaggedPoints.push({ 
                    index: idx, 
                    issues: [`Statistical outlier (value: ${capacities[idx]})`] 
                });
            });
        }

        return {
            isValid: this.errors.length === 0,
            errors: this.errors,
            warnings: this.warnings,
            flaggedCount: this.flaggedPoints.length
        };
    }
}

// ============================================================================
// SECTION 2: THERMODYNAMIC CALCULATIONS
// ============================================================================

const R = 0.08314; // L·bar/(mol·K)

class Thermodynamics {
    /**
     * Convert Celsius to Kelvin
     */
    static celsiusToKelvin(tC) {
        return tC + 273.15;
    }

    /**
     * Ideal Gas Law: PV = nRT -> n = PV/RT
     * Calculates theoretical moles of gas
     */
    static idealGasMoles(pressure, volume, tempC) {
        const T = this.celsiusToKelvin(tempC);
        return (pressure * volume) / (R * T);
    }

    /**
     * Henry's Law: C = kH * P
     */
    static henrysLaw(kH, pressure) {
        return kH * pressure;
    }

    /**
     * Van der Waals Equation parameters from Critical Properties
     * a = 27 * (R^2 * Tc^2) / (64 * Pc)
     * b = (R * Tc) / (8 * Pc)
     */
    static getVdwParameters(Tc, Pc) {
        const TcK = typeof Tc === 'number' && Tc < 100 ? this.celsiusToKelvin(Tc) : Tc; // Handle if Tc is in C
        const a = (27 * Math.pow(R * TcK, 2)) / (64 * Pc);
        const b = (R * TcK) / (8 * Pc);
        return { a, b };
    }

    /**
     * Van der Waals Pressure: P = (nRT)/(V-nb) - (an^2)/V^2
     */
    static vanDerWaalsPressure(n, V, T, a, b) {
        const TK = this.celsiusToKelvin(T);
        const term1 = (n * R * TK) / (V - n * b);
        const term2 = (a * Math.pow(n, 2)) / Math.pow(V, 2);
        return term1 - term2;
    }

    /**
     * Peng-Robinson Alpha Function
     */
    static pengRobinsonAlpha(T, Tc, omega) {
        const TK = this.celsiusToKelvin(T);
        const Tr = TK / Tc;
        const kappa = 0.37464 + 1.54226 * omega - 0.26992 * Math.pow(omega, 2);
        return Math.pow(1 + kappa * (1 - Math.sqrt(Tr)), 2);
    }

    /**
     * Compressibility Factor Z (Approximate via VdW for simplicity in JS port)
     * Z = PV / nRT
     */
    static compressibilityFactor(P, V, n, T) {
        const TK = this.celsiusToKelvin(T);
        return (P * V) / (n * R * TK);
    }

    /**
     * Arrhenius Equation: k = A * exp(-Ea / RT)
     */
    static arrheniusRate(A, Ea, T) {
        const TK = this.celsiusToKelvin(T);
        return A * Math.exp(-Ea / (8.314 * TK)); // Ea in J/mol, R=8.314 J/(mol K)
    }

    /**
     * Antoine Equation: log10(P) = A - B/(T+C) -> P in mmHg
     * Returns pressure in bar
     */
    static antoineVaporPressure(A, B, C, T) {
        // T expected in Celsius for standard Antoine constants
        const logP = A - (B / (T + C));
        const pHg = Math.pow(10, logP);
        return pHg * 0.00133322; // Convert mmHg to bar
    }
}

// ============================================================================
// SECTION 3: STATISTICAL ANALYSIS & UNCERTAINTY
// ============================================================================

class Statistics {
    /**
     * Calculate Mean
     */
    static mean(data) {
        if (data.length === 0) return 0;
        return data.reduce((a, b) => a + b, 0) / data.length;
    }

    /**
     * Calculate Standard Deviation (Sample)
     */
    static stdDev(data) {
        if (data.length < 2) return 0;
        const m = this.mean(data);
        const variance = data.reduce((sum, val) => sum + Math.pow(val - m, 2), 0) / (data.length - 1);
        return Math.sqrt(variance);
    }

    /**
     * Linear Regression (Least Squares)
     * Returns slope, intercept, rSquared
     */
    static linearRegression(x, y) {
        const n = x.length;
        if (n !== y.length || n === 0) return null;

        const sumX = x.reduce((a, b) => a + b, 0);
        const sumY = y.reduce((a, b) => a + b, 0);
        const sumXY = x.reduce((sum, xi, i) => sum + xi * y[i], 0);
        const sumXX = x.reduce((sum, xi) => sum + xi * xi, 0);

        const slope = (n * sumXY - sumX * sumY) / (n * sumXX - sumX * sumX);
        const intercept = (sumY - slope * sumX) / n;

        // Calculate R²
        const yMean = sumY / n;
        const ssTot = y.reduce((sum, yi) => sum + Math.pow(yi - yMean, 2), 0);
        const ssRes = y.reduce((sum, yi, i) => {
            const pred = slope * x[i] + intercept;
            return sum + Math.pow(yi - pred, 2);
        }, 0);

        const rSquared = 1 - (ssRes / ssTot);

        return { slope, intercept, rSquared };
    }

    /**
     * Type A Uncertainty (Statistical): uA = s / sqrt(n)
     */
    static typeAUncertainty(data) {
        const s = this.stdDev(data);
        return s / Math.sqrt(data.length);
    }

    /**
     * Combined Uncertainty: uc = sqrt(uA² + uB²)
     */
    static combinedUncertainty(uA, uB) {
        return Math.sqrt(Math.pow(uA, 2) + Math.pow(uB, 2));
    }

    /**
     * Expanded Uncertainty: U = k * uc
     */
    static expandedUncertainty(uc, k = 2) {
        return k * uc;
    }
}

// ============================================================================
// SECTION 4: DEVIATION METRICS & SENSITIVITY
// ============================================================================

class DeviationAnalysis {
    /**
     * Calculate RMSE
     */
    static rmse(experimental, predicted) {
        if (experimental.length !== predicted.length) throw new Error("Array lengths mismatch");
        const n = experimental.length;
        const sumSq = experimental.reduce((sum, exp, i) => {
            return sum + Math.pow(exp - predicted[i], 2);
        }, 0);
        return Math.sqrt(sumSq / n);
    }

    /**
     * Calculate MAPE (%)
     */
    static mape(experimental, predicted) {
        if (experimental.length !== predicted.length) throw new Error("Array lengths mismatch");
        const n = experimental.length;
        const sumPercent = experimental.reduce((sum, exp, i) => {
            if (exp === 0) return sum;
            return sum + Math.abs((exp - predicted[i]) / exp);
        }, 0);
        return (sumPercent / n) * 100;
    }

    /**
     * Calculate R²
     */
    static rSquared(experimental, predicted) {
        const reg = Statistics.linearRegression(
            experimental, // Using experimental as X for correlation check, or predicted vs actual
            predicted
        );
        // Standard R² calculation between two series
        const meanExp = Statistics.mean(experimental);
        const ssTot = experimental.reduce((sum, val) => sum + Math.pow(val - meanExp, 2), 0);
        const ssRes = experimental.reduce((sum, val, i) => sum + Math.pow(val - predicted[i], 2), 0);
        return 1 - (ssRes / ssTot);
    }

    /**
     * Sensitivity Coefficient (Finite Difference Approximation)
     * d(Absorption)/d(Temperature)
     */
    static sensitivityTemperature(calcFunc, baseParams, deltaT = 0.1) {
        const paramsPlus = { ...baseParams, temperature: baseParams.temperature + deltaT };
        const paramsMinus = { ...baseParams, temperature: baseParams.temperature - deltaT };
        
        const valPlus = calcFunc(paramsPlus);
        const valMinus = calcFunc(paramsMinus);
        
        return (valPlus - valMinus) / (2 * deltaT);
    }

    /**
     * Sensitivity Coefficient (Finite Difference Approximation)
     * d(Absorption)/d(Pressure)
     */
    static sensitivityPressure(calcFunc, baseParams, deltaP = 0.01) {
        const paramsPlus = { ...baseParams, pressure: baseParams.pressure + deltaP };
        const paramsMinus = { ...baseParams, pressure: baseParams.pressure - deltaP };
        
        const valPlus = calcFunc(paramsPlus);
        const valMinus = calcFunc(paramsMinus);
        
        return (valPlus - valMinus) / (2 * deltaP);
    }
}

// ============================================================================
// SECTION 5: DASHBOARD DATA GENERATOR
// ============================================================================

class DashboardGenerator {
    /**
     * Prepares data structure for 3D Surface Plots (compatible with Plotly.js)
     */
    static generate3DSurfaceData(dataPoints, idealFunc) {
        // Group by Temperature and Pressure to form a grid
        const temps = [...new Set(dataPoints.map(d => d.temperature))].sort((a,b)=>a-b);
        const pressures = [...new Set(dataPoints.map(d => d.pressure))].sort((a,b)=>a-b);
        
        const zExperimental = [];
        const zIdeal = [];

        temps.forEach(t => {
            const rowExp = [];
            const rowIdeal = [];
            pressures.forEach(p => {
                const point = dataPoints.find(d => d.temperature === t && d.pressure === p);
                rowExp.push(point ? point.absorption_capacity : null);
                
                // Calculate Ideal
                if (idealFunc) {
                    rowIdeal.push(idealFunc(t, p));
                } else {
                    rowIdeal.push(null);
                }
            });
            zExperimental.push(rowExp);
            zIdeal.push(rowIdeal);
        });

        return {
            x: pressures,
            y: temps,
            zExp: zExperimental,
            zIdeal: zIdeal
        };
    }

    /**
     * Prepares data for Deviation Heatmap
     */
    static generateHeatmapData(dataPoints, idealValues) {
        return dataPoints.map((pt, i) => ({
            temperature: pt.temperature,
            pressure: pt.pressure,
            deviation: Math.abs(pt.absorption_capacity - idealValues[i]),
            relativeError: ((pt.absorption_capacity - idealValues[i]) / idealValues[i]) * 100
        }));
    }

    /**
     * Generates KPI Cards Data
     */
    static calculateKPIs(dataPoints, idealValues) {
        const absValues = dataPoints.map(d => d.absorption_capacity);
        const deviations = dataPoints.map((d, i) => Math.abs(d.absorption_capacity - idealValues[i]));
        
        return {
            avgAbsorption: Statistics.mean(absValues),
            maxDeviation: Math.max(...deviations),
            rmse: DeviationAnalysis.rmse(absValues, idealValues),
            rSquared: DeviationAnalysis.rSquared(absValues, idealValues)
        };
    }
}

// ============================================================================
// SECTION 6: EXPORT UTILITIES
// ============================================================================

const ExportUtils = {
    /**
     * Convert data to CSV string
     */
    toCSV: function(dataArray) {
        if (!dataArray || dataArray.length === 0) return "";
        const headers = Object.keys(dataArray[0]);
        const csvRows = [
            headers.join(','),
            ...dataArray.map(row => 
                headers.map(fieldName => {
                    const val = row[fieldName];
                    // Escape quotes and wrap in quotes if contains comma
                    const str = String(val === null ? '' : val);
                    return str.includes(',') ? `"${str}"` : str;
                }).join(',')
            )
        ];
        return csvRows.join('\n');
    },

    /**
     * Generate JSON Report Structure
     */
    generateReportJSON: function(experimentMeta, results, kpis, validationResults) {
        return {
            meta: experimentMeta,
            generatedAt: new Date().toISOString(),
            summary: {
                keyFindings: [
                    `Average Absorption: ${kpis.avgAbsorption.toFixed(4)} mol/L`,
                    `Model Fit (R²): ${kpis.rSquared.toFixed(4)}`,
                    `RMSE: ${kpis.rmse.toFixed(4)}`
                ],
                validationStatus: validationResults.isValid ? "PASSED" : "FAILED"
            },
            statistics: {
                rmse: kpis.rmse,
                rSquared: kpis.rSquared,
                maxDeviation: kpis.maxDeviation
            },
            validation: validationResults,
            rawData: results.dataPoints,
            analysis: results.calculatedValues
        };
    },

    /**
     * Generate standalone HTML Dashboard skeleton
     * (In a real app, this would inject Plotly.js and the data)
     */
    generateHTMLDashboard: function(reportData) {
        const scriptData = JSON.stringify(reportData);
        return `<!DOCTYPE html>
<html>
<head>
    <title>Experimental Data Dashboard</title>
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        .kpi-container { display: flex; gap: 20px; margin-bottom: 20px; }
        .kpi-card { border: 1px solid #ddd; padding: 15px; border-radius: 5px; flex: 1; text-align: center; }
        .chart-container { width: 100%; height: 500px; margin-bottom: 20px; }
    </style>
</head>
<body>
    <h1>Gas Absorption Analysis Report</h1>
    <div id="kpi-display" class="kpi-container"></div>
    <div id="3d-plot" class="chart-container"></div>
    <div id="heatmap" class="chart-container"></div>

    <script>
        const report = ${scriptData};
        
        // Render KPIs
        const kpiContainer = document.getElementById('kpi-display');
        const kpis = report.statistics;
        kpiContainer.innerHTML = \`
            <div class="kpi-card"><h3>Avg Absorption</h3><p>\${kpis.avgAbsorption ? kpis.avgAbsorption.toFixed(4) : 'N/A'}</p></div>
            <div class="kpi-card"><h3>R² Score</h3><p>\${kpis.rSquared.toFixed(4)}</p></div>
            <div class="kpi-card"><h3>RMSE</h3><p>\${kpis.rmse.toFixed(4)}</p></div>
        \`;

        // Note: Actual Plotly rendering logic would go here using report.analysis.surfaceData
        console.log("Dashboard loaded with data:", report);
        document.body.insertAdjacentHTML('beforeend', '<p><em>Interactive charts would render here using Plotly.js with the embedded data.</em></p>');
    <\/script>
</body>
</html>`;
    }
};

// ============================================================================
// SECTION 8: VALIDATION & TESTS
// ============================================================================

function runValidationTests() {
    console.log("--- Running Validation Tests ---");
    
    // Test 1: Thermodynamics
    const n = Thermodynamics.idealGasMoles(1, 1, 25); // 1 bar, 1 L, 25C
    const expectedN = 0.0409; // Approx
    const test1Pass = Math.abs(n - expectedN) < 0.001;
    console.log(`Test 1 (Ideal Gas Moles): ${test1Pass ? 'PASS' : 'FAIL'} (Got: ${n.toFixed(4)})`);

    // Test 2: Statistics
    const data = [10, 12, 23, 23, 16, 23, 21, 16];
    const meanVal = Statistics.mean(data);
    const test2Pass = Math.abs(meanVal - 18) < 0.001;
    console.log(`Test 2 (Mean Calculation): ${test2Pass ? 'PASS' : 'FAIL'} (Got: ${meanVal})`);

    // Test 3: Deviation
    const exp = [10, 20, 30];
    const pred = [10, 20, 30];
    const rmseVal = DeviationAnalysis.rmse(exp, pred);
    const test3Pass = rmseVal === 0;
    console.log(`Test 3 (RMSE Perfect Match): ${test3Pass ? 'PASS' : 'FAIL'} (Got: ${rmseVal})`);

    // Test 4: Validation
    const validator = new DataValidator();
    const badData = [{ temperature: -60, pressure: 1, absorption_capacity: 0.5 }];
    const result = validator.validateDataset(badData);
    const test4Pass = !result.isValid && result.flaggedCount > 0;
    console.log(`Test 4 (Range Validation): ${test4Pass ? 'PASS' : 'FAIL'} (Flagged: ${result.flaggedCount})`);

    console.log("--- Tests Complete ---");
    return test1Pass && test2Pass && test3Pass && test4Pass;
}

// ============================================================================
// EXAMPLE USAGE
// ============================================================================

/*
// Example: Processing a dataset
const rawData = [
    { temperature: 25, pressure: 1.0, absorption_capacity: 0.041, time: 0 },
    { temperature: 25, pressure: 2.0, absorption_capacity: 0.082, time: 10 },
    { temperature: 50, pressure: 1.0, absorption_capacity: 0.035, time: 0 },
    { temperature: 50, pressure: 2.0, absorption_capacity: 0.070, time: 10 },
];

// 1. Validate
const validator = new DataValidator();
const valResult = validator.validateDataset(rawData);

// 2. Calculate Ideal Values (Henry's Law example)
const kH = 0.041; // hypothetical constant
const idealValues = rawData.map(d => Thermodynamics.henrysLaw(kH, d.pressure));

// 3. Analyze Deviations
const kpis = DashboardGenerator.calculateKPIs(rawData, idealValues);

// 4. Generate Report Data
const report = ExportUtils.generateReportJSON(
    { title: "CO2 Absorption Exp", date: new Date() },
    { dataPoints: rawData, calculatedValues: idealValues },
    kpis,
    valResult
);

// 5. Export
const csv = ExportUtils.toCSV(rawData);
const html = ExportUtils.generateHTMLDashboard(report);
*/

// Export modules for Node.js
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        DataValidator,
        Thermodynamics,
        Statistics,
        DeviationAnalysis,
        DashboardGenerator,
        ExportUtils,
        runValidationTests,
        validateTemperature,
        validatePressure,
        detectOutliersIQR
    };
}

// Auto-run tests if executed directly
if (typeof require !== 'undefined' && require.main === module) {
    runValidationTests();
}
