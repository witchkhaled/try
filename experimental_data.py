"""
Data structures and import/validation module for experimental gas absorption data.

This module provides:
- Data structures for experimental data points, gas properties, and system parameters
- Data import functions for CSV/Excel, manual entry, JSON, and real-time sensor API
- Data validation including outlier detection and range checks
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime
import csv
import json
from pathlib import Path


# =============================================================================
# 1.1 Data Structures
# =============================================================================

@dataclass
class ExperimentalDataPoint:
    """Represents a single experimental data point."""
    temperature: float  # °C
    pressure: float     # bar
    absorption_capacity: float  # mol/kg or similar unit
    time: float  # seconds or minutes
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            'temperature': self.temperature,
            'pressure': self.pressure,
            'absorption_capacity': self.absorption_capacity,
            'time': self.time,
            'timestamp': self.timestamp.isoformat(),
            'metadata': self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ExperimentalDataPoint':
        """Create from dictionary representation."""
        timestamp = data.get('timestamp')
        if isinstance(timestamp, str):
            timestamp = datetime.fromisoformat(timestamp)
        elif timestamp is None:
            timestamp = datetime.now()
        
        return cls(
            temperature=data['temperature'],
            pressure=data['pressure'],
            absorption_capacity=data['absorption_capacity'],
            time=data['time'],
            timestamp=timestamp,
            metadata=data.get('metadata', {})
        )


@dataclass
class GasProperties:
    """Represents gas properties."""
    name: str
    molar_mass: float  # g/mol
    critical_temperature: float  # K
    critical_pressure: float  # bar
    additional_properties: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            'name': self.name,
            'molar_mass': self.molar_mass,
            'critical_temperature': self.critical_temperature,
            'critical_pressure': self.critical_pressure,
            'additional_properties': self.additional_properties
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'GasProperties':
        """Create from dictionary representation."""
        return cls(
            name=data['name'],
            molar_mass=data['molar_mass'],
            critical_temperature=data['critical_temperature'],
            critical_pressure=data['critical_pressure'],
            additional_properties=data.get('additional_properties', {})
        )


@dataclass
class SystemParameters:
    """Represents system parameters for the experimental setup."""
    solvent_type: str
    flow_rate: float  # L/min or similar
    column_diameter: float  # cm
    column_height: float  # cm
    column_material: Optional[str] = None
    packing_type: Optional[str] = None
    operating_mode: str = "batch"  # batch, continuous
    additional_parameters: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            'solvent_type': self.solvent_type,
            'flow_rate': self.flow_rate,
            'column_diameter': self.column_diameter,
            'column_height': self.column_height,
            'column_material': self.column_material,
            'packing_type': self.packing_type,
            'operating_mode': self.operating_mode,
            'additional_parameters': self.additional_parameters
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SystemParameters':
        """Create from dictionary representation."""
        return cls(
            solvent_type=data['solvent_type'],
            flow_rate=data['flow_rate'],
            column_diameter=data['column_diameter'],
            column_height=data['column_height'],
            column_material=data.get('column_material'),
            packing_type=data.get('packing_type'),
            operating_mode=data.get('operating_mode', 'batch'),
            additional_parameters=data.get('additional_parameters', {})
        )


@dataclass
class Experiment:
    """Container for a complete experiment with all related data."""
    experiment_id: str
    gas_properties: GasProperties
    system_parameters: SystemParameters
    data_points: List[ExperimentalDataPoint] = field(default_factory=list)
    notes: str = ""
    created_at: datetime = field(default_factory=datetime.now)
    
    def add_data_point(self, point: ExperimentalDataPoint) -> None:
        """Add a data point to the experiment."""
        self.data_points.append(point)
    
    def add_data_points(self, points: List[ExperimentalDataPoint]) -> None:
        """Add multiple data points to the experiment."""
        self.data_points.extend(points)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            'experiment_id': self.experiment_id,
            'gas_properties': self.gas_properties.to_dict(),
            'system_parameters': self.system_parameters.to_dict(),
            'data_points': [dp.to_dict() for dp in self.data_points],
            'notes': self.notes,
            'created_at': self.created_at.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Experiment':
        """Create from dictionary representation."""
        created_at = data.get('created_at')
        if isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at)
        elif created_at is None:
            created_at = datetime.now()
        
        return cls(
            experiment_id=data['experiment_id'],
            gas_properties=GasProperties.from_dict(data['gas_properties']),
            system_parameters=SystemParameters.from_dict(data['system_parameters']),
            data_points=[ExperimentalDataPoint.from_dict(dp) for dp in data.get('data_points', [])],
            notes=data.get('notes', ''),
            created_at=created_at
        )


# =============================================================================
# 1.2 Data Import Functions
# =============================================================================

class DataImporter:
    """Handles data import from various sources."""
    
    @staticmethod
    def import_from_csv(file_path: str, experiment_id: str = "exp_001") -> Experiment:
        """
        Import experimental data from a CSV file.
        
        Expected CSV columns: temperature, pressure, absorption_capacity, time
        Optional columns: timestamp, and any metadata columns
        
        Args:
            file_path: Path to the CSV file
            experiment_id: Unique identifier for the experiment
            
        Returns:
            Experiment object with imported data
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"CSV file not found: {file_path}")
        
        data_points = []
        gas_properties = None
        system_parameters = None
        
        with open(path, 'r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            
            for row in reader:
                # Check if this is a metadata row (for gas properties or system params)
                if 'property_type' in row:
                    if row['property_type'] == 'gas':
                        gas_properties = GasProperties(
                            name=row.get('name', 'Unknown'),
                            molar_mass=float(row.get('molar_mass', 0)),
                            critical_temperature=float(row.get('critical_temperature', 0)),
                            critical_pressure=float(row.get('critical_pressure', 0))
                        )
                    elif row['property_type'] == 'system':
                        system_parameters = SystemParameters(
                            solvent_type=row.get('solvent_type', 'Unknown'),
                            flow_rate=float(row.get('flow_rate', 0)),
                            column_diameter=float(row.get('column_diameter', 0)),
                            column_height=float(row.get('column_height', 0))
                        )
                    continue
                
                # Regular data point
                try:
                    point = ExperimentalDataPoint(
                        temperature=float(row['temperature']),
                        pressure=float(row['pressure']),
                        absorption_capacity=float(row['absorption_capacity']),
                        time=float(row['time']),
                        metadata={k: v for k, v in row.items() 
                                 if k not in ['temperature', 'pressure', 
                                             'absorption_capacity', 'time']}
                    )
                    data_points.append(point)
                except (KeyError, ValueError) as e:
                    raise ValueError(f"Invalid data format in CSV: {e}")
        
        # Use defaults if not provided
        if gas_properties is None:
            gas_properties = GasProperties(
                name="Unknown",
                molar_mass=0,
                critical_temperature=0,
                critical_pressure=0
            )
        
        if system_parameters is None:
            system_parameters = SystemParameters(
                solvent_type="Unknown",
                flow_rate=0,
                column_diameter=0,
                column_height=0
            )
        
        experiment = Experiment(
            experiment_id=experiment_id,
            gas_properties=gas_properties,
            system_parameters=system_parameters,
            data_points=data_points
        )
        
        return experiment
    
    @staticmethod
    def import_from_excel(file_path: str, experiment_id: str = "exp_001",
                         sheet_name: Optional[str] = None) -> Experiment:
        """
        Import experimental data from an Excel file.
        
        Args:
            file_path: Path to the Excel file
            experiment_id: Unique identifier for the experiment
            sheet_name: Name of the sheet to import (default: first sheet)
            
        Returns:
            Experiment object with imported data
        """
        try:
            import pandas as pd
        except ImportError:
            raise ImportError("pandas is required for Excel import. Install with: pip install pandas openpyxl")
        
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"Excel file not found: {file_path}")
        
        # Read Excel file
        if sheet_name:
            df = pd.read_excel(file_path, sheet_name=sheet_name)
        else:
            xl_file = pd.ExcelFile(file_path)
            sheet_name = xl_file.sheet_names[0]
            df = pd.read_excel(file_path, sheet_name=sheet_name)
        
        # Convert to list of dicts and create data points
        data_points = []
        for _, row in df.iterrows():
            try:
                point = ExperimentalDataPoint(
                    temperature=float(row['temperature']),
                    pressure=float(row['pressure']),
                    absorption_capacity=float(row['absorption_capacity']),
                    time=float(row['time'])
                )
                data_points.append(point)
            except (KeyError, ValueError) as e:
                raise ValueError(f"Invalid data format in Excel: {e}")
        
        # Try to read gas properties and system parameters from other sheets
        gas_properties = GasProperties(name="Unknown", molar_mass=0, 
                                       critical_temperature=0, critical_pressure=0)
        system_parameters = SystemParameters(solvent_type="Unknown", flow_rate=0,
                                            column_diameter=0, column_height=0)
        
        for sheet in xl_file.sheet_names:
            if sheet.lower() == 'gas_properties':
                props_df = pd.read_excel(file_path, sheet_name=sheet)
                if not props_df.empty:
                    row = props_df.iloc[0]
                    gas_properties = GasProperties(
                        name=row.get('name', 'Unknown'),
                        molar_mass=row.get('molar_mass', 0),
                        critical_temperature=row.get('critical_temperature', 0),
                        critical_pressure=row.get('critical_pressure', 0)
                    )
            elif sheet.lower() == 'system_parameters':
                params_df = pd.read_excel(file_path, sheet_name=sheet)
                if not params_df.empty:
                    row = params_df.iloc[0]
                    system_parameters = SystemParameters(
                        solvent_type=row.get('solvent_type', 'Unknown'),
                        flow_rate=row.get('flow_rate', 0),
                        column_diameter=row.get('column_diameter', 0),
                        column_height=row.get('column_height', 0)
                    )
        
        experiment = Experiment(
            experiment_id=experiment_id,
            gas_properties=gas_properties,
            system_parameters=system_parameters,
            data_points=data_points
        )
        
        return experiment
    
    @staticmethod
    def import_from_json(file_path: str) -> Experiment:
        """
        Import experiment configuration from a JSON file.
        
        Args:
            file_path: Path to the JSON file
            
        Returns:
            Experiment object with imported data
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"JSON file not found: {file_path}")
        
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        return Experiment.from_dict(data)
    
    @staticmethod
    def import_from_api(api_url: str, api_key: Optional[str] = None,
                       experiment_id: str = "exp_001") -> Experiment:
        """
        Import real-time sensor data from an API.
        
        Args:
            api_url: URL of the sensor data API
            api_key: Optional API key for authentication
            experiment_id: Unique identifier for the experiment
            
        Returns:
            Experiment object with imported data
        """
        try:
            import requests
        except ImportError:
            raise ImportError("requests is required for API import. Install with: pip install requests")
        
        headers = {}
        if api_key:
            headers['Authorization'] = f'Bearer {api_key}'
        
        response = requests.get(api_url, headers=headers, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        
        # Parse the API response
        data_points = []
        for reading in data.get('readings', []):
            point = ExperimentalDataPoint(
                temperature=float(reading['temperature']),
                pressure=float(reading['pressure']),
                absorption_capacity=float(reading['absorption_capacity']),
                time=float(reading['time'])
            )
            data_points.append(point)
        
        # Extract gas properties and system parameters if available
        gas_data = data.get('gas_properties', {})
        gas_properties = GasProperties(
            name=gas_data.get('name', 'Unknown'),
            molar_mass=gas_data.get('molar_mass', 0),
            critical_temperature=gas_data.get('critical_temperature', 0),
            critical_pressure=gas_data.get('critical_pressure', 0)
        )
        
        system_data = data.get('system_parameters', {})
        system_parameters = SystemParameters(
            solvent_type=system_data.get('solvent_type', 'Unknown'),
            flow_rate=system_data.get('flow_rate', 0),
            column_diameter=system_data.get('column_diameter', 0),
            column_height=system_data.get('column_height', 0)
        )
        
        experiment = Experiment(
            experiment_id=experiment_id,
            gas_properties=gas_properties,
            system_parameters=system_parameters,
            data_points=data_points
        )
        
        return experiment
    
    @staticmethod
    def create_from_manual_entry(
        experiment_id: str,
        gas_properties: Dict[str, Any],
        system_parameters: Dict[str, Any],
        data_points: List[Dict[str, Any]]
    ) -> Experiment:
        """
        Create an experiment from manually entered data.
        
        Args:
            experiment_id: Unique identifier for the experiment
            gas_properties: Dictionary with gas properties
            system_parameters: Dictionary with system parameters
            data_points: List of dictionaries with data point values
            
        Returns:
            Experiment object with the entered data
        """
        gas_props = GasProperties.from_dict(gas_properties)
        sys_params = SystemParameters.from_dict(system_parameters)
        
        points = [ExperimentalDataPoint.from_dict(dp) for dp in data_points]
        
        return Experiment(
            experiment_id=experiment_id,
            gas_properties=gas_props,
            system_parameters=sys_params,
            data_points=points
        )


# =============================================================================
# 1.3 Data Validation
# =============================================================================

class ValidationError(Exception):
    """Exception raised for data validation errors."""
    pass


@dataclass
class ValidationResult:
    """Result of data validation."""
    is_valid: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    outliers: List[int] = field(default_factory=list)  # Indices of outlier data points
    flagged_points: List[int] = field(default_factory=list)  # Indices of flagged points
    
    def summary(self) -> str:
        """Return a summary of the validation result."""
        status = "VALID" if self.is_valid else "INVALID"
        summary = f"Validation Status: {status}\n"
        
        if self.errors:
            summary += f"Errors ({len(self.errors)}):\n"
            for error in self.errors:
                summary += f"  - {error}\n"
        
        if self.warnings:
            summary += f"Warnings ({len(self.warnings)}):\n"
            for warning in self.warnings:
                summary += f"  - {warning}\n"
        
        if self.outliers:
            summary += f"Outliers detected at indices: {self.outliers}\n"
        
        if self.flagged_points:
            summary += f"Flagged points at indices: {self.flagged_points}\n"
        
        return summary


class DataValidator:
    """Validates experimental data."""
    
    # Validation ranges
    TEMP_MIN = -50.0  # °C
    TEMP_MAX = 500.0  # °C
    PRESSURE_MIN = 0.1  # bar
    PRESSURE_MAX = 100.0  # bar
    
    @classmethod
    def validate_temperature_range(cls, temperature: Optional[float]) -> Tuple[bool, Optional[str]]:
        """
        Validate temperature is within acceptable range.
        
        Args:
            temperature: Temperature value in °C
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if temperature is None:
            return False, "Temperature is missing (None)"
        if temperature < cls.TEMP_MIN:
            return False, f"Temperature {temperature}°C is below minimum ({cls.TEMP_MIN}°C)"
        if temperature > cls.TEMP_MAX:
            return False, f"Temperature {temperature}°C is above maximum ({cls.TEMP_MAX}°C)"
        return True, None
    
    @classmethod
    def validate_pressure_range(cls, pressure: Optional[float]) -> Tuple[bool, Optional[str]]:
        """
        Validate pressure is within acceptable range.
        
        Args:
            pressure: Pressure value in bar
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if pressure is None:
            return False, "Pressure is missing (None)"
        if pressure < cls.PRESSURE_MIN:
            return False, f"Pressure {pressure} bar is below minimum ({cls.PRESSURE_MIN} bar)"
        if pressure > cls.PRESSURE_MAX:
            return False, f"Pressure {pressure} bar is above maximum ({cls.PRESSURE_MAX} bar)"
        return True, None
    
    @classmethod
    def detect_outliers_iqr(cls, values: List[float], multiplier: float = 1.5) -> List[int]:
        """
        Detect outliers using the IQR (Interquartile Range) method.
        
        Args:
            values: List of numerical values
            multiplier: IQR multiplier for outlier threshold (default: 1.5)
            
        Returns:
            List of indices where outliers are detected
        """
        if len(values) < 4:
            return []  # Not enough data for IQR method
        
        sorted_values = sorted(values)
        n = len(sorted_values)
        
        # Calculate Q1 (25th percentile) and Q3 (75th percentile)
        q1_idx = n // 4
        q3_idx = (3 * n) // 4
        
        q1 = sorted_values[q1_idx]
        q3 = sorted_values[q3_idx]
        
        iqr = q3 - q1
        lower_bound = q1 - multiplier * iqr
        upper_bound = q3 + multiplier * iqr
        
        outlier_indices = []
        for i, value in enumerate(values):
            if value < lower_bound or value > upper_bound:
                outlier_indices.append(i)
        
        return outlier_indices
    
    @classmethod
    def check_missing_data(cls, experiment: Experiment) -> List[str]:
        """
        Check for missing or inconsistent data points.
        
        Args:
            experiment: Experiment object to validate
            
        Returns:
            List of error messages for missing/inconsistent data
        """
        errors = []
        
        # Check gas properties
        if experiment.gas_properties.molar_mass <= 0:
            errors.append("Invalid or missing molar mass")
        if experiment.gas_properties.critical_temperature <= 0:
            errors.append("Invalid or missing critical temperature")
        if experiment.gas_properties.critical_pressure <= 0:
            errors.append("Invalid or missing critical pressure")
        
        # Check system parameters
        if not experiment.system_parameters.solvent_type:
            errors.append("Missing solvent type")
        if experiment.system_parameters.flow_rate < 0:
            errors.append("Invalid flow rate (negative value)")
        if experiment.system_parameters.column_diameter <= 0:
            errors.append("Invalid column diameter")
        if experiment.system_parameters.column_height <= 0:
            errors.append("Invalid column height")
        
        # Check data points
        for i, point in enumerate(experiment.data_points):
            if point.temperature is None:
                errors.append(f"Data point {i}: Missing temperature")
            if point.pressure is None:
                errors.append(f"Data point {i}: Missing pressure")
            if point.absorption_capacity is None:
                errors.append(f"Data point {i}: Missing absorption capacity")
            if point.time is None:
                errors.append(f"Data point {i}: Missing time")
        
        return errors
    
    @classmethod
    def validate_experiment(cls, experiment: Experiment, 
                           check_outliers: bool = True) -> ValidationResult:
        """
        Perform comprehensive validation on an experiment.
        
        Args:
            experiment: Experiment object to validate
            check_outliers: Whether to perform outlier detection
            
        Returns:
            ValidationResult object with validation details
        """
        result = ValidationResult(is_valid=True)
        
        # Check for missing data
        missing_errors = cls.check_missing_data(experiment)
        if missing_errors:
            result.errors.extend(missing_errors)
            result.is_valid = False
        
        # Validate each data point
        temperatures = []
        pressures = []
        absorption_capacities = []
        times = []
        
        for i, point in enumerate(experiment.data_points):
            # Temperature range check
            temp_valid, temp_error = cls.validate_temperature_range(point.temperature)
            if not temp_valid:
                result.errors.append(f"Data point {i}: {temp_error}")
                result.flagged_points.append(i)
                result.is_valid = False
            
            # Pressure range check
            pressure_valid, pressure_error = cls.validate_pressure_range(point.pressure)
            if not pressure_valid:
                result.errors.append(f"Data point {i}: {pressure_error}")
                result.flagged_points.append(i)
                result.is_valid = False
            
            # Collect values for outlier detection
            temperatures.append(point.temperature)
            pressures.append(point.pressure)
            absorption_capacities.append(point.absorption_capacity)
            times.append(point.time)
        
        # Outlier detection
        if check_outliers and len(experiment.data_points) >= 4:
            # Detect outliers in temperature
            temp_outliers = cls.detect_outliers_iqr(temperatures)
            if temp_outliers:
                result.outliers.extend(temp_outliers)
                result.warnings.append(f"Temperature outliers detected at indices: {temp_outliers}")
            
            # Detect outliers in pressure
            pressure_outliers = cls.detect_outliers_iqr(pressures)
            if pressure_outliers:
                # Add only unique indices
                for idx in pressure_outliers:
                    if idx not in result.outliers:
                        result.outliers.append(idx)
                result.warnings.append(f"Pressure outliers detected at indices: {pressure_outliers}")
            
            # Detect outliers in absorption capacity
            abs_outliers = cls.detect_outliers_iqr(absorption_capacities)
            if abs_outliers:
                for idx in abs_outliers:
                    if idx not in result.outliers:
                        result.outliers.append(idx)
                result.warnings.append(f"Absorption capacity outliers detected at indices: {abs_outliers}")
            
            # Sort outlier indices
            result.outliers = sorted(set(result.outliers))
        
        # Add warnings for outliers even if data is valid
        if result.outliers and result.is_valid:
            result.warnings.append("Outliers detected but data is within acceptable ranges")
        
        return result


# =============================================================================
# 2.1 Ideal Gas Law Calculations
# =============================================================================

class IdealGasCalculator:
    """
    Implements Ideal Gas Law and related calculations for gas absorption.
    
    Includes:
    - PV = nRT for absorption capacity calculations
    - Theoretical absorption at each T&P condition
    - Henry's Law: C = kH × P
    """
    
    # Universal gas constant in different units
    R_J_mol_K = 8.314462618  # J/(mol·K)
    R_L_bar_mol_K = 0.08314462618  # L·bar/(mol·K)
    R_cm3_bar_mol_K = 83.14462618  # cm³·bar/(mol·K)
    
    def __init__(self, gas_constant: float = None):
        """
        Initialize the calculator with a specific gas constant.
        
        Args:
            gas_constant: Gas constant value (default: R_L_bar_mol_K for L·bar/(mol·K))
        """
        self.R = gas_constant if gas_constant else self.R_L_bar_mol_K
    
    @staticmethod
    def celsius_to_kelvin(temperature_c: float) -> float:
        """Convert temperature from Celsius to Kelvin."""
        return temperature_c + 273.15
    
    @staticmethod
    def kelvin_to_celsius(temperature_k: float) -> float:
        """Convert temperature from Kelvin to Celsius."""
        return temperature_k - 273.15
    
    def calculate_moles(self, pressure: float, volume: float, temperature_k: float) -> float:
        """
        Calculate moles of gas using Ideal Gas Law: n = PV/RT
        
        Args:
            pressure: Pressure in bar
            volume: Volume in liters
            temperature_k: Temperature in Kelvin
            
        Returns:
            Number of moles
        """
        if temperature_k <= 0:
            raise ValueError("Temperature must be positive in Kelvin")
        if pressure < 0:
            raise ValueError("Pressure cannot be negative")
        if volume < 0:
            raise ValueError("Volume cannot be negative")
            
        return (pressure * volume) / (self.R * temperature_k)
    
    def calculate_pressure(self, n: float, volume: float, temperature_k: float) -> float:
        """
        Calculate pressure using Ideal Gas Law: P = nRT/V
        
        Args:
            n: Number of moles
            volume: Volume in liters
            temperature_k: Temperature in Kelvin
            
        Returns:
            Pressure in bar
        """
        if temperature_k <= 0:
            raise ValueError("Temperature must be positive in Kelvin")
        if volume <= 0:
            raise ValueError("Volume must be positive")
        if n < 0:
            raise ValueError("Moles cannot be negative")
            
        return (n * self.R * temperature_k) / volume
    
    def calculate_volume(self, n: float, pressure: float, temperature_k: float) -> float:
        """
        Calculate volume using Ideal Gas Law: V = nRT/P
        
        Args:
            n: Number of moles
            pressure: Pressure in bar
            temperature_k: Temperature in Kelvin
            
        Returns:
            Volume in liters
        """
        if temperature_k <= 0:
            raise ValueError("Temperature must be positive in Kelvin")
        if pressure <= 0:
            raise ValueError("Pressure must be positive")
        if n < 0:
            raise ValueError("Moles cannot be negative")
            
        return (n * self.R * temperature_k) / pressure
    
    def calculate_theoretical_absorption(self, pressure: float, temperature_c: float,
                                         solvent_volume: float, max_capacity: float) -> float:
        """
        Calculate theoretical absorption capacity at given T&P conditions.
        
        This calculates the maximum amount of gas that can be absorbed based on
        ideal gas behavior and available solvent volume.
        
        Args:
            pressure: Pressure in bar
            temperature_c: Temperature in Celsius
            solvent_volume: Volume of solvent in liters
            max_capacity: Maximum absorption capacity (mol/L of solvent)
            
        Returns:
            Theoretical absorption capacity in mol
        """
        temperature_k = self.celsius_to_kelvin(temperature_c)
        
        # Calculate moles of gas available at given P&T per liter
        moles_per_liter = pressure / (self.R * temperature_k)
        
        # Theoretical absorption is limited by both gas availability and solvent capacity
        theoretical_max = moles_per_liter * solvent_volume
        actual_absorption = min(theoretical_max, max_capacity * solvent_volume)
        
        return actual_absorption
    
    def henrys_law_concentration(self, henry_constant: float, pressure: float,
                                temperature_c: float = None) -> float:
        """
        Calculate gas concentration in liquid using Henry's Law: C = kH × P
        
        Args:
            henry_constant: Henry's law constant (mol/(L·bar) or similar units)
            pressure: Partial pressure of gas in bar
            temperature_c: Optional temperature for temperature-dependent kH
            
        Returns:
            Concentration of dissolved gas (mol/L or matching kH units)
        """
        if henry_constant < 0:
            raise ValueError("Henry's constant cannot be negative")
        if pressure < 0:
            raise ValueError("Pressure cannot be negative")
            
        return henry_constant * pressure
    
    def henrys_law_with_temperature(self, henry_constant_ref: float, 
                                    pressure: float, temperature_k: float,
                                    enthalpy_solution: float,
                                    reference_temp: float = 298.15) -> float:
        """
        Calculate Henry's law constant at different temperatures using van't Hoff equation.
        
        kH(T) = kH(Tref) × exp(-ΔH_sol/R × (1/T - 1/Tref))
        
        Args:
            henry_constant_ref: Henry's constant at reference temperature (mol/(L·bar))
            pressure: Partial pressure in bar
            temperature_k: Temperature in Kelvin
            enthalpy_solution: Enthalpy of solution in J/mol
            reference_temp: Reference temperature in Kelvin (default: 298.15 K = 25°C)
            
        Returns:
            Concentration of dissolved gas (mol/L)
        """
        if temperature_k <= 0:
            raise ValueError("Temperature must be positive in Kelvin")
        if reference_temp <= 0:
            raise ValueError("Reference temperature must be positive in Kelvin")
            
        # Calculate temperature-corrected Henry's constant
        exponent = (-enthalpy_solution / self.R_J_mol_K) * (1/temperature_k - 1/reference_temp)
        henry_constant_t = henry_constant_ref * (2.718281828 ** exponent)  # e^x
        
        return henry_constant_t * pressure
    
    def absorption_from_experiment(self, data_point: 'ExperimentalDataPoint',
                                   solvent_mass: float) -> Dict[str, float]:
        """
        Calculate absorption metrics from an experimental data point.
        
        Args:
            data_point: ExperimentalDataPoint object
            solvent_mass: Mass of solvent in kg
            
        Returns:
            Dictionary with calculated absorption metrics
        """
        temperature_k = self.celsius_to_kelvin(data_point.temperature)
        
        # Moles absorbed based on experimental capacity
        moles_absorbed = data_point.absorption_capacity * solvent_mass
        
        # Theoretical maximum based on ideal gas at experimental conditions
        # Assuming 1 L headspace volume for calculation
        theoretical_moles = self.calculate_moles(data_point.pressure, 1.0, temperature_k)
        
        # Absorption efficiency
        if theoretical_moles > 0:
            efficiency = (moles_absorbed / theoretical_moles) * 100
        else:
            efficiency = 0
        
        return {
            'moles_absorbed': moles_absorbed,
            'theoretical_moles': theoretical_moles,
            'efficiency_percent': efficiency,
            'temperature_k': temperature_k
        }


# =============================================================================
# 2.2 Real Gas Corrections
# =============================================================================

class RealGasCalculator:
    """
    Implements real gas equations of state and corrections.
    
    Includes:
    - Van der Waals equation
    - Peng-Robinson equation of state
    - Compressibility factor (Z-factor) calculations
    - Fugacity coefficients
    """
    
    # Universal gas constant
    R = 0.08314462618  # L·bar/(mol·K)
    
    def __init__(self, gas_properties: 'GasProperties' = None):
        """
        Initialize with gas properties for real gas calculations.
        
        Args:
            gas_properties: GasProperties object with critical properties
        """
        self.gas_properties = gas_properties
        self.a = None  # Van der Waals parameter a
        self.b = None  # Van der Waals parameter b
    
    def calculate_vdw_parameters(self) -> Tuple[float, float]:
        """
        Calculate Van der Waals parameters from critical properties.
        
        a = 27R²Tc²/(64Pc)
        b = RTc/(8Pc)
        
        Returns:
            Tuple of (a, b) parameters
        """
        if self.gas_properties is None:
            raise ValueError("Gas properties must be provided")
        
        Tc = self.gas_properties.critical_temperature  # K
        Pc = self.gas_properties.critical_pressure  # bar
        
        self.a = (27 * (self.R ** 2) * (Tc ** 2)) / (64 * Pc)
        self.b = (self.R * Tc) / (8 * Pc)
        
        return self.a, self.b
    
    def van_der_waals_pressure(self, n: float, volume: float, temperature_k: float) -> float:
        """
        Calculate pressure using Van der Waals equation:
        P = nRT/(V-nb) - an²/V²
        
        Args:
            n: Number of moles
            volume: Volume in liters
            temperature_k: Temperature in Kelvin
            
        Returns:
            Pressure in bar
        """
        if self.a is None or self.b is None:
            self.calculate_vdw_parameters()
        
        if volume <= n * self.b:
            raise ValueError("Volume too small for given moles (V must be > nb)")
        
        term1 = (n * self.R * temperature_k) / (volume - n * self.b)
        term2 = (self.a * (n ** 2)) / (volume ** 2)
        
        return term1 - term2
    
    def van_der_waals_volume(self, pressure: float, n: float, temperature_k: float,
                            max_iterations: int = 100, tolerance: float = 1e-6) -> float:
        """
        Solve Van der Waals equation for volume using iterative method.
        
        Args:
            pressure: Pressure in bar
            n: Number of moles
            temperature_k: Temperature in Kelvin
            max_iterations: Maximum iterations for convergence
            tolerance: Convergence tolerance
            
        Returns:
            Volume in liters
        """
        if self.a is None or self.b is None:
            self.calculate_vdw_parameters()
        
        # Initial guess from ideal gas law
        V = (n * self.R * temperature_k) / pressure
        
        for _ in range(max_iterations):
            # Van der Waals equation rearranged: f(V) = 0
            f_V = pressure - (n * self.R * temperature_k) / (V - n * self.b) + (self.a * n**2) / (V**2)
            
            # Derivative df/dV
            df_dV = (n * self.R * temperature_k) / ((V - n * self.b)**2) - (2 * self.a * n**2) / (V**3)
            
            if abs(df_dV) < 1e-12:
                break
                
            V_new = V - f_V / df_dV
            
            if abs(V_new - V) < tolerance:
                return V_new
            
            V = V_new
        
        return V
    
    def compressibility_factor(self, pressure: float, temperature_k: float) -> float:
        """
        Calculate compressibility factor Z = PV/(nRT).
        
        Uses Van der Waals equation to estimate Z.
        
        Args:
            pressure: Pressure in bar
            temperature_k: Temperature in Kelvin
            
        Returns:
            Compressibility factor Z
        """
        if self.a is None or self.b is None:
            self.calculate_vdw_parameters()
        
        # Reduced properties
        Tr = temperature_k / self.gas_properties.critical_temperature
        Pr = pressure / self.gas_properties.critical_pressure
        
        # Solve cubic equation for Z from Van der Waals
        # Z³ - (1 + B)Z² + AZ - AB = 0
        # where A = aP/(R²T²) and B = bP/(RT)
        
        A = (self.a * pressure) / ((self.R ** 2) * (temperature_k ** 2))
        B = (self.b * pressure) / (self.R * temperature_k)
        
        # Use iterative approach to find Z
        Z = 1.0  # Initial guess (ideal gas)
        
        for _ in range(50):
            # Z = 1 + B - A/Z (simplified iteration)
            if Z != 0:
                Z_new = 1 + B - A / Z
                if abs(Z_new - Z) < 1e-8:
                    return Z_new
                Z = Z_new
        
        return Z
    
    def peng_robinson_parameters(self) -> Tuple[float, float, float]:
        """
        Calculate Peng-Robinson equation parameters.
        
        PR EOS: P = RT/(V-b) - aα/(V² + 2bV - b²)
        
        Returns:
            Tuple of (a, b, alpha) parameters
        """
        if self.gas_properties is None:
            raise ValueError("Gas properties must be provided")
        
        Tc = self.gas_properties.critical_temperature
        Pc = self.gas_properties.critical_pressure
        
        # Peng-Robinson constants
        Omega_a = 0.45724
        Omega_b = 0.07780
        
        # Parameter b
        b = Omega_b * self.R * Tc / Pc
        
        # Parameter a at critical point
        a_c = Omega_a * (self.R ** 2) * (Tc ** 2) / Pc
        
        return a_c, b, None  # alpha calculated separately
    
    def peng_robinson_alpha(self, temperature_k: float, acentric_factor: float = 0) -> float:
        """
        Calculate alpha function for Peng-Robinson equation.
        
        α = [1 + κ(1 - √Tr)]²
        κ = 0.37464 + 1.54226ω - 0.26992ω²
        
        Args:
            temperature_k: Temperature in Kelvin
            acentric_factor: Acentric factor ω (default: 0 for simple gases)
            
        Returns:
            Alpha value
        """
        if self.gas_properties is None:
            raise ValueError("Gas properties must be provided")
        
        Tr = temperature_k / self.gas_properties.critical_temperature
        
        if Tr <= 0:
            raise ValueError("Temperature must be positive in Kelvin")
        
        # Calculate kappa
        kappa = 0.37464 + 1.54226 * acentric_factor - 0.26992 * (acentric_factor ** 2)
        
        # Calculate alpha
        sqrt_Tr = Tr ** 0.5
        alpha = (1 + kappa * (1 - sqrt_Tr)) ** 2
        
        return alpha
    
    def peng_robinson_pressure(self, n: float, volume: float, temperature_k: float,
                               acentric_factor: float = 0) -> float:
        """
        Calculate pressure using Peng-Robinson equation of state.
        
        P = RT/(V-b) - aα/(V² + 2bV - b²)
        
        Args:
            n: Number of moles
            volume: Volume in liters
            temperature_k: Temperature in Kelvin
            acentric_factor: Acentric factor ω
            
        Returns:
            Pressure in bar
        """
        a_c, b, _ = self.peng_robinson_parameters()
        alpha = self.peng_robinson_alpha(temperature_k, acentric_factor)
        a = a_c * alpha
        
        if volume <= n * b:
            raise ValueError("Volume too small for given moles")
        
        molar_volume = volume / n
        
        term1 = (self.R * temperature_k) / (molar_volume - b)
        denominator = (molar_volume ** 2) + 2 * b * molar_volume - (b ** 2)
        term2 = (a * alpha) / denominator
        
        return term1 - term2
    
    def fugacity_coefficient(self, pressure: float, temperature_k: float,
                            acentric_factor: float = 0) -> float:
        """
        Calculate fugacity coefficient using Peng-Robinson EOS.
        
        ln(φ) = Z - 1 - ln(Z - B) - (A/(2√2B)) × ln((Z + (1+√2)B)/(Z + (1-√2)B))
        
        Args:
            pressure: Pressure in bar
            temperature_k: Temperature in Kelvin
            acentric_factor: Acentric factor ω
            
        Returns:
            Fugacity coefficient φ
        """
        a_c, b, _ = self.peng_robinson_parameters()
        alpha = self.peng_robinson_alpha(temperature_k, acentric_factor)
        a = a_c * alpha
        
        # Calculate A and B
        A = (a * alpha * pressure) / ((self.R ** 2) * (temperature_k ** 2))
        B = (b * pressure) / (self.R * temperature_k)
        
        # Get compressibility factor
        Z = self.compressibility_factor_peng_robinson(pressure, temperature_k, acentric_factor)
        
        # Calculate fugacity coefficient
        sqrt_2 = 2 ** 0.5
        
        if Z - B <= 0:
            # Handle edge case
            return 1.0
        
        import math
        ln_phi = (Z - 1) - math.log(max(Z - B, 1e-10))
        
        if B > 0:
            term = A / (2 * sqrt_2 * B)
            arg1 = Z + (1 + sqrt_2) * B
            arg2 = max(Z + (1 - sqrt_2) * B, 1e-10)
            
            if arg1 > 0 and arg2 > 0:
                ln_phi -= term * math.log(arg1 / arg2)
        
        return math.exp(ln_phi)
    
    def compressibility_factor_peng_robinson(self, pressure: float, temperature_k: float,
                                             acentric_factor: float = 0,
                                             max_iterations: int = 100) -> float:
        """
        Calculate compressibility factor using Peng-Robinson EOS.
        
        Solves the cubic equation: Z³ + (C-1)Z² + (A-3B²-2BC-B-C)Z + (B²C + B² - AB) = 0
        
        Args:
            pressure: Pressure in bar
            temperature_k: Temperature in Kelvin
            acentric_factor: Acentric factor ω
            max_iterations: Maximum iterations
            
        Returns:
            Compressibility factor Z
        """
        a_c, b, _ = self.peng_robinson_parameters()
        alpha = self.peng_robinson_alpha(temperature_k, acentric_factor)
        a = a_c * alpha
        
        A = (a * alpha * pressure) / ((self.R ** 2) * (temperature_k ** 2))
        B = (b * pressure) / (self.R * temperature_k)
        
        # Simplified iterative approach
        Z = 1.0  # Initial guess
        
        for _ in range(max_iterations):
            # Cubic equation iteration
            denom = (Z ** 2) + 2 * B * Z - (B ** 2)
            if abs(denom) < 1e-10:
                break
            Z_new = 1 + B - A * (Z - B) / denom
            
            if abs(Z_new - Z) < 1e-8:
                return Z_new
            Z = Z_new
        
        return Z
    
    def calculate_real_gas_absorption(self, pressure: float, temperature_c: float,
                                     solvent_volume: float, max_capacity: float,
                                     acentric_factor: float = 0) -> Dict[str, float]:
        """
        Calculate absorption capacity with real gas corrections.
        
        Args:
            pressure: Pressure in bar
            temperature_c: Temperature in Celsius
            solvent_volume: Volume of solvent in liters
            max_capacity: Maximum absorption capacity (mol/L)
            acentric_factor: Acentric factor for the gas
            
        Returns:
            Dictionary with real gas corrected absorption metrics
        """
        temperature_k = IdealGasCalculator.celsius_to_kelvin(temperature_c)
        
        # Calculate compressibility factor
        Z = self.compressibility_factor_peng_robinson(pressure, temperature_k, acentric_factor)
        
        # Calculate fugacity coefficient
        phi = self.fugacity_coefficient(pressure, temperature_k, acentric_factor)
        
        # Effective pressure (fugacity)
        fugacity = phi * pressure
        
        # Corrected moles available (accounting for Z factor)
        moles_corrected = (pressure * solvent_volume) / (Z * self.R * temperature_k)
        
        # Fugacity-based absorption estimate
        fugacity_based_absorption = moles_corrected * phi
        
        return {
            'compressibility_factor': Z,
            'fugacity_coefficient': phi,
            'fugacity': fugacity,
            'corrected_moles': moles_corrected,
            'fugacity_based_absorption': fugacity_based_absorption,
            'ideal_moles': (pressure * solvent_volume) / (self.R * temperature_k),
            'deviation_from_ideal': (1 - Z) * 100  # Percentage deviation
        }


# =============================================================================
# 2.3 Temperature & Pressure Dependencies
# =============================================================================

class ThermodynamicDependencies:
    """
    Implements temperature and pressure dependency calculations.
    
    Includes:
    - Arrhenius equation for temperature effects
    - Antoine equation for vapor pressure
    - Heat of absorption calculations
    """
    
    # Universal gas constant
    R = 8.314462618  # J/(mol·K)
    
    def arrhenius_rate(self, pre_exponential: float, activation_energy: float,
                       temperature_k: float) -> float:
        """
        Calculate reaction rate using Arrhenius equation.
        
        k = A × exp(-Ea/RT)
        
        Args:
            pre_exponential: Pre-exponential factor A (same units as k)
            activation_energy: Activation energy Ea in J/mol
            temperature_k: Temperature in Kelvin
            
        Returns:
            Reaction rate constant k
        """
        if temperature_k <= 0:
            raise ValueError("Temperature must be positive in Kelvin")
        if activation_energy < 0:
            raise ValueError("Activation energy cannot be negative")
            
        import math
        exponent = -activation_energy / (self.R * temperature_k)
        return pre_exponential * math.exp(exponent)
    
    def arrhenius_ratio(self, activation_energy: float, T1: float, T2: float) -> float:
        """
        Calculate ratio of reaction rates at two temperatures.
        
        k2/k1 = exp[(Ea/R) × (1/T1 - 1/T2)]
        
        Args:
            activation_energy: Activation energy in J/mol
            T1: First temperature in Kelvin
            T2: Second temperature in Kelvin
            
        Returns:
            Ratio k2/k1
        """
        if T1 <= 0 or T2 <= 0:
            raise ValueError("Temperatures must be positive in Kelvin")
            
        import math
        exponent = (activation_energy / self.R) * (1/T1 - 1/T2)
        return math.exp(exponent)
    
    def absorption_rate_temperature(self, base_rate: float, activation_energy: float,
                                   base_temp: float, target_temp: float) -> float:
        """
        Calculate absorption rate at different temperature using Arrhenius.
        
        Args:
            base_rate: Known absorption rate at base temperature
            activation_energy: Activation energy for absorption process (J/mol)
            base_temp: Base temperature in Kelvin
            target_temp: Target temperature in Kelvin
            
        Returns:
            Absorption rate at target temperature
        """
        ratio = self.arrhenius_ratio(activation_energy, base_temp, target_temp)
        return base_rate * ratio
    
    def antoine_vapor_pressure(self, A: float, B: float, C: float,
                               temperature_c: float) -> float:
        """
        Calculate vapor pressure using Antoine equation.
        
        log10(P) = A - B/(T + C)
        
        Where P is in mmHg (torr) and T is in °C by default.
        Constants A, B, C are substance-specific.
        
        Args:
            A: Antoine constant A
            B: Antoine constant B
            C: Antoine constant C
            temperature_c: Temperature in Celsius
            
        Returns:
            Vapor pressure in mmHg (torr)
        """
        if temperature_c + C <= 0:
            raise ValueError("Invalid temperature for Antoine equation (T + C must be positive)")
        
        log10_P = A - B / (temperature_c + C)
        return 10 ** log10_P
    
    def antoine_vapor_pressure_bar(self, A: float, B: float, C: float,
                                   temperature_c: float) -> float:
        """
        Calculate vapor pressure in bar using Antoine equation.
        
        Args:
            A: Antoine constant A
            B: Antoine constant B
            C: Antoine constant C
            temperature_c: Temperature in Celsius
            
        Returns:
            Vapor pressure in bar
        """
        pressure_mmhg = self.antoine_vapor_pressure(A, B, C, temperature_c)
        # Convert mmHg to bar (1 mmHg = 0.00133322 bar)
        return pressure_mmhg * 0.00133322
    
    def heat_of_absorption_clausius_clapeyron(self, P1: float, T1: float,
                                               P2: float, T2: float) -> float:
        """
        Calculate heat of absorption using Clausius-Clapeyron relation.
        
        ΔH = -R × ln(P2/P1) / (1/T2 - 1/T1)
        
        Args:
            P1: Pressure at temperature T1 (any consistent unit)
            T1: Temperature 1 in Kelvin
            P2: Pressure at temperature T2 (same unit as P1)
            T2: Temperature 2 in Kelvin
            
        Returns:
            Heat of absorption in J/mol (negative for exothermic)
        """
        if T1 <= 0 or T2 <= 0:
            raise ValueError("Temperatures must be positive in Kelvin")
        if P1 <= 0 or P2 <= 0:
            raise ValueError("Pressures must be positive")
        
        import math
        ln_ratio = math.log(P2 / P1)
        temp_diff = (1/T2) - (1/T1)
        
        if abs(temp_diff) < 1e-10:
            raise ValueError("Temperatures too close for accurate calculation")
        
        return -self.R * ln_ratio / temp_diff
    
    def heat_of_absorption_van_hoff(self, equilibrium_constants: List[float],
                                   temperatures: List[float]) -> float:
        """
        Calculate heat of absorption from multiple equilibrium measurements.
        
        Using van't Hoff equation: ln(K) = -ΔH/(RT) + ΔS/R
        Slope of ln(K) vs 1/T gives -ΔH/R
        
        Args:
            equilibrium_constants: List of equilibrium constants K
            temperatures: List of corresponding temperatures in Kelvin
            
        Returns:
            Heat of absorption in J/mol
        """
        if len(equilibrium_constants) != len(temperatures):
            raise ValueError("Must have equal number of K and T values")
        if len(equilibrium_constants) < 2:
            raise ValueError("Need at least 2 data points")
        
        import math
        
        # Calculate ln(K) and 1/T
        ln_K = [math.log(k) for k in equilibrium_constants]
        inv_T = [1/t for t in temperatures]
        
        # Linear regression to find slope
        n = len(ln_K)
        sum_x = sum(inv_T)
        sum_y = sum(ln_K)
        sum_xy = sum(x*y for x, y in zip(inv_T, ln_K))
        sum_xx = sum(x*x for x in inv_T)
        
        # Slope = (n*Σxy - Σx*Σy) / (n*Σx² - (Σx)²)
        denominator = n * sum_xx - sum_x * sum_x
        if abs(denominator) < 1e-10:
            raise ValueError("Cannot calculate slope (data may be collinear)")
        
        slope = (n * sum_xy - sum_x * sum_y) / denominator
        
        # ΔH = -slope × R
        return -slope * self.R
    
    def temperature_correction_factor(self, reference_temp: float, operating_temp: float,
                                     activation_energy: float) -> float:
        """
        Calculate temperature correction factor for absorption capacity.
        
        Args:
            reference_temp: Reference temperature in Kelvin
            operating_temp: Operating temperature in Kelvin
            activation_energy: Apparent activation energy in J/mol
            
        Returns:
            Correction factor (multiply reference capacity by this)
        """
        return self.arrhenius_ratio(activation_energy, reference_temp, operating_temp)
    
    def pressure_correction_factor(self, reference_pressure: float,
                                  operating_pressure: float,
                                  compression_factor: float = 1.0) -> float:
        """
        Calculate pressure correction factor for absorption capacity.
        
        For physical absorption, capacity often scales linearly with pressure
        (Henry's law region). For chemical absorption, relationship is more complex.
        
        Args:
            reference_pressure: Reference pressure in bar
            operating_pressure: Operating pressure in bar
            compression_factor: Exponent for non-linear scaling (default: 1.0 for linear)
            
        Returns:
            Correction factor
        """
        if reference_pressure <= 0:
            raise ValueError("Reference pressure must be positive")
        
        return (operating_pressure / reference_pressure) ** compression_factor
    
    def combined_tp_correction(self, reference_capacity: float,
                               ref_temp: float, ref_pressure: float,
                               op_temp: float, op_pressure: float,
                               activation_energy: float = 50000,
                               pressure_exponent: float = 1.0) -> Dict[str, float]:
        """
        Calculate combined temperature and pressure correction for absorption capacity.
        
        Args:
            reference_capacity: Known capacity at reference conditions (mol/kg or similar)
            ref_temp: Reference temperature in Kelvin
            ref_pressure: Reference pressure in bar
            op_temp: Operating temperature in Kelvin
            op_pressure: Operating pressure in bar
            activation_energy: Apparent activation energy in J/mol (default: 50 kJ/mol)
            pressure_exponent: Pressure scaling exponent (default: 1.0 for linear)
            
        Returns:
            Dictionary with corrected capacity and individual factors
        """
        temp_factor = self.temperature_correction_factor(ref_temp, op_temp, activation_energy)
        pressure_factor = self.pressure_correction_factor(ref_pressure, op_pressure, pressure_exponent)
        
        corrected_capacity = reference_capacity * temp_factor * pressure_factor
        
        return {
            'reference_capacity': reference_capacity,
            'corrected_capacity': corrected_capacity,
            'temperature_factor': temp_factor,
            'pressure_factor': pressure_factor,
            'combined_factor': temp_factor * pressure_factor,
            'operating_conditions': {
                'temperature_k': op_temp,
                'pressure_bar': op_pressure
            },
            'reference_conditions': {
                'temperature_k': ref_temp,
                'pressure_bar': ref_pressure
            }
        }
    
    def calculate_absorption_enthalpy_from_data(self, data_points: List['ExperimentalDataPoint'],
                                                constant_pressure: float) -> float:
        """
        Estimate absorption enthalpy from experimental data at constant pressure.
        
        Uses the temperature dependence of absorption capacity to estimate ΔH.
        
        Args:
            data_points: List of experimental data points at constant pressure
            constant_pressure: The pressure at which measurements were taken
            
        Returns:
            Estimated heat of absorption in J/mol
        """
        if len(data_points) < 2:
            raise ValueError("Need at least 2 data points")
        
        import math
        
        # Filter data points at approximately the same pressure
        tolerance = constant_pressure * 0.05  # 5% tolerance
        filtered_points = [dp for dp in data_points 
                         if abs(dp.pressure - constant_pressure) < tolerance]
        
        if len(filtered_points) < 2:
            raise ValueError("Not enough data points at specified pressure")
        
        # Use absorption capacity as proxy for equilibrium constant
        # ln(C) vs 1/T should give slope = ΔH/R
        temperatures = [IdealGasCalculator.celsius_to_kelvin(dp.temperature) 
                       for dp in filtered_points]
        capacities = [dp.absorption_capacity for dp in filtered_points]
        
        # Check for zero or negative capacities
        valid_indices = [i for i, c in enumerate(capacities) if c > 0]
        if len(valid_indices) < 2:
            raise ValueError("Need at least 2 positive capacity values")
        
        temperatures = [temperatures[i] for i in valid_indices]
        capacities = [capacities[i] for i in valid_indices]
        
        return self.heat_of_absorption_van_hoff(capacities, temperatures)


# =============================================================================
# Convenience Functions
# =============================================================================

def calculate_ideal_absorption(pressure: float, temperature_c: float,
                              solvent_volume: float = 1.0) -> Dict[str, float]:
    """
    Quick calculation of ideal gas absorption metrics.
    
    Args:
        pressure: Pressure in bar
        temperature_c: Temperature in Celsius
        solvent_volume: Solvent volume in liters (default: 1.0 L)
        
    Returns:
        Dictionary with absorption metrics
    """
    calc = IdealGasCalculator()
    temperature_k = calc.celsius_to_kelvin(temperature_c)
    
    moles_available = calc.calculate_moles(pressure, solvent_volume, temperature_k)
    
    return {
        'pressure_bar': pressure,
        'temperature_c': temperature_c,
        'temperature_k': temperature_k,
        'moles_gas_available': moles_available,
        'solvent_volume_l': solvent_volume
    }


def calculate_real_gas_correction(pressure: float, temperature_c: float,
                                 gas_properties: GasProperties,
                                 acentric_factor: float = 0) -> Dict[str, float]:
    """
    Quick calculation of real gas correction factors.
    
    Args:
        pressure: Pressure in bar
        temperature_c: Temperature in Celsius
        gas_properties: GasProperties object with critical properties
        acentric_factor: Acentric factor for the gas
        
    Returns:
        Dictionary with correction factors
    """
    calc = RealGasCalculator(gas_properties)
    temperature_k = IdealGasCalculator.celsius_to_kelvin(temperature_c)
    
    return calc.calculate_real_gas_absorption(
        pressure=pressure,
        temperature_c=temperature_c,
        solvent_volume=1.0,
        max_capacity=1.0,
        acentric_factor=acentric_factor
    )


# =============================================================================
# Convenience Functions
# =============================================================================

def load_experiment_from_csv(file_path: str, experiment_id: str = "exp_001",
                            validate: bool = True) -> Tuple[Experiment, Optional[ValidationResult]]:
    """
    Load and optionally validate an experiment from a CSV file.
    
    Args:
        file_path: Path to the CSV file
        experiment_id: Unique identifier for the experiment
        validate: Whether to perform validation
        
    Returns:
        Tuple of (Experiment, ValidationResult or None)
    """
    importer = DataImporter()
    experiment = importer.import_from_csv(file_path, experiment_id)
    
    validation_result = None
    if validate:
        validator = DataValidator()
        validation_result = validator.validate_experiment(experiment)
    
    return experiment, validation_result


def load_experiment_from_json(file_path: str, 
                             validate: bool = True) -> Tuple[Experiment, Optional[ValidationResult]]:
    """
    Load and optionally validate an experiment from a JSON file.
    
    Args:
        file_path: Path to the JSON file
        validate: Whether to perform validation
        
    Returns:
        Tuple of (Experiment, ValidationResult or None)
    """
    importer = DataImporter()
    experiment = importer.import_from_json(file_path)
    
    validation_result = None
    if validate:
        validator = DataValidator()
        validation_result = validator.validate_experiment(experiment)
    
    return experiment, validation_result


if __name__ == "__main__":
    # Example usage and testing
    
    # Create sample data
    gas_props = {
        'name': 'CO2',
        'molar_mass': 44.01,
        'critical_temperature': 304.13,
        'critical_pressure': 73.8
    }
    
    sys_params = {
        'solvent_type': 'MEA',
        'flow_rate': 2.5,
        'column_diameter': 5.0,
        'column_height': 100.0
    }
    
    data_points = [
        {'temperature': 25.0, 'pressure': 1.0, 'absorption_capacity': 0.5, 'time': 0},
        {'temperature': 25.0, 'pressure': 2.0, 'absorption_capacity': 0.8, 'time': 10},
        {'temperature': 25.0, 'pressure': 3.0, 'absorption_capacity': 1.1, 'time': 20},
        {'temperature': 25.0, 'pressure': 4.0, 'absorption_capacity': 1.3, 'time': 30},
        {'temperature': 25.0, 'pressure': 5.0, 'absorption_capacity': 1.5, 'time': 40},
    ]
    
    # Create experiment from manual entry
    experiment = DataImporter.create_from_manual_entry(
        experiment_id="test_exp_001",
        gas_properties=gas_props,
        system_parameters=sys_params,
        data_points=data_points
    )
    
    print("Created experiment:")
    print(f"  ID: {experiment.experiment_id}")
    print(f"  Gas: {experiment.gas_properties.name}")
    print(f"  Solvent: {experiment.system_parameters.solvent_type}")
    print(f"  Data points: {len(experiment.data_points)}")
    
    # Validate
    validator = DataValidator()
    result = validator.validate_experiment(experiment)
    
    print("\nValidation Result:")
    print(result.summary())
    
    # Test outlier detection
    print("\n--- Testing Outlier Detection ---")
    values_with_outlier = [1.0, 1.2, 1.1, 1.3, 1.2, 10.0]  # 10.0 is an outlier
    outliers = DataValidator.detect_outliers_iqr(values_with_outlier)
    print(f"Values: {values_with_outlier}")
    print(f"Outlier indices: {outliers}")
    
    # Test range validation
    print("\n--- Testing Range Validation ---")
    temp_valid, temp_msg = DataValidator.validate_temperature_range(25.0)
    print(f"Temperature 25°C valid: {temp_valid}")
    
    temp_valid, temp_msg = DataValidator.validate_temperature_range(-60.0)
    print(f"Temperature -60°C valid: {temp_valid}, message: {temp_msg}")
    
    temp_valid, temp_msg = DataValidator.validate_temperature_range(550.0)
    print(f"Temperature 550°C valid: {temp_valid}, message: {temp_msg}")
    
    pressure_valid, pressure_msg = DataValidator.validate_pressure_range(50.0)
    print(f"Pressure 50 bar valid: {pressure_valid}")
    
    pressure_valid, pressure_msg = DataValidator.validate_pressure_range(0.05)
    print(f"Pressure 0.05 bar valid: {pressure_valid}, message: {pressure_msg}")
    
    # ========================================================================
    # Section 2: Thermodynamic Calculations Tests
    # ========================================================================
    
    print("\n" + "="*70)
    print("SECTION 2: THERMODYNAMIC CALCULATIONS")
    print("="*70)
    
    # 2.1 Ideal Gas Law Tests
    print("\n--- 2.1 Ideal Gas Law Calculations ---")
    
    ideal_calc = IdealGasCalculator()
    
    # Test PV = nRT
    print("\nIdeal Gas Law (PV = nRT):")
    n = ideal_calc.calculate_moles(pressure=1.0, volume=1.0, temperature_k=298.15)
    print(f"  Moles at 1 bar, 1 L, 25°C: {n:.6f} mol")
    
    P = ideal_calc.calculate_pressure(n=0.04, volume=1.0, temperature_k=298.15)
    print(f"  Pressure for 0.04 mol in 1 L at 25°C: {P:.4f} bar")
    
    V = ideal_calc.calculate_volume(n=0.04, pressure=1.0, temperature_k=298.15)
    print(f"  Volume for 0.04 mol at 1 bar, 25°C: {V:.4f} L")
    
    # Test theoretical absorption
    theo_abs = ideal_calc.calculate_theoretical_absorption(
        pressure=5.0, temperature_c=25, solvent_volume=1.0, max_capacity=2.0
    )
    print(f"\nTheoretical absorption at 5 bar, 25°C: {theo_abs:.6f} mol")
    
    # Test Henry's Law
    print("\nHenry's Law (C = kH × P):")
    kH = 0.034  # mol/(L·bar) for CO2 in water at 25°C
    conc = ideal_calc.henrys_law_concentration(kH, pressure=2.0)
    print(f"  CO2 concentration at 2 bar (kH={kH}): {conc:.6f} mol/L")
    
    # 2.2 Real Gas Corrections
    print("\n--- 2.2 Real Gas Corrections ---")
    
    gas_props_obj = GasProperties(**gas_props)
    real_calc = RealGasCalculator(gas_props_obj)
    
    # Van der Waals parameters
    a, b = real_calc.calculate_vdw_parameters()
    print(f"\nVan der Waals parameters for {gas_props['name']}: ")
    print(f"  a = {a:.6f} L²·bar/mol²")
    print(f"  b = {b:.6f} L/mol")
    
    # VdW pressure
    p_vdw = real_calc.van_der_waals_pressure(n=1.0, volume=1.0, temperature_k=300)
    print(f"\nVdW pressure for 1 mol in 1 L at 300 K: {p_vdw:.4f} bar")
    
    # Compressibility factor
    Z = real_calc.compressibility_factor(pressure=50, temperature_k=304.13)
    print(f"\nCompressibility factor Z at 50 bar, 304.13 K: {Z:.6f}")
    print(f"  Deviation from ideal: {(1-Z)*100:.2f}%")
    
    # Peng-Robinson
    print("\nPeng-Robinson EOS:")
    a_c, b_pr, _ = real_calc.peng_robinson_parameters()
    alpha = real_calc.peng_robinson_alpha(temperature_k=300, acentric_factor=0.225)
    print(f"  a_c = {a_c:.6f}")
    print(f"  b = {b_pr:.6f}")
    print(f"  α at 300 K (ω=0.225): {alpha:.6f}")
    
    # Fugacity coefficient
    phi = real_calc.fugacity_coefficient(pressure=50, temperature_k=300, acentric_factor=0.225)
    print(f"\nFugacity coefficient at 50 bar, 300 K: {phi:.6f}")
    
    # Real gas absorption correction
    real_results = real_calc.calculate_real_gas_absorption(
        pressure=50, temperature_c=25, solvent_volume=1.0, 
        max_capacity=2.0, acentric_factor=0.225
    )
    print(f"\nReal gas absorption correction at 50 bar:")
    print(f"  Z = {real_results['compressibility_factor']:.6f}")
    print(f"  φ = {real_results['fugacity_coefficient']:.6f}")
    print(f"  Ideal moles: {real_results['ideal_moles']:.6f}")
    print(f"  Corrected moles: {real_results['corrected_moles']:.6f}")
    print(f"  Deviation: {real_results['deviation_from_ideal']:.2f}%")
    
    # 2.3 Temperature & Pressure Dependencies
    print("\n--- 2.3 Temperature & Pressure Dependencies ---")
    
    thermo = ThermodynamicDependencies()
    
    # Arrhenius equation
    print("\nArrhenius Equation:")
    A = 1e10  # pre-exponential factor
    Ea = 50000  # J/mol
    k_298 = thermo.arrhenius_rate(A, Ea, 298.15)
    k_350 = thermo.arrhenius_rate(A, Ea, 350)
    print(f"  Rate at 298 K: {k_298:.2e}")
    print(f"  Rate at 350 K: {k_350:.2e}")
    print(f"  Rate ratio (350K/298K): {k_350/k_298:.2f}")
    
    # Antoine equation (water)
    print("\nAntoine Equation (Water):")
    A_ant, B_ant, C_ant = 8.07131, 1730.63, 233.426  # Water constants
    vp_25 = thermo.antoine_vapor_pressure_bar(A_ant, B_ant, C_ant, 25)
    vp_100 = thermo.antoine_vapor_pressure_bar(A_ant, B_ant, C_ant, 100)
    print(f"  Vapor pressure at 25°C: {vp_25:.6f} bar")
    print(f"  Vapor pressure at 100°C: {vp_100:.4f} bar")
    
    # Heat of absorption
    print("\nHeat of Absorption (Clausius-Clapeyron):")
    P1, T1 = 1.0, 298.15
    P2, T2 = 2.0, 310.0
    dH = thermo.heat_of_absorption_clausius_clapeyron(P1, T1, P2, T2)
    print(f"  Between ({T1} K, {P1} bar) and ({T2} K, {P2} bar):")
    print(f"  ΔH = {dH:.2f} J/mol = {dH/1000:.2f} kJ/mol")
    
    # Combined T&P correction
    print("\nCombined Temperature & Pressure Correction:")
    correction = thermo.combined_tp_correction(
        reference_capacity=1.0,
        ref_temp=298.15,
        ref_pressure=1.0,
        op_temp=323.15,  # 50°C
        op_pressure=10.0,
        activation_energy=45000
    )
    print(f"  Reference: {correction['reference_conditions']}")
    print(f"  Operating: {correction['operating_conditions']}")
    print(f"  Temperature factor: {correction['temperature_factor']:.4f}")
    print(f"  Pressure factor: {correction['pressure_factor']:.4f}")
    print(f"  Combined factor: {correction['combined_factor']:.4f}")
    print(f"  Corrected capacity: {correction['corrected_capacity']:.4f}")
    
    print("\n" + "="*70)
    print("All thermodynamic calculations completed successfully!")
    print("="*70)
