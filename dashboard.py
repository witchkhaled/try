"""
Module 5: Interactive Dashboard and Visualization System
Implements Sections 5.1 - 5.3
"""

import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.express as px
import pandas as pd
import numpy as np
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime

# Import previous modules for data structures and calculations
# Assuming experimental_data.py is in the same path
try:
    from experimental_data import Experiment, DataValidator, IdealGasCalculator, RealGasCalculator, AbsorptionMetrics, UncertaintyAnalyzer, DeviationAnalyzer
except ImportError:
    # Fallback definitions for standalone testing if needed
    class Experiment: pass
    class DataValidator: pass
    class IdealGasCalculator: pass
    class RealGasCalculator: pass
    class AbsorptionMetrics: pass
    class UncertaintyAnalyzer: pass
    class DeviationAnalyzer: pass


class DashboardLayout:
    """
    5.1 Main Dashboard Layout Generator
    Creates the structural layout for the dashboard including Header, KPIs, and Filters.
    """
    
    def __init__(self, project_title: str, gas_type: str, date_range: Tuple[str, str]):
        self.project_title = project_title
        self.gas_type = gas_type
        self.date_range = date_range
        
    def generate_header(self) -> Dict[str, Any]:
        """Generates the header component."""
        return {
            'type': 'html',
            'content': f"""
            <div style="background-color: #f0f2f5; padding: 20px; border-radius: 8px; margin-bottom: 20px;">
                <h1 style="margin: 0; color: #2c3e50;">{self.project_title}</h1>
                <div style="display: flex; gap: 20px; margin-top: 10px; color: #7f8c8d;">
                    <span><strong>Gas Type:</strong> {self.gas_type}</span>
                    <span><strong>Date Range:</strong> {self.date_range[0]} to {self.date_range[1]}</span>
                    <span><strong>Generated:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M')}</span>
                </div>
            </div>
            """
        }
    
    def generate_kpi_cards(self, avg_absorption: float, max_deviation: float, uncertainty_range: str) -> Dict[str, Any]:
        """Generates KPI cards for Avg Absorption, Max Deviation, and Uncertainty."""
        return {
            'type': 'kpi_container',
            'cards': [
                {'title': 'Avg Absorption', 'value': f"{avg_absorption:.4f} mol/L", 'color': '#3498db'},
                {'title': 'Max Deviation', 'value': f"{max_deviation:.2f}%", 'color': '#e74c3c' if max_deviation > 10 else '#2ecc71'},
                {'title': 'Uncertainty Range', 'value': uncertainty_range, 'color': '#f39c12'}
            ]
        }
    
    def generate_filter_panel(self, temp_min: float, temp_max: float, pressures: List[float]) -> Dict[str, Any]:
        """Generates the filter panel with sliders and dropdowns."""
        return {
            'type': 'filter_panel',
            'components': [
                {
                    'id': 'temp-slider',
                    'type': 'slider',
                    'label': 'Temperature Range (°C)',
                    'min': temp_min,
                    'max': temp_max,
                    'step': 1,
                    'value': [temp_min, temp_max]
                },
                {
                    'id': 'pressure-dropdown',
                    'type': 'multi-select',
                    'label': 'Pressure Conditions (bar)',
                    'options': [{'label': f"{p} bar", 'value': p} for p in pressures],
                    'value': pressures
                },
                {
                    'id': 'gas-dropdown',
                    'type': 'dropdown',
                    'label': 'Gas Type',
                    'options': [{'label': 'CO2', 'value': 'CO2'}, {'label': 'CH4', 'value': 'CH4'}, {'label': 'N2', 'value': 'N2'}],
                    'value': self.gas_type
                }
            ]
        }

    def get_full_layout_config(self, kpi_data: Dict, filter_data: Dict) -> Dict[str, Any]:
        """Assembles the full dashboard layout configuration."""
        return {
            'header': self.generate_header(),
            'kpis': self.generate_kpi_cards(**kpi_data),
            'filters': self.generate_filter_panel(**filter_data),
            'plots_container': {'id': 'plots-grid', 'style': {'display': 'grid', 'gridTemplateColumns': '1fr 1fr'}}
        }


class VisualizationEngine:
    """
    5.2 Visualization Components
    Generates interactive Plotly figures for 3D surfaces, comparisons, heatmaps, etc.
    """
    
    def __init__(self, experiment: Experiment):
        self.experiment = experiment
        self.data_points = experiment.data_points if hasattr(experiment, 'data_points') else []
        self.df = self._prepare_dataframe()
        
    def _prepare_dataframe(self) -> pd.DataFrame:
        """Converts experiment data points to a Pandas DataFrame for plotting."""
        if not self.data_points:
            return pd.DataFrame()
        
        data = []
        for point in self.data_points:
            row = {
                'temperature': point.temperature,
                'pressure': point.pressure,
                'absorption_exp': point.absorption_capacity,
                'time': point.time,
                'timestamp': point.timestamp
            }
            # Calculate Ideal for comparison if gas properties exist
            if hasattr(self.experiment, 'gas_properties') and self.experiment.gas_properties:
                gp = self.experiment.gas_properties
                # Simple ideal estimation for demo: C_ideal approx P / (R * T) * scaling
                # Using Henry's law approximation for demo purposes if kH known, else generic
                R = 0.08314 # L bar / (mol K)
                T_K = point.temperature + 273.15
                # Mock ideal capacity calculation (assuming some solubility factor)
                # In real scenario, use IdealGasCalculator from Module 2
                c_ideal = (point.pressure / (R * T_K)) * 0.5 # 0.5 is a mock Henry constant
                row['absorption_ideal'] = c_ideal
                row['deviation'] = abs(point.absorption_capacity - c_ideal)
                row['relative_error'] = (abs(point.absorption_capacity - c_ideal) / c_ideal) * 100 if c_ideal != 0 else 0
            
            # Add uncertainty if available
            if hasattr(point, 'uncertainty'):
                row['uncertainty'] = point.uncertainty
            else:
                row['uncertainty'] = 0.05 * point.absorption_capacity # Default 5%
                
            data.append(row)
            
        return pd.DataFrame(data)

    def create_3d_surface_plot(self) -> go.Figure:
        """
        A) 3D Surface Plot
        X: Temperature, Y: Pressure, Z: Absorption
        Two surfaces: Experimental (gradient) vs Ideal (wireframe)
        """
        if self.df.empty or 'absorption_ideal' not in self.df.columns:
            return go.Figure(layout={'title': 'No data available for 3D plot'})

        fig = make_subplots(specs=[[{'type': 'surface'}]])
        
        # Pivot data for surface
        # Note: Real implementation needs grid data. Here we scatter or interpolate.
        # For demonstration, we use scatter3d for experimental and a calculated surface for ideal
        
        # Experimental Scatter
        fig.add_trace(go.Scatter3d(
            x=self.df['temperature'],
            y=self.df['pressure'],
            z=self.df['absorption_exp'],
            mode='markers',
            marker=dict(size=5, color=self.df['absorption_exp'], colorscale='Viridis'),
            name='Experimental'
        ))
        
        # Ideal Surface (Wireframe approximation via line plots or surface if gridded)
        # Creating a meshgrid for ideal surface visualization
        T_min, T_max = self.df['temperature'].min(), self.df['temperature'].max()
        P_min, P_max = self.df['pressure'].min(), self.df['pressure'].max()
        T_grid = np.linspace(T_min, T_max, 20)
        P_grid = np.linspace(P_min, P_max, 20)
        T_mesh, P_mesh = np.meshgrid(T_grid, P_grid)
        
        # Calculate Ideal Z for mesh
        R = 0.08314
        Z_mesh = (P_mesh / (R * (T_mesh + 273.15))) * 0.5
        
        fig.add_trace(go.Surface(
            x=T_mesh, y=P_mesh, z=Z_mesh,
            opacity=0.3,
            showscale=False,
            colorscale='Greys',
            name='Ideal (Wireframe)',
            contours=dict(
                z=dict(show=True, usecolormap=True, highlightcolor="#fff", project_z=True)
            )
        ))
        
        fig.update_layout(
            title='3D Absorption Capacity: Experimental vs Ideal',
            scene=dict(
                xaxis_title='Temperature (°C)',
                yaxis_title='Pressure (bar)',
                zaxis_title='Absorption Capacity'
            ),
            height=600
        )
        return fig

    def create_comparison_bar_chart(self, mode: str = 'absolute') -> go.Figure:
        """
        B) Comparison Charts
        Side-by-side bars: Exp vs Ideal with error bars.
        Mode: 'absolute' or 'relative'
        """
        if self.df.empty:
            return go.Figure()
            
        df_plot = self.df.copy()
        if mode == 'relative':
            df_plot['exp_val'] = 100 # Baseline
            df_plot['ideal_val'] = (df_plot['absorption_ideal'] / df_plot['absorption_exp']) * 100
            y_title = 'Relative Performance (%)'
        else:
            df_plot['exp_val'] = df_plot['absorption_exp']
            df_plot['ideal_val'] = df_plot['absorption_ideal']
            y_title = 'Absorption Capacity'
            
        fig = go.Figure()
        
        fig.add_trace(go.Bar(
            name='Experimental',
            x=df_plot.index.astype(str),
            y=df_plot['exp_val'],
            error_y=dict(type='data', array=df_plot['uncertainty'], visible=True),
            marker_color='#3498db'
        ))
        
        fig.add_trace(go.Bar(
            name='Ideal',
            x=df_plot.index.astype(str),
            y=df_plot['ideal_val'],
            marker_color='#95a5a6'
        ))
        
        fig.update_layout(
            title=f'Experimental vs Ideal Absorption ({mode.title()})',
            xaxis_title='Data Point Index',
            yaxis_title=y_title,
            barmode='group',
            hovermode='x unified'
        )
        return fig

    def create_deviation_heatmap(self) -> go.Figure:
        """
        C) Deviation Heatmap
        Matrix of T x P conditions. Color intensity = deviation magnitude.
        """
        if self.df.empty or 'deviation' not in self.df.columns:
            return go.Figure()
            
        # Pivot to create matrix
        pivot_df = self.df.pivot_table(index='pressure', columns='temperature', values='deviation', aggfunc='mean')
        
        fig = go.Figure(data=go.Heatmap(
            z=pivot_df.values,
            x=pivot_df.columns,
            y=pivot_df.index,
            colorscale='RdYlBu_r', # Red high, Blue low
            colorbar=dict(title='Deviation')
        ))
        
        fig.update_layout(
            title='Deviation Heatmap (Temperature vs Pressure)',
            xaxis_title='Temperature (°C)',
            yaxis_title='Pressure (bar)'
        )
        return fig

    def create_uncertainty_band_plot(self) -> go.Figure:
        """
        D) Uncertainty Visualization
        Error band plots showing ±U around measurements.
        """
        if self.df.empty:
            return go.Figure()
            
        df_sorted = self.df.sort_values('time') if 'time' in self.df.columns else self.df
        
        fig = go.Figure()
        
        # Main line
        fig.add_trace(go.Scatter(
            x=df_sorted.index,
            y=df_sorted['absorption_exp'],
            mode='lines+markers',
            name='Measurement',
            line=dict(color='#2c3e50')
        ))
        
        # Upper bound
        fig.add_trace(go.Scatter(
            x=df_sorted.index,
            y=df_sorted['absorption_exp'] + df_sorted['uncertainty'],
            mode='lines',
            line=dict(width=0),
            showlegend=False,
            hoverinfo='skip'
        ))
        
        # Lower bound (fill to upper)
        fig.add_trace(go.Scatter(
            x=df_sorted.index,
            y=df_sorted['absorption_exp'] - df_sorted['uncertainty'],
            mode='lines',
            line=dict(width=0),
            fill='tonexty',
            fillcolor='rgba(52, 152, 219, 0.3)',
            name='± Uncertainty'
        ))
        
        fig.update_layout(
            title='Measurements with Uncertainty Bands',
            yaxis_title='Absorption Capacity',
            hovermode='x unified'
        )
        return fig
    
    def create_uncertainty_pie_chart(self) -> go.Figure:
        """Uncertainty contribution pie chart (Mock breakdown)."""
        labels = ['Instrument Precision', 'Calibration', 'Environmental', 'Repeatability']
        values = [40, 25, 20, 15] # Mock percentages
        
        fig = go.Figure(data=[go.Pie(labels=labels, values=values, hole=.3)])
        fig.update_layout(title='Uncertainty Contribution Sources')
        return fig

    def create_time_series_plot(self) -> go.Figure:
        """
        E) Time Series
        Absorption vs time, kinetic fit, residuals.
        """
        if self.df.empty or 'time' not in self.df.columns:
            return go.Figure()
            
        df_sorted = self.df.sort_values('time')
        
        fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.05, row_heights=[0.7, 0.3])
        
        # Main Plot
        fig.add_trace(go.Scatter(
            x=df_sorted['time'],
            y=df_sorted['absorption_exp'],
            mode='markers',
            name='Data',
            marker_color='#3498db'
        ), row=1, col=1)
        
        # Mock Kinetic Fit (Exponential approach)
        t = df_sorted['time'].values
        y = df_sorted['absorption_exp'].values
        if len(t) > 2:
            # Simple fit: y = A * (1 - exp(-kt))
            A_est = max(y)
            k_est = 0.1 # Mock
            y_fit = A_est * (1 - np.exp(-k_est * t))
            
            fig.add_trace(go.Scatter(
                x=df_sorted['time'],
                y=y_fit,
                mode='lines',
                name='Kinetic Model',
                line=dict(color='#e74c3c', dash='dash')
            ), row=1, col=1)
            
            # Residuals
            residuals = y - y_fit
            fig.add_trace(go.Scatter(
                x=df_sorted['time'],
                y=residuals,
                mode='markers',
                name='Residuals',
                marker_color='#2ecc71'
            ), row=2, col=1)
            
        fig.update_layout(height=600, title='Kinetic Analysis: Time Series & Residuals')
        fig.update_yaxes(title_text="Absorption", row=1, col=1)
        fig.update_yaxes(title_text="Residuals", row=2, col=1)
        fig.update_xaxes(title_text="Time", row=2, col=1)
        
        return fig


class InteractiveDashboard:
    """
    5.3 Interactive Features Manager
    Manages cross-filtering, tooltips, and export configurations.
    Can be integrated into a Dash/Streamlit app.
    """
    
    def __init__(self, experiment: Experiment):
        self.viz_engine = VisualizationEngine(experiment)
        self.layout_gen = None # Initialized later with metadata
        
    def generate_dashboard_config(self, project_title: str, gas_type: str) -> Dict[str, Any]:
        """Generates the complete configuration for the interactive dashboard."""
        
        # Prepare KPI data
        if not self.viz_engine.df.empty:
            avg_abs = self.viz_engine.df['absorption_exp'].mean()
            max_dev = self.viz_engine.df['relative_error'].max() if 'relative_error' in self.viz_engine.df.columns else 0.0
            u_range = f"±{self.viz_engine.df['uncertainty'].mean():.4f}"
        else:
            avg_abs, max_dev, u_range = 0, 0, "N/A"
            
        self.layout_gen = DashboardLayout(project_title, gas_type, ("2023-01-01", "2023-12-31"))
        
        layout_config = self.layout_gen.get_full_layout_config(
            kpi_data={'avg_absorption': avg_abs, 'max_deviation': max_dev, 'uncertainty_range': u_range},
            filter_data={
                'temp_min': self.viz_engine.df['temperature'].min() if not self.viz_engine.df.empty else 0,
                'temp_max': self.viz_engine.df['temperature'].max() if not self.viz_engine.df.empty else 100,
                'pressures': sorted(self.viz_engine.df['pressure'].unique().tolist()) if not self.viz_engine.df.empty else []
            }
        )
        
        # Generate Plots
        plots = {
            '3d_surface': self.viz_engine.create_3d_surface_plot(),
            'comparison_bar': self.viz_engine.create_comparison_bar_chart(),
            'deviation_heatmap': self.viz_engine.create_deviation_heatmap(),
            'uncertainty_band': self.viz_engine.create_uncertainty_band_plot(),
            'uncertainty_pie': self.viz_engine.create_uncertainty_pie_chart(),
            'time_series': self.viz_engine.create_time_series_plot()
        }
        
        # Convert Plotly figures to JSON for frontend consumption (or Dash components)
        plot_jsons = {name: fig.to_json() for name, fig in plots.items()}
        
        return {
            'layout': layout_config,
            'plots': plot_jsons,
            'interactive_features': {
                'hover_tooltips': True,
                'cross_filtering': True,
                'export_formats': ['PNG', 'SVG', 'JSON'],
                'zoom_pan': True
            }
        }

# Verification Code
if __name__ == "__main__":
    print("Generating Dashboard Verification...")
    
    # Create mock experiment data
    from experimental_data import Experiment, ExperimentalDataPoint, GasProperties, SystemParameters
    
    gas_props = GasProperties("CO2", 44.01, 304.1, 73.8)
    sys_params = SystemParameters("MEA", 1.5, 0.1, 2.0)
    
    points = []
    np.random.seed(42)
    for t in [20, 40, 60, 80]:
        for p in [1, 5, 10, 20]:
            # Mock experimental data with some noise
            abs_cap = (p / (0.08314 * (t + 273.15))) * 0.5 * np.random.uniform(0.9, 1.1)
            points.append(ExperimentalDataPoint(
                temperature=t,
                pressure=p,
                absorption_capacity=abs_cap,
                time=len(points)*10
            ))
            
    exp = Experiment(
        experiment_id="EXP-005",
        gas_properties=gas_props,
        system_parameters=sys_params,
        data_points=points
    )
    
    # Initialize Dashboard
    dashboard = InteractiveDashboard(exp)
    config = dashboard.generate_dashboard_config("CO2 Absorption Study", "CO2")
    
    print(f"Dashboard Config Generated:")
    print(f"- Layout Sections: {list(config['layout'].keys())}")
    print(f"- Plots Generated: {list(config['plots'].keys())}")
    print(f"- Interactive Features: {config['interactive_features']}")
    
    # Save a sample plot to JSON to verify structure
    import json
    sample_plot = json.loads(config['plots']['comparison_bar'])
    print(f"\nSample Plot Title: {sample_plot.get('layout', {}).get('title', {}).get('text', 'No Title')}")
    print(f"Number of Traces: {len(sample_plot.get('data', []))}")
    
    print("\nDashboard module verification complete.")
