from dash import Dash, html, dcc, Input, Output, State, callback_context
import plotly.express as px
from controls.layer_controls import LayerControls
from layers.map_layers import MapLayers
from data_processing.data_loader import DataLoader
import json
import geopandas as gpd
import sys

# Initialize components
data_loader = DataLoader()
map_layers = MapLayers()

# Initialize the Dash app
app = Dash(__name__, suppress_callback_exceptions=True)

# Create the app layout
app.layout = html.Div([
    # Main container
    html.Div([
        # Left side - Map
        html.Div([
            # Map
            dcc.Graph(
                id='map-container',
                style={'height': '100vh'},
                figure=map_layers.create_base_map(),
                config={'displayModeBar': True}
            ),
        ], style={
            'flex': '1',
            'height': '100vh',
            'position': 'relative'
        }),
        
        # Right side - Controls and Bus Stop Info
        LayerControls.create_right_panel()
    ], style={
        'display': 'flex',
        'height': '100vh',
        'width': '100%'
    }),
    
    # Store components for managing state
    dcc.Store(id='selected-station-store'),
    dcc.Store(id='affected-areas-store')
], style={
    'height': '100vh',
    'width': '100%',
    'margin': 0,
    'padding': 0
})

@app.callback(
    [Output('selected-station-store', 'data'),
     Output('affected-areas-store', 'data')],
    [Input('map-container', 'clickData'),
     Input('radius-slider', 'value')],
    [State('year-selector', 'value')]
)
def handle_click(clickData, radius, selected_year):
    if not clickData:
        return None, None

    ctx = callback_context
    if not ctx.triggered:
        return None, None

    try:
        point = clickData['points'][0]
        
        # Handle station click
        if 'customdata' in point and isinstance(point['customdata'], dict):
            station_name = point['customdata'].get('name')
            station_line = point['customdata'].get('line')
            
            if not station_name:
                return None, None
                
            # Load cityline data
            selected_year = selected_year or '2025'
            cityline_data = data_loader.load_cityline_data(selected_year)
            
            # Find the station
            station = cityline_data[cityline_data['name'] == station_name]
            if station.empty:
                return None, None
                
            station = station.iloc[0]
            
            # Get affected areas
            point_geom = station.geometry
            affected_areas = data_loader.get_areas_within_radius(point_geom, radius or 400)
            affected_areas_json = affected_areas.__geo_interface__
            
            # Prepare station info
            station_info = {
                'name': station_name,
                'line': station_line,
                'coordinates': list(point_geom.coords)[0]
            }
            
            return station_info, affected_areas_json
            
    except Exception as e:
        print("ERROR IN CLICK HANDLER:", str(e))
        import traceback
        traceback.print_exc()
        sys.stdout.flush()
    
    return None, None

@app.callback(
    [Output('bus-stop-name', 'children'),
     Output('bus-stop-lines', 'children')],
    [Input('selected-station-store', 'data')]
)
def update_bus_stop_info(station_info):
    if not station_info:
        return "No station selected", "Click a station on the map to view details"
        
    try:
        name = station_info['name']
        lines = station_info['line'].split('/')  # Split lines if multiple
        
        # Format lines with bullet points and colors
        formatted_lines = []
        for line in lines:
            line = line.strip()
            color = line.lower()
            formatted_lines.append(
                html.Div([
                    "• ",
                    html.Span(f"{line.capitalize()} Line", 
                             style={'color': color, 'fontWeight': 'bold'})
                ], style={'marginBottom': '5px'})
            )
        
        return name, html.Div(formatted_lines)
    except Exception as e:
        print("ERROR UPDATING BUS STOP INFO:", str(e))
        sys.stdout.flush()
        return "Error displaying station info", "Please try selecting another station"

@app.callback(
    Output('map-container', 'figure'),
    [Input('year-selector', 'value'),
     Input('radius-slider', 'value'),
     Input('layer-toggles', 'value'),
     Input('selected-station-store', 'data'),
     Input('affected-areas-store', 'data')]
)
def update_map(selected_year, radius, active_layers, selected_station, affected_areas_json):
    try:
        # Create base map
        fig = map_layers.create_base_map()
        
        # Set default active layers if none selected
        if not active_layers:
            active_layers = ['cityline']  # Always show cityline by default
            
        # Load cityline data
        selected_year = selected_year or '2025'
        cityline_data = data_loader.load_cityline_data(selected_year)
        
        # Add affected areas first (if a station is selected)
        if selected_station and affected_areas_json:
            fig = map_layers.add_affected_areas_layer(fig, affected_areas_json)
        
        # Add smasvaedi layer if selected
        if 'smasvaedi' in active_layers:
            small_areas = data_loader.load_small_areas()
            fig = map_layers.add_small_areas_layer(fig, small_areas)
        
        # Add cityline layer with year-specific routes
        if 'cityline' in active_layers:
            fig = map_layers.add_cityline_layer(fig, cityline_data, selected_year)
        
        # Add coverage circles if needed
        if 'coverage' in active_layers and radius:
            for _, station in cityline_data.iterrows():
                fig = map_layers.add_radius_circle(fig, station.geometry, radius, station['line'])
        
        # Add population density only if specifically requested
        if 'density' in active_layers:
            small_areas = data_loader.load_small_areas()
            population_data = data_loader.load_population_data()
            total_pop = population_data.groupby('smasvaedi')['fjoldi'].sum()
            small_areas['fjoldi'] = total_pop
            fig = map_layers.add_small_areas_layer(fig, small_areas, show_population=True)

        # Add schools layer if selected
        if 'schools' in active_layers:
            schools_data = data_loader.load_schools_data()
            fig = map_layers.add_schools_layer(fig, schools_data)
        
        return fig
    except Exception as e:
        print("ERROR UPDATING MAP:", str(e))
        sys.stdout.flush()
        return map_layers.create_base_map()

if __name__ == '__main__':
    print("\nStarting Borgarlínan Visualization...")
    print("Access the application at http://localhost:8050")
    print("\nIMPORTANT: When you click a station, debug information will appear here in this terminal.")
    print("\nInitializing application...")
    sys.stdout.flush()
    app.run_server(debug=True, port=8050)
