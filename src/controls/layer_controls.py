from dash import html, dcc
import plotly.express as px

class LayerControls:
    @staticmethod
    def create_year_selector():
        """Create year selection dropdown"""
        return html.Div([
            html.Label('Select Year:', style={'fontWeight': 'bold', 'marginBottom': '10px'}),
            dcc.Dropdown(
                id='year-selector',
                options=[
                    {'label': '2025', 'value': '2025'},
                    {'label': '2029', 'value': '2029'},
                    {'label': '2030', 'value': '2030'}
                ],
                value='2025',
                clearable=False
            )
        ], style={'marginBottom': '20px'})

    @staticmethod
    def create_radius_slider():
        """Create radius control slider"""
        return html.Div([
            html.Label('Coverage Radius (meters):', style={'fontWeight': 'bold', 'marginBottom': '10px'}),
            dcc.Slider(
                id='radius-slider',
                min=200,
                max=1000,
                step=50,
                value=400,
                marks={
                    200: '200m',
                    400: '400m',
                    600: '600m',
                    800: '800m',
                    1000: '1000m'
                },
                tooltip={'placement': 'bottom', 'always_visible': True},
                persistence=True
            )
        ], style={'marginBottom': '20px'})

    @staticmethod
    def create_layer_toggles():
        """Create layer visibility toggles"""
        return html.Div([
            html.Label('Map Layers:', style={'fontWeight': 'bold', 'marginBottom': '10px'}),
            dcc.Checklist(
                id='layer-toggles',
                options=[
                    {'label': ' Cityline', 'value': 'cityline'},
                    {'label': ' Coverage Areas', 'value': 'coverage'},
                    {'label': ' Population Density', 'value': 'density'},
                    {'label': ' Small Areas (Smásvæði)', 'value': 'smasvaedi'},
                    {'label': ' Schools', 'value': 'schools'}
                ],
                value=['cityline'],  # Default to showing only cityline
                persistence=True,
                style={'display': 'flex', 'flexDirection': 'column', 'gap': '10px'}
            )
        ], style={'marginBottom': '20px'})

    @staticmethod
    def create_bus_box():
        """Create bus stop info box"""
        return html.Div([
            html.Div([
                html.H3('Selected Bus Stop', style={
                    'marginBottom': '15px',
                    'color': '#2c3e50',
                    'borderBottom': '2px solid #3498db',
                    'paddingBottom': '10px'
                }),
                html.Div(id='bus-stop-name', style={
                    'fontSize': '18px',
                    'fontWeight': 'bold',
                    'color': '#2c3e50',
                    'marginBottom': '10px',
                    'padding': '10px',
                    'backgroundColor': '#f8f9fa',
                    'borderRadius': '5px',
                    'border': '1px solid #dee2e6'
                }),
                html.Div(id='bus-stop-lines', style={
                    'fontSize': '16px',
                    'color': '#34495e',
                    'padding': '10px',
                    'backgroundColor': '#f8f9fa',
                    'borderRadius': '5px',
                    'border': '1px solid #dee2e6',
                    'whiteSpace': 'pre-line'  # This will preserve line breaks
                })
            ], style={
                'padding': '20px',
                'backgroundColor': 'white',
                'borderRadius': '8px',
                'boxShadow': '0 2px 4px rgba(0,0,0,0.1)',
                'border': '1px solid #e9ecef'
            })
        ], style={
            'padding': '20px',
            'backgroundColor': '#ffffff',
            'marginTop': '20px'
        })

    @staticmethod
    def create_right_panel():
        """Create the complete right panel with controls and bus stop info"""
        return html.Div([
            # Controls Section
            html.Div([
                html.H3('Controls', style={'marginBottom': '20px', 'color': '#2c3e50'}),
                LayerControls.create_year_selector(),
                LayerControls.create_radius_slider(),
                LayerControls.create_layer_toggles()
            ], style={
                'padding': '20px',
                'borderBottom': '1px solid #ddd',
                'backgroundColor': '#ffffff'
            }),
            
            # Bus Stop Info Box
            LayerControls.create_bus_box()
        ], style={
            'width': '400px',
            'height': '100vh',
            'backgroundColor': '#f8f9fa',
            'boxShadow': '-2px 0px 5px rgba(0,0,0,0.1)',
            'overflowY': 'auto',
            'display': 'flex',
            'flexDirection': 'column'
        })
