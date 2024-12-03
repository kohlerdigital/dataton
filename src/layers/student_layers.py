import pandas as pd
import folium
import branca.colormap as cm

def create_student_layers(gdf):
    """Create layers for student age groups"""
    
    # Define age groups and their labels
    age_groups = {
        'elementary': '6-12 years',
        'middle': '13-15 years',
        'high': '16-19 years'
    }
    
    student_layers = []
    student_colormaps = []
    
    for group_id, group_label in age_groups.items():
        column_name = f'students_{group_id}'
        
        # Check if column exists and has data
        if column_name in gdf.columns and not gdf[column_name].isna().all():
            layer = folium.FeatureGroup(name=f'Students {group_label}')
            
            # Create colormap for this age group
            values = gdf[column_name].dropna()
            if len(values) > 0:
                colormap = cm.LinearColormap(
                    colors=['#fff7ec', '#fee8c8', '#fdd49e', '#fdbb84', '#fc8d59', '#ef6548', '#d7301f', '#990000'],
                    vmin=values.min(),
                    vmax=values.max(),
                    caption=f'Students {group_label}'
                )
                
                # Create GeoJson layer
                folium.GeoJson(
                    gdf,
                    style_function=lambda feature: {
                        'fillColor': colormap(feature['properties'].get(column_name, 0)),
                        'color': 'black',
                        'weight': 1,
                        'fillOpacity': 0.7
                    },
                    tooltip=folium.GeoJsonTooltip(
                        fields=[column_name],
                        aliases=[f'Students {group_label}:'],
                        localize=True,
                        sticky=True
                    )
                ).add_to(layer)
                
                student_layers.append(layer)
                student_colormaps.append(colormap)
                
    return student_layers, student_colormaps