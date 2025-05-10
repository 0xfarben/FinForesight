import logging
import yfinance as yf
# import yfinance_cache as yf
import pandas as pd
import numpy as np
from datetime import datetime
import os
import json

logger = logging.getLogger(__name__)

def get_financials(ticker):
    """
    Get financial statements for a company
    
    Args:
        ticker (str): Stock ticker symbol
        
    Returns:
        list: Financial statements as list of dictionaries
    """
    try:
        # Initialize ticker object
        stock = yf.Ticker(ticker)
        
        # Get financial data
        income_stmt = stock.income_stmt
        balance_sheet = stock.balance_sheet
        cash_flow = stock.cashflow
        
        if income_stmt.empty and balance_sheet.empty and cash_flow.empty:
            logger.warning(f"No financial data available for {ticker}")
            return []
        
        # Process Income Statement
        income_data = []
        if not income_stmt.empty:
            # Convert to dictionaries with date keys
            for col in income_stmt.columns:
                date_str = col.strftime('%Y-%m-%d') if hasattr(col, 'strftime') else str(col).split(' ')[0]
                period = 'Annual'
                
                # Create a row for each date
                income_row = {
                    'ticker': ticker,
                    'statement_type': 'Income Statement',
                    'date': date_str,
                    'period': period,
                    'data': {}
                }
                
                # Add line items
                for idx, value in income_stmt[col].items():
                    if isinstance(value, (np.integer, np.floating)):
                        income_row['data'][idx] = float(value)
                    elif pd.isna(value):
                        income_row['data'][idx] = None
                    else:
                        income_row['data'][idx] = value
                        
                income_data.append(income_row)
        
        # Process Balance Sheet
        balance_data = []
        if not balance_sheet.empty:
            # Convert to dictionaries with date keys
            for col in balance_sheet.columns:
                date_str = col.strftime('%Y-%m-%d') if hasattr(col, 'strftime') else str(col).split(' ')[0]
                period = 'Annual'
                
                # Create a row for each date
                balance_row = {
                    'ticker': ticker,
                    'statement_type': 'Balance Sheet',
                    'date': date_str,
                    'period': period,
                    'data': {}
                }
                
                # Add line items
                for idx, value in balance_sheet[col].items():
                    if isinstance(value, (np.integer, np.floating)):
                        balance_row['data'][idx] = float(value)
                    elif pd.isna(value):
                        balance_row['data'][idx] = None
                    else:
                        balance_row['data'][idx] = value
                        
                balance_data.append(balance_row)
                
        # Process Cash Flow
        cash_flow_data = []
        if not cash_flow.empty:
            # Convert to dictionaries with date keys
            for col in cash_flow.columns:
                date_str = col.strftime('%Y-%m-%d') if hasattr(col, 'strftime') else str(col).split(' ')[0]
                period = 'Annual'
                
                # Create a row for each date
                cash_flow_row = {
                    'ticker': ticker,
                    'statement_type': 'Cash Flow',
                    'date': date_str,
                    'period': period,
                    'data': {}
                }
                
                # Add line items
                for idx, value in cash_flow[col].items():
                    if isinstance(value, (np.integer, np.floating)):
                        cash_flow_row['data'][idx] = float(value)
                    elif pd.isna(value):
                        cash_flow_row['data'][idx] = None
                    else:
                        cash_flow_row['data'][idx] = value
                        
                cash_flow_data.append(cash_flow_row)
                
        # Combine all statements
        all_statements = income_data + balance_data + cash_flow_data
        
        # Sort by date (newest first)
        all_statements.sort(key=lambda x: x['date'], reverse=True)
        
        return all_statements
            
    except Exception as e:
        logger.error(f"Error getting financial statements for {ticker}: {e}")
        return []


def get_company_financials(ticker):
    """
    Get company financial statements with error handling
    
    Args:
        ticker (str): Stock ticker symbol
        
    Returns:
        list/dict: Financial statements or error message
    """
    try:
        financials = get_financials(ticker)
        if not financials:
            return {
                'ticker': ticker,
                'error': 'No financial data available'
            }

        # Save financials to JSON file
        try:
            os.makedirs('data_archive', exist_ok=True)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            file_path = os.path.join('data_archive', f'{ticker}_financial_statement_{timestamp}.json')
            with open(file_path, 'w') as f:
                json.dump(financials, f, indent=4)
            logger.info(f"Financial statements for {ticker} saved to {file_path}")
        except Exception as e:
            logger.error(f"Error saving financial statements to file: {str(e)}")

        return financials
    except Exception as e:
        logger.error(f"Error in get_company_financials for {ticker}: {e}")
        return {
            'ticker': ticker,
            'error': str(e)
        }
