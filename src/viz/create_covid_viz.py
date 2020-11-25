import folium
import os
import requests
import utils
import glob
import json
import pandas as pd
import numpy as np
import geopandas as gpd
import branca.colormap as cm
from branca.element import MacroElement
from jinja2 import Template

# Important paths
script_dir_path = os.path.dirname(os.path.realpath(__file__))
data_dir_path = os.path.join(script_dir_path, '..', 'data')
geojson_path = os.path.normpath(os.path.join(script_dir_path, '..', 'data', 'borders_geo.json'))
newest_dataset = glob.glob(os.path.join(data_dir_path, 'covid*'))[0]

# Color palettes
color_dict = {
    'Confirmed': ['#808080','#fff7fb','#ece7f2','#d0d1e6','#a6bddb','#74a9cf','#3690c0','#0570b0','#045a8d','#023858'],
    'Deaths': ['#808080','#fff7ec','#fee8c8','#fdd49e','#fdbb84','#fc8d59','#ef6548','#d7301f','#b30000','#7f0000'],
    'Active': ['#808080','#fff7f3','#fde0dd','#fcc5c0','#fa9fb5','#f768a1','#dd3497','#ae017e','#7a0177','#49006a'],
    'Incident_Rate': ['#808080','#fcfbfd','#efedf5','#dadaeb','#bcbddc','#9e9ac8','#807dba','#6a51a3','#54278f','#3f007d'],
    'Case_Fatality_Ratio': ['#808080','#fff5f0','#fee0d2','#fcbba1','#fc9272','#fb6a4a','#ef3b2c','#cb181d','#a50f15','#67000d']
}

# pandas options
pd.set_option('display.max_rows', None)

def download_covid_data():
    '''
    Download the latest JHU CSSE COVID-19 dataset from github
    '''
    # Get information on the newest dataset currently available
    folder_url = 'https://api.github.com/repos/CSSEGISandData/COVID-19/contents/csse_covid_19_data/csse_covid_19_daily_reports'
    try:
        req = requests.get(folder_url)
    except:
        print('Could not get data from requested URL')
        return
        
    if req.status_code == 200:
        req = req.json()
    else:
        print('Could not get data from requested URL')
        return
    
    global newest_dataset
    newest_dataset = req[-2]['name']
    print('Latest available dataset: ' + newest_dataset)

    # Check if the newest available dataset on github is newer than the one currently possesed
    download_url = 'https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_daily_reports/' + newest_dataset
    try:
        utils.download_file(download_url=download_url, location=data_dir_path, 
                            filename='covid_' + newest_dataset)
        covid_old_csv = glob.glob(os.path.join(data_dir_path, 'covid*'))
        for filename in covid_old_csv:
            if newest_dataset in filename:
                covid_old_csv.remove(filename)
        for filename in covid_old_csv:
            os.remove(filename)
            
    except Exception as e:
        print(str(e) + '\nCould not fetch newest dataset. Aborting the viz update.')
        return

def create_covid_viz():    
    '''
    Load and pre-process the geojson file
    '''
    world_geojson = gpd.read_file(geojson_path)
    world_geojson.drop(columns=['ISO_A2'], inplace=True)
    
    '''
    Load and pre-process the COVID-19 data
    '''
    # Load the COVID-19 data
    # df_covid_path = os.path.join(data_dir_path, 'covid_' + newest_dataset)
    df_covid = pd.read_csv(newest_dataset)
    print(df_covid.head())
    print(df_covid['Last_Update'][0])
    timestamp = df_covid['Last_Update'][0]
    
    # Replace some country names
    df_covid.replace(to_replace={'Country_Region' : 'US'}, value='United States of America', inplace=True)
    df_covid.replace(to_replace={'Country_Region' : 'Bahamas'}, value='The Bahamas', inplace=True)
    df_covid.replace(to_replace={'Country_Region' : 'Congo (Brazzaville)'}, value='Republic of Congo', inplace=True)
    df_covid.replace(to_replace={'Country_Region' : 'Congo (Kinshasa)'}, value='Democratic Republic of the Congo', inplace=True)
    df_covid.replace(to_replace={'Country_Region' : 'Taiwan*'}, value='Taiwan', inplace=True)
    df_covid.replace(to_replace={'Country_Region' : "Cote d'Ivoire"}, value='Ivory Coast', inplace=True)
    df_covid.replace(to_replace={'Country_Region' : "Czechia"}, value='Czech Republic', inplace=True)
    world_geojson.replace(to_replace={'ADMIN' : 'Macedonia'}, value='North Macedonia', inplace=True)
    
    # Change the name of 'ADMIN' column in the geojson DF to match the one in COVID DF
    world_geojson.rename(columns={'ADMIN': 'Country_Region'}, inplace=True)
    
    # Aggregate the data for countries that have regional information
    df_covid_agg = df_covid.groupby('Country_Region').agg({'Confirmed': 'sum', 'Deaths': 'sum', 'Recovered': 'sum',
                                 'Active': 'sum', 'Incident_Rate': 'mean', 'Case_Fatality_Ratio': 'mean'})
    #df_covid_sum = df_covid.groupby('Country_Region', as_index=False).sum()
    world_geojson = world_geojson.sort_values('Country_Region').reset_index(drop=True)
    print(df_covid_agg)
    print(world_geojson)
    
    # Join the geojson with the DataFrame
    df_covid_joined = df_covid_agg.merge(world_geojson, how='right', on='Country_Region')
    print(df_covid_joined)
    
    # Count min and max values for specific columns
    min_dict, max_dict = {}, {}
    column_names = ['Confirmed', 'Deaths', 'Active', 'Incident_Rate', 'Case_Fatality_Ratio']
    for name in column_names:
        min_dict[name] = min(df_covid_joined[name])
        max_dict[name] = max(df_covid_joined[name])
    
    # Replace NaNs in the DataFrame with '-1'
    df_covid_joined.fillna(-1, inplace=True)
    
    # Add the data columns to geo json for future popup displaying
    world_geojson = world_geojson.assign(Confirmed=df_covid_joined['Confirmed'],
                                         Deaths=df_covid_joined['Deaths'],
                                         Active=df_covid_joined['Active'],
                                         Incident_Rate=df_covid_joined['Incident_Rate'],
                                         Case_Fatality_Ratio=df_covid_joined['Case_Fatality_Ratio'])
    print(world_geojson)
    
    # Set the correct index columns
    df_covid_joined.set_index('Country_Region', inplace=True)
    
    # Create a lists of evenly spaced attribute values over computed min-max intervals and assign corresponding colors to the DataFrame
    colormap_dict = {}
    bins = []
    for name in column_names:
        # Work-around for geometric space not accepting zeros in the sequence
        tmp_min = min_dict[name]
        if min_dict[name] < 1:
            min_dict[name] = 1
        
        inner_bins = np.geomspace(start=min_dict[name], stop=max_dict[name], num=10)
        min_dict[name] = tmp_min
        inner_bins = np.delete(inner_bins, 0)
        inner_bins = np.insert(inner_bins, 0, min_dict[name])
        inner_bins = np.insert(inner_bins, 0, -1.)
        inner_bins = inner_bins.tolist()
        
        # Round the inner_bins values before appending to the bins list
        if name in ['Confirmed', 'Deaths', 'Active']:
            inner_bins = [int(round(bin, 0)) for bin in inner_bins]
        else:
            inner_bins = [round(bin, 2) for bin in inner_bins]
        
        bins.append(inner_bins)
        colormap_dict[name] = cm.StepColormap(colors=color_dict[name], index=inner_bins, vmin=min_dict[name], vmax=max_dict[name])
        df_covid_joined[name+'_color'] = df_covid_joined[name].map(lambda x: colormap_dict[name].rgb_hex_str(x))
    
    ''' 
    Initialize the map
    '''
    map_covid = folium.Map(location=[0, 0], zoom_start=4, max_bounds=True, tiles=None)
    base_map = folium.FeatureGroup(name='Basemap', overlay=True, control=False)
    folium.TileLayer(min_zoom=3, tiles='OpenStreetMap').add_to(base_map)
    base_map.add_to(map_covid) 
    
    '''
    Create the content of the map
    '''
    # Create FeatureGroups to group the data
    feature_groups = []
    for category, _ in color_dict.items():
        group = folium.FeatureGroup(category, overlay=False)
        feature_groups.append(group)
    
    # Create the choropleths
    choropleth_confirmed = folium.GeoJson(data=world_geojson,
                                          zoom_on_click=False,
                                          name='Confirmed Cases',
                                          style_function=lambda x: {
                                              'fillColor': df_covid_joined['Confirmed_color'][x['properties']['Country_Region']],
                                              'fillOpacity': 0.7,
                                              'color': 'black',
                                              'weight': 0.5
                                          }).add_to(feature_groups[0])
    popup_confirmed = folium.GeoJsonPopup(fields=['Country_Region', 'Confirmed'], labels=False).add_to(choropleth_confirmed)
    
    choropleth_deaths = folium.GeoJson(data=world_geojson,
                                       name='Deaths',
                                       style_function=lambda x: {
                                           'fillColor': df_covid_joined['Deaths_color'][x['properties']['Country_Region']],
                                           'fillOpacity': 0.7,
                                           'color': 'black',
                                           'weight': 1
                                        }).add_to(feature_groups[1])
    popup_deaths = folium.GeoJsonPopup(fields=['Country_Region', 'Deaths'], labels=False).add_to(choropleth_deaths)
    
    choropleth_active = folium.GeoJson(data=world_geojson,
                                       name='Active Cases',
                                       style_function=lambda x: {
                                           'fillColor': df_covid_joined['Active_color'][x['properties']['Country_Region']],
                                           'fillOpacity': 0.7,
                                           'color': 'black',
                                           'weight': 1
                                        }).add_to(feature_groups[2])
    popup_active = folium.GeoJsonPopup(fields=['Country_Region', 'Active'], labels=False).add_to(choropleth_active)
    
    choropleth_incident_rate = folium.GeoJson(data=world_geojson,
                                              name='Incident Rate',
                                              style_function=lambda x: {
                                                  'fillColor': df_covid_joined['Incident_Rate_color'][x['properties']['Country_Region']],
                                                  'fillOpacity': 0.7,
                                                  'color': 'black',
                                                  'weight': 1
                                                  }).add_to(feature_groups[3])
    popup_incident_rate = folium.GeoJsonPopup(fields=['Country_Region', 'Incident_Rate'], labels=False).add_to(choropleth_incident_rate)
    
    
    choropleth_case_fatality_ratio = folium.GeoJson(data=world_geojson,
                                                     name='Case Fatality Ratio',
                                                     style_function=lambda x: {
                                                         'fillColor': df_covid_joined['Case_Fatality_Ratio_color'][x['properties']['Country_Region']],
                                                         'fillOpacity': 0.7,
                                                         'color': 'black',
                                                         'weight': 1
                                                         }).add_to(feature_groups[4])
    popup_case_fatality_ratio = folium.GeoJsonPopup(fields=['Country_Region', 'Case_Fatality_Ratio'], labels=False).add_to(choropleth_case_fatality_ratio)
    
    # Create the map legends templates
    legend_str_dict = {}
    for i, (k, v) in enumerate(color_dict.items()):
        legend_labels_dict = {}
        j = 0
        for color in v:
            if j == 0:
                legend_labels_dict[color] = 'No data'
            elif j == len(v) - 1:
                legend_labels_dict[color] = '> ' + str(bins[i][j])
                break
            else:
                legend_labels_dict[color] = str(bins[i][j]) + ' - ' + str(bins[i][j+1])
            j += 1
        legend_str_dict[k] = legend_labels_dict
    
    print(legend_str_dict)    
    template = utils.create_legend(caption='COVID-19 status as of: ' +str(timestamp), legend_labels=legend_str_dict)
    macro = MacroElement()
    macro._template = Template(template)
    map_covid.get_root().add_child(macro)
    # Create the macros for map legends    
    # legends_arr = []
    # for legend in legends_str_arr:   
    #     macro = MacroElement()
    #     macro._name = 'Temp'
    #     macro._template = Template(legend)
    #     legends_arr.append(macro)
        # map_covid.get_root().add_child(macro)
    
        
    # for i, legend in enumerate(legends_arr, start=0):
    #     legend.add_to(feature_groups[i])
    
    for feature_group in feature_groups:
        feature_group.add_to(map_covid)

    # Add the colormaps to the map object
    # for category in column_names:
    #     colormap_dict[category].add_to(map_covid)
        
    # Bind choropleths with corresponding colormaps    
    # utils.BindColormap(choropleth_confirmed, legends_arr[0]).add_to(map_covid)
    # utils.BindColormap(choropleth_active, legends_arr[1]).add_to(map_covid)
    # utils.BindColormap(choropleth_deaths, legends_arr[2]).add_to(map_covid)
    # utils.BindColormap(choropleth_incident_rate, legends_arr[3]).add_to(map_covid)
    # utils.BindColormap(choropleth_case_fatality_ratio, legends_arr[4]).add_to(map_covid)
    
    # Activate Layer Control
    folium.LayerControl(collapsed=True).add_to(map_covid)
    
    '''
    Save completed map viz to an appropriate folder
    '''
    map_covid.save(os.path.join(script_dir_path, 'maps', 'COVID-19_viz.html'))
    
if __name__ == '__main__':
    create_covid_viz()