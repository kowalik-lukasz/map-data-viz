import folium
import branca.colormap as cm
import os
import pandas as pd
import geopandas as gpd
import numpy as np
import json
import time
from datetime import datetime
from folium.plugins import TimeSliderChoropleth
from branca.element import Template, MacroElement
import utils

script_dir_path = os.path.dirname(os.path.realpath(__file__))
pd.set_option('display.max_rows', None)

'''
Load and pre-process the geojson file
'''
geojson_path = os.path.normpath(os.path.join(script_dir_path, '..', 'data', 'borders_geo.json'))
world_geojson = gpd.read_file(geojson_path)
world_geojson.drop(columns=['ISO_A2', 'ADMIN'], inplace=True)
world_geojson.drop(world_geojson[world_geojson['ISO_A3'] == '-99'].index, inplace=True)
country_list = world_geojson['ISO_A3'].tolist()

'''
Load and pre-process the GDP data
'''
# Load the GDP data
df_GDP_path = os.path.normpath(os.path.join(script_dir_path, '..', 'data', 'GDP_per_capita_world_data.csv'))
df_GDP = pd.read_csv(df_GDP_path, index_col='Country Code', skiprows=4)

# Drop unnecessary data
df_GDP.drop(labels='2020', axis=1, inplace=True)  

csv_country_list = df_GDP.index.tolist()
country_list = list(set(country_list).intersection(csv_country_list))
df_GDP.drop(df_GDP[~df_GDP.index.isin(country_list)].index, inplace=True)
world_geojson.drop(world_geojson[~world_geojson['ISO_A3'].isin(country_list)].index, inplace=True)
print(df_GDP)
print(world_geojson)
print(len(world_geojson.index))
print(country_list)
country_list.sort()

# Create an enumerated country dict for id mapping
country_dict = {k: v for v, k in enumerate(country_list)}
world_geojson['country_id']=world_geojson['ISO_A3'].map(country_dict)
print(country_dict)
print(world_geojson)

# Count min and max GDP values
min_GDP_val, max_GDP_val = df_GDP[df_GDP.columns[4:]].min().min(), df_GDP[df_GDP.columns[4:]].max().max()
print(min_GDP_val, max_GDP_val)

# Create a color list

color_list = [
        '#808080','#A50026','#D73027','#F46D43','#FDAE61','#FEE08B','#FFFFBF','#D9EF8B','#A6D96A','#66BD63','#1A9850','#006837'
    ]

# Create a list of geometrically spaced numbers over a min-max interval
bins = np.geomspace(min_GDP_val, max_GDP_val, 12)

# Replace NaNs (records with no data available) with '-1'
df_GDP.fillna(-1, inplace=True)

# Add NaN category to the bins
bins = np.insert(bins, 0, -1.)
bins = bins.tolist()
print(bins)

# Append 'color_[year]' columns to the GDP DataFrame
year = 1960
while year <= 2019:
    pasted_col_id = df_GDP.columns.get_loc(str(year)) + 1
    col_value = pd.cut(df_GDP[str(year)], bins, include_lowest=True, labels = [
        '#808080','#A50026','#D73027','#F46D43','#FDAE61','#FEE08B','#FFFFBF','#D9EF8B','#A6D96A','#66BD63','#1A9850','#006837'
    ])
    df_GDP.insert(loc=pasted_col_id, column='color_'+str(year), value=col_value)
    year += 1 

print(df_GDP)

'''
Create appropriately formatted dictionary that the TimeSliderChoropleth will receive as an input
'''
gdp_dict = {}
for country_code in df_GDP.index.tolist():
    country_id = str(country_dict[country_code]) 
    gdp_dict[country_id] = {}
    year = 1960
    while year <= 2019:
        dt_obj = datetime(year=year, month=12, day=31)
        year_in_ms = str(time.mktime(dt_obj.timetuple()))
        color_hex = df_GDP.at[country_code, 'color_'+str(year)]
        gdp_dict[country_id][year_in_ms] = {'color':color_hex, 'opacity':0.7} 
        year += 1

print(list(gdp_dict.items())[10])
with open(os.path.join(script_dir_path, '..', 'data', 'styledict.json'), 'w') as outfile:
    json.dump(gdp_dict, outfile)
    
with open(os.path.join(script_dir_path, '..', 'data', 'data.json'), 'w') as outfile:
    json.dump(world_geojson.to_json(), outfile)
    
''' 
Initialize the map
'''
map_GDP = folium.Map(location=[0, 0], zoom_start=4, max_bounds=True, min_zoom=3)    

'''
Create the map content and add it to the map object
'''
# Create the choropleth
choropleth = TimeSliderChoropleth(
    world_geojson.set_index('country_id').to_json(),
    styledict=gdp_dict
).add_to(map_GDP)

# Create the map legend
legend_labels_dict = {}
i = 0
for color in color_list:
    if i == 0:
        legend_labels_dict[color_list[i]] = 'No data'
    elif i == len(color_list) - 1:
        legend_labels_dict[color_list[i]] = '> ' + str(round(bins[i], 2)) + '$'
        break
    else:         
        legend_labels_dict[color] = str(round(bins[i], 2)) + '$' + ' - ' + str(round(bins[i+1], 2)) + '$'
    i += 1

print(legend_labels_dict)
template = utils.create_legend(caption='GDP per capita in USD', legend_labels=legend_labels_dict)
macro = MacroElement()
macro._template = Template(template)
map_GDP.get_root().add_child(macro)

'''
Save completed map viz to an appropriate folder
'''
map_GDP.save(os.path.join(script_dir_path, 'maps', 'GDP_viz.html'))