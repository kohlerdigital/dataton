import folium
import json
from folium import GeoJson

class CircleHoverMarker(folium.CircleMarker):
    """Custom CircleMarker that shows buffer on hover"""
    def __init__(self, location, radius, popup, color, buffer_radius=400, **kwargs):
        super().__init__(location=location, radius=radius, popup=popup, color=color, **kwargs)
        self.buffer_radius = buffer_radius
        
        # Create and store the buffer circle as an instance attribute
        self._buffer = folium.Circle(
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
    
    @property
    def buffer(self):
        """Property to access the buffer circle"""
        return self._buffer

def create_borgarlina_layer():
    """
    Creates Borgarlína lines and stations layers
    
    Returns:
    tuple: (lines_group, stations_group)
    """
    try:
        # Read the JSON data
        with open('data/processed/cityline_2025_4326.geojson', 'r', encoding='utf-8') as f:
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

        return lines_group, stations_group, stations

    except Exception as e:
        print(f"Error creating Borgarlína layers: {e}")
        raise