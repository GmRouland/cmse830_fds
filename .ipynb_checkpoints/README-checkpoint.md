I've chosen this dataset because it is adjacent to my field of research. I also find groundwater levels to be an extremely important but often overlooked environmental feature that is very interesting to discuss.
The longitudinal and latitudinal data present in this also gives me the opportunity to create some type of interactive map which I am very excited to do. 

Progress Summary
A key list is below;
groupby(): My data comprises of a series of well stations located in central California with daily data collected over multiple years. It is a very expansive data set and the station names are long so I was able to add .ngroup to encode each station with a number.

.interpolate: my dataset comprised of time series data and groundwater levels have relatively minimal change on a daily basis so I interpolated between missing datapoints based on the datetime data that I had. I found the data to be MCAR after sorting the data by station.
After this interpolation, almost all of my data had values, except for a few sections. I discovered these sections represented wells that had no data in multiple categories and thus removed them as there was no starting point to fill the data from. 

I learned how to start utilizing folium, which has a convenient integration with streamlit that allows for me to develop a code that can react to map interations. I created a map with markers and was able to upload to streamlit. 


My data is in multiple different forms so it will take some time for me to fully understand what it represents and how to do a more detailed EDA. 

Next Steps: 

I want to perform more detailed EDA and understand how location, surface elevation, and other factors may impact groundwater levels. 
I want to improve my streamlit site beyond the basics and add in interactivity; 
  Ability to click a location on the map and find the nearest well stations for analysis.
  Ability to select any number of stations and compare their statistics and data side by side through multiple graphs. 
  Sliders on the date range for plots. 
  Let the user set thresholds/search for wells that meet certain conditions. 

I also have learned how to utilize github desktop to make pushing files to github simple. 
