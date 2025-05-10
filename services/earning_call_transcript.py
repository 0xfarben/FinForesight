import os
import requests
import logging
import json
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Get the API key from the environment
API_KEY = os.getenv('ALPHA_VANTAGE_API_KEY')

def get_earnings_call_transcript(symbol, quarter):
    """
    Get earnings call transcript for a company
    
    Args:
        symbol (str): Stock ticker symbol
        quarter (str): Quarter in format YYYYQN (e.g. 2023Q1)
        
    Returns:
        dict: Earnings call transcript data
    """
    if not API_KEY:
        logger.error("Alpha Vantage API key is missing")
        return {"error": "API key is missing! Make sure to set ALPHA_VANTAGE_API_KEY in the environment."}
    
    logger.info(f"Fetching earnings call transcript for {symbol} {quarter}")
    url = f"https://www.alphavantage.co/query?function=EARNINGS_CALL_TRANSCRIPT&symbol={symbol}&quarter={quarter}&apikey={API_KEY}"
    
    try:
        response = requests.get(url)
        response.raise_for_status()
        
        data = response.json()
        
        # Check for error messages
        if 'Error Message' in data:
            logger.error(f"Alpha Vantage API Error: {data['Error Message']}")
            return {"error": data['Error Message']}
            
        if 'Information' in data:
            logger.warning(f"Alpha Vantage API Information: {data['Information']}")
            if 'call frequency' in data['Information']:
                return {"error": "API call frequency exceeded. Please wait and try again."}
        
        # Check if transcript is available
        if not data.get('transcript'):
            logger.warning(f"No transcript available for {symbol} {quarter}")
            return {"error": f"No transcript available for {symbol} {quarter}"}
        
        # Save the transcript data to a JSON file
        try:
            os.makedirs('data_archive', exist_ok=True)
            quarter_clean = quarter.replace(' ', '_').replace('/', '_')
            file_path = os.path.join('data_archive', f"{symbol}_earnings_transcript_{quarter_clean}.json")
            with open(file_path, 'w') as f:
                json.dump(data, f, indent=4)
            logger.info(f"Saved transcript to {file_path}")
        except Exception as e:
            logger.error(f"Error saving transcript to file: {str(e)}")
            
        logger.info(f"Successfully fetched transcript for {symbol} {quarter}")
        return data
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Request error: {str(e)}")
        return {"error": f"Failed to fetch data from Alpha Vantage API: {str(e)}"}
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return {"error": f"An unexpected error occurred: {str(e)}"}

