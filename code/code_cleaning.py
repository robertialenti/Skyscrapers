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


#%% Section 2: Cleaning Data
# Import Geocoded Data
df = pd.read_excel(filepath + "data/montreal_data.xlsx", usecols=lambda x: 'Unnamed' not in x)

# Remove Potential Duplicate Buildings
df = df.drop_duplicates(subset = ["name_building", "address_building"]).reset_index(drop = True)

# Convert Year Started and Year Finished to Integer
df['year_started_building'] = pd.to_numeric(df['year_started_building'], errors='coerce')
df['year_finished_building'] = pd.to_numeric(df['year_finished_building'], errors='coerce')
df["year_started_building"] = df["year_started_building"].astype(pd.Int64Dtype())
df["year_finished_building"] = df["year_finished_building"].astype(pd.Int64Dtype())

# Convert Building Height to Metres
df = df.rename(columns = {"height_building": "height_building_ft"})
df["height_building_m"] = df["height_building_ft"]*0.3048

# Identify Skyscrapers
df['skyscraper'] = df['height_building_m'].apply(lambda x: True if x >= 100 else False)

# Identify Relevant Skyscrapers
relevant_uses = ["residential", "commercial", "office", "retail", "mixed use", "conference", "court", "government", "hotel", "hospital", "observation", "education"]
pattern = '|'.join(relevant_uses)
df = df[df['use_building'].str.contains(pattern, case=False, regex=True)]

# Retain Built Skyscrapers
df = df[df["status_building"] == "built"]

# Save Cleaned Data
df.to_excel(filepath + "data/montreal_data.xlsx", index = False)