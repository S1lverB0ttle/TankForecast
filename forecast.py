import numpy as np
import pandas as pd
from statsmodels.tsa.seasonal import seasonal_decompose
from statsmodels.tsa.statespace.sarimax import SARIMAX
import statsmodels.api as sm
from sklearn.metrics import mean_squared_error, mean_absolute_error


def find_best_order(series):
    acf_values = sm.tsa.acf(series, fft=True, nlags=40)
    pacf_values = sm.tsa.pacf(series, nlags=40)
    p = next((i for i, x in enumerate(pacf_values) if abs(x) < 0.5), 0)
    
    # Define a range for the MA parameter
    ma_range = range(0,8)  # Example range from 1 to 7
    
    # Define a range for the differencing parameter d
    d_range = range(0,4)  # Example range from 0 to 2
    
    # Iterate over the MA and d ranges to find the best order
    best_aic = float('inf')
    best_ma = 0
    best_d = 0
    for ma in ma_range:
        for d in d_range:
            model = SARIMAX(series, order=(p, d, ma))
            results = model.fit(disp=False, maxiter = 5000)
            aic = results.aic
            if aic < best_aic:
                best_aic = aic
                best_ma = ma
                best_d = d
    
    
    return p, best_d, best_ma

def forecast_next_n_days(df, column, n, holiday_dates):
    try:
        # Prepare holiday indicator variables
        df['is_holiday'] = df.index.isin(holiday_dates).astype(int)

        # Apply SARIMAX model to the entire data with holiday indicators
        exog_data = df[['is_holiday']]
        decomposition = seasonal_decompose(df[column], model='additive', period=365)
        deseasonalized_data = df[column] - decomposition.seasonal
        sarimax_order = find_best_order(df[column])
        model_sarimax = SARIMAX(deseasonalized_data, exog=exog_data, order=sarimax_order, enforce_stationarity=False, enforce_invertibility=False)
        model_fit_sarimax = model_sarimax.fit(disp=False)

        # Forecast for the next n days
        forecast_index = pd.date_range(start=df.index[-1], periods=n + 1, freq='D')[1:]  # Exclude the current date
        exog_forecast = pd.DataFrame({'is_holiday': [1 if date in holiday_dates else 0 for date in forecast_index]}, index=forecast_index)
        forecast_sarimax = model_fit_sarimax.forecast(steps=n, exog=exog_forecast)

        # Evaluate forecast metrics
        mse = mean_squared_error(deseasonalized_data[-n:], forecast_sarimax)
        mae = mean_absolute_error(deseasonalized_data[-n:], forecast_sarimax)
        rmse = np.sqrt(mse)

        return column, forecast_index, forecast_sarimax, mse, mae, rmse

    except Exception as e:
        print(f"Failed to fit SARIMAX model for {column}: {e}")
        return column, None, np.full(n, np.nan), np.nan, np.nan, np.nan