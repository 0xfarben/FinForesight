import logging
import os
import requests
import time
from typing import Dict, Any, List
from datetime import datetime
import json

logger = logging.getLogger(__name__)

# List of backup API keys - these would typically be stored securely, not in code
BACKUP_KEYS = [
    os.environ.get('ALPHA_VANTAGE_API_KEY'),  # Primary key from environment
]

def fetch_indicator(symbol, function, interval, time_period, series_type='close', apikey=None):
    """
    Fetches a technical indicator from Alpha Vantage.

    Parameters:
    - symbol: Ticker symbol (e.g., 'IBM').
    - function: Indicator function (e.g., 'ADX', 'SMA').
    - interval: Data interval ('1min', '5min', '15min', '30min', '60min', 'daily', 'weekly', 'monthly').
    - time_period: Time period (integer, e.g., 10).
    - series_type: Price type ('close', 'open', 'high', 'low').
    - apikey: Alpha Vantage API key (defaults to env var ALPHA_VANTAGE_API_KEY).

    Returns a dict mapping timestamp -> indicator values.
    """
    # Try with the provided key first
    if apikey:
        result = try_fetch_with_key(symbol, function, interval, time_period, series_type, apikey)
        if result and "Error Message" not in result and "Information" not in result:
            # Save successful API response to JSON file
            try:
                os.makedirs('data_archive', exist_ok=True)
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                file_path = os.path.join('data_archive', f'{symbol}_{function}_{interval}_{timestamp}.json')
                with open(file_path, 'w') as f:
                    json.dump(result, f, indent=4)
                logger.info(f"Technical indicator data saved to {file_path}")
            except Exception as e:
                logger.error(f"Error saving technical indicator data to file: {str(e)}")
            return result
    
    # Try with backup keys
    for key in BACKUP_KEYS:
        if key and key != apikey:  # Skip if same as provided key
            result = try_fetch_with_key(symbol, function, interval, time_period, series_type, key)
            if result and "Error Message" not in result and "Information" not in result:
                # Save successful API response to JSON file
                try:
                    os.makedirs('data_archive', exist_ok=True)
                    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                    file_path = os.path.join('data_archive', f'{symbol}_{function}_{interval}_{timestamp}.json')
                    with open(file_path, 'w') as f:
                        json.dump(result, f, indent=4)
                    logger.info(f"Technical indicator data saved to {file_path}")
                except Exception as e:
                    logger.error(f"Error saving technical indicator data to file: {str(e)}")
                return result
    
    # If we get here, all keys failed or no valid keys available
    return {"Error Message": "Could not fetch data. API keys may be missing, invalid, or rate limited."}


def try_fetch_with_key(symbol, function, interval, time_period, series_type, apikey):
    """Helper function to try fetching with a specific API key"""
    try:
        base_url = "https://www.alphavantage.co/query"
        
        # Build parameters based on indicator type
        params = {
            "symbol": symbol,
            "function": function,
            "interval": interval,
            "time_period": time_period,
            "series_type": series_type,
            "apikey": apikey
        }
        
        # Special handling for certain indicators
        if function in ["BBANDS", "MACD", "STOCH", "STOCHF", "MACDEXT", "AROON", "AROONOSC", "ADOSC"]:
            # These have additional parameters but we'll use defaults
            pass
        elif function in ["AD", "OBV", "TRANGE", "HT_TRENDLINE", "HT_SINE", "HT_TRENDMODE", "HT_DCPERIOD", "HT_DCPHASE", "HT_PHASOR"]:
            # These don't need time_period or series_type
            params.pop("time_period", None)
            params.pop("series_type", None)
        
        # Make the request
        response = requests.get(base_url, params=params)
        
        if response.status_code != 200:
            logger.warning(f"Failed API request: {response.status_code}")
            return None
            
        data = response.json()
        
        # Check for API errors
        if "Error Message" in data:
            logger.warning(f"API error: {data['Error Message']}")
            return data
        
        if "Information" in data:
            logger.warning(f"API info: {data['Information']}")
            return data
        
        # Parse the results
        result_key = None
        for key in data.keys():
            if key.startswith("Technical Analysis"):
                result_key = key
                break
        
        if not result_key:
            logger.warning(f"Unexpected API response format: {list(data.keys())}")
            return {"Error Message": "Unexpected API response format"}
            
        # Return the time series data
        return data[result_key]
            
    except Exception as e:
        logger.error(f"Error fetching indicator: {e}")
        return {"Error Message": str(e)}
