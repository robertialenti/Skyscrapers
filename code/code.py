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

# APIs
geocoding_api_key = "AIzaSyB5ej9kIbpM7IHUHVUUcLEkCI5ZoFI_Bz8"


#%% Section 2: Scraping Data
# Define Function for Launching Undetected Browser
def launch_browser():
    browser = uc.Chrome()

    # Apply stealth settings to the driver
    #stealth(browser,
    #        languages=["en-US", "en"],
    #        vendor="Google Inc.",
    #        platform="Win32",
    #        webgl_vendor="Intel Inc.",
    #        renderer="Intel Iris OpenGL Engine",
    #        fix_hairline=True,
    #        )

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
                time.sleep(10)
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
#df = pd.DataFrame()
df = pd.read_excel(filepath + "data/raw_data.xlsx")

# Launch Browser
browser = launch_browser()

# Iterate Over Cities
for id_city in tqdm(range(140,7000)):
    # Scrape Buildings in Selected City
    df_temp = scrape(df, id_city)
    
    # Append Scraped Data to Already-Collected Data
    df = pd.concat([df, df_temp], ignore_index = True)
    df = df.drop_duplicates(subset = ["name_building", "address_building"]).reset_index(drop = True)

    # Save Data
    df.to_excel(filepath + "data/raw_data.xlsx")


#%% Section 3: Geocoding
df = pd.read_excel(filepath + "data/raw_data.xlsx", usecols=lambda x: 'Unnamed' not in x)
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
    
    print("Could not locate building.")
    return None, None


# Geocode Sample of Buildings in Each Metro Area
df_sample = df.groupby('name_metro_area').head(10)
tqdm.pandas()
df_sample[['latitude_building', 'longitude_building']] = df_sample['address_building'].progress_apply(lambda x: geocode(x)).apply(pd.Series)
df_sample = df_sample.groupby("name_metro_area")[["latitude_building", "longitude_building"]].mean().reset_index()
df_sample = df_sample.drop_duplicates(subset = ["name_metro_area"]).reset_index(drop = True)

# Assign Coordinates to Each Metro Area Based on Geocoded Sample
df = pd.merge(df, 
              df_sample[['name_metro_area', 'latitude_building', 'longitude_building']], 
              on = "name_metro_area",
              how = "left")


#%% Section 4: Cleaning Data
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
df = df[df["skyscraper"] == True]

# Identify Relevant Skyscrapers
relevant_uses = ["residential", "commercial", "office", "retail", "mixed use", "conference", "court", "government", "hotel", "hospital", "observation"]
pattern = '|'.join(relevant_uses)
df = df[df['use_building'].str.contains(pattern, case=False, regex=True)]

# Retain Built Skyscrapers
df = df[df["status_building"] == "built"]


#%% Section 4: Aggregating Data Prior to Mapping
# Create Dataset for Aggregating
df_agg = df

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


#%% Section 5: Mapping
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
                         size_max = 20,
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
def map_skyscraper_construction(data, type): 
    # Find Last Year
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
    elif type == "animated":
        pio.renderers.default = 'browser'
        animation_frame = "year_finished_building"
        title = f"Worldwide Skyscraper Construction, 1900-{last_year_str}"
        fig = map_parameters(data, animation_frame, title)
        fig.write_html(filepath + "output/animated_map.html")
        fig.show()
    
    # GIF Map
    elif type == "gif":
        images = []
        pio.renderers.default = 'png'
        animation_frame = None
        
        # Iterate Over Years
        for year in tqdm(data["year_finished_building"].unique().tolist()):
            # Duplicate DataFrame 
            data_temp = data
            
            # Select Date
            data_temp = data_temp[data_temp["year_finished_building"] == year]
            year_str = year.strftime('%Y')
            title = f"Worldwide Skyscraper Construction, {year_str}"
            fig = map_parameters(data_temp, animation_frame, title)
            
            # Save Map as Image
            try:
                img_bytes = PlotlyImage.get(fig)
                image = PILImage.open(io.BytesIO(img_bytes))
                image.save(filepath + "images/" + "image" + year_str + ".png")
                images.append(image)
            except:
                break
 
        # Create GIF from Compressed Images
        image_files = [f for f in os.listdir(filepath + "images") if f.endswith(('.png'))]
        image_files.sort()
        images = [Image.open(os.path.join(filepath + "images", file)) for file in image_files]
        images[0].save(filepath + "output/gif_map.gif",
                       save_all = True, 
                       append_images = images[1:], 
                       optimize = True, 
                       duration = 200, 
                       loop = 0)
        

# Create Maps of Worldwide Skyscraper Construction
map_skyscraper_construction(df_map, type = "static")
map_skyscraper_construction(df_map, type = "animated")
#map_skyscraper_construction(df_map, type = "gif")