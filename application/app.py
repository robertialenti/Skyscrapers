#%% Section 1: Preliminaries
# Libraries
# General
import openpyxl
import pandas as pd
from pathlib import Path

# Applications
import folium
from shiny import App, reactive, render, ui

# Paths
filepath = "C:/Users/Robert/OneDrive/Desktop/Bobby/GitHub/Skyscrapers/"


#%% Section 2: Application Development
# Import Clean Data
df = pd.read_excel(Path(__file__).parent.parent / "application/cleaned_data.xlsx")

# Remove Buildings with Missing Values
df = df.dropna()

# Retain Only Metropolitain Areas With Atleast One Skyscraper
df = df[df.groupby("name_metro_area")["skyscraper"].transform("sum") > 0]

# UI
app_ui = ui.page_fluid(
    ui.h2("Skyscrapers by Metro Area"),
    ui.HTML("""
        <p>
            This Shiny app visualizes the locations and details of buildings in metropolitan areas around the world. <br>
            The data used in the app includes building heights, completion years, and whether or not the building is classified as a skyscraper. <br>
            Only buildings with a height of at least 50 meters are shown. Skyscrapers are defined as buildings with a height of at least 100 meters. <br>
            Data is collected from SkyscraperPage, a website that tracks the construction of tall buildings.
        </p>
    """),
    ui.input_select(id="country_building", 
                    label="Choose a Country Area:", 
                    choices=sorted(df["country_building"].unique()), 
                    selected="Canada"),
    
    ui.output_ui("metro_area_ui"),  # Placeholder for dynamically updated metro area dropdown

    ui.output_ui("map_output"),
)

# Server
def server(input, output, session):
    @reactive.Calc
    def filtered_country():
        return df[df["country_building"] == input.country_building()]

    @output
    @render.ui
    def metro_area_ui():
        metro_choices = sorted(filtered_country()["name_metro_area"].unique())
        return ui.input_select(id="name_metro_area", 
                               label="Choose a Metro Area:", 
                               choices=metro_choices, 
                               selected=metro_choices[0] if metro_choices else None)

    @reactive.Calc
    def filtered_data():
        filtered = filtered_country()
        return filtered[filtered["name_metro_area"] == input.name_metro_area()]

    @reactive.Calc
    def center_coordinates():
        selected_rows = filtered_data()
        if not selected_rows.empty:
            lat = selected_rows["latitude_building"].mean()
            long = selected_rows["longitude_building"].mean()
            return lat, long
        return 0, 0  

    @output
    @render.ui
    def map_output():
        lat, lon = center_coordinates()
        map = folium.Map(location=[lat, lon], 
                         zoom_start=12, 
                         width='1600px', 
                         height='800px')

        for _, row in filtered_data().iterrows():
            popup_content = f"""
            <b>Name:</b> {row['name_building']}<br>
            <b>Address:</b> {row['address_building']}<br>
            <b>Height:</b> {round(row['height_building_m'], 2)} meters<br>
            <b>Year Completed:</b> {int(row['year_finished_building'])}<br>
            <b>Skyscraper:</b> {'Yes' if row['skyscraper'] else 'No'}
            """

            folium.Circle(
                location=[row["latitude_building"], row["longitude_building"]],
                radius=30,  
                color='blue' if row["skyscraper"] else 'gray',
                fill=True,
                fill_color='blue' if row["skyscraper"] else 'gray',
                fill_opacity=1,
                popup=folium.Popup(popup_content, max_width=500)
            ).add_to(map)

        return ui.HTML(map._repr_html_())

# Deploy Application
app = App(app_ui, server)
