
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import streamlit as st 
import seaborn as sns
import folium
from streamlit_folium import st_folium

### Beginning
daily = pd.read_csv('dailydata.csv')
station = pd.read_csv('gwl-stations.csv')
Uniq_Stats = list(dict.fromkeys(daily['STATION']))
Merged = pd.merge(daily, station, on = 'STATION', how = 'inner')
Key_data = Merged[['STATION','MSMT_DATE','WLM_RPE','WLM_GSE','RPE_WSE', 'GSE_WSE','WSE','LATITUDE','LONGITUDE']]
Key_data.loc['MSMT_DATE'] = pd.to_datetime(Key_data['MSMT_DATE'])
Sort_KD = Key_data.sort_values(by = ['STATION', 'MSMT_DATE'], ascending = True)
Sort_KD = Sort_KD.set_index('MSMT_DATE')
#This section was completed with the assistance of Google AI Studio version 2.5 10/15/25
# Group by 'STATION', select the 'value' column, and apply interpolation.
# The lambda function operates on each group (each station's data) separately.
Sort_KD['RPE_WSE'] = Sort_KD.groupby('STATION')['RPE_WSE'].transform(
    lambda group: group.interpolate(method='time').ffill().bfill())
Sort_KD['GSE_WSE'] = Sort_KD.groupby('STATION')['GSE_WSE'].transform(
    lambda group: group.interpolate(method='time').ffill().bfill())
Sort_KD['WSE'] = Sort_KD.groupby('STATION')['WSE'].transform(
    lambda group: group.interpolate(method='time').ffill().bfill())

# Reset the index to bring 'MSMT_DATE' back as a regular column
Sort_KD = Sort_KD.reset_index()
droplist = (Sort_KD['STATION'][Sort_KD['GSE_WSE'].isnull()].unique())
Data_Final = Sort_KD[~Sort_KD['STATION'].isin(droplist)]
Data_Final['Station_Num'] = Data_Final.groupby('STATION').ngroup()
Coords = Data_Final.groupby('Station_Num')[['LATITUDE', 'LONGITUDE']].first()
#Done with the assistance of Google AI Studio Gemini 2.5 10/15/25
california = folium.Map(max_bounds = True, location=[36.7783, -119.4179], zoom_start=6, min_lat=36,max_lat=40,min_lon=-124,max_lon=-119)
for i in Coords.index:
    folium.CircleMarker(
    location= [Coords.iloc[i,0],Coords.iloc[i,1]], radius = 5, 
    tooltip= 'Click Me',  # Optional: tooltip on hover
    popup = f'Station {i}'
    ).add_to(california)
  

### Site
st.title("Analyzing Central California Groundwater")
station_short = station[station['STATION'].isin(Uniq_Stats)]
tab1, tab2, tab3 = st.tabs(['Introduction', "Initial Analysis and Data Prep", "Individual Station Analysis"])

#Functions
def Line_stat(station = 0, parameter = 'GSE_WSE'):
    data = Data_Final[Data_Final['Station_Num'] == station]
    fig = plt.figure(figsize = (18,10))
    plot = plt.plot(data['MSMT_DATE'],data[parameter])
    plt.tight_layout()
    return fig

with tab1:
    st.header("Introduction")
    st.write("Our Variables")
    st.markdown("""* Station = Unique Station identifier for most also well number 
    * MSMT_Data = Date/Time in PST when collected
    * WLM_RPE = Reference Point Elevation used to collect measurement
    * WLM_GSE = Ground surface elevation at well site
    * RPE_WSE = Depth to the water surface in feet below the reference point
    * GSE_WSE = Depth below ground surface or distance from ground surface to
    water surface in feet
    * WSE = Water Surface Elevation in feet above Mean Sea Level
    * Longitude
    * Latitude """)
    st.write("Initial Dataframes")
    col1, col2 = st.columns(2)
    with col1:
        st.write('This is the daily data at every station, with the earliest data from 1992')
        st.dataframe(daily)
    with col2:
        st.write('This dataframe contains the information about the stations, the coordinates are the important part')
        st.dataframe(station)
    st.write('I combined the datasets and began to analyze for missingness')
    st.dataframe(Key_data)
    st.dataframe(Key_data.describe())
    fig, ax = plt.subplots(figsize=(8, 10))
    sns.heatmap(Sort_KD.isnull(), cbar=False, yticklabels=False, cmap='viridis', ax=ax)
    ax.set_title('Missing Values in the Combined Dataset')
    plt.tight_layout()
    st.pyplot(fig)

with tab2:
    st.header("Initial Analysis and Data Prep")
    st.write("I sorted the data, encoded each station label to have it's own numeric label for easier reading and mapping and found there was no change in the missingness when sorted by station.")
    st.write("Based on this I found the data to be MCAR and decided to proceed with a simple interpolation. Groundwater data does not drastically shift on a daily basis so interpolating between dates was suitable.")
    st.write("There were a few stations still missing data after interpolation. I discovered these were completely missing all data and decided to remove them due to this. A significant portion of the data remained")
   #California map showing sites
    #fig, ax = plt.subplots(figsize=(8, 10))
    #sns.heatmap(Key_data.isnull(), cbar=False, yticklabels=False, cmap='viridis', ax=ax)
    #ax.set_title('Sorted Data before Removing Completely Missing Data')
    #plt.tight_layout()
    #st.pyplot(fig)
    st.write("Map showing site locations")
    st_data = st_folium(california, width=725)
    

with tab3:
    #Done with the assistance of Google AI Studio Gemini 2.5 10/19/25
    st.header("Individual Station Analysis")
    
    # Get the valid range of station numbers for user guidance
    max_station_num = Data_Final['Station_Num'].max()
    
    # User input for station number
    station_num_input = st.text_input(
        f"Enter a Station Number (from 0 to {max_station_num}):"
    )

    if station_num_input:
        try:
            station_num = int(station_num_input)

            # Check if the entered station number is valid
            if station_num in Coords.index:
                
                # Create a two-column layout for the plot and map
                col1, col2 = st.columns(2)

                with col1:
                    st.subheader(f"Data Plot for Station {station_num}")
                    
                    # Dropdown to select which parameter to plot
                    parameter = st.selectbox(
                        "Select a parameter to plot:",
                        ('GSE_WSE', 'RPE_WSE', 'WSE'), key=f'select_{station_num}'
                    )
                    
                    # Generate and display the plot using your function
                    fig = Line_stat(station=station_num, parameter=parameter)
                    st.pyplot(fig)

                with col2:
                    st.subheader(f"Location of Station {station_num}")
                    
                    # Get coordinates for the selected station
                    station_coords = Coords.loc[station_num]
                    lat = station_coords['LATITUDE']
                    lon = station_coords['LONGITUDE']
                    
                    # Create a new Folium map centered on the selected station
                    station_map = folium.Map(location=[lat, lon], zoom_start=14)
                    folium.Marker(
                        [lat, lon],
                        popup=f"Station {station_num}",
                        tooltip=f"Station {station_num}"
                    ).add_to(station_map)
                    
                    # Display the focused map
                    st_folium(station_map, width=600, height=500)
            
            else:
                st.error(f"Station number {station_num} is not valid. Please enter a number between 0 and {max_station_num}.")

        except ValueError:
            st.error("Invalid input. Please enter a valid integer for the station number.")
    else:
        st.info("Enter a station number above to see its data and location.")
