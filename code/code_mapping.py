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


#%% Section 2: Aggregating
# Import Clean Data
df = pd.read_excel(filepath + "data/cleaned_data.xlsx", usecols=lambda x: 'Unnamed' not in x)

# Create Dataset for Aggregating
df_agg = df

# Calculate Coordinates by Metro Area
df_coordinates = df_agg.groupby("name_metro_area")[["latitude_building", "longitude_building"]].mean().reset_index()
df_coordinates = df_coordinates.drop_duplicates(subset = ["name_metro_area"]).reset_index(drop = True)

# Assign Coordinates to Each Metro Area Based on Geocoded Sample
df_agg = pd.merge(df_agg.loc[:, ~df_agg.columns.isin(["latitude_building", "longitude_building"])], 
                  df_coordinates[['name_metro_area', 'latitude_building', 'longitude_building']], 
                  on = "name_metro_area",
                  how = "left")

# Retain Skyscrapers
df_agg = df_agg[df_agg["skyscraper"] == True]

# Select Date Range to Animate
df_agg = df_agg[df_agg["year_started_building"] >= 1900]
df_agg = df_agg[df_agg["year_finished_building"] <= 2025]

# Aggregate Variables of Interest by Metro Area and Year
df_agg["count"] = 1
df_agg = df_agg.groupby(["name_metro_area", "year_finished_building"]).agg(
    {"count": "sum",
     "height_building_m": "sum",
     "latitude_building": "mean",
     "longitude_building": "mean"}
    ).reset_index()

# Rectangularize Data
all_years = pd.Series(range(int(df_agg["year_finished_building"].min()), int(df_agg["year_finished_building"].max()) + 1))
metro_areas = df_agg["name_metro_area"].unique()
all_combinations = pd.MultiIndex.from_product([metro_areas, all_years], names=["name_metro_area", "year_finished_building"]).to_frame(index=False)
df_agg = all_combinations.merge(df_agg, 
    on=["name_metro_area", "year_finished_building"], 
    how="left")

# Filling Missing Variables of Interest
df_agg['latitude_building'] = df_agg.groupby('name_metro_area')['latitude_building'].transform(lambda group: group.ffill().bfill())
df_agg['longitude_building'] = df_agg.groupby('name_metro_area')['longitude_building'].transform(lambda group: group.ffill().bfill())
df_agg.fillna({"count": 0, 'height_building_m': 0}, inplace=True)
df_agg = df_agg.sort_values(by = ["name_metro_area", "year_finished_building"])

# Generate Cumulative Variables of Interest
df_agg["cum_count"] = df_agg.groupby("name_metro_area")["count"].cumsum()
df_agg["cum_height"] = df_agg.groupby("name_metro_area")["height_building_m"].cumsum()


#%% Section 3: Mapping
# Create Dataset for Mapping
df_map = df_agg

# Define Function for Specifying Map Parameters
def map_parameters(data, animation_frame, title):
    # Specify Map Parameters
    fig = px.scatter_geo(data, 
                         scope = "world",
                         projection = "robinson",
                         lat = 'latitude_building', 
                         lon = 'longitude_building',
                         size = 'cum_count',
                         size_max = 50,
                         opacity = 0.85,
                         color = 'cum_height',
                         animation_frame = animation_frame,
                         hover_name = 'name_metro_area', 
                         hover_data = {"year_finished_building": False,
                                       "latitude_building": False,
                                       "longitude_building": False},
                         labels = {"name_metro_area": "Metro Area",
                                   "year_finished_building": "Year",
                                   "cum_count": "Total Number of Skyscrapers",
                                   "cum_height": "Total Height of Skyscrapers (m)"})
    
    # Adjust Map Position
    fig.update_layout(mapbox_style="open-street-map",
                      mapbox = dict(
                          center = go.layout.mapbox.Center(
                              lat = 45.515,
                              lon = -73.630),
                          zoom = 10.5))
    
    # Adjust Height Scale
    fig.update_layout(
        coloraxis = dict(
            colorscale = "Darkmint"))
    
    # Add Title
    fig.update_layout(
        title = {
            "text": title,
            "font_size": 20,
            "x": 0.50})
    
    # Add Caption
    fig.update_layout(
        annotations = [dict(
        x= 0.50,
        y = -0.05,
        font_size = 12,
        showarrow = False,
        text = "")])
    
    # Adjust Map Size
    fig.update_layout(
        width = 1800,
        height = 1000) 
    
    # Return Map
    return fig


# Define Function for Creating Map of Skyscraper Construction
def create_map(data, type): 
    # Define First Year
    first_year = data["year_finished_building"].min()
    first_year_str = str(first_year)

    # Define Last Year
    last_year = data["year_finished_building"].max()
    last_year_str = str(last_year)

    # Static Map
    if type == "static":
        pio.renderers.default = 'browser'
        animation_frame = None
        title = f"Worldwide Skyscraper Construction, {last_year_str}"
        data = data[data["year_finished_building"] == last_year]
        fig = map_parameters(data, animation_frame, title)
        fig.write_html(filepath + "output/static_map.html")
        fig.show()
        
    # Animated Map
    else:
        pio.renderers.default = 'browser'
        animation_frame = "year_finished_building"
        title = f"Worldwide Skyscraper Construction, {first_year_str}-{last_year_str}"
        fig = map_parameters(data, animation_frame, title)
        fig.write_html(filepath + "output/animated_map.html")
        fig.show()
        

# Create Maps of Worldwide Skyscraper Construction
create_map(df_map, type = "static")
create_map(df_map, type = "animated")