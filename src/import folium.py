import geopandas as gpd
import folium
from folium import GeoJson, Choropleth
import json
import os
import pandas as pd
import branca.colormap as cm

def create_zone_map():
    # Get the absolute path
    current_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(current_dir)
    geojson_path = os.path.join(parent_dir, 'data/processed/geo', 'capital.json')
    csv_path = os.path.join(parent_dir, 'data/raw/habitants/', 'ibuafjoldi.csv')
    
    try:
        # Read the GeoJSON data
        with open(geojson_path, 'r') as f:
            geojson_data = json.load(f)
            
        # Convert to GeoDataFrame
        gdf = gpd.GeoDataFrame.from_features(geojson_data['features'])
        
        # Read and process the population data
        df = pd.read_csv(csv_path)
        
        # Convert smasvaedi to string type
        df['smasvaedi'] = df['smasvaedi'].astype(str).str.zfill(4)
        
        # Aggregate total population by zone
        population_by_zone = df.groupby('smasvaedi')['fjoldi'].sum().reset_index()
        population_by_zone.columns = ['smsv_label', 'total_population']  # Rename columns
        
        # Ensure smsv_label in gdf is string
        gdf['smsv_label'] = gdf['smsv_label'].astype(str)
        
        # Merge population data with GeoDataFrame
        gdf = gdf.merge(population_by_zone, on='smsv_label', how='left')
        
        # Fill any NaN values with 0
        gdf['total_population'] = gdf['total_population'].fillna(0)
        
        # Set the CRS and convert to WGS84
        gdf = gdf.set_crs(epsg=3057, allow_override=True)
        gdf = gdf.to_crs(epsg=4326)
        
        # Create a dictionary for population values
        zone_population = population_by_zone.set_index('smsv_label')['total_population'].to_dict()
        
        # Get the center of the data
        center = [gdf.geometry.centroid.y.mean(), gdf.geometry.centroid.x.mean()]
        
        # Create the map
        m = folium.Map(location=center, zoom_start=13)
        
        # Create color map
        colormap = cm.LinearColormap(
            colors=['#fee5d9', '#fcae91', '#fb6a4a', '#de2d26', '#a50f15'],
            vmin=min(zone_population.values()),
            vmax=max(zone_population.values()),
            caption='Population per Zone'
        )
        
        # Define the style function
        def style_function(feature):
            zone_id = feature['properties']['smsv_label']
            population = zone_population.get(zone_id, 0)
            return {
                'fillColor': colormap(population),
                'color': '#000000',
                'weight': 2,
                'fillOpacity': 0.7
            }
        
        # Add the zones with population-based coloring
        GeoJson(
            gdf.to_json(),
            name='Zones',
            style_function=style_function,
            tooltip=folium.GeoJsonTooltip(
                fields=['smsv_label', 'tlsv_label', 'total_population'],
                aliases=['Zone:', 'District:', 'Population:'],
                localize=True,  # Format numbers with local settings
                sticky=True
            )
        ).add_to(m)
        
        # Add the colormap to the map
        colormap.add_to(m)
        
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
    map_zones.save('population_map.html')