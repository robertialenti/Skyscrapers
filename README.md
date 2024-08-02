# Worldwide Skyscraper Construction
This repository includes the code and dependencies needed to generate an animation of worldwide skyscraper construction over the period 1900-2024. The [code](https://github.com/robertialenti/Skyscrapers/blob/main/code.py) is written in a Jupyter notebook and separated into 5 sections.

## 1. Importing Libraries
In this section, I import the libraries needed to scrape, clean, and plot data.

## 2. Scraping
The building-level data is gathered from [](https://skyscraperpage.com/), which provides comprehensive coverage of large buildings across more than 7,500 cities. The scraper uses Selenium and BeautifulSoup to dynamically navigate the website and parse HTML on webpages. For each building, the scraper gathers information for the following variables of interest:

- city_id: A city-specific identifier

## 3. Geocoding

## 4. Cleaning Data

## 5. Mapping
The map is produced and animated with the Plotly Express module.
