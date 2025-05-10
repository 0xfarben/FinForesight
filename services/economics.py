import os
import logging
import requests
from datetime import datetime, timedelta
import json

logger = logging.getLogger(__name__)

def get_economic_indicators():
    """
    Get economic indicators from FRED API
    
    Returns:
        dict: Economic indicators data
    """
    try:
        # Get API key from environment variable
        api_key = os.environ.get('FRED_API_KEY')
        if not api_key:
            logger.warning("FRED API key not set, returning sample data")
            return get_sample_economic_data()
        
        # Define indicators to fetch
        indicators = {
            'GDP': 'GDP',  # Gross Domestic Product
            'UNRATE': 'Unemployment Rate',  # Unemployment Rate
            'CPIAUCSL': 'Consumer Price Index',  # Consumer Price Index for All Urban Consumers
            'FEDFUNDS': 'Federal Funds Rate',  # Federal Funds Effective Rate
            'T10Y2Y': 'Treasury Yield Spread',  # 10-Year Treasury Constant Maturity Minus 2-Year Treasury Constant Maturity
            'INDPRO': 'Industrial Production',  # Industrial Production Index
            'HOUST': 'Housing Starts',  # Housing Starts
            'UMCSENT': 'Consumer Sentiment',  # University of Michigan Consumer Sentiment
            'RSAFS': 'Retail Sales',  # Retail Sales
            'RRSFS': 'Real Retail Sales',  # Real Retail and Food Services Sales
            'USREC': 'Recession Indicator'  # Recession Indicator (1 = recession, 0 = no recession)
        }
        
        # Initialize results
        results = {}
        
        # FRED API base URL
        base_url = "https://api.stlouisfed.org/fred/series/observations"
        
        # Get date range (past 2 years)
        end_date = datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=730)).strftime('%Y-%m-%d')
        
        # Fetch data for each indicator
        for series_id, name in indicators.items():
            params = {
                'series_id': series_id,
                'api_key': api_key,
                'file_type': 'json',
                'observation_start': start_date,
                'observation_end': end_date,
                'sort_order': 'desc',
                'limit': 1000  # Get all available data points
            }
            
            response = requests.get(base_url, params=params)
            
            if response.status_code != 200:
                logger.warning(f"Failed to fetch {name} data: {response.status_code}")
                continue
                
            data = response.json()
            
            if 'observations' not in data:
                logger.warning(f"No observations found for {name}")
                continue
                
            # Extract data points
            values = []
            for obs in data['observations']:
                if obs['value'] == '.':  # Missing data
                    continue
                    
                values.append({
                    'date': obs['date'],
                    'value': float(obs['value']) if obs['value'] not in ['.', ''] else None
                })
                
            if not values:
                logger.warning(f"No valid values found for {name}")
                continue
                
            # Calculate changes
            if len(values) > 1:
                current = values[0]['value']
                previous = values[1]['value']
                
                if current is not None and previous is not None and previous != 0:
                    change_pct = ((current - previous) / previous) * 100
                else:
                    change_pct = None
            else:
                change_pct = None
                
            # Store results
            results[series_id] = {
                'name': name,
                'current_value': values[0]['value'] if values else None,
                'change_pct': change_pct,
                'latest_date': values[0]['date'] if values else None,
                'values': values[:20]  # Limit to recent values
            }
            
        if not results:
            logger.warning("No economic data retrieved, returning sample data")
            return get_sample_economic_data()
            
        # Save results to JSON file
        try:
            os.makedirs('data_archive', exist_ok=True)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            file_path = os.path.join('data_archive', f'economics_fred_{timestamp}.json')
            with open(file_path, 'w') as f:
                json.dump(results, f, indent=4)
            logger.info(f"Saved FRED economic data to {file_path}")
        except Exception as e:
            logger.error(f"Error saving FRED economic data to file: {str(e)}")
            
        return results
        
    except Exception as e:
        logger.error(f"Error getting economic indicators: {e}")
        return get_sample_economic_data()


def get_sample_economic_data():
    """
    Return sample economic data if FRED API is unavailable
    """
    logger.info("Using sample economic data")
    return {
        'GDP': {
            'name': 'Gross Domestic Product',
            'current_value': 26948.473,
            'change_pct': 1.2,
            'latest_date': '2023-06-30',
            'values': [
                {'date': '2023-06-30', 'value': 26948.473},
                {'date': '2023-03-31', 'value': 26621.988},
                {'date': '2022-12-31', 'value': 26408.406},
                {'date': '2022-09-30', 'value': 26235.283},
            ]
        },
        'UNRATE': {
            'name': 'Unemployment Rate',
            'current_value': 3.8,
            'change_pct': 0.0,
            'latest_date': '2023-08-01',
            'values': [
                {'date': '2023-08-01', 'value': 3.8},
                {'date': '2023-07-01', 'value': 3.8},
                {'date': '2023-06-01', 'value': 3.6},
                {'date': '2023-05-01', 'value': 3.7},
            ]
        },
        'CPIAUCSL': {
            'name': 'Consumer Price Index',
            'current_value': 305.904,
            'change_pct': 0.2,
            'latest_date': '2023-07-01',
            'values': [
                {'date': '2023-07-01', 'value': 305.904},
                {'date': '2023-06-01', 'value': 305.294},
                {'date': '2023-05-01', 'value': 304.790},
                {'date': '2023-04-01', 'value': 304.161},
            ]
        },
        'FEDFUNDS': {
            'name': 'Federal Funds Rate',
            'current_value': 5.33,
            'change_pct': 0.0,
            'latest_date': '2023-07-01',
            'values': [
                {'date': '2023-07-01', 'value': 5.33},
                {'date': '2023-06-01', 'value': 5.08},
                {'date': '2023-05-01', 'value': 5.06},
                {'date': '2023-04-01', 'value': 4.83},
            ]
        },
        'T10Y2Y': {
            'name': 'Treasury Yield Spread',
            'current_value': -0.69,
            'change_pct': -9.5,
            'latest_date': '2023-08-25',
            'values': [
                {'date': '2023-08-25', 'value': -0.69},
                {'date': '2023-08-24', 'value': -0.63},
                {'date': '2023-08-23', 'value': -0.75},
                {'date': '2023-08-22', 'value': -0.82},
            ]
        }
    }
