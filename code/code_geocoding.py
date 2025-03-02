#%% Section 1: Preliminaries
# Libraries
# General
from tqdm import tqdm
import pandas as pd
import time
import random
import re
import io
import os
import warnings
import requests

# Web Scraping
import undetected_chromedriver as uc
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium_stealth import stealth
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait

# Mapping
import plotly.io as pio
from PIL import Image
import plotly.graph_objects as go
from PIL import Image as PILImage
from chart_studio.plotly import image as PlotlyImage
import plotly.express as px
pio.renderers.default = 'browser'

# Other
warnings.filterwarnings("ignore", category=FutureWarning, message="The frame.append method is deprecated and will be removed from pandas in a future version. Use pandas.concat instead.")
pd.set_option("display.expand_frame_repr", False)

# Paths
filepath = "C:/Users/Robert/OneDrive/Desktop/Bobby/GitHub/Skyscrapers/"

# APIs
geocoding_api_key = "AIzaSyB5ej9kIbpM7IHUHVUUcLEkCI5ZoFI_Bz8"

#%% Section 2: Geocoding
# Import Raw Data and Crosswalk
df = pd.read_excel(filepath + "data/raw_data.xlsx", usecols=lambda x: 'Unnamed' not in x)
#df = df[df["name_city"] == "Montreal"].reset_index(drop = True)
df_crosswalk = pd.read_excel(filepath + "data/city_crosswalk.xlsx", sheet_name = "Crosswalk")

# Correct Address
def correct_address(row):
    if row['name_city'] in row['address_building']:
        return row['address_building'].replace(row['name_city'], f" {row['name_city']}")
    return row['address_building']
df['address_building'] = df.apply(correct_address, axis=1)

# Map Cities to Single Metro Area
df = pd.merge(df, 
              df_crosswalk[["id_city", "name_metro_area"]], 
              on = "id_city", 
              how = "left")

# Replace Metro Area Name with City Name if Standalone City
df['name_metro_area'] = df['name_metro_area'].fillna(df['name_city'])

# Define Function for Geocoding Metro Areas
def geocode(address):
    print(f"Geocoding: {address}")

    # Specify Parameters
    base_url = "https://maps.googleapis.com/maps/api/geocode/json?"
    parameters = {"key": geocoding_api_key,
                  "address": address}
    
    # Generate Reponse
    response = requests.get(base_url, parameters).json()

    # Gather Coodinates
    if response["status"] == "OK":
        geometry = response["results"][0]["geometry"]
        latitude_building = geometry["location"]["lat"]
        longitude_building = geometry["location"]["lng"]
        
        return latitude_building, longitude_building
    
    else:
        print("Could not geolocate building.")
        return None, None


# Geocode Buildings
tqdm.pandas()
df[['latitude_building', 'longitude_building']] = (
    df.progress_apply(
        lambda row: geocode(f"{row['name_building']}, {row['address_building']}"), axis=1
    ).apply(pd.Series)
)

# Save Geocoded Data
df.to_excel(filepath + "data/geocoded_data.xlsx", index = False)
#df.to_excel(filepath + "data/montreal_data.xlsx", index = False)