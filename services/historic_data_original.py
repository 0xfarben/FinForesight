import logging
import json
import os
import pandas as pd
# import yfinance as yf
import yfinance_cache as yf
from datetime import datetime, timedelta
import numpy as np

logger = logging.getLogger(__name__)

def get_historic_data(ticker: str,
                      start_date: str = None,
                      end_date: str = None,
                      interval: str = '1d') -> pd.DataFrame:
    """
    Fetch historical OHLCV data from Yahoo Finance.

    Args:
        ticker (str): Stock ticker symbol
        start_date (str): Start date in YYYY-MM-DD format
        end_date (str): End date in YYYY-MM-DD format
        interval (str): Data interval (1d, 1wk, 1mo, etc.)

    Returns:
        DataFrame with OHLCV data
    """
    try:
        # Default to past year if no dates provided
        if not start_date:
            start_date = (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d')
        if not end_date:
            end_date = datetime.now().strftime('%Y-%m-%d')
            
        # Fetch data
        df = yf.download(ticker, start=start_date, end=end_date, interval=interval, 
                         progress=False, auto_adjust=True, multi_level_index=False)
        
        if df.empty:
            logger.warning(f"No data found for {ticker} from {start_date} to {end_date}")
            return pd.DataFrame()
            
        # Reset index to make 'Date' a column
        df = df.reset_index()
        if 'Date' not in df.columns:
            logger.error(f"Could not find 'Date' column in DataFrame for {ticker}")
            return pd.DataFrame()
        
        # Remove the extra 'date' column if it exists and is not the same as 'Date'
        if 'date' in df.columns and 'Date' in df.columns:
            df = df.drop(columns=['date'])
        
        # Convert 'Date' to string format
        df['Date'] = df['Date'].dt.strftime('%Y-%m-%d')
        
        # Convert numeric columns to float for JSON serialization
        numeric_columns = df.select_dtypes(include=[np.number]).columns
        for col in numeric_columns:
            df[col] = df[col].astype(float)
        
        # Replace NaN values with None for JSON serialization
        df = df.replace({np.nan: None})
        
        return df
        
    except Exception as e:
        logger.error(f"Error fetching historic data for {ticker}: {e}")
        return pd.DataFrame()


class DataArchiver:
    """Archive fetched data as a timestamped, timezone-aware JSON file."""
    
    def __init__(self, archive_dir: str = 'data_archive'):
        self.archive_dir = archive_dir
        os.makedirs(archive_dir, exist_ok=True)
        
    def _convert_to_json_serializable(self, value):
        """Convert pandas/numpy types to JSON serializable types."""
        if pd.isna(value):
            return None
        elif isinstance(value, (pd.Timestamp, pd.DatetimeTZDtype)):
            return value.strftime('%Y-%m-%d')
        elif isinstance(value, (np.integer, np.int64)):
            return int(value)
        elif isinstance(value, (np.floating, np.float64)):
            return float(value)
        elif isinstance(value, (int, float, str, bool)):
            return value
        else:
            return str(value)
        
    def archive_historic_data(self,
                              ticker: str,
                              start_date: str = None,
                              end_date: str = None,
                              df: pd.DataFrame = None) -> str:
        """
        Archive historical data to a JSON file.
        
        Args:
            ticker: Stock ticker symbol
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            df: DataFrame with historical data (will be fetched if not provided)
            
        Returns:
            Path to the archived JSON file
        """
        try:
            # Fetch data if not provided
            if df is None or df.empty:
                df = get_historic_data(ticker, start_date, end_date)
            
            if df.empty:
                logger.error(f"No data to archive for {ticker}")
                return f"No data available for {ticker}"
            
            # Generate timestamp for the filename
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
            # Create filename
            filename = f"{ticker}_{timestamp}.json"
            filepath = os.path.join(self.archive_dir, filename)
        
            # Convert DataFrame to list of dictionaries
            data_list = []
            for date, row in df.iterrows():
                row_dict = {}
                for col in df.columns:
                    # Convert each value to ensure it's JSON serializable
                    value = row[col]
                    if isinstance(value, (pd.Timestamp, pd.DatetimeTZDtype)):
                        value = value.strftime('%Y-%m-%d')
                    elif pd.isna(value):
                        value = None
                    elif isinstance(value, (np.integer, np.int64)):
                        value = int(value)
                    elif isinstance(value, (np.floating, np.float64)):
                        value = float(value)
                    row_dict[col] = value
                
                # Add date as string
                row_dict['date'] = date.strftime('%Y-%m-%d')
                data_list.append(row_dict)
            
            # Save to JSON
            with open(filepath, 'w') as f:
                json.dump(data_list, f, indent=2)
            
            logger.info(f"Archived data for {ticker} to {filepath}")
            return filepath
            
        except Exception as e:
            logger.error(f"Error archiving data for {ticker}: {e}")
            return f"Error archiving data: {str(e)}"

if __name__ == "__main__":
    ticker = "TSLA"
    start_date = "2024-01-01"
    end_date = "2024-12-31"
    df = get_historic_data(ticker, start_date, end_date)
    # print(df)
    archiver = DataArchiver()
    archiver.archive_historic_data(ticker, start_date, end_date, df)
    
