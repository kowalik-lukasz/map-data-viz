import sys
import os

script_dir_path = os.path.dirname(os.path.realpath(__file__))
sys.path.append(os.path.join(script_dir_path, '..', 'viz'))
from covid_viz import download_covid_data, create_covid_viz
from sf_crime_viz import download_sf_crime_data, create_sf_crime_viz
from gdp_viz import create_gdp_viz
from uk_accidents_viz import create_uk_accidents_viz

def covid_update():
    download_covid_data()
    create_covid_viz()
    
def sf_crime_update():
    download_sf_crime_data()
    create_sf_crime_viz()

def create_all():
    download_covid_data()
    create_covid_viz()
    
    download_sf_crime_data()
    create_sf_crime_viz()
    
    create_gdp_viz()
    
    create_uk_accidents_viz()