
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import streamlit as st 
import seaborn as sns
import folium
import warnings
from streamlit_folium import st_folium
from statsmodels.tsa.stattools import adfuller, kpss
from statsmodels.graphics.tsaplots import plot_acf, plot_pacf
from statsmodels.tsa.arima.model import ARIMA
from sklearn.metrics import mean_squared_error

### Beginning
## Additional optimization for memory purposes done with Google AI Studio version 2.5 11/10/25
#Changing the datatypes from default ones like float64 to float 32 in order to improve memory utilization
station_dtypes = {
    'STATION': 'category',
    'LATITUDE': 'float32',
    'LONGITUDE': 'float32'
}

daily_dtypes = {
    'STATION': 'category',
    'WLM_RPE': 'float32',
    'WLM_GSE': 'float32',
    'RPE_WSE': 'float32',
    'GSE_WSE': 'float32',
    'WSE': 'float32'
}
#Directly Loading Columns in to minimize copies of large data table
daily_cols = ['STATION','MSMT_DATE','WLM_RPE','WLM_GSE','RPE_WSE', 'GSE_WSE','WSE']
station_cols = ['STATION', 'LATITUDE', 'LONGITUDE']
daily = pd.read_csv('dailydata.csv', usecols=daily_cols, dtype=daily_dtypes)
station = pd.read_csv('gwl-stations.csv', usecols=station_cols, dtype=station_dtypes)
Key_data = pd.merge(daily, station, on = 'STATION', how = 'inner')
Key_data['MSMT_DATE'] = pd.to_datetime(Key_data['MSMT_DATE'], errors='coerce')
Key_data = Key_data.dropna(subset=['MSMT_DATE'])
Key_data['MSMT_DATE'] = Key_data['MSMT_DATE'].dt.floor('min')
Sort_KD = Key_data.sort_values(by = ['STATION', 'MSMT_DATE'], ascending = True).copy()
Sort_KD['STATION'] = Sort_KD['STATION'].astype(str)
Sort_KD = Sort_KD.set_index('MSMT_DATE')
sns.set_theme()
#This section was completed with the assistance of Google AI Studio version 2.5 10/15/25
# Group by 'STATION', select the 'value' column, and apply interpolation.
# The lambda function operates on each group (each station's data) separately.
#Try to identify stations that require ffill and bfill and only apply to those ones
Sort_KD['RPE_WSE'] = Sort_KD.groupby('STATION')['RPE_WSE'].transform(
    lambda group: group.interpolate(method='time').ffill().bfill())
Sort_KD['GSE_WSE'] = Sort_KD.groupby('STATION')['GSE_WSE'].transform(
    lambda group: group.interpolate(method='time').ffill().bfill())
Sort_KD['WSE'] = Sort_KD.groupby('STATION')['WSE'].transform(
    lambda group: group.interpolate(method='time').ffill().bfill())
#del unecessary stations
# Reset the index to bring 'MSMT_DATE' back as a regular column
Sort_KD = Sort_KD.reset_index()
Sort_KD['MSMT_DATE'] = Sort_KD['MSMT_DATE'].dt.floor('min')
droplist = (Sort_KD['STATION'][Sort_KD['GSE_WSE'].isnull()].unique())
Data_Final = Sort_KD[~Sort_KD['STATION'].isin(droplist)].copy()
Data_Final['Station_Num'] = Data_Final.groupby('STATION').ngroup()
Coords = Data_Final.groupby('Station_Num')[['LATITUDE', 'LONGITUDE']].first()
#Done with the assistance of Google AI Studio Gemini 2.5 10/15/25
st.set_page_config(layout="wide")

### Site
st.title("Analyzing Central California Groundwater")
tab1, tab2, tab3 = st.tabs(['Introduction', "Initial Analysis and Data Prep", "Individual Station Analysis"])

#Functions
def Line_stat(station = 0, parameter = 'GSE_WSE'):
    data = Data_Final[Data_Final['Station_Num'] == station]
    fig = plt.figure(figsize = (18,10))
    plot = plt.plot(data['MSMT_DATE'],data[parameter])
    plt.title(f'Analysis of {parameter} at Station {station}')
    plt.ylabel(f'{parameter} (feet)')
    plt.tight_layout()
    return fig
def autocor(series, parameter = 'GSE_WSE'):
    fig, axes = plt.subplots(3, 1, figsize=(12, 10))
    # station_data = Data_Final[Data_Final['Station_Num'] == station]
    data = series
    axes[0].plot(data.index, data.values)
    axes[0].set_title('Time Series')
    axes[0].set_ylabel('Value')
    axes[0].grid(True, alpha=0.3)
                
    # ACF
    plot_acf(data, lags=40, ax=axes[1], alpha=0.05)
    axes[1].set_title('Autocorrelation Function')
                
    # PACF  
    plot_pacf(data, lags=40, ax=axes[2], alpha=0.05)
    axes[2].set_title('Partial Autocorrelation Function')
    st.pyplot(fig)            
    
def comprehensive_stationarity_test(station, parameter = 'GSE_WSE', name='Series',auto_diff= True):
    """Run ADF and KPSS tests with interpretation for Streamlit"""
    
    if auto_diff == True:
        station_data = Data_Final[Data_Final['Station_Num'] == station]
        series = station_data[parameter]
    else:
        station_data = Data_Final[Data_Final['Station_Num'] == station]
        series = station_data[parameter].diff().dropna()
    st.subheader(f"Stationarity Tests for {name}")
    
    # Create two columns for side-by-side comparison
    col1, col2 = st.columns(2)
    
    # --- ADF Test (H0: unit root / non-stationary) ---
    with col1:
        st.markdown("#### 1. ADF Test")
        st.caption("Null Hypothesis (H0): Non-stationary")
        
        adf_result = adfuller(series, autolag='AIC')
        
        # Display metrics nicely
        st.write(f"**Test Statistic:** {adf_result[0]:.4f}")
        st.write(f"**p-value:** {adf_result[1]:.4f}")
        st.write(f"**Lags used:** {adf_result[2]}")
        
        if adf_result[1] < 0.05:
            adf_conclusion = "STATIONARY"
            st.success("✓ Reject H0: Evidence for stationarity")
        else:
            adf_conclusion = "NON-STATIONARY"
            st.warning("✗ Fail to reject H0: Evidence for unit root")

    # --- KPSS Test (H0: stationary) ---
    with col2:
        st.markdown("#### 2. KPSS Test")
        st.caption("Null Hypothesis (H0): Stationary")
        
        # Catch warnings often thrown by KPSS
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            kpss_result = kpss(series, regression='c', nlags='auto')
        
        st.write(f"**Test Statistic:** {kpss_result[0]:.4f}")
        st.write(f"**p-value:** {kpss_result[1]:.4f}")
        st.write(f"**Lags used:** {kpss_result[2]}")
        
        if kpss_result[1] > 0.05:
            kpss_conclusion = "STATIONARY"
            st.success("✓ Fail to reject H0: Evidence for stationarity")
        else:
            kpss_conclusion = "NON-STATIONARY"
            st.warning("✗ Reject H0: Evidence for non-stationarity")
    
    # --- Combined interpretation ---
    st.divider()
    st.markdown("### Combined Interpretation")
    
    if adf_conclusion == "STATIONARY" and kpss_conclusion == "STATIONARY":
        st.success("✓✓ Both tests agree: Series is **STATIONARY**")
        st.info("→ Use AR(p) model without differencing")
        recommendation = "stationary"
        autocor(series)
    elif adf_conclusion == "NON-STATIONARY" and kpss_conclusion == "NON-STATIONARY":
        st.warning("✓✓ Both tests agree: Series is **NON-STATIONARY**")
        st.info("→ Difference the series, or use ARIMA(p,1,q)")
        recommendation = "non-stationary"
        
    else:
        st.error("⚠⚠ Tests DISAGREE - investigate further")
        st.markdown("""
        **Possible causes:**
        * Structural breaks in the data
        * Near unit root (highly persistent but stationary)
        * Small sample size
        
        **Recommendation:** Check for breaks, try differencing, and retest.
        """)
        recommendation = "ambiguous"
        if auto_diff and recommendation in ['non-stationary', 'ambiguous']:
            st.markdown("---")
            st.info(f"📉 Since {name} is {recommendation}, automatically testing First Difference...")
        
        # Recursive call: Pass auto_diff=False so we only diff once (prevents infinite loop)
            comprehensive_stationarity_test(station, parameter = 'GSE_WSE',name=f"First Diff of {name}", auto_diff=False)

            
    return {
        'adf_statistic': adf_result[0],
        'adf_pvalue': adf_result[1],
        'kpss_statistic': kpss_result[0],
        'kpss_pvalue': kpss_result[1],
        'recommendation': recommendation
    }
def fit_ar_manual(data, p):
    """
    Fit AR(p) model using ordinary least squares
    
    Parameters
    ----------
    data : array-like
        Time series data (1D array or Series)
    p : int
        Number of autoregressive lags
        
    Returns
    -------
    coefficients : ndarray
        Estimated coefficients [c, φ_1, φ_2, ..., φ_p]
        where c is the constant/intercept term
    """
    data = np.asarray(data).flatten()
    T = len(data)
    
    # Step 1: Create design matrix X (T-p rows, p+1 columns)
    X = np.ones((T - p, p + 1))  # Initialize with ones for constant
    
    # Fill in lagged values
    for i in range(p):
        X[:, i + 1] = data[p - 1 - i : T - 1 - i]
    
    # Step 2: Create response vector y (T-p rows)
    y = data[p:]
    
    # Step 3: Solve using OLS: β = (X'X)^(-1) X'y
    # Using lstsq is numerically more stable than computing inverse explicitly
    coefficients, _, _, _ = np.linalg.lstsq(X, y, rcond=None)
    
    return coefficients


def forecast_ar_manual(data, coefficients, steps):
    """
    Generate multi-step forecasts from fitted AR model
    
    Parameters
    ----------
    data : array-like
        Historical time series data
    coefficients : ndarray
        Model coefficients [c, φ_1, φ_2, ..., φ_p]
    steps : int
        Number of steps ahead to forecast
        
    Returns
    -------
    forecasts : ndarray
        Array of forecasted values
    """
    data = np.asarray(data).flatten()
    p = len(coefficients) - 1
    c = coefficients[0]
    phi = coefficients[1:]
    
    # Initialize history with last p observations
    history = list(data[-p:])
    
    forecasts = []
    for _ in range(steps):
        # One-step forecast: c + φ_1*y_{t-1} + φ_2*y_{t-2} + ... + φ_p*y_{t-p}
        yhat = c + sum(phi[i] * history[-(i + 1)] for i in range(p))
        forecasts.append(yhat)
        history.append(yhat)  # Add forecast to history for next iteration
    
    return np.array(forecasts)

# Actual Streamlit Site
with tab1:
    #use .head() to show a portion of full dataframe 
    st.header("Introduction")
    st.write("Our Variables")
    st.markdown("""* Station = Unique Station identifier for most also well number 
    * MSMT_Data = Date/Time in PST when collected
    * WLM_RPE = Reference Point Elevation used to collect measurement (feet)
    * WLM_GSE = Ground surface elevation at well site (feet)
    * RPE_WSE = Depth to the water surface in feet below the reference point (feet)
    * GSE_WSE = Depth below ground surface or distance from ground surface to
    water surface in feet (feet)
    * WSE = Water Surface Elevation in feet above Mean Sea Level (feet)
    * Longitude
    * Latitude """)
    st.write("Initial Dataframes")
    col1, col2 = st.columns(2)
    with col1:
        st.write('This is the daily data at every station, with the earliest data from 1992')
        st.dataframe(daily.head())
    with col2:
        st.write('This dataframe contains the information about the stations, the coordinates are the important part')
        st.dataframe(station.head())
    st.write('I combined the datasets and began to analyze for missingness')
    st.dataframe(Key_data.head())
    st.write('The basic statistics of the key dataset is shown below.')
    st.dataframe(Key_data.describe())
    #sns.heatmap(Sort_KD.isnull(), cbar=False, yticklabels=False, cmap='viridis', ax=ax)
    #I originally wanted to do a heatmap but that consumed too much memory to run successfully
    st.subheader("Percentage of Missing Data per Column")

    # Calculate the percentage of nulls in each column
    missing_percentage = Sort_KD.isnull().mean() * 100

    # Display the percentages in a table for clarity
    st.write(missing_percentage)

    # Create a bar chart for easy visualization
    st.bar_chart(missing_percentage)
    st.write("I sorted the data, encoded each station label to have it's own numeric label for easier reading and mapping and found there was no change in the missingness when sorted by station.")
    st.write("Based on this I found the data to be MCAR and decided to proceed with a simple interpolation. Groundwater data does not drastically shift on a daily basis so interpolating between dates was suitable.")
    st.write("There were a few stations still missing data after interpolation. I discovered these were completely missing all data and decided to remove them due to this. A significant portion of the data remained")
with tab2:
    st.header("Initial Analysis and Data Prep")
   #California map showing sites
    #fig, ax = plt.subplots(figsize=(8, 10))
    #sns.heatmap(Key_data.isnull(), cbar=False, yticklabels=False, cmap='viridis', ax=ax)
    #ax.set_title('Sorted Data before Removing Completely Missing Data')
    #plt.tight_layout()
    #st.pyplot(fig)
    california = folium.Map(max_bounds = True, location=[36.7783, -119.4179], zoom_start=6, min_lat=36,max_lat=40,min_lon=-124,max_lon=-119)
for i in Coords.index:
    folium.CircleMarker(
    location= [Coords.iloc[i,0],Coords.iloc[i,1]], radius = 5, 
    tooltip= 'Click Me',  # Optional: tooltip on hover
    popup = f'Station {i}'
    ).add_to(california)
st.write("I am utiliziing the streamlit_folium integration to add interactability to the map.")
st_data = st_folium(california, width=725)
    
with tab3:
    #Done with the assistance of Google AI Studio Gemini 2.5 10/19/25
    st.header("Individual Station Analysis")
    st.markdown("""* Station = Unique Station identifier for most also well number 
    * MSMT_Data = Date/Time in PST when collected
    * WLM_RPE = Reference Point Elevation used to collect measurement (feet)
    * WLM_GSE = Ground surface elevation at well site (feet)
    * RPE_WSE = Depth to the water surface in feet below the reference point (feet)
    * GSE_WSE = Depth below ground surface or distance from ground surface to
    water surface in feet (feet)
    * WSE = Water Surface Elevation in feet above Mean Sea Level (feet)
    * Longitude
    * Latitude """)
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
                comprehensive_stationarity_test(station_num,parameter, f'Station {station_num}')
                # Split data into train/test
                # Hold out last 30 days for testing
                station_data = Data_Final[Data_Final['Station_Num'] == station_num]
                data = station_data[parameter].diff().dropna()
                train_size = len(data) - 30
                train = data[:train_size]
                test = data[train_size:]
                
                print(f"Training size: {len(train)} days")
                print(f"Test size: {len(test)} days")
                
                # Fit with your implementation
                p = 3  # Start with AR(5)
                print(f"\nFitting AR({p}) model...")
                
                manual_coef = fit_ar_manual(train.values, p)
                manual_forecast = forecast_ar_manual(train.values, manual_coef, len(test))
                
                # Compare with statsmodels ARIMA
                arima_model = ARIMA(train, order=(p, 0, 0))
                arima_fit = arima_model.fit()
                arima_forecast = arima_fit.forecast(steps=len(test))
                
                # Validation
                print("\n" + "="*70)
                print("VALIDATION: Your Implementation vs. Statsmodels ARIMA")
                print("="*70)
                
                print(f"\nCoefficients comparison:")
                print(f"Your implementation:  {manual_coef}")
                print(f"ARIMA implementation: {arima_fit.params.values}")
                coef_diff = np.abs(manual_coef - arima_fit.params.values).max()
                print(f"Maximum difference:   {coef_diff:.8f}")
                
                if coef_diff < 0.001:
                    print("✓ Coefficients match! (difference < 0.001)")
                else:
                    print("✗ Coefficients don't match - check your implementation")
                
                print(f"\nForecast comparison:")
                manual_rmse = np.sqrt(mean_squared_error(test, manual_forecast))
                arima_rmse = np.sqrt(mean_squared_error(test, arima_forecast))
                print(f"Your RMSE:   {manual_rmse:.4f}")
                print(f"ARIMA RMSE:  {arima_rmse:.4f}")
                forecast_diff = np.abs(manual_forecast - arima_forecast).max()
                print(f"Maximum forecast difference: {forecast_diff:.8f}")
                
                if forecast_diff < 0.0001:
                    print("✓ Forecasts match! (difference < 0.0001)")
                else:
                    print("✗ Forecasts don't match - check your implementation")
                
                print("="*70)
                
                # Visualization
                fig, axes = plt.subplots(2, 1, figsize=(14, 10))
                
                # Full series with train/test split
                axes[0].plot(train.index, train.values, label='Training Data', alpha=0.7, linewidth=0.5)
                axes[0].plot(test.index, test.values, label='Actual Test Data', linewidth=1.5, color='black')
                axes[0].plot(test.index, manual_forecast, '--', label='Your AR Forecast', linewidth=2)
                axes[0].plot(test.index, arima_forecast, ':', label='ARIMA Forecast', linewidth=2, alpha=0.7)
                axes[0].axvline(train.index[-1], color='red', linestyle='--', alpha=0.5, label='Train/Test Split')
                axes[0].axhline(0, color='gray', linestyle='-', alpha=0.3, linewidth=0.5)
                axes[0].legend()
                axes[0].set_title(f'AR({p}) Forecast: {your_series_name}')
                axes[0].set_ylabel('Return (%)')
                axes[0].grid(True, alpha=0.3)
                
                # Zoom in on test period
                axes[1].plot(test.index, test.values, 'o-', label='Actual', linewidth=2, markersize=4)
                axes[1].plot(test.index, manual_forecast, 's--', label='Your Forecast', linewidth=2, markersize=4)
                axes[1].plot(test.index, arima_forecast, '^:', label='ARIMA Forecast', linewidth=2, 
                             markersize=4, alpha=0.7)
                axes[1].axhline(0, color='gray', linestyle='-', alpha=0.3)
                axes[1].legend()
                axes[1].set_title('Test Period Detail')
                axes[1].set_xlabel('Date')
                axes[1].set_ylabel('Return (%)')
                axes[1].grid(True, alpha=0.3)
                
                st.pyplot(fig)
            else:
                st.error(f"Station number {station_num} is not valid. Please enter a number between 0 and {max_station_num}.")

        except ValueError:
            st.error("Invalid input. Please enter a valid integer for the station number.")
    else:
        st.info("Enter a station number above to see its data and location.")
