import plotly.graph_objects as go
import plotly.express as px
import json
import numpy as np
from shapely.geometry import Point, LineString
from src.data_processing.age_groups import calculate_age_group_percentages, format_age_group_info
from src.layers.straeto_layer import add_straeto_layer

class MapLayers:
    def __init__(self):
        self.base_style = "carto-positron"
        self.center = {"lat": 64.11, "lon": -21.90}
        self.default_zoom = 11
        self.line_colors = {
            'red': 'red',
            'blue': 'blue',
            'green': 'green',
            'orange': 'orange',
            'purple': 'purple'
        }
        self.line_sequences = {
            '2025': {
                'red': ['Vatnsendi', 'Salir', 'Lindir', 'Smáralind', 'Hamraborg', 'Sundlaug Kópavogs', 
                       'Bakkabraut', 'HR', 'Landspítalinn', 'BSÍ', 'HÍ', 'Lækjartorg'],
                'blue': ['Egilshöll', 'Spöngin', 'Krossmýrartorg', 'Vogabyggð', 'Laugardalur', 
                        'Hátún', 'Hlemmur']
            },
            '2029': {
                'red': ['Vatnsendi', 'Salir', 'Lindir', 'Smáralind', 'Hamraborg', 'Sundlaug Kópavogs', 
                       'Bakkabraut', 'HR', 'Landspítalinn', 'BSÍ', 'HÍ', 'Lækjartorg'],
                'blue': ['Egilshöll', 'Spöngin', 'Krossmýrartorg', 'Vogabyggð', 'Laugardalur', 
                        'Hátún', 'Hlemmur', 'HÍ', 'BSÍ', 'Lækjartorg'],
                'green': ['Salir', 'Fell', 'Mjódd', 'Vogabyggð', 'Kringlan', 'Landspítalinn', 
                         'BSÍ', 'HÍ', 'Eiðistorg'],
                'orange': ['Norðlingaholt', 'Árbær', 'Kringlan', 'Landspítalinn', 'BSÍ', 
                          'HÍ', 'Lækjartorg', 'Grandi']
            },
            '2030': {
                'red': ['Vatnsendi', 'Salir', 'Lindir', 'Smáralind', 'Hamraborg', 'Sundlaug Kópavogs', 
                       'Bakkabraut', 'HR', 'Landspítalinn', 'BSÍ', 'HÍ', 'Lækjartorg'],
                'blue': ['Egilshöll', 'Spöngin', 'Krossmýrartorg', 'Vogabyggð', 'Laugardalur', 
                        'Hátún', 'Hlemmur', 'HÍ', 'BSÍ', 'Lækjartorg'],
                'green': ['Salir', 'Fell', 'Mjódd', 'Vogabyggð', 'Kringlan', 'Landspítalinn', 
                         'BSÍ', 'HÍ', 'Eiðistorg'],
                'orange': ['Norðlingaholt', 'Árbær', 'Kringlan', 'Landspítalinn', 'BSÍ', 
                          'HÍ', 'Lækjartorg', 'Grandi'],
                'purple': ['Vellir', 'Fjörður', 'Garðabær', 'Hamraborg', 'Kringlan', 'Hátún', 
                          'Hlemmur', 'BSÍ', 'HÍ', 'Lækjartorg']
            }
        }

    def get_polygon_coordinates(self, geometry):
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

    def create_base_map(self):
        """Create the base map with initial settings"""
        fig = go.Figure()
        
        fig.update_layout(
            mapbox=dict(
                style=self.base_style,
                center=self.center,
                zoom=self.default_zoom
            ),
            margin={"r":0,"t":0,"l":0,"b":0},
            showlegend=True,
            height=800
        )
        
        return fig

    def add_schools_layer(self, fig, schools_data):
        """Add schools layer to the map"""
        try:
            if schools_data.empty:
                return fig

            fig.add_trace(go.Scattermapbox(
                mode="markers",
                lon=schools_data.geometry.x,
                lat=schools_data.geometry.y,
                marker=dict(
                    size=5,
                    color='orange',
                    opacity=0.8
                ),
                text=schools_data['Name'],
                name="Schools",
                hovertemplate="<b>%{text}</b><br><extra></extra>",
                showlegend=True
            ))

        except Exception as e:
            print(f"Error adding schools layer: {e}")
            import traceback
            traceback.print_exc()
        return fig

    def add_cityline_layer(self, fig, geojson_data, small_areas_data=None, year='2025'):
        """Add cityline layer to the map"""
        try:
            if geojson_data.empty:
                return fig

            station_coords = {}
            for _, station in geojson_data.iterrows():
                coords = list(station.geometry.coords)[0]
                station_coords[station['name']] = coords

            year_sequences = self.line_sequences.get(year, self.line_sequences['2025'])

            # Add lines first (so they appear under stations)
            for line_color, sequence in year_sequences.items():
                valid_sequence = [s for s in sequence if s in station_coords]
                
                if len(valid_sequence) > 1:
                    line_lons = [station_coords[name][0] for name in valid_sequence]
                    line_lats = [station_coords[name][1] for name in valid_sequence]
                    
                    fig.add_trace(go.Scattermapbox(
                        mode="lines",
                        lon=line_lons,
                        lat=line_lats,
                        line=dict(width=3, color=self.line_colors[line_color]),
                        name=f"{line_color.capitalize()} Line",
                        showlegend=True
                    ))

            # Then add stations on top
            for _, station in geojson_data.iterrows():
                coords = list(station.geometry.coords)[0]
                lines = station['line'].split('/')
                size = 15 if len(lines) > 1 else 10
                color = self.line_colors[lines[0]]
                station_name = station['name']
                
                # Add station marker
                fig.add_trace(go.Scattermapbox(
                    mode="markers+text",
                    lon=[coords[0]],
                    lat=[coords[1]],
                    marker=dict(
                        size=size,
                        color=color,
                        opacity=0.8
                    ),
                    text=[station_name],
                    textposition="top center",
                    name=station_name,
                    customdata=[{
                        'name': station_name,
                        'line': station['line']
                    }],
                    hovertemplate=(
                        "<b>%{text}</b><br>" +
                        "<br>Click for details<extra></extra>"
                    ),
                    showlegend=False
                ))

        except Exception as e:
            print(f"Error adding cityline layer: {e}")
            import traceback
            traceback.print_exc()
        return fig

    def add_radius_circle(self, fig, geometry, radius, line_color='red'):
        """Add a circle showing the coverage radius around a point"""
        try:
            if not geometry or not hasattr(geometry, 'coords'):
                print("Invalid geometry for radius circle")
                return fig

            coords = list(geometry.coords)[0]
            center_point = Point(coords)
            
            theta = np.linspace(0, 2*np.pi, 100)
            radius_in_degrees = radius / 111000
            
            lat_correction = np.cos(np.radians(center_point.y))
            
            circle_lats = center_point.y + radius_in_degrees * np.cos(theta)
            circle_lons = center_point.x + (radius_in_degrees / lat_correction) * np.sin(theta)
            
            if '/' in line_color:
                line_color = line_color.split('/')[0]
            
            base_color = self.line_colors.get(line_color, 'red')
            
            rgb_values = {
                'red': (255, 0, 0),
                'blue': (0, 0, 255),
                'green': (0, 128, 0),
                'orange': (255, 165, 0),
                'purple': (128, 0, 128)
            }
            
            rgb = rgb_values.get(base_color, (255, 0, 0))
            fill_color = f"rgba({rgb[0]},{rgb[1]},{rgb[2]},0.3)"
            
            fig.add_trace(go.Scattermapbox(
                mode="lines",
                lon=circle_lons.tolist(),
                lat=circle_lats.tolist(),
                fill="toself",
                fillcolor=fill_color,
                line=dict(
                    width=1,
                    color=base_color
                ),
                opacity=1,
                name=f"{radius}m Coverage",
                showlegend=False,
                hoverinfo="skip"
            ))
            
        except Exception as e:
            print(f"Error adding radius circle: {e}")
            import traceback
            traceback.print_exc()
        return fig

    def add_affected_areas_layer(self, fig, affected_areas_json):
        """Add affected areas layer with light blue highlight"""
        try:
            if not affected_areas_json or 'features' not in affected_areas_json:
                print("No valid affected areas data")
                return fig
            
            for feature in affected_areas_json['features']:
                if feature['geometry']['type'] == 'Polygon':
                    coords = feature['geometry']['coordinates'][0]
                    lons, lats = zip(*coords)
                    
                    fig.add_trace(go.Scattermapbox(
                        mode="lines",
                        lon=list(lons),
                        lat=list(lats),
                        fill="toself",
                        fillcolor="rgba(135,206,250,0.4)",
                        line=dict(
                            width=1,
                            color="rgba(30,144,255,0.8)"
                        ),
                        name="Affected Area",
                        showlegend=False,
                        hoverinfo="skip"
                    ))
            
        except Exception as e:
            print(f"Error adding affected areas layer: {e}")
            import traceback
            traceback.print_exc()
        return fig

    def add_small_areas_layer(self, fig, small_areas_data, show_population=False):
        """Add small areas layer with outlines"""
        try:
            if small_areas_data.empty:
                print("No small areas data to display")
                return fig

            print(f"Adding small areas layer with {len(small_areas_data)} areas")
            print(f"Sample geometry type: {small_areas_data.geometry.iloc[0].geom_type}")
            
            # Convert GeoDataFrame to GeoJSON for Plotly
            geojson_data = small_areas_data.__geo_interface__
            print(f"GeoJSON features: {len(geojson_data['features'])}")

            if show_population and 'fjoldi' in small_areas_data.columns:
                # Show population density choropleth
                fig.add_trace(go.Choroplethmapbox(
                    geojson=geojson_data,
                    locations=small_areas_data.index,
                    z=small_areas_data['fjoldi'],
                    colorscale='Viridis',
                    marker=dict(
                        opacity=0.7,
                        line=dict(
                            width=2,
                            color='black'
                        )
                    ),
                    name="Population Density",
                    showscale=True,
                    colorbar=dict(
                        title="Population",
                        thickness=15,
                        len=0.5,
                        x=0.95
                    ),
                    hovertemplate=(
                        "<b>Area:</b> %{customdata[0]}<br>" +
                        "<b>Population:</b> %{z}<br>" +
                        "<extra></extra>"
                    ),
                    customdata=[[
                        small_areas_data.at[idx, 'smsv_label']
                    ] for idx in small_areas_data.index]
                ))
            else:
                # Show only outlines
                fig.add_trace(go.Choroplethmapbox(
                    geojson=geojson_data,
                    locations=small_areas_data.index,
                    z=[1] * len(small_areas_data),
                    colorscale=[[0, "rgba(0,0,0,0)"], [1, "rgba(0,0,0,0)"]],  # Transparent fill
                    showscale=False,
                    marker=dict(
                        opacity=1,
                        line=dict(
                            width=2,
                            color='black'
                        )
                    ),
                    name="Small Areas",
                    showlegend=True,
                    hovertemplate=(
                        "<b>Area:</b> %{customdata[0]}<br>" +
                        "<extra></extra>"
                    ),
                    customdata=[[
                        small_areas_data.at[idx, 'smsv_label']
                    ] for idx in small_areas_data.index]
                ))
            
        except Exception as e:
            print(f"Error adding small areas layer: {e}")
            import traceback
            traceback.print_exc()
        return fig

    def update_map_center(self, fig, lat, lon, zoom=None):
        """Update the map center and zoom level"""
        try:
            if zoom is None:
                zoom = self.default_zoom
                
            fig.update_layout(
                mapbox=dict(
                    center=dict(lat=lat, lon=lon),
                    zoom=zoom
                )
            )
        except Exception as e:
            print(f"Error updating map center: {e}")
        return fig
