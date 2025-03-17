# Worldwide Skyscraper Construction
This repository includes the Python code needed to scrape SkyscraperPage - a database with information about more than 130,000 buildings around the world, explore and generate an animation of worldwide skyscraper construction over the period 1900-2025, and produce a ShinyApp allowing users to explore skyscrapers by metropolitain area. The [code](https://github.com/robertialenti/Skyscrapers/blob/main/code.py) to do so is separated into 5 sections.

## Code
### 1. Scraping
In this section, I import the libraries needed to scrape the building data. The building-level data is gathered from [SkyscraperPage](https://skyscraperpage.com/), which provides comprehensive coverage of large buildings across more than 7,000 cities. The scraper uses Selenium and BeautifulSoup to dynamically navigate the website and parse HTML on each city's webpage. In each city, I collect property-level information for all buildings, which includes their address, completion status, height, etc. The scraper uses an undetected Chrome instance. I also recommend also using a VPN.

### 2. Geocoding
Next, I geocode all of the buildings whose details I gathered by programatically passing their addresses into Google's Geocoding API.

### 3. Cleaning
In this section, I clean the data by removing potential duplicates, extracting country from building address, and imputing building height for buildings without a published height.
As I will be plotting skyscraper construction by metro area, I choose to simply geoccode a small sample of buildings from each metropolitain area and use the average latitude and longitude to geolocate the metro area. This reduces the number of geocoding calls performed with Google's Geocoding API - as it circumvents the need to geolocate each metro areas constituent cities - and makes the visualization more readable.

The data is aggregated by metropolitain area using SkyscraperPage's aggregation. Cities that do not belong to metropolitain areas are left ungrouped. 

I clean the data by retaining only buildings with a height of at least 100 meters, as this is the threshold commonly used to ___

### 4. Mapping

The dataset is collapsed by metro area and year. I take the sum of count and building height. The aggregate variables are then used to track total number of buildings and total building height built by metro area over time.

Here is a static version of worldwide skyscraper distribution.

<img src="https://github.com/robertialenti/Canadian-Place-Name-Etymology/raw/main/output/static_map.png">

You can also view an [animation of worlwide skyscraper construction](https://robertialenti.github.io/Skyscrapers/output/animated_map.html).

### 5. Application
The ShinyApp can be accessed here: https://robertialenti.shinyapps.io/application/

As Skyscraperpage's privacy policy asks that data is not published publicly, I choose not to post the dataset in this repository.



