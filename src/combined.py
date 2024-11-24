import geopandas as gpd
import folium
from folium import GeoJson
import json
import os
import pandas as pd
import branca.colormap as cm
import numpy as np
from shapely.geometry import Point, LineString
import folium.plugins
import straeto

class CircleHoverMarker(folium.CircleMarker):
    """Custom CircleMarker that shows buffer on hover"""
    def __init__(self, location, radius, popup, color, buffer_radius=400, **kwargs):
        super().__init__(location=location, radius=radius, popup=popup, color=color, **kwargs)
        self.buffer_radius = buffer_radius
        
        # Create the buffer circle
        self.buffer = folium.Circle(
            location=location,
            radius=buffer_radius,
            color='red',
            fill=True,
            opacity=0.4,
            fill_opacity=0.2,
            weight=1,
            className=f'buffer-{hash(str(location))}'
        )
        
        # Add hover JavaScript
        self.hover_js = f"""
            <script>
                var circle = document.querySelector('.buffer-{hash(str(location))}');
                circle.style.display = 'none';
                var marker = document.querySelector('#{self.get_name()}');
                marker.addEventListener('mouseover', function() {{
                    circle.style.display = 'block';
                }});
                marker.addEventListener('mouseout', function() {{
                    circle.style.display = 'none';
                }});
            </script>
        """

def add_borgarlina_lines(map_obj):
    """Add Borgarlína lines and stations with hover buffers to an existing Folium map"""
    try:
        # Read the JSON data
        with open('data/processed/cityline_2025_4326.geojson', 'r') as f:
            data = json.load(f)

        # Create lists to store points for each line
        red_line_points = []
        blue_line_points = []
        stations = []

        # Sort features by line color and store coordinates
        for feature in data['features']:
            coords = feature['geometry']['coordinates']
            if feature['properties']['line'] == 'red':
                red_line_points.append(coords)
            else:
                blue_line_points.append(coords)
            stations.append({
                'coords': coords,
                'name': feature['properties']['name'],
                'color': feature['properties']['line']
            })

        # Create feature groups
        lines_group = folium.FeatureGroup(name='Borgarlína Lines')
        stations_group = folium.FeatureGroup(name='Borgarlína Stations')

        # Add red line
        if red_line_points:
            folium.PolyLine(
                locations=[[p[1], p[0]] for p in red_line_points],
                color='red',
                weight=4,
                opacity=0.8
            ).add_to(lines_group)

        # Add blue line
        if blue_line_points:
            folium.PolyLine(
                locations=[[p[1], p[0]] for p in blue_line_points],
                color='blue',
                weight=4,
                opacity=0.8
            ).add_to(lines_group)

        # Add stations with hover buffers
        for station in stations:
            marker = CircleHoverMarker(
                location=[station['coords'][1], station['coords'][0]],
                radius=6,
                popup=station['name'],
                color=station['color'],
                fill=True,
                weight=2
            )
            marker.add_to(stations_group)
            marker.buffer.add_to(stations_group)
            
            # Add the hover JavaScript to the map
            map_obj.get_root().header.add_child(folium.Element(marker.hover_js))

        # Add groups to map in correct order
        lines_group.add_to(map_obj)
        stations_group.add_to(map_obj)

        return map_obj
    except Exception as e:
        print(f"Error adding Borgarlína lines: {e}")
        return map_obj

def create_combined_map():
    try:
        # Get file paths
        current_dir = os.path.dirname(os.path.abspath(__file__))
        parent_dir = os.path.dirname(current_dir)
        geojson_path = os.path.join(parent_dir, 'data/processed/geo', 'capital.json')
        population_path = os.path.join(parent_dir, 'data/processed/habitants', 'summarized_population_2023.csv')
        
        # Read data files
        with open(geojson_path, 'r', encoding='utf-8') as f:
            geojson_data = json.load(f)
                
        # Convert to GeoDataFrame
        gdf = gpd.GeoDataFrame.from_features(geojson_data['features'])
        population_df = pd.read_csv(population_path, encoding='utf-8')
        
        # Process population data
        max_year = population_df['ar'].max()
        recent_pop = population_df[population_df['ar'] == max_year]
        zone_population = recent_pop.groupby('smasvaedi')['fjoldi'].sum().reset_index()
        zone_population['smasvaedi'] = zone_population['smasvaedi'].astype(str)
        
        # Extract codes and merge data
        gdf['zone_code'] = gdf['smsv_label'].apply(lambda x: str(int(x.strip().split('-')[-1].strip())))
        gdf = gdf.merge(
            zone_population,
            how='left',
            left_on='zone_code',
            right_on='smasvaedi'
        )
        
        # Set CRS and convert to WGS84
        if gdf.crs is None:
            gdf = gdf.set_crs(epsg=3057, allow_override=True)
        gdf = gdf.to_crs(epsg=4326)
        
        # Calculate map center
        bounds = gdf.total_bounds
        center = [(bounds[1] + bounds[3])/2, (bounds[0] + bounds[2])/2]
        
        # Create base map
        m = folium.Map(location=center, zoom_start=11)
        
        # Create population choropleth layer
        valid_values = gdf['fjoldi'].dropna()
        if len(valid_values) == 0:
            raise ValueError("No valid population data after merging")
        
        # Create color map
        colormap = cm.LinearColormap(
            colors=['#440154', '#414487', '#2a788e', '#22a884', '#7ad151', '#fde725'],  # Viridis color scheme
            vmin=valid_values.min(),
            vmax=valid_values.max(),
            caption=f'Population ({max_year})'
        )
        
        # Add population choropleth
        population_layer = folium.FeatureGroup(name='Population Density')
        folium.GeoJson(
            gdf.to_json(),
            style_function=lambda feature: {
                'fillColor': colormap(feature['properties']['fjoldi']) 
                    if feature['properties'].get('fjoldi') is not None 
                    else '#CCCCCC',
                'color': 'black',
                'weight': 1,
                'fillOpacity': 0.2
            },
            tooltip=folium.GeoJsonTooltip(
                fields=['smsv_label', 'fjoldi'],
                aliases=['Zone:', 'Population:'],
                localize=True,
                sticky=True
            )
        ).add_to(population_layer)
        
        # Add layers to map in correct order
        population_layer.add_to(m)
        colormap.add_to(m)
        
        # Add bus routes and stops first (removed show_labels parameter)
        m = straeto.add_bus_layer(m, show_stops=True, show_routes=True)
        
        # Add Borgarlína on top
        m = add_borgarlina_lines(m)
        
        # Add layer control
        folium.LayerControl().add_to(m)
        
        return m
    except Exception as e:
        print(f"Error creating combined map: {e}")
        raise

if __name__ == "__main__":
    try:
        combined_map = create_combined_map()
        combined_map.save('combined_map.html')
        print("Combined map successfully created and saved as 'combined_map.html'")
    except Exception as e:
        print(f"Failed to create map: {e}")