import logging
import yfinance as yf
# import yfinance_cache as yf
import pandas as pd
import numpy as np
from datetime import datetime
import os
import json

logger = logging.getLogger(__name__)

def get_financial_ratios(ticker_symbol):
    """
    Get key financial ratios for a company
    
    Args:
        ticker_symbol (str): Stock ticker symbol
        
    Returns:
        dict: Financial ratios
    """
    try:
        logger.info(f"Calculating financial ratios for {ticker_symbol}")
        
        # Initialize ticker object
        ticker = yf.Ticker(ticker_symbol)
        
        # Get financial data
        info = ticker.info
        income_stmt = ticker.income_stmt
        balance_sheet = ticker.balance_sheet
        cash_flow = ticker.cashflow
        
        ratios = {}
        
        # Price ratios
        ratios['pe_ratio'] = {
            'value': info.get('trailingPE'),
            'description': 'Price to Earnings Ratio',
            'interpretation': 'Measures the current share price relative to earnings per share.'
        }
        
        ratios['pb_ratio'] = {
            'value': info.get('priceToBook'),
            'description': 'Price to Book Ratio',
            'interpretation': 'Compares a company\'s market value to its book value.'
        }
        
        ratios['ps_ratio'] = {
            'value': info.get('priceToSalesTrailing12Months'),
            'description': 'Price to Sales Ratio',
            'interpretation': 'Compares a company\'s stock price to its revenues.'
        }
        
        # Dividend ratios
        ratios['dividend_yield'] = {
            'value': info.get('dividendYield', 0) * 100 if info.get('dividendYield') else None,
            'description': 'Dividend Yield (%)',
            'interpretation': 'Annual dividend payments relative to share price.'
        }
        
        ratios['payout_ratio'] = {
            'value': info.get('payoutRatio', 0) * 100 if info.get('payoutRatio') else None,
            'description': 'Payout Ratio (%)',
            'interpretation': 'Percentage of earnings paid to shareholders in dividends.'
        }
        
        # Profitability ratios
        if not income_stmt.empty and not balance_sheet.empty:
            try:
                # Get most recent year data
                recent_income = income_stmt.iloc[:, 0]
                recent_balance = balance_sheet.iloc[:, 0]
                
                # Profit margins
                gross_profit = recent_income.get('Gross Profit', None)
                total_revenue = recent_income.get('Total Revenue', None)
                net_income = recent_income.get('Net Income', None)
                total_assets = recent_balance.get('Total Assets', None)
                total_equity = recent_balance.get('Total Stockholder Equity', None)
                
                # Calculate ratios
                if gross_profit is not None and total_revenue is not None and total_revenue != 0:
                    ratios['gross_margin'] = {
                        'value': round((gross_profit / total_revenue) * 100, 2),
                        'description': 'Gross Margin (%)',
                        'interpretation': 'Percentage of revenue retained as gross profit.'
                    }
                
                if net_income is not None and total_revenue is not None and total_revenue != 0:
                    ratios['net_margin'] = {
                        'value': round((net_income / total_revenue) * 100, 2),
                        'description': 'Net Profit Margin (%)',
                        'interpretation': 'Percentage of revenue retained as net income.'
                    }
                
                if net_income is not None and total_assets is not None and total_assets != 0:
                    ratios['roa'] = {
                        'value': round((net_income / total_assets) * 100, 2),
                        'description': 'Return on Assets (%)',
                        'interpretation': 'How efficiently a company is using its assets to generate earnings.'
                    }
                
                if net_income is not None and total_equity is not None and total_equity != 0:
                    ratios['roe'] = {
                        'value': round((net_income / total_equity) * 100, 2),
                        'description': 'Return on Equity (%)',
                        'interpretation': 'How efficiently a company is using its equity to generate earnings.'
                    }
            except Exception as calc_error:
                logger.warning(f"Error calculating profitability ratios: {calc_error}")
        
        # Liquidity ratios
        if not balance_sheet.empty:
            try:
                # Get most recent year data
                recent_balance = balance_sheet.iloc[:, 0]
                
                current_assets = recent_balance.get('Current Assets', None)
                current_liabilities = recent_balance.get('Current Liabilities', None)
                inventory = recent_balance.get('Inventory', None)
                
                # Calculate ratios
                if current_assets is not None and current_liabilities is not None and current_liabilities != 0:
                    ratios['current_ratio'] = {
                        'value': round(current_assets / current_liabilities, 2),
                        'description': 'Current Ratio',
                        'interpretation': 'Company\'s ability to pay short-term obligations.'
                    }
                    
                    if inventory is not None:
                        ratios['quick_ratio'] = {
                            'value': round((current_assets - inventory) / current_liabilities, 2),
                            'description': 'Quick Ratio',
                            'interpretation': 'Company\'s ability to pay short-term obligations with liquid assets.'
                        }
            except Exception as liq_error:
                logger.warning(f"Error calculating liquidity ratios: {liq_error}")
                
        # Solvency ratios
        if not balance_sheet.empty and not income_stmt.empty:
            try:
                # Get most recent year data
                recent_balance = balance_sheet.iloc[:, 0]
                recent_income = income_stmt.iloc[:, 0]
                
                total_assets = recent_balance.get('Total Assets', None)
                total_liabilities = recent_balance.get('Total Liabilities Net Minority Interest', None)
                total_debt = recent_balance.get('Total Debt', None)
                total_equity = recent_balance.get('Total Stockholder Equity', None)
                ebit = recent_income.get('EBIT', None)
                interest_expense = recent_income.get('Interest Expense', None)
                
                # Calculate ratios
                if total_liabilities is not None and total_assets is not None and total_assets != 0:
                    ratios['debt_to_assets'] = {
                        'value': round((total_liabilities / total_assets) * 100, 2),
                        'description': 'Debt to Assets (%)',
                        'interpretation': 'Percentage of a company\'s assets that are financed by debt.'
                    }
                
                if total_debt is not None and total_equity is not None and total_equity != 0:
                    ratios['debt_to_equity'] = {
                        'value': round((total_debt / total_equity) * 100, 2),
                        'description': 'Debt to Equity (%)',
                        'interpretation': 'Relative proportion of shareholders\' equity and debt used to finance assets.'
                    }
                
                if ebit is not None and interest_expense is not None and interest_expense != 0:
                    ratios['interest_coverage'] = {
                        'value': round(ebit / interest_expense, 2),
                        'description': 'Interest Coverage Ratio',
                        'interpretation': 'Company\'s ability to pay its interest expenses on outstanding debt.'
                    }
            except Exception as solv_error:
                logger.warning(f"Error calculating solvency ratios: {solv_error}")
        
        # Efficiency ratios
        if not income_stmt.empty and not balance_sheet.empty:
            try:
                # Get most recent year data
                recent_income = income_stmt.iloc[:, 0]
                recent_balance = balance_sheet.iloc[:, 0]
                
                total_revenue = recent_income.get('Total Revenue', None)
                total_assets = recent_balance.get('Total Assets', None)
                inventory = recent_balance.get('Inventory', None)
                accounts_receivable = recent_balance.get('Accounts Receivable', None)
                
                # Calculate ratios
                if total_revenue is not None and total_assets is not None and total_assets != 0:
                    ratios['asset_turnover'] = {
                        'value': round(total_revenue / total_assets, 2),
                        'description': 'Asset Turnover Ratio',
                        'interpretation': 'Efficiency of a company\'s use of its assets to generate sales.'
                    }
                
                if total_revenue is not None and inventory is not None and inventory != 0:
                    # Using average inventory would be better, but this is a simplification
                    ratios['inventory_turnover'] = {
                        'value': round(total_revenue / inventory, 2),
                        'description': 'Inventory Turnover Ratio',
                        'interpretation': 'How many times a company sells and replaces its inventory in a period.'
                    }
                
                if total_revenue is not None and accounts_receivable is not None and accounts_receivable != 0:
                    ratios['receivables_turnover'] = {
                        'value': round(total_revenue / accounts_receivable, 2),
                        'description': 'Receivables Turnover Ratio',
                        'interpretation': 'How efficiently a company collects revenue from customers.'
                    }
            except Exception as eff_error:
                logger.warning(f"Error calculating efficiency ratios: {eff_error}")
        
        # Growth ratios
        # For growth ratios, we would need historical data to calculate year-over-year changes
        # This would be a more complex calculation that would require multiple years of data
        
        # Save ratios to JSON file
        try:
            os.makedirs('data_archive', exist_ok=True)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            file_path = os.path.join('data_archive', f'{ticker_symbol}_ratios_{timestamp}.json')
            with open(file_path, 'w') as f:
                json.dump(ratios, f, indent=4)
            logger.info(f"Financial ratios for {ticker_symbol} saved to {file_path}")
        except Exception as e:
            logger.error(f"Error saving financial ratios to file: {str(e)}")
        
        return ratios
        
    except Exception as e:
        logger.error(f"Error calculating financial ratios for {ticker_symbol}: {e}")
        return {
            'error': str(e)
        }
