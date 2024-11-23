import geopandas as gpd
import folium
from folium import GeoJson
import json
import os

def create_zone_map():
    # Get the absolute path
    current_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(current_dir)
    geojson_path = os.path.join(parent_dir, 'data/processed/geo', 'capital.json')

    # Debug: Print the path
    print(f"Looking for file at: {geojson_path}")
    
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
    map_zones = create_zone_map()
    map_zones.save('map.html')