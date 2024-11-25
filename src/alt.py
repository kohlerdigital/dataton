import geopandas as gpd
import folium
from folium import GeoJson
import json
import os
import pandas as pd
import branca.colormap as cm
import numpy as np

def extract_zone_code(label):
    """Extract the numeric code from the end of the zone label."""
    try:
        # Extract the last 4 digits from the label
        code = label.strip().split('-')[-1].strip()
        # Remove leading zeros and return
        return str(int(code))
    except:
        return None

def create_population_map():
    # Get the absolute path
    current_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(current_dir)
    
    # Paths for both files
    geojson_path = os.path.join(parent_dir, 'data/processed/geo', 'capital.json')
    population_path = os.path.join(parent_dir, 'data/processed/habitants', 'summarized_population_2023.csv')
    
    try:
        # Read GeoJSON with UTF-8 encoding
        with open(geojson_path, 'r', encoding='utf-8') as f:
            geojson_data = json.load(f)
            
        # Convert to GeoDataFrame
        gdf = gpd.GeoDataFrame.from_features(geojson_data['features'])
        
        # Read population data
        population_df = pd.read_csv(population_path, encoding='utf-8')
        
        # Process population data:
        # 1. Get the most recent year
        max_year = population_df['ar'].max()
        print(f"Processing data for year: {max_year}")
        
        # 2. Filter for most recent year
        recent_pop = population_df[population_df['ar'] == max_year]
        
        # 3. Group by zone (smasvaedi) and sum population (fjoldi)
        zone_population = recent_pop.groupby('smasvaedi')['fjoldi'].sum().reset_index()
        zone_population['smasvaedi'] = zone_population['smasvaedi'].astype(str)
        
        # Extract numeric codes from GeoJSON labels
        gdf['zone_code'] = gdf['smsv_label'].apply(extract_zone_code)
        
        # Print some sample mappings for verification
        print("\nSample zone mappings (first 5):")
        for label, code in zip(gdf['smsv_label'].head(), gdf['zone_code'].head()):
            print(f"{label} -> {code}")
        
        # Merge GeoDataFrame with population data
        gdf = gdf.merge(
            zone_population,
            how='left',
            left_on='zone_code',
            right_on='smasvaedi'
        )
        
        # Print merge results
        print(f"\nTotal zones: {len(gdf)}")
        print(f"Zones with population data: {len(gdf[gdf['fjoldi'].notna()])}")
        
        # Set the CRS and convert to WGS84
        if gdf.crs is None:
            gdf = gdf.set_crs(epsg=3057, allow_override=True)
        gdf = gdf.to_crs(epsg=4326)
        
        # Calculate center
        bounds = gdf.total_bounds
        center = [(bounds[1] + bounds[3])/2, (bounds[0] + bounds[2])/2]
        
        # Create the map
        m = folium.Map(location=center, zoom_start=11)
        
        # Check if we have any valid population data
        valid_values = gdf['fjoldi'].dropna()
        if len(valid_values) == 0:
            raise ValueError("No valid population data after merging")
            
        # Create color bins
        min_pop = valid_values.min()
        max_pop = valid_values.max()
        bins = np.linspace(min_pop, max_pop, 6)  # 5 categories
        
        # Create color map
        colormap = cm.LinearColormap(
            colors=['#fee5d9', '#fcbba1', '#fc9272', '#fb6a4a', '#de2d26'],
            vmin=min_pop,
            vmax=max_pop,
            caption=f'Population ({max_year})'
        )
        
        # Create a GeoJson layer with the choropleth
        folium.GeoJson(
            gdf.to_json(),
            style_function=lambda feature: {
                'fillColor': colormap(feature['properties']['fjoldi']) 
                    if feature['properties'].get('fjoldi') is not None 
                    else '#CCCCCC',
                'color': 'black',
                'weight': 1,
                'fillOpacity': 0.7
            },
            tooltip=folium.GeoJsonTooltip(
                fields=['smsv_label', 'fjoldi'],
                aliases=['Zone:', 'Population:'],
                localize=True,
                sticky=True
            )
        ).add_to(m)
        
        # Add the colormap to the map
        colormap.add_to(m)
        
        # Add layer control
        folium.LayerControl().add_to(m)
        
        return m
        
    except FileNotFoundError as e:
        print(f"File not found: {str(e)}")
        print(f"Current directory is: {os.getcwd()}")
        raise
    except Exception as e:
        print(f"Error: {str(e)}")
        print("Current working directory:", os.getcwd())
        print("Error details:", str(e))
        raise

if __name__ == "__main__":
    try:
        map_zones = create_population_map()
        map_zones.save('output/population_map.html')
        print("Population map successfully created and saved as 'population_map.html'")
    except Exception as e:
        print(f"Failed to create map: {str(e)}")