# -*- coding: utf-8 -*-
"""borgarlina_ggplot.ipynb

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/1NxUlTN4pT3_uvNUaccPxEPasV8Pdksu-
"""
"""
!pip install contextily
!pip install osmnx
!pip install ipyleaflet
!pip install geopandas matplotlib
!pip install folium
"""

import geopandas as gpd
import pandas as pd
import matplotlib.pyplot as plt

# Load data (assuming file paths are correct)
lina1 = gpd.read_file("cityline_2025.geojson")
pop = pd.read_csv("ibuafjoldi.csv")
smallarea = gpd.read_file("smasvaedi_2021.json")
dwellings = pd.read_csv("ibudir.csv")

# Reproject to WGS 84
lina1 = lina1.to_crs(epsg=4326)
smallarea = smallarea.to_crs(epsg=4326)

# Data processing
pop['smasvaedi'] = pop['smasvaedi'].astype(str).str.zfill(4)
pop2024 = pop[(pop['ar'] == 2024) & (pop['aldursflokkur'] == "10-14 ára") & (pop['kyn'] == 1)]
all_dwellings = dwellings[dwellings['framvinda'] == "Fullbúið"].groupby('smasvaedi')['Fjöldi'].sum().reset_index()
pop2024_smallarea = pd.merge(smallarea, pop2024, left_on='smsv', right_on='smasvaedi', how='left')
all_dwellings_smallarea = pd.merge(smallarea, all_dwellings, left_on='fid', right_on='smasvaedi', how='left')

# Create maps
fig, ax = plt.subplots(1, 1, figsize=(10, 10)) # Adjust figsize as needed
pop2024_smallarea[pop2024_smallarea['nuts3'] == "001"].plot(column='fjoldi', ax=ax, legend=True, cmap='viridis') # Customize cmap
lina1.plot(ax=ax, facecolor='none', edgecolor='black')
ax.set_title("Population Map") # Add title
plt.show()

fig, ax = plt.subplots(1, 1, figsize=(10, 10))
all_dwellings_smallarea[all_dwellings_smallarea['nuts3'] == "001"].plot(column='Fjöldi', ax=ax, legend=True, cmap='viridis')
lina1.plot(ax=ax, facecolor='none', edgecolor='black')
ax.set_title("Dwellings Map")

plt.show()
