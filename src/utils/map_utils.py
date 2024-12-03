from dash import Dash, html, dcc
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import geopandas as gpd
import json

def create_map_layout(app):
    """Create the main layout with map and right-side controls"""
    return html.Div([
        # Main container with map and controls
        html.Div([
            # Left side - Map
            html.Div([
                dcc.Graph(
                    id='main-map',
                    style={'height': '100vh'},
                    config={'scrollZoom': True}
                )
            ], style={'flex': '1', 'height': '100vh'}),
            
            # Right side - Controls and Statistics
            html.Div([
                # Cohort Selection Section
                html.Div([
                    html.H3('Cohort Selection', style={'marginBottom': '20px'}),
                    dcc.Dropdown(
                        id='year-selector',
                        options=[
                            {'label': '2025', 'value': '2025'},
                            {'label': '2029', 'value': '2029'},
                            {'label': '2030', 'value': '2030'}
                        ],
                        value='2025',
                        style={'marginBottom': '15px'}
                    ),
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
                        tooltip={'placement': 'bottom', 'always_visible': True}
                    )
                ], style={'padding': '20px', 'borderBottom': '1px solid #ddd'}),
                
                # Statistics Section
                html.Div([
                    html.H3('Statistics', style={'marginBottom': '20px'}),
                    html.Div([
                        html.Div([
                            html.H4('Population'),
                            html.Div(id='total-population')
                        ], style={'marginBottom': '20px'}),
                        html.Div([
                            html.H4('Age Distribution'),
                            dcc.Graph(id='age-distribution')
                        ], style={'marginBottom': '20px'}),
                        html.Div([
                            html.H4('Income Distribution'),
                            dcc.Graph(id='income-distribution')
                        ])
                    ], id='statistics-container')
                ], style={'padding': '20px', 'overflowY': 'auto'})
            ], style={
                'width': '400px',
                'height': '100vh',
                'backgroundColor': 'white',
                'boxShadow': '-2px 0px 5px rgba(0,0,0,0.1)',
                'display': 'flex',
                'flexDirection': 'column'
            })
        ], style={
            'display': 'flex',
            'height': '100vh',
            'width': '100%'
        })
    ], style={
        'height': '100vh',
        'width': '100%',
        'margin': 0,
        'padding': 0
    })

def create_base_map(geojson_data, center_lat=64.11, center_lon=-21.90):
    """Create the base map with the GeoJSON data"""
    fig = go.Figure()
    
    # Add the GeoJSON layer
    fig.add_trace(go.Choroplethmapbox(
        geojson=geojson_data,
        locations=[], # Will be filled with actual data
        z=[], # Will be filled with actual data
        colorscale="Viridis",
        marker_opacity=0.5,
        marker_line_width=0,
        showscale=False
    ))
    
    # Update the layout
    fig.update_layout(
        mapbox=dict(
            style="carto-positron",
            center=dict(lat=center_lat, lon=center_lon),
            zoom=11
        ),
        margin={"r":0,"t":0,"l":0,"b":0},
        showlegend=False
    )
    
    return fig

def update_map_data(fig, geojson_data, data_values, locations):
    """Update the map with new data"""
    fig.update_traces(
        geojson=geojson_data,
        locations=locations,
        z=data_values
    )
    return fig

def create_age_distribution_chart(age_data):
    """Create age distribution bar chart"""
    fig = go.Figure(data=[
        go.Bar(
            x=list(age_data.keys()),
            y=list(age_data.values()),
            marker_color='#1f77b4'
        )
    ])
    
    fig.update_layout(
        margin=dict(l=20, r=20, t=20, b=40),
        height=200,
        xaxis_title="Age Groups",
        yaxis_title="Count"
    )
    
    return fig

def create_income_distribution_chart(income_data):
    """Create income distribution bar chart"""
    fig = go.Figure(data=[
        go.Bar(
            x=list(income_data.keys()),
            y=list(income_data.values()),
            marker_color='#2ca02c'
        )
    ])
    
    fig.update_layout(
        margin=dict(l=20, r=20, t=20, b=40),
        height=200,
        xaxis_title="Income Brackets",
        yaxis_title="Count"
    )
    
    return fig
