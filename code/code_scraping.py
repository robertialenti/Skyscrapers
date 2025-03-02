"""
This script scrapes data on buildings, cleans addresses, maps properties to coordinates, prepares the data for mapping, maps, and animates skyscraper growth by metropolitain area over time.
"""

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


#%% Section 2: Scraping Data
# Define Function for Launching Undetected Browser
def launch_browser():
    # Initialize Browser
    browser = uc.Chrome()

    # Return Browser
    return browser


# Define Function for Choosing City
def choose_city(id_city):
    link_city = f"https://skyscraperpage.com/cities/?cityID={id_city}"
    try:
        browser.get(link_city)
        time.sleep(5)
        return link_city
    except:
        pass
    

# Define Function for Gathering City ID
def get_city_id(soup):
    ids_city = soup.find_all('a', href=True)
    for id_city in ids_city:
        match = re.search(r"cityID=(\d+)", id_city['href'])
        if match:
            id_city = int(match.group(1))
            break
    return id_city
    

# Define Function for Gathering City Name
def get_city_name(soup):
    span = soup.find('span', class_='lrgb')
    if span:
        name_city = span.get_text().strip()
        return name_city
    return None
   

# Define Function for Gathering Number of Buildings in City
def get_number_buildings(soup):
    match = soup.find(string=lambda text: text and "Listing 1 to" in text and "buildings" in text)
    match = re.search(r"Listing 1 to (\d+) of (\d+) buildings", match)
    if match:
        number_buildings = int(match.group(2))
        return number_buildings
    return
    

# Define Function for Gathering Building Name    
def get_building_name(soup):
    span = soup.find('span', class_='lrgb')
    if span:
        building_name = span.get_text().strip()
        return building_name
    return None


# Define Function for Gathering Building Status
def get_building_status(soup):
    list_styles = ["border:3px solid #333333;padding:0px 4px 0px 4px",
                   "border:3px solid #59e817;padding:0px 4px 0px 4px",
                   "border:3px solid #1589ff;padding:0px 4px 0px 4px",
                   "border:3px solid #ffff00;padding:0px 4px 0px 4px"]
    for style in list_styles:
        div = soup.find("div", attrs={"style": style})
        if div:
            building_status = div.get_text().strip()
            return building_status
    return None


# Define Function for Gathering Building Height
def get_building_height(soup):
    span = soup.find("span", id = "height_0")
    if span:
        building_height = span.get_text().strip()
        if not pd.isna(building_height):
            building_height = int(''.join(filter(str.isdigit, str(building_height))))
        return building_height
    return None


# Define Function for Gathering Building Floor Count
def get_building_floors(soup):
    td = soup.find("td")
    if td:
        building_floors = td.get_text().strip()
        if "Floor Count" in building_floors:
            building_floors = building_floors.split('Floor Count')[1].strip()
            
            numeric_floors = ""
            for char in building_floors:
                if char.isdigit():
                    numeric_floors += char
                else:
                    break
            return numeric_floors if numeric_floors else None
    return None


# Define Function for Gathering Building Use
def get_building_use(soup):
    td = soup.find("td").get_text()
    if td: 
        use_building = re.search(r'Building Uses(.*)', td)
        use_building = use_building.group(1)
        
        end_position = use_building.find("Structural")
        if end_position != -1:
            use_building = use_building[:end_position]
        use_building = use_building.replace("-", "").strip()
        return use_building
    return None


# Define Function for Gathering Building Address
def get_building_address(soup, name_building):
    td = soup.find("td").get_text()
    if td: 
        address_building = re.search(r"(.*?)(?=Status)", td)
        address_building = address_building.group()
        
        first_position = address_building.find(name_building)
        if first_position != -1:
            second_position = address_building.find(name_building, first_position + len(name_building))
            if second_position != -1:
                start_index = second_position + len(name_building)
                address_building = address_building[start_index:].strip()
                if "http" in address_building:
                    address_building = address_building.split("http", 1)[0].strip()
               
        return address_building
    return None
        

# Define Function for Gathering Building Construction Dates
def get_building_construction_date(soup, type):
    list_strings = soup.find_all("tr")
    if list_strings:
        for string in list_strings:
            string = string.get_text()
            keywords = ["Begin", "Began", "Will begin"] if type == "start" else ["End", "Finished", "Will finish"]
            index = -1
            
            for keyword in keywords:
                if keyword in string:
                    index = string.find(keyword)
                    break 
            
            if index == -1:
                continue
            
            year = string[index:]
            year = year.split(keyword)[1]
            year = year[:4].strip()
            return year
    return None
    
    
# Define Function for Changing Page
def change_page(link_city, number_building, number_buildings, number_page):
    if number_buildings < 100:
        # Return to List of Buildings
        browser.get(link_city)
    else:
        # Verify if Page Change is Necessary
        if number_building % 100 == 0:
            # Increment Page Number
            number_page = number_page + 1
            # Navigate to Page
            browser.get(link_city + f"&offset={number_page*100}")
            # Reset Building Number
            number_building = 1
        else:
            # Navigate to Page
            browser.get(link_city + f"&offset={number_page*100}")
    time.sleep(5)    
    return number_building, number_page
    
    
# Define Function for Scraping Building Data for a City
def scrape(df, id_city):
    try:
        # Choose City
        link_city = choose_city(id_city)
        
        # Initialize Building Number
        number_building = 1
        
        # Initialize Page Number
        number_page = 0
        
        # Store City-Specific HTML
        soup = BeautifulSoup(browser.page_source, "html.parser")
        
        # Gather City Name
        name_city = get_city_name(soup)
        
        # Gather Number of Buildings in City
        number_buildings = get_number_buildings(soup)
        
        # Iterate Over Buildings in City
        while (number_building + (number_page*100)) <= (number_buildings + 1):
            try:
                # Select a Building
                base_string = "/html/body/table/tbody/tr[1]/td/table[5]/tbody/tr/td[3]/table/tbody/tr/td/table/tbody/tr/td/table[2]/tbody/tr/td/table[4]/tbody/tr/td/table[2]/tbody/tr"
                base_string_alt = "/html/body/table/tbody/tr[1]/td/table[5]/tbody/tr/td[3]/table/tbody/tr/td/table/tbody/tr/td/table[2]/tbody/tr/td/table[3]/tbody/tr/td/table[2]/tbody/tr"
                if number_building == 1:
                    try:
                        browser.find_element(By.XPATH, f"{base_string}[{number_building*4}]/td[2]/a").click()
                    except:
                        browser.find_element(By.XPATH, f"{base_string_alt}[{number_building*4}]/td[2]/a").click()           
                else:
                    try:
                        browser.find_element(By.XPATH, f"{base_string}[{4 + 2*(number_building-1)}]/td[2]/a").click()
                    except:
                        browser.find_element(By.XPATH, f"{base_string_alt}[{4 + 2*(number_building-1)}]/td[2]/a").click()

                # Store Building-Specific HTML
                time.sleep(5)
                soup = BeautifulSoup(browser.page_source, "html.parser")

                # Gather Building Characteristics
                # Name
                name_building = get_building_name(soup)
    
                # Address
                address_building = get_building_address(soup, name_building)
    
                # Status
                status_building = get_building_status(soup)
                
                # Height
                height_building = get_building_height(soup)
                
                # Floor Count
                floors_building = get_building_floors(soup)
 
                # Use
                use_building = get_building_use(soup)
    
                # Year of Construction Start
                year_started_building = get_building_construction_date(soup, type = "start")

                # Year of Construction Finish
                year_finished_building = get_building_construction_date(soup, type = "finish")
    
                # Append Building Data to Dataframe
                new_data = {"id_city": id_city,
                            "name_city": name_city,
                            "name_building": name_building,
                            "address_building": address_building,
                            "status_building": status_building,
                            "height_building": height_building,
                            "floors_building": floors_building,
                            "use_building": use_building,
                            "year_started_building": year_started_building,
                            "year_finished_building": year_finished_building}
                new_data = pd.DataFrame([new_data])
                
                df = pd.concat([df, new_data], ignore_index=True)
                print(df)
                
            except:
                print("Could not scrape building details.")
                pass
            
            # Increment Building Number
            number_building = number_building + 1

            # Return to List of Buildings or Change Page
            number_building, number_page = change_page(link_city, number_building, number_buildings, number_page)
            print(f"City: {name_city},",
                  f"Number Page: {number_page + 1},", 
                  f"Number Building: {number_building},", 
                  f"Number of Buildings: {number_buildings}")
    
    # Return Completed Dataframe for City if Error is Encountered
    except:
        return df
    

    
    # Return Completed Dataframe for City
    return df


# Create Empty Dataframe to Hold Results
df = pd.DataFrame()

# Launch Browser
browser = launch_browser()

# Iterate Over Cities
for id_city in tqdm(range(1,7000)):
    # Scrape Buildings in Selected City
    df_temp = scrape(df, id_city)
    
    # Append Scraped Data to Already-Collected Data
    df = pd.concat([df, df_temp], ignore_index = True)
    df = df.drop_duplicates(subset = ["name_building", "address_building"]).reset_index(drop = True)

    # Save Raw Data
    df.to_excel(filepath + "data/raw_data.xlsx")