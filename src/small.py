import geopandas as gpd
import folium
from folium import GeoJson
import json
import os

def create_zone_map():
    # Read the GeoJSON file from the correct path
    geojson_path = '../data/smasvaedi_2021.json'
    
    # Create a GeoDataFrame from the GeoJSON file
    gdf = gpd.read_file(geojson_path)
    
    # Convert from ISN93 to WGS84 (EPSG:4326) which is required for web mapping
    gdf = gdf.set_crs(epsg=3057, allow_override=True)  # Set the original CRS (ISN93)
    gdf = gdf.to_crs(epsg=4326)  # Convert to WGS84
    
    # Get the center of the data for map initialization
    center = [gdf.geometry.centroid.y.mean(), gdf.geometry.centroid.x.mean()]
    
    # Create a base map centered on the data
    m = folium.Map(location=center, zoom_start=13)
    
    # Style function for the zones
    def style_function(feature):
        return {
            'fillColor': '#3388ff',
            'color': '#000000',
            'weight': 2,
            'fillOpacity': 0.3
        }
    
    # Add the zones to the map with tooltips
    GeoJson(
        gdf.to_json(),
        name='Zones',
        style_function=style_function,
        tooltip=folium.GeoJsonTooltip(
            fields=['smsv_label', 'tlsv_label', 'smsv'],
            aliases=['Zone Name:', 'District:', 'Zone ID:'],
            sticky=True
        )
    ).add_to(m)
    
    # Add layer control
    folium.LayerControl().add_to(m)
    
    return m

def add_points_to_map(map_object, points_data):
    """
    Add points to the existing map
    
    points_data should be a list of dictionaries with format:
    [
        {
            'location': [y, x],  # Coordinates in ISN93
            'popup': 'Point description',
            'tooltip': 'Point name'
        },
        ...
    ]
    """
    # Create a temporary GeoDataFrame to convert point coordinates
    if points_data:
        points_gdf = gpd.GeoDataFrame(
            points_data,
            geometry=gpd.points_from_xy([p['location'][1] for p in points_data], 
                                      [p['location'][0] for p in points_data]),
            crs='EPSG:3057'
        )
        # Convert to WGS84
        points_gdf = points_gdf.to_crs('EPSG:4326')
        
        # Add points to map
        for idx, point in points_gdf.iterrows():
            folium.CircleMarker(
                location=[point.geometry.y, point.geometry.x],
                radius=8,
                popup=points_data[idx]['popup'],
                tooltip=points_data[idx]['tooltip'],
                color='red',
                fill=True,
                fill_color='red'
            ).add_to(map_object)
    
    return map_object

# Example usage
if __name__ == "__main__":
    # Create the base map with zones
    map_zones = create_zone_map()
    
    # Example points in ISN93 coordinates
    points = [
        {
            'location': [408197.924, 356204.443],  # [y, x] in ISN93
            'popup': 'Point 1 Description',
            'tooltip': 'Point 1'
        }
    ]
    
    # Add points to the map
    map_zones = add_points_to_map(map_zones, points)
    
    # Save the final map
    map_zones.save('zones_and_points_map.html')