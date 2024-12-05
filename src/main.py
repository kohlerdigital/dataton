from dash import Dash, html, dcc, Input, Output, State, callback_context
import plotly.express as px
from src.controls.layer_controls import LayerControls
from src.layers.map_layers import MapLayers
from src.data_processing.data_loader import DataLoader
from src.data_processing.station_coverage import calculate_station_coverage
from src.data_processing.age_groups import calculate_age_group_percentages, format_age_group_info
import json
import geopandas as gpd
import sys
from shapely.geometry import MultiPolygon

# Initialize components
data_loader = DataLoader()
map_layers = MapLayers()

# Initialize the Dash app
app = Dash(__name__, suppress_callback_exceptions=True)

# Create the app layout
app.layout = html.Div([
    # Main container
    html.Div([
        # Map container that takes full width
        html.Div([
            dcc.Graph(
                id='map-container',
                style={'height': '100vh', 'width': '100%'},
                figure=map_layers.create_base_map(),
                config={'displayModeBar': True}
            ),
        ], style={
            'height': '100vh',
            'width': '100%',
            'position': 'relative'
        }),
        
        # Controls panel overlaid on top of map
        html.Div([
            LayerControls.create_right_panel()
        ], style={
            'position': 'absolute',
            'top': 0,
            'right': 0,
            'zIndex': 1000,
            'backgroundColor': 'rgba(248, 249, 250, 0.9)',  # Semi-transparent background
        }),
    ], style={
        'height': '100vh',
        'width': '100%',
        'position': 'relative'
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

def get_polygon_coordinates(geometry):
    """Extract coordinates from a geometry object, handling Point, Polygon, and MultiPolygon types"""
    if geometry.geom_type == 'Point':
        return list(geometry.coords)[0]
    elif geometry.geom_type == 'Polygon':
        return list(geometry.exterior.coords)
    elif geometry.geom_type == 'MultiPolygon':
        # For MultiPolygon, use the largest polygon's coordinates
        largest_polygon = max(geometry.geoms, key=lambda p: p.area)
        return list(largest_polygon.exterior.coords)
    else:
        raise ValueError(f"Unsupported geometry type: {geometry.geom_type}")

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
            
            # Extract station coordinates
            station_coords = list(point_geom.coords)[0]
            
            # Prepare area data for coverage calculation
            area_data = []
            for idx, geom in affected_areas.geometry.items():
                try:
                    coords = get_polygon_coordinates(geom)
                    area_data.append({
                        "id": str(idx),
                        "geometry": coords
                    })
                except Exception as e:
                    print(f"Error processing area {idx}: {e}")
                    continue
            
            # Calculate coverage for each area using just the lon, lat coordinates
            covered_areas = calculate_station_coverage(
                area_data,
                (station_coords[0], station_coords[1]),  # Extract just lon, lat
                radius or 400
            )
            
            # Calculate age group percentages
            small_areas = data_loader.load_small_areas()
            formatted_areas = []
            for idx, geom in small_areas.geometry.items():
                try:
                    area_coords = get_polygon_coordinates(geom)
                    formatted_areas.append({
                        "id": str(idx),
                        "geometry": area_coords
                    })
                except Exception as e:
                    print(f"Error formatting area {idx}: {e}")
                    continue
            
            # Calculate age group percentages
            percentages = calculate_age_group_percentages(station_coords, radius or 400, formatted_areas)
            age_groups = format_age_group_info(percentages)
            
            # Prepare station info
            station_info = {
                'name': station_name,
                'line': station_line,
                'coordinates': station_coords,
                'covered_areas': covered_areas,
                'age_groups': age_groups
            }
            
            print("\nStation Info:", station_info)  # Debug print
            print("Covered Areas:", covered_areas)  # Debug print
            
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
        covered_areas = station_info.get('covered_areas', [])
        age_groups = station_info.get('age_groups', [])
        
        print("\nUpdating bus stop info:")  # Debug print
        print("Name:", name)  # Debug print
        print("Lines:", lines)  # Debug print
        print("Covered areas:", covered_areas)  # Debug print
        print("Age groups:", age_groups)  # Debug print
        
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
        
        # Add age group information
        if age_groups:
            formatted_lines.append(
                html.Div([
                    html.Hr(style={'margin': '10px 0'}),
                    html.Div("Age Group Coverage:", 
                            style={'marginTop': '10px', 'fontWeight': 'bold'}),
                    *[html.Div(group, style={'marginTop': '5px', 'fontSize': '14px'})
                      for group in age_groups]
                ])
            )
        
        # Add affected areas information with coverage percentages
        if covered_areas:
            area_strings = [
                f"{area['id']} ({area['area_coverage_percent']:.1f}%)"
                for area in covered_areas
            ]
            formatted_lines.append(
                html.Div([
                    html.Hr(style={'margin': '10px 0'}),
                    html.Div("Affected areas:", 
                            style={'marginTop': '10px', 'fontWeight': 'bold'}),
                    html.Div(', '.join(area_strings),
                            style={'marginTop': '5px', 'fontSize': '14px'})
                ])
            )
        
        return name, html.Div(formatted_lines)
    except Exception as e:
        print("ERROR UPDATING BUS STOP INFO:", str(e))
        import traceback
        traceback.print_exc()
        sys.stdout.flush()
        return "Error displaying station info", "Please try selecting another station"

@app.callback(
    Output('map-container', 'figure'),
    [Input('year-selector', 'value'),
     Input('radius-slider', 'value'),
     Input('layer-toggles', 'value'),
     Input('selected-station-store', 'data'),
     Input('affected-areas-store', 'data'),
     Input('age-group-selector', 'value')],
    [State('map-container', 'figure')]
)
def update_map(selected_year, radius, active_layers, selected_station, affected_areas_json, age_group, current_figure):
    try:
        # Create base map while preserving the current view state
        fig = map_layers.create_base_map()
        
        # Preserve the current view state if it exists
        if current_figure and 'layout' in current_figure and 'mapbox' in current_figure['layout']:
            current_mapbox = current_figure['layout']['mapbox']
            if 'center' in current_mapbox:
                fig.update_layout(
                    mapbox=dict(
                        center=current_mapbox['center'],
                        zoom=current_mapbox.get('zoom', map_layers.default_zoom)
                    )
                )
        
        # Load data that might be needed by multiple layers
        cityline_data = data_loader.load_cityline_data(selected_year or '2025')
        small_areas = None
        if 'smasvaedi' in (active_layers or []) or 'density' in (active_layers or []):
            small_areas = data_loader.load_small_areas()
        
        # Add layers in specific order for proper visibility
        
        # 1. Add base layers first
        if active_layers and 'smasvaedi' in active_layers:
            fig = map_layers.add_small_areas_layer(fig, small_areas)
        
        if active_layers and 'density' in active_layers:
            population_data = data_loader.load_population_data()
            if age_group:
                age_range = f"{age_group} ára"
                population_data = population_data[population_data['aldursflokkur'] == age_range]
            population_data['smasvaedi'] = population_data['smasvaedi'].astype(str).str.zfill(4)
            total_pop = population_data.groupby('smasvaedi')['fjoldi'].sum()
            small_areas = small_areas.copy()
            small_areas.index = small_areas.index.astype(str)
            small_areas['fjoldi'] = 0
            for area_id, pop in total_pop.items():
                if area_id in small_areas.index:
                    small_areas.at[area_id, 'fjoldi'] = pop
            fig = map_layers.add_small_areas_layer(fig, small_areas, show_population=True)
        
        # 2. Add coverage circles if enabled
        if active_layers and 'coverage' in active_layers and radius:
            for _, station in cityline_data.iterrows():
                fig = map_layers.add_radius_circle(fig, station.geometry, radius, station['line'])
        
        # 3. Add affected areas if a station is selected
        if selected_station and affected_areas_json:
            fig = map_layers.add_affected_areas_layer(fig, affected_areas_json)
        
        # 4. Add cityline and stations on top
        if not active_layers or 'cityline' in active_layers:  # Show cityline by default if no layers selected
            fig = map_layers.add_cityline_layer(fig, cityline_data, None, selected_year)
        
        # 5. Add schools last if enabled
        if active_layers and 'schools' in active_layers:
            schools_data = data_loader.load_schools_data()
            fig = map_layers.add_schools_layer(fig, schools_data)
        
        # Preserve interactive state
        fig.update_layout(uirevision=True)
        
        return fig
    except Exception as e:
        print("ERROR UPDATING MAP:", str(e))
        import traceback
        traceback.print_exc()
        sys.stdout.flush()
        return map_layers.create_base_map()

if __name__ == '__main__':
    print("\nStarting Borgarlínan Visualization...")
    print("Access the application at http://localhost:8050")
    print("\nIMPORTANT: When you click a station, debug information will appear here in this terminal.")
    print("\nInitializing application...")
    sys.stdout.flush()
    app.run_server(debug=True, port=8050)
