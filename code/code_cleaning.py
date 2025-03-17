#%% Section 1: Preliminaries
# Libraries
# General
import pandas as pd
import warnings
import pycountry

# Other
warnings.filterwarnings("ignore", category=FutureWarning, message="The frame.append method is deprecated and will be removed from pandas in a future version. Use pandas.concat instead.")
pd.set_option("display.expand_frame_repr", False)

# Paths
filepath = "C:/Users/Robert/OneDrive/Desktop/Bobby/GitHub/Skyscrapers/"


#%% Section 2: Cleaning Data
# Import Geocoded Data
df = pd.read_excel(filepath + "data/geocoded_data.xlsx", usecols=lambda x: 'Unnamed' not in x)

# Trim Whitespace from String Variables
for column in df.select_dtypes(include = ["object"]).columns:
    df[column] = df[column].str.strip()

# Remove Potential Duplicate Buildings
df = df.drop_duplicates(subset = ["name_building", "address_building"]).reset_index(drop = True)

# Extract Country from Building Address
countries = [country.name for country in pycountry.countries]
df["country_building"] = df["address_building"].apply(lambda x: next((country for country in countries if country.lower() in x.lower()), None))

# Convert Year Started and Year Finished to Integer
df['year_started_building'] = pd.to_numeric(df['year_started_building'], errors='coerce')
df['year_finished_building'] = pd.to_numeric(df['year_finished_building'], errors='coerce')
df["year_started_building"] = df["year_started_building"].astype(pd.Int64Dtype())
df["year_finished_building"] = df["year_finished_building"].astype(pd.Int64Dtype())

# Convert Building Height to Metres
df = df.rename(columns = {"height_building": "height_building_ft"})
df["height_building_m"] = df["height_building_ft"]*0.3048

# Interpolate Missing Building Height
average_floor_height_m = 3.5
df["height_building_m"] = df.apply(
    lambda row: row["floors_building"] * average_floor_height_m
    if pd.isna(row["height_building_m"]) or row["height_building_m"] == 0
    else row["height_building_m"],
    axis=1,
)

# Retain Only Tall Buildings
df = df[df["height_building_m"] >= 50]

# Identify Skyscrapers
df['skyscraper'] = df['height_building_m'].apply(lambda x: True if x >= 100 else False)

# Identify Relevant Skyscrapers
relevant_uses = ["residential", "commercial", "office", "retail", "mixed use", "conference", "court", "government", "hotel", "hospital", "observation", "education"]
pattern = '|'.join(relevant_uses)
df = df[df['use_building'].str.contains(pattern, case=False, regex=True)]

# Retain Built Skyscrapers
df = df[df["status_building"] == "built"]

# Save Cleaned Data
df.to_excel(filepath + "data/cleaned_data.xlsx", index = False)
df.to_excel(filepath + "application/cleaned_data.xlsx", index = False)