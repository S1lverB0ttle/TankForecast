
import pandas as pd
import holidays
import scipy.stats as stats

def get_indian_holidays(year):
    return holidays.India(years=year)

def preprocess_data(df, year):
    df.index = pd.to_datetime(df.index)
    df = df.sort_index()
    df.index.freq = pd.infer_freq(df.index)
    df = df.ffill()
    
    # Add a column for holidays
    indian_holidays = get_indian_holidays(year)
    df['is_holiday'] = df.index.map(lambda x: 1 if x in indian_holidays else 0)
    
    return df