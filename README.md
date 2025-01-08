# Worldwide Skyscraper Construction
This repository includes the Python code needed to scrape a database with information about more than 100,000 buildings in xx cities and generate an animation of worldwide skyscraper construction over the period 1900-2024. The [code](https://github.com/robertialenti/Skyscrapers/blob/main/code.py) is separated into 5 sections.

## Code

### 1. Prelinimaries
In this section, I import the libraries needed to scrape, clean, and plot the data. The scraping is done with a combination of Selenium, Beautifulsoup, and Pandas.

### 2. Scraping
The building-level data is gathered from [SkyscraperPage](https://skyscraperpage.com/), which provides comprehensive coverage of large buildings across more than 7,500 cities. The scraper uses Selenium and BeautifulSoup to dynamically navigate the website and parse HTML on each city's webpage. In each city, I collect property-level information for all buildings. 

### 3. Geocoding
As I will be plotting skyscraper construction by metro area, I choose to simply geoccode a small sample of buildings from each metropolitain area, and use the average latitude and longitude. This reduces the number of geocoding calls performed with Google's Geocoding API and makes the visualization more readable.

### 4. Preparing Data
The complete dataset has the following variables. The dataset includes xx buildings from yy cities and zz metropoltain areas.
- id_city: City unique identifier
- name_metro_area: Metropolitain area name
- name_city: City name
- name_building: Building name
- address_building: Building address
- status_building: Building status (built, proposed, in construction, postponed)
- height_building_ft: Building height in feet
- height_building_m: Building height in meters
- year_started_building: Year that building construction began or is expected to begin
- year_finished_building: Year that building construction ended or is expected to end
- latitude_building: Building latitude
- longitude_building: Building longitude
- skyscraper: Indicator variable, equal to 1 if a building has a height greater than 100 meters, and 0 otherwise

The data is aggregated by metropolitain area using SkyscraperPage's aggregation. Cities that do not belong to metropolitain areas are left ungrouped. 

I clean the data by retaining only buildings with a height of at least 100 meters, as this is the threshold commonly used to ___

As Skyscraperpage's privacy policy asks that data is not published publicly, I choose not to post the dataset in this repository.

### 5. Aggregating

The dataset is collapsed by metro area and year. I take the sum of count and building height. The aggregate variables are then used to track total number of buildings and total building height built by metro area over time.

### 6. Mapping
Here is a static map, showing the state of skyscraper construction in 2024.

Here is an animated version, showing the growing prevalence of skyscrapers over the last 125 years. It is clear to see...
