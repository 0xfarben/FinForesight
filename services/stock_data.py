import json
import logging
import os
from collections import OrderedDict
from datetime import datetime, timedelta

import yfinance as yf
# import yfinance_cache as yf
import pandas as pd
import numpy as np
import requests

logger = logging.getLogger(__name__)

def fetch_stock_basics(ticker):
    """Fetch basic stock data and additional metrics for the given ticker."""
    try:
        # Initialize stock data dictionary
        stock_data = OrderedDict()
        
        # Get ticker data
        ticker_obj = yf.Ticker(ticker)
        info = ticker_obj.info
        
        # Basic company info
        stock_data['company_name'] = info.get('shortName', 'N/A')
        stock_data['ticker'] = ticker
        stock_data['sector'] = info.get('sector', 'N/A')
        stock_data['industry'] = info.get('industry', 'N/A')
        
        # Stock Overview
        # stock_data['close'] = info.get('regularMarketPrice', 0)
        # stock_data['close'] = info.get('previousClose', 0)
        # stock_data['previous_close'] = info.get('regularMarketPrice', 0)
        # stock_data['percent_change'] = ((stock_data['close'] - stock_data['previous_close']) / stock_data['previous_close'] * 100) if stock_data['previous_close'] else 0

        stock_data['previous_close'] = info.get('previousClose', 0)
        stock_data['close'] = info.get('regularMarketPrice', 0)
        stock_data['percent_change'] = (
            ((stock_data['close'] - stock_data['previous_close']) / stock_data['previous_close']) * 100
            if stock_data['previous_close'] else 0
        )
        stock_data['volume'] = info.get('volume', 0)
        stock_data['beta'] = info.get('beta', 0)
        stock_data['vwap'] = info.get('regularMarketPrice', 0) * 1.02  # Estimated VWAP
        stock_data['52_week_range'] = f"{info.get('fiftyTwoWeekLow', 0):.2f} - {info.get('fiftyTwoWeekHigh', 0):.2f}"
        
        # # Financial Ratios
        stock_data['roe'] = info.get('returnOnEquity', 0) * 100 if info.get('returnOnEquity') else 0
        stock_data['roa'] = info.get('returnOnAssets', 0) * 100 if info.get('returnOnAssets') else 0
        stock_data['profit_margin'] = info.get('profitMargins', 0) * 100 if info.get('profitMargins') else 0
        stock_data['current_ratio'] = info.get('currentRatio', 0)
        stock_data['debt_to_equity'] = info.get('debtToEquity', 0) / 100 if info.get('debtToEquity') else 0
        stock_data['eps'] = info.get('trailingEps', 0)
        stock_data['pe_ratio'] = info.get('trailingPE', 0)
        stock_data['price_to_book'] = info.get('priceToBook', 0)
        stock_data['dividend_yield'] = info.get('dividendYield', 0) * 100 if info.get('dividendYield') else 0
        stock_data['payout_ratio'] = info.get('payoutRatio', 0) * 100 if info.get('payoutRatio') else 0
        
        # # Financial Statements
        stock_data['total_revenue'] = info.get('totalRevenue', 0)
        stock_data['gross_profit'] = info.get('grossProfits', 0)
        stock_data['operating_income'] = info.get('operatingIncome', 0)
        stock_data['net_income'] = info.get('netIncome', 0)
        stock_data['ebitda'] = info.get('ebitda', 0)
        stock_data['operating_cash_flow'] = info.get('operatingCashflow', 0)
        stock_data['free_cash_flow'] = info.get('freeCashflow', 0)
        stock_data['market_cap'] = info.get('marketCap', 0)
        
        return stock_data
        
    except Exception as e:
        logger.error(f"Error fetching data for {ticker}: {str(e)}")
        return {'error': str(e)}

# if __name__ == "__main__":
#     ticker = "TSLA"
#     data = fetch_stock_basics(ticker)
#     json.dumps(data, indent=4)
#     print(data)