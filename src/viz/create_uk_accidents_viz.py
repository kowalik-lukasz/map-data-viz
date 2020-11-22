import folium
import os
import pandas as pd
import numpy as np
from folium.plugins import HeatMapWithTime

script_dir_path = os.path.dirname(os.path.realpath(__file__))

'''
Load and pre-process the UK accidents data
'''
# Load the accidents data
df_accidents_path = os.path.normpath(os.path.join(script_dir_path, '..', 'data', 'Accidents0515.csv'))
fields = ['Accident_Index', 'Latitude', 'Longitude', 'Date', 'Accident_Severity']
df_accidents = pd.read_csv(df_accidents_path, index_col='Accident_Index', usecols=fields)
print(df_accidents.head())

# Format and sort by date
df_accidents['Date'] = pd.to_datetime(df_accidents['Date'], format='%d/%m/%Y', errors='raise')
print(df_accidents.head())
#df_accidents['Date'] = df_accidents['Date'].dt.strftime('%Y-%m-%d')
df_accidents.sort_values('Date', inplace=True)

# Drop the rows in which there's no lat lon data
df_accidents = df_accidents[df_accidents['Latitude'].notna()]

# Leave only the 2015 accidents
df_accidents = df_accidents[df_accidents['Date'].dt.year == 2015]
print(df_accidents)
#print(df_accidents.groupby('Accident_Severity').count())

# Get the heatmap index values
heatmap_time_dates = df_accidents['Date'].dt.strftime('%Y-%m-%d %A').unique().tolist()

# Get the heatmap data
i = 0
heatmap_time_data = []
for date in heatmap_time_dates:
    df_accidents_daily = df_accidents.loc[df_accidents['Date'] == date]
    heatmap_time_data.append(df_accidents_daily[['Latitude', 'Longitude']].to_numpy().tolist())

'''    
Initialize the map
'''
map_accidents = folium.Map(location=[54, -2.4220],
                           zoom_start=6,
                           max_bounds=True,
                           min_zoom=3,
                           max_lat=60,
                           max_lon=5,
                           min_lat=49,
                           min_lon=-12)

'''
Create the map content and add it to the map object
'''
# Create the HeatMapWithTime
heatmap = HeatMapWithTime(heatmap_time_data, index=heatmap_time_dates, name='Traffic accidents in Great Britain (2015)')
heatmap.add_to(map_accidents)

'''
Save completed map viz to an appropriate folder
'''
map_accidents.save(os.path.join(script_dir_path, 'maps', 'UK_accidents_viz.html'))