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

# Applications
import folium
from shiny import App, reactive, render, ui

# Other
warnings.filterwarnings("ignore", category=FutureWarning, message="The frame.append method is deprecated and will be removed from pandas in a future version. Use pandas.concat instead.")
pd.set_option("display.expand_frame_repr", False)

# Paths
filepath = "C:/Users/Robert/OneDrive/Desktop/Bobby/GitHub/Skyscrapers/"

# APIs
geocoding_api_key = "AIzaSyB5ej9kIbpM7IHUHVUUcLEkCI5ZoFI_Bz8"


#%% Section 2: Application Development
# Import Clean Data
df = pd.read_excel(filepath + "data/cleaned_data.xlsx", usecols=lambda x: 'Unnamed' not in x)

# UI
app_ui = ui.page_fluid(
    ui.h2("Skyscrapers by Metro Area"),
    ui.input_select("name_metro_area", "Choose a Metro Area:", choices=sorted(df["name_metro_area"].unique())),
    ui.output_ui("map_output"),
)

# Server
def server(input, output, session):
    @reactive.Calc
    def filtered_data():
        # Retain Only Selected Metro Area
        return df[df["name_metro_area"] == input.name_metro_area()]

    @reactive.Calc
    def center_coordinates():
        selected_rows = filtered_data()
        if not selected_rows.empty:
            # Find Mean Latitude and Longitude by Metro Area
            lat = selected_rows["latitude_building"].mean()
            long = selected_rows["longitude_building"].mean()
            return lat, long
        return 0, 0  

    @output
    @render.ui
    def map_output():
        # Center Map
        lat, lon = center_coordinates()
        # Initialize Map
        map = folium.Map(location=[lat, lon], zoom_start=9)

        # Add Markers for Buildings
        for _, row in filtered_data().iterrows():
            # Create popup content
            popup_content = f"""
            <b>Name:</b> {row['name_building']}<br>
            <b>Address:</b> {row['address_building']}<br>
            <b>Height:</b> {round(row['height_building_m'], 2)} meters<br>
            <b>Year Completed:</b> {row['year_finished_building']}<br>
            <b>Skyscraper:</b> {'Yes' if row['skyscraper'] else 'No'}
            """

            # Add gray markers for non-skyscrapers
            if not row["skyscraper"]:
                folium.Circle(
                    location=[row["latitude_building"], row["longitude_building"]],
                    radius=30,  
                    color='gray',
                    fill=True,
                    fill_color='gray',
                    fill_opacity=0.50,
                    popup=folium.Popup(popup_content, max_width=500)
                ).add_to(map)

            else:
                folium.Circle(
                    location=[row["latitude_building"], row["longitude_building"]],
                    radius=30, 
                    color='blue',
                    fill=True,
                    fill_color='blue',
                    fill_opacity=1,
                    popup=folium.Popup(popup_content, max_width=500)
                ).add_to(map)

        # Render Map
        return ui.HTML(map._repr_html_())
    

# Deploy Application
app = App(app_ui, server)