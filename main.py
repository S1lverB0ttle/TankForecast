import logging
import holidays
from preprocessing import get_indian_holidays
import pandas as pd
from warnings import filterwarnings
from flask import Flask, jsonify, request
from flask_restful import Api, Resource, reqparse
from datetime import datetime
from forecast import forecast_next_n_days
from preprocessing import preprocess_data
from configparser import ConfigParser
import os

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
api = Api(app)

# Define parser for request arguments
parser = reqparse.RequestParser()
parser.add_argument('start_date', type=lambda x: datetime.strptime(x, '%d-%m-%Y'))
parser.add_argument('end_date', type=lambda x: datetime.strptime(x, '%d-%m-%Y'))

def get_indian_holidays(year):
    return holidays.India(years=year)

def read_config():
    config = ConfigParser()
    if os.path.exists('config.ini'):
        config.read('config.ini')
    else:
        # Create a new config.ini with default values
        config['File'] = {'file_path': 'tank_levels.xlsx'}
        with open('config.ini', 'w') as configfile:
            config.write(configfile)
    return config

def read_data():
    config = read_config()
    file_path = config.get('File', 'file_path')
    df = pd.read_excel(file_path, index_col=0)
    return df


class TankForecast(Resource):
    def get(self):
        filterwarnings('ignore')
        # Read data from Excel and preprocess
        df = read_data()
        
        # Get the current year
        current_year = datetime.now().year
        
        # Get holiday dates for the current year
        holiday_dates = get_indian_holidays(current_year)
        
        # Preprocess the data for the current year
        df = preprocess_data(df, current_year)
        
        all_forecasts = []

        for column in ['Tank1', 'Tank14']:
            # Forecasting for each column
            forecast_result = forecast_next_n_days(df, column, 30, holiday_dates)
            if forecast_result:
                column, forecast_index, forecast_values, mse, mae, rmse = forecast_result
                forecast_data = [{
                    'date': date.strftime('%d-%m-%Y'),  
                    'value': round(value,3)
                } for date, value in zip(forecast_index, forecast_values)]
                forecast_info = {
                    'tank': column,
                    'forecast': forecast_data,
                }
                all_forecasts.append(forecast_info)

        print(f"MSE:{mse}, MAE:{mae}, RMSE:{rmse}")
        return jsonify(all_forecasts)
    

class Sample(Resource):
    def post(self):
        filterwarnings('ignore')
        args = parser.parse_args()
        start_date = args['start_date'].date()
        end_date = args['end_date'].date()
        year = start_date.year  # Extract year from start_date
        
        # Read data from Excel and preprocess
        df = read_data()
        
        # Get holiday dates for the specified year
        holiday_dates = get_indian_holidays(year)
        
        # Preprocess the data for the specified year
        df = preprocess_data(df, year)
        
        all_forecasts = []

        for column in ['Tank1', 'Tank14']:
            # Forecasting from start date to end date
            forecast_result = forecast_next_n_days(df, column, (end_date - start_date).days + 1, holiday_dates)
            if forecast_result:
                column, forecast_index, forecast_values, mse, mae, rmse = forecast_result
                date_range = [start_date + pd.DateOffset(days=i) for i in range((end_date - start_date).days + 1)]
                forecast_data = [{
                    'date': date.strftime('%d-%m-%Y'),
                    'value': round(value,3)
                } for date, value in zip(date_range, forecast_values)]
                forecast_info = {
                    'tank': column,
                    'forecast': forecast_data,
                }
                all_forecasts.append(forecast_info)

        return jsonify(all_forecasts)
    

api.add_resource(TankForecast, '/tank_forecast')
api.add_resource(Sample, '/tank_forecast_with_dates')

if __name__ == '__main__':
    # Run the Flask app
    app.run(debug=True)