
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
Key_data['MSMT_DATE'] = pd.to_datetime(Key_data['MSMT_DATE'])
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
california = folium.Map(max_bounds = True, location=[36.7783, -119.4179], zoom_start=6, min_lat=36,max_lat=40,min_lon=-124,max_lon=-119)

### Site
st.title("Analyzing Central California Groundwater")
station_short = station[station['STATION'].isin(Uniq_Stats)]
tab1, tab2 = st.tabs(['Introduction', "Initial Analysis and Data Prep"])

#Functions
def Line_stat(station = 0, parameter = 'GSE_WSE'):
    data = Data_Final[Data_Final['Station_Num'] == station]
    fig = plt.figure(figsize = (18,10))
    plot = plt.plot(data['MSMT_DATE'],data[parameter])
    plt.tight_layout()
    return fig

with tab1:
    st.header("Introduction")
    st.write("Overview")
    st.pyplot(Line_stat(10))


with tab2:
    st.header("Initial Analysis and Data Prep")
    #plot of spectral signatures
    st.write("Map")
    for i in Coords.index:
     folium.Marker(
        location= [Coords.iloc[i,0],Coords.iloc[i,1]],
        tooltip= 'Click Me',  # Optional: tooltip on hover
        popup = f'Station {i}'
    ).add_to(california)
    st_data = st_folium(california, width=725)
    
