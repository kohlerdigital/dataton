import json
import geopandas as gpd
import folium
from folium import GeoJson
from shapely.geometry import Point, LineString
import os

def add_bus_lines(map_obj):
    """Add bus lines to an existing Folium map"""
    # Read the JSON data
    with open('data/processed/cityline_2025_4326.geojson', 'r') as f:
        data = json.load(f)

    # Create lists to store points for each line
    red_line_points = []
    blue_line_points = []

    # Sort features by line color and store coordinates
    for feature in data['features']:
        coords = feature['geometry']['coordinates']
        if feature['properties']['line'] == 'red':
            red_line_points.append(coords)
        else:
            blue_line_points.append(coords)

    # Add red line
    red_line = LineString(red_line_points)
    folium.PolyLine(
        locations=[[p[1], p[0]] for p in red_line_points],
        color='red',
        weight=3,
        opacity=0.8
    ).add_to(map_obj)

    # Add blue line
    blue_line = LineString(blue_line_points)
    folium.PolyLine(
        locations=[[p[1], p[0]] for p in blue_line_points],
        color='blue',
        weight=3,
        opacity=0.8
    ).add_to(map_obj)

    # Add markers for stations
    for feature in data['features']:
        coords = feature['geometry']['coordinates']
        name = feature['properties']['name']
        color = feature['properties']['line']
        
        folium.CircleMarker(
            location=[coords[1], coords[0]],
            radius=5,
            color=color,
            fill=True,
            popup=name
        ).add_to(map_obj)

    return map_obj

def create_combined_map():
    # Get the absolute path
    current_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(current_dir)
    geojson_path = os.path.join(parent_dir, 'data/processed/geo', 'capital.json')

    try:
        # First try to read as JSON
        with open(geojson_path, 'r') as f:
            geojson_data = json.load(f)
            
        # Convert to GeoDataFrame
        gdf = gpd.GeoDataFrame.from_features(geojson_data['features'])
        
        # Set the CRS (since we know it's ISN93)
        gdf = gdf.set_crs(epsg=3057, allow_override=True)
        
        # Convert to WGS84 for web mapping
        gdf = gdf.to_crs(epsg=4326)
        
        # Get the center of the data
        center = [gdf.geometry.centroid.y.mean(), gdf.geometry.centroid.x.mean()]
        
        # Create the map
        m = folium.Map(location=center, zoom_start=13)
        
        # Add the zones
        GeoJson(
            gdf.to_json(),
            name='Zones',
            style_function=lambda x: {
                'fillColor': '#3388ff',
                'color': '#000000',
                'weight': 2,
                'fillOpacity': 0.3
            },
            tooltip=folium.GeoJsonTooltip(
                fields=['smsv_label', 'tlsv_label'],
                aliases=['Zone:', 'District:'],
                sticky=True
            )
        ).add_to(m)
        
        # Add bus lines to the same map
        m = add_bus_lines(m)
        
        return m
        
    except FileNotFoundError:
        print(f"File not found. Current directory is: {os.getcwd()}")
        print(f"Directory contents of {os.path.dirname(geojson_path)}:")
        print(os.listdir(os.path.dirname(geojson_path)))
        raise
    except json.JSONDecodeError:
        print("File found but not valid JSON")
        raise
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        raise

if __name__ == "__main__":
    # Create the combined map with both zones and bus lines
    combined_map = create_combined_map()
    combined_map.save('combined_map.html')