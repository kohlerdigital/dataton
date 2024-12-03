import folium
import pandas as pd
import branca.colormap as cm
import os

def create_population_layer(gdf, year=2023):
    try:
        # Read population data
        population_path = os.path.join('data', 'processed', 'habitants', f'summarized_population_{year}.csv')
        population_df = pd.read_csv(population_path, encoding='utf-8')
        
        # Process population data
        max_year = population_df['ar'].max()
        recent_pop = population_df[population_df['ar'] == max_year]
        
        # Create zone_population
        zone_population = recent_pop.groupby('smasvaedi')['fjoldi'].sum().reset_index()
        
        # Ensure both keys are strings
        zone_population['smasvaedi'] = zone_population['smasvaedi'].astype(str).str.zfill(4)
        gdf['zone_code'] = gdf['zone_code'].astype(str).str.zfill(4)
        
        print("\nBefore merge:")
        print("Sample zone_codes:", gdf['zone_code'].head())
        print("Sample smasvaedi:", zone_population['smasvaedi'].head())
        
        # Merge dataframes
        updated_gdf = gdf.merge(
            zone_population,
            left_on='zone_code',
            right_on='smasvaedi',
            how='left'
        )
        
        print("\nAfter merge:")
        print("Number of rows in original GDF:", len(gdf))
        print("Number of rows after merge:", len(updated_gdf))
        print("Sample of merged data:")
        print(updated_gdf[['zone_code', 'smasvaedi', 'fjoldi']].head())
        
        # Create population layer
        population_layer = folium.FeatureGroup(name='Population Density')
        
        # Create color map
        valid_values = updated_gdf['fjoldi'].dropna()
        if len(valid_values) == 0:
            raise ValueError("No valid population data after merging")
            
        colormap = cm.LinearColormap(
            colors=['#440154', '#414487', '#2a788e', '#22a884', '#7ad151', '#fde725'],
            vmin=valid_values.min(),
            vmax=valid_values.max(),
            caption=f'Population ({max_year})'
        )
        
        folium.GeoJson(
            updated_gdf.to_json(),
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
        
        return updated_gdf, population_layer, colormap
        
    except Exception as e:
        print(f"Error in create_population_layer: {e}")
        print("\nGDF columns:", gdf.columns)
        raise