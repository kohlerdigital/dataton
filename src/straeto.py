import pandas as pd
import folium
from folium import plugins
import json
import os
import numpy as np

def generate_viridis_greens(n):
    """Generate n different shades of green inspired by viridis colormap"""
    if n <= 0:
        return []
    greens = []
    for i in range(n):
        # Create a range of greens from darker (32,89,48) to lighter (119,209,152)
        ratio = i / (n - 1) if n > 1 else 0
        r = int(32 + (119 - 32) * ratio)
        g = int(89 + (209 - 89) * ratio)
        b = int(48 + (152 - 48) * ratio)
        hex_color = f"#{r:02x}{g:02x}{b:02x}"
        greens.append(hex_color)
    return greens

def load_bus_data():
    """Load and process bus stops, routes, and shapes data"""
    try:
        # Read stops data
        stops_df = pd.read_csv('data/raw/bus/stops.txt')
        
        # Read routes data
        routes_df = pd.read_csv('data/raw/bus/routes.txt')
        
        # Read shapes data
        shapes_df = pd.read_csv('data/raw/bus/shapes.txt')
        
        # Clean and process stops data
        stops_df = stops_df[['stop_id', 'stop_name', 'stop_lat', 'stop_lon']]
        stops_df = stops_df.dropna(subset=['stop_lat', 'stop_lon'])
        
        # Process routes data
        routes_df = routes_df[['route_id', 'route_short_name', 'route_long_name']]
        
        # Process shapes data
        shapes_df = shapes_df.sort_values(['shape_id', 'shape_pt_sequence'])
        
        return stops_df, routes_df, shapes_df
    except Exception as e:
        print(f"Error loading bus data: {e}")
        return None, None, None

def add_bus_stops(map_obj, stops_df):
    """Add bus stops to the map with special highlighting for popular stops"""
    if map_obj is None or stops_df is None:
        print("Error: Invalid map object or stops data")
        return map_obj

    try:
        # Create a feature group for bus stops
        stops_group = folium.FeatureGroup(name='Bus Stops')
        
        # Read popular stops data
        try:
            popular_stops_df = pd.read_csv('data/processed/20.csv')
            popular_stop_names = set(popular_stops_df['stop_name'])
            flow_dict = dict(zip(popular_stops_df['stop_name'], 
                               popular_stops_df['Passenger flow in 2023']))
            rank_dict = dict(zip(popular_stops_df['stop_name'], 
                               popular_stops_df['Popularity rating']))
        except Exception as e:
            print(f"Warning: Could not load popular stops data. Error: {e}")
            popular_stop_names = set()
            flow_dict = {}
            rank_dict = {}
        
        # Add each stop as a circle marker
        for _, stop in stops_df.iterrows():
            stop_name = stop['stop_name']
            
            # Check if this stop is popular
            is_popular = any(stop_name.startswith(pop_name) or pop_name.startswith(stop_name) 
                            for pop_name in popular_stop_names)
            
            if is_popular:
                matching_name = next(pop_name for pop_name in popular_stop_names 
                                   if stop_name.startswith(pop_name) or pop_name.startswith(stop_name))
                rank = rank_dict[matching_name]
                radius = 20 - ((rank - 1) * 0.25)
                color = 'black'
                fill_color = '#2d6a3e'  # Medium green from our palette
                weight = 2
                popup_text = (
                    f"<b>{stop_name}</b><br>"
                    f"Daily Passengers: {flow_dict[matching_name]:,}<br>"
                    f"Rank: #{rank}"
                )
            else:
                radius = 6
                color = 'black'
                fill_color = 'white'
                weight = 2
                popup_text = f"{stop_name}"
            
            folium.CircleMarker(
                location=[stop['stop_lat'], stop['stop_lon']],
                radius=radius,
                color=color,
                fill=True,
                fillColor=fill_color,
                fillOpacity=0.6,
                weight=weight,
                popup=folium.Popup(popup_text, parse_html=True)
            ).add_to(stops_group)
        
        # Add the stops group to the map
        stops_group.add_to(map_obj)
        
        # Add legend
        legend_html = """
        <div style="position: fixed; 
                    bottom: 50px; left: 50px; width: 180px;
                    border:2px solid grey; z-index:9999; font-size:14px;
                    background-color:white;
                    padding: 10px;
                    opacity: 0.8;">
            <p><strong>Bus Stops</strong></p>
            <p>
                <svg height="20" width="20">
                    <circle cx="10" cy="10" r="7" stroke="black" stroke-width="2" fill="#2d6a3e"/>
                </svg>
                Popular Stops<br>
                (size indicates rank)
            </p>
            <p>
                <svg height="20" width="20">
                    <circle cx="10" cy="10" r="5" stroke="black" stroke-width="2" fill="white"/>
                </svg>
                Regular Stops
            </p>
        </div>
        """
        map_obj.get_root().html.add_child(folium.Element(legend_html))
        
        return map_obj
    except Exception as e:
        print(f"Error adding bus stops: {e}")
        return map_obj

def add_bus_routes(map_obj, routes_df, shapes_df):
    """Add bus routes to the map using shapes data with viridis green color scheme"""
    if map_obj is None or routes_df is None or shapes_df is None:
        print("Error: Invalid map object or route data")
        return map_obj

    try:
        # Create a feature group for bus routes
        routes_group = folium.FeatureGroup(name='Bus Routes')
        
        # Get unique route IDs and generate colors
        unique_routes = routes_df['route_id'].unique()
        route_colors = generate_viridis_greens(len(unique_routes))
        color_mapping = dict(zip(unique_routes, route_colors))
        
        # Process each shape
        for shape_id, shape_points in shapes_df.groupby('shape_id'):
            try:
                # Extract potential route number from shape_id
                str_shape_id = str(shape_id)
                potential_route_ids = [
                    str_shape_id[:1],
                    str_shape_id[:2],
                    str_shape_id[:3]
                ]
                
                # Find matching route
                for pot_id in potential_route_ids:
                    matching_routes = routes_df[routes_df['route_id'].astype(str) == pot_id]
                    if not matching_routes.empty:
                        route = matching_routes.iloc[0]
                        route_color = color_mapping.get(route['route_id'], '#2d6a3e')  # Default to medium green if no color found
                        
                        coordinates = shape_points[['shape_pt_lat', 'shape_pt_lon']].values.tolist()
                        
                        folium.PolyLine(
                            locations=coordinates,
                            weight=2,
                            color=route_color,
                            opacity=0.7,
                            popup=f"Route {route['route_short_name']}: {route['route_long_name']}"
                        ).add_to(routes_group)
                        break
            
            except Exception as e:
                print(f"Error processing shape {shape_id}: {e}")
                continue
        
        routes_group.add_to(map_obj)
        return map_obj
    except Exception as e:
        print(f"Error adding bus routes: {e}")
        return map_obj

def add_bus_layer(map_obj, show_stops=True, show_routes=True):
    """Main function to add bus information to a map"""
    if map_obj is None:
        print("Error: Invalid map object provided")
        return None

    try:
        # Load data
        stops_df, routes_df, shapes_df = load_bus_data()
        
        if all(df is not None for df in [stops_df, routes_df, shapes_df]):
            # Add routes first (so they appear under stops)
            if show_routes:
                map_obj = add_bus_routes(map_obj, routes_df, shapes_df)
            
            # Add stops on top
            if show_stops:
                map_obj = add_bus_stops(map_obj, stops_df)
        else:
            print("Error: Failed to load required data")
        
        return map_obj
    except Exception as e:
        print(f"Error in add_bus_layer: {e}")
        return map_obj