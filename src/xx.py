import json
import pandas as pd
import geopandas as gpd
from shapely.geometry import Point, LineString
import folium

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

# Create a map centered on Reykjavik
m = folium.Map(location=[64.13, -21.85], zoom_start=12)

# Add red line
red_line = LineString(red_line_points)
folium.PolyLine(
    locations=[[p[1], p[0]] for p in red_line_points],
    color='red',
    weight=3,
    opacity=0.8
).add_to(m)

# Add blue line
blue_line = LineString(blue_line_points)
folium.PolyLine(
    locations=[[p[1], p[0]] for p in blue_line_points],
    color='blue',
    weight=3,
    opacity=0.8
).add_to(m)

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
    ).add_to(m)

# Save the map
m.save('reykjavik_bus_lines.html')