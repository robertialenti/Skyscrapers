"""
This script scrapes data on buildings, cleans addresses, maps properties to coordinates, prepares the data for mapping, maps, and animates skyscraper growth by metropolitain area over time.
"""

#%% Section 1: Preliminaries
# Libraries
# General
from bs4 import BeautifulSoup
from tqdm import tqdm
import pandas as pd
import time
import re
import warnings
import requests

# Web Scraping
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait

# Mapping
import plotly.io as pio
import plotly.express as px
import json
from urllib.request import urlopen
with urlopen('https://raw.githubusercontent.com/plotly/datasets/master/geojson-counties-fips.json') as response:
    counties = json.load(response)
pio.renderers.default = 'browser'

# Other
warnings.filterwarnings("ignore", category=FutureWarning, message="The frame.append method is deprecated and will be removed from pandas in a future version. Use pandas.concat instead.")
pd.set_option("display.expand_frame_repr", False)

# Paths
filepath = "C:/Users/rialenti/Dropbox (Harvard University)/skyscrapers/"

# APIs
google_api_key = "AIzaSyB5ej9kIbpM7IHUHVUUcLEkCI5ZoFI_Bz8"


#%% Section 2: Scrape Data
# Define Function for Launching Browser
def launch_browser():
    global browser
    options = webdriver.ChromeOptions()
    s = Service(filepath + "chromedriver.exe")
    browser = webdriver.Chrome(service=s, options=options)
    browser.maximize_window()
    global wait
    wait = WebDriverWait(browser, 3) 
    

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


# Define Function for Gathering Building Use
def get_building_use(soup):
    td = soup.find("td").get_text()
    if td: 
        use_building = re.search(r'Building Uses(.*)', td)
        use_building = use_building.group(1)
        
        end_pos = use_building.find("Structural")
        if end_pos != -1:
            use_building = use_building[:end_pos]
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
            # Change Link for City
            browser.get(link_city + f"&offset={number_page*100}")
            # Next Page
            browser.find_element(By.XPATH, "/html/body/table/tbody/tr[1]/td/table[5]/tbody/tr/td[3]/table/tbody/tr/td/table/tbody/tr/td/table[2]/tbody/tr/td/table[4]/tbody/tr/td/table[1]/tbody/tr[2]/td/*").click()
            # Reset Building Number
            number_building = 1
            # Increment Page Number
            number_page = number_page + 1
        else:
            browser.get(link_city + f"&offset={number_page*100}")
    return number_building, number_page
    time.sleep(5)
    
    
# Define Function for Scraping Building Data for a City
def scrape(df, id_city):
    # Choose City
    link_city = choose_city(id_city)
    
    # Initialize Building Number
    number_building = 1
    
    # Initialize Page Number
    number_page = 0
    
    # Parse
    try: 
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
                time.sleep(5)
    
                # Store Building-Specific HTML
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
                            "use_building": use_building,
                            "year_started_building": year_started_building,
                            "year_finished_building": year_finished_building}
                df = df.append(new_data, ignore_index = True)
                print(df)
                
            except:
                print("Not a valid building.")
                pass
            
            # Increment Building Number
            number_building = number_building + 1
            
            # Return to List of Buildings or Change Page
            number_building, number_page = change_page(link_city, number_building, number_buildings, number_page)

    except:
        print("City does not have any buildings.")
        pass
    
    # Return Completed Dataframe for City
    return df


# Perform Scraping
# Identify Missing Cities
df = pd.read_excel(filepath + "raw_data.xlsx", usecols=lambda x: 'Unnamed' not in x)
df_done = df.drop_duplicates(subset = "id_city")
df_done = df_done["id_city"].tolist()

# Create Empty Dataframe
df2 = pd.DataFrame()

# Launch Browser
launch_browser()

# Iterate Over Cities
for id_city in tqdm(range(0,8000)):
    # Check if Buildings in City Already Scraped
    if id_city in df_done:
        id_city = id_city + 1
    else:
        # Scrape Buildings in City
        print(f"Currently scraping city: {id_city}")
        df2 = scrape(df2, id_city)
    df_done = df_done.append(id_city)

# Export
df = df.append(df2, ignore_index = True)
#df.to_excel(filepath + "raw_data.xlsx")


#%% Section 3: Geocode
df = pd.read_excel(filepath + "raw_data.xlsx", usecols=lambda x: 'Unnamed' not in x)
df_crosswalk = pd.read_excel(filepath + "city_crosswalk.xlsx", sheet_name = "Crosswalk")

# Map Many Cities to Single Metro Area
df = pd.merge(df, 
              df_crosswalk[["id_city", "name_metro_area"]], 
              on = "id_city", 
              how = "left")

# Replace Metro Area Name with City Name if Standalone City
if df["name_metro_area"] is None:
    df["name_metro_area"] = df["name_city" ]

# Define Function for Geocoding Metro Areas
def geocode(address):
    # Specify Parameters
    base_url = "https://maps.googleapis.com/maps/api/geocode/json?"
    parameters = {"key": google_api_key,
                  "address": address}
    
    # Generate Reponse
    response = requests.get(base_url, parameters).json()

    # Gather Coodinates
    if response["status"] == "OK":
        geometry = response["results"][0]["geometry"]
        latitude = geometry["location"]["lat"]
        longitude = geometry["location"]["lng"]
        
        return latitude, longitude
    
    print("Could not locate building.")
    return None, None


# Geocode Sample of Buildings in Each Metro Area
df_sample = df.groupby('name_metro_area').head(10)
tqdm.pandas()
#df_sample[['latitude', 'longitude']] = df_sample['address_building'].progress_apply(lambda x: geocode(x)).apply(pd.Series)
#df_sample = df_sample.groupby("name_metro_area")["latitude", "longitude"].mean().reset_index()
#df_sample.to_excel(filepath + "geocoded_sample.xlsx")

# Assign Coordinates to Each Metro Area Based on Geocoded Sample
df_geocoded_sample = pd.read_excel(filepath + "geocoded_sample.xlsx")
df = pd.merge(df, 
              df_geocoded_sample, 
              on = "name_metro_area",
              how = "left")


#%% Section 4: Prepare Data for Mapping
# Remove Potential Duplicate Buildings
df = df.drop_duplicates(subset = ["name_building", "address_building"]).reset_index(drop = True)

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

# Aggregate Variables of Interest by Metro Area
df["count"] = 1
df = df.groupby(["name_metro_area", "year_finished_building"]).agg(
    {"count": "sum",
     "height_building_m": "sum",
     "latitude": "mean",
     "longitude": "mean"}
    ).reset_index()

# Rectangularize Dataset
all_years = pd.Series(range(int(df["year_finished_building"].min()), int(df["year_finished_building"].max()) + 1))
metro_areas = df["name_metro_area"].unique()
all_combinations = pd.MultiIndex.from_product([metro_areas, all_years], names=["name_metro_area", "year_finished_building"]).to_frame(index=False)
df = all_combinations.merge(df, on=["name_metro_area", "year_finished_building"], how="left")

# Filling Missing Variables of Interest
df['latitude'] = df.groupby('name_metro_area')['latitude'].apply(lambda group: group.ffill().bfill())
df['longitude'] = df.groupby('name_metro_area')['longitude'].apply(lambda group: group.ffill().bfill())
df.fillna({"count": 0, 'height_building_m': 0}, inplace=True)
df = df.sort_values(by = ["name_metro_area", "year_finished_building"])

# Generate Cumulative Variables of Interest
df["cum_count"] = df.groupby("name_metro_area")["count"].cumsum()
df["cum_height"] = df.groupby("name_metro_area")["height_building_m"].cumsum()


#%% Section 5: Create Map
# Create Dataset for Mapping
df_map = df

# Define Function for Creating Animated Map
def animated_plot(data, type, start_date, end_date):
    # Select Parameters
    if type == "animated":
        animation_frame = "year_finished_building"
        data = data[(data["year_finished_building"] >= start_date) & (data["year_finished_building"] <= end_date)]
    elif type == "static":
        animation_frame = None
        data = data[data["year_finished_building"] == end_date]
         
    # Select Title and Caption
    title = f"Worldwide Skyscraper Construction, {end_date}"
    if type == "animated":
        title = f"Worldwide Skyscraper Construction, {start_date}-{end_date}"
    caption = f"Source: Skyscraperpage.com <br> This figure plots all buildings built between {start_date}-{end_date} with a height of at least 100 metres. <br> Skyscrapers can be residential, commercial, office, hotel, mixed use buildings. Buildings used exclusively for telecommunications, such as antennas or radio towers, are excluded. <br> Total height reflects height at top of antenna, if one exists. A metro areaa can, and typically does, include several cities."
    
    # Specify Map Parameters
    fig = px.scatter_geo(data, 
                         scope = "world",
                         projection = "robinson",
                         lat = 'latitude', 
                         lon = 'longitude',
                         size = 'cum_count',
                         size_max = 20,
                         opacity = 0.75,
                         color = 'cum_height',
                         hover_name = 'name_metro_area', 
                         hover_data = {"year_finished_building": False,
                                       "latitude": False,
                                       "longitude": False},
                         animation_frame = animation_frame,
                         labels = {"name_metro_area": "Metro Area",
                                   "year_finished_building": "Year",
                                   "cum_count": "Total Number of Skyscrapers",
                                   "cum_height": "Total Height of Skyscrapers (m)"})
    
    # Adjust Height Scale
    fig.update_layout(
        coloraxis = dict(
            colorscale = "Darkmint"))
    
    # Add Title
    fig.update_layout(
        title = {
            "text": title,
            "x": 0.45})
    
    # Add Caption
    fig.update_layout(
        annotations = [dict(
        x= 0.5,
        y = -0.10,
        font_size = 12,
        text = caption)])
    
    # Create Map and Save as HTML File
    fig.write_html(filepath + "animated_map.html")
    return fig.show()


# View Map
animated_plot(df_map, type = "static", start_date = 1900, end_date = 2024)
animated_plot(df_map, type = "animated", start_date = 1900, end_date = 2024)


# Problems
# There are some cities, such as London and Busan, for which data is available, which must be added on later.