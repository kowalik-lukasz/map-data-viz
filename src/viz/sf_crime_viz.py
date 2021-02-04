import os
import requests
import utils
import glob
import pandas as pd
import folium
from branca.element import Template, MacroElement
from folium.plugins import MarkerCluster
from config import *
from sodapy import Socrata
from datetime import datetime, timedelta

script_dir_path = os.path.dirname(os.path.realpath(__file__))
data_dir_path = os.path.join(script_dir_path, '..', 'data')
pd.set_option('display.max_rows', None)

def download_sf_crime_data():
    '''
    Download the latest San Francisco Police Department Incident Reports dataset
    '''
    # Setting up the Socrata API client    
    client = Socrata('data.sfgov.org', sf_data_token)
    
    # Subtracting a day from the current timestamp, since the data updates introduce yesterday's data
    current_timestamp = datetime.now() - timedelta(days=1)
    week_before = current_timestamp - timedelta(weeks=1)
    current_timestamp = current_timestamp.strftime('%Y-%m-%d')
    week_before = week_before.strftime('%Y-%m-%d')
    where_clause = 'incident_date between \''  + str(week_before) + 'T00:00:00.000\' and \'' + str(current_timestamp) + 'T00:00:00.000\' ' 
    
    # Getting the data with Socrata API and applying an SoQL clause to the downloaded .json
    try:  
        results = client.get('wg3w-h783', where=where_clause, limit=100000)
    except Exception as e:
        print(str(e) + '\nCould not fetch newest dataset.')
        return
    df_results = pd.DataFrame.from_records(results)
    df_results.to_csv(os.path.join(data_dir_path, 'last_week_SF_crimes.csv'))
    print(df_results) 

def create_sf_crime_viz():
    '''
    Load and pre-process the San Francisco crime data
    '''
    # Load the crime data
    df_crime = pd.read_csv(os.path.join(data_dir_path, 'last_week_SF_crimes.csv'))
    
    # Drop the rows in which there's no lat lon data
    df_crime = df_crime[df_crime['latitude'].notna()]
    df_crime = df_crime[df_crime['longitude'].notna()]
    
    # Create popups and their contents
    popups_list, locations_list = [], []
    for _, row in df_crime.iterrows():
        # Trim unnecessary information from the timestamp
        incident_timestamp = row['incident_datetime']
        incident_timestamp = incident_timestamp.replace('T', ' ')
        incident_timestamp = incident_timestamp[:-7]
        
        # Create a popup object and append it to the popups array
        popup_content = '<strong>Timestamp: </strong>' + incident_timestamp + '<br>' \
                        + '<strong>Day of the week: </strong>' + row['incident_day_of_week'] + '<br>' \
                        + '<strong>Description: </strong>' + row['incident_description']
        popups_list.append(folium.Popup(html=popup_content))
        
        # Get the lat, lon location data and add it to the list
        locations_list.append(row[['latitude', 'longitude']].to_numpy().tolist())
    
    ''' 
    Initialize the map
    '''
    map_crime = folium.Map(location=[37.773972, -122.431297], 
                           zoom_start=11, 
                           max_bounds=True, 
                           min_zoom=9,
                           max_lat=38.5,
                           max_lon=-122,
                           min_lat=37,
                           min_lon=-123)
    
    '''
    Create the map content and add it to the map object
    '''
    # Create marker cluster
    icon_list = []
    for _ in range(len(locations_list)):
        icon_list.append(folium.Icon(icon='exclamation', prefix='fa', color='orange'))

    marker_cluster = MarkerCluster(locations=locations_list, popups=popups_list, icons=icon_list)
    marker_cluster.add_to(map_crime)
    
    # Create map legend
    current_timestamp = datetime.now() - timedelta(days=1)
    week_before = current_timestamp - timedelta(weeks=1)
    current_timestamp = current_timestamp.strftime('%Y-%m-%d')
    week_before = week_before.strftime('%Y-%m-%d')
    
    template = utils.create_legend(caption='San Francisco crimes between ' + week_before + ' and ' + current_timestamp)
    macro = MacroElement()
    macro._template = Template(template)
    map_crime.get_root().add_child(macro)  
    
    '''
    Save completed map viz to an appropriate folder
    '''
    map_crime.save(os.path.join(script_dir_path, '..', 'webapp', 'templates', 'SF_crime_viz.html'))
    print('Successfully created the San Francisco crime viz!')    
    
if __name__ == '__main__':
    download_sf_crime_data()
    create_sf_crime_viz()