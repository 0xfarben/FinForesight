import json
import logging
from collections import OrderedDict
import os
from typing import Dict, Any, Optional

from .stock_data import fetch_stock_basics
from .financial_statement import get_company_financials
from .ratios import get_financial_ratios
# from economics import get_economic_indicators
from .news_sentiment import get_news_sentiment

logger = logging.getLogger(__name__)

def get_stock_overview(ticker_symbol: str) -> Dict[str, Any]:
    """
    Provides a comprehensive overview of a stock by aggregating data from various services
    
    Args:
        ticker_symbol (str): The stock ticker symbol
        
    Returns:
        Dict[str, Any]: Comprehensive stock overview including basic data, financials,
                       ratios, technical indicators, and news sentiment
    """
    try:
        logger.info(f"Fetching stock overview for {ticker_symbol}")
        
        # Get basic stock data
        stock_data = fetch_stock_basics(ticker_symbol)
        if 'error' in stock_data:
            return stock_data
            
        # Get key financial statements (most recent quarter)
        financials = get_company_financials(ticker_symbol)
        # financials = get_company_financials(ticker_symbol, period='quarterly', limit=1)
        
        # Get important financial ratios
        ratios = get_financial_ratios(ticker_symbol)
        
        # Get economic indicators
        # economic = get_economic_indicators(ticker_symbol)
        
        # Get news sentiment
        news = get_news_sentiment(ticker_symbol)
        
        # Combine all data into a comprehensive overview
        overview = OrderedDict([
            # Basic company and price information
            ('company_info', {
                'name': stock_data['company_name'],
                'ticker': stock_data['ticker'],
                'sector': stock_data['sector'],
                'industry': stock_data['industry']
            }),
            
            # Current trading data
            ('trading_data', {
                'current_price': stock_data['close'],
                'price_change': stock_data['percent_change'],
                # 'previous_close': stock_data['previous_close'],
                '52_week_range': stock_data['52_week_range'],
                'volume': stock_data['volume'],
                'beta': stock_data['beta'],
                'vwap': stock_data['vwap']
            }),
            
            # Market metrics
            ('market_metrics', {
                'market_cap': stock_data['market_cap'],
                'pe_ratio': stock_data['pe_ratio'],
                'eps': stock_data['eps'],
                'dividend_yield': stock_data['dividend_yield']
            }),
            
            # Ecocomic indicators
            # ('technical_indicators', economic),
            
            # Financial highlights
            ('financial_highlights', financials),
            
            # Key ratios
            ('key_ratios', ratios),
            
            # News and sentiment
            ('news_sentiment', news),
            
            # Recent price history for charts
            # ('price_history', stock_data['recent_prices'])
        ])
            
        return overview
        
    except Exception as e:
        logger.error(f"Error generating stock overview for {ticker_symbol}: {e}")
        return {
            'ticker': ticker_symbol,
            'error': str(e)
        } 
    
def get_refined_data(stock_data):
    """Transform raw stock overview data into frontend-friendly format"""
    try:
        # Basic validation
        if not stock_data or not isinstance(stock_data, dict):
            return {"error": "Invalid stock data format"}

        # Company Info
        company_info = stock_data.get("company_info", {})
        if not company_info:
            return {"error": "Company information not available"}

        # Stock Overview Section
        trading_data = stock_data.get("trading_data", {})
        market_metrics = stock_data.get("market_metrics", {})
        overview = {
            "company_name": company_info.get("name", "N/A"),
            "ticker": company_info.get("ticker", "N/A"),
            "sector": company_info.get("sector", "N/A"),
            "industry": company_info.get("industry", "N/A"),
            "current_price": trading_data.get("current_price", "N/A"),
            "price_change": trading_data.get("price_change", 0),
            "market_cap": market_metrics.get("market_cap", "N/A"),
            "volume": trading_data.get("volume", "N/A"),
            "pe_ratio": market_metrics.get("pe_ratio", "N/A"),
            "52_week_range": trading_data.get("52_week_range", "N/A"),
            "dividend_yield": market_metrics.get("dividend_yield", "N/A"),
            "beta": trading_data.get("beta", "N/A"),
            "vwap": trading_data.get("vwap", "N/A")
        }

        # Financial Ratios Section
        key_ratios = stock_data.get("key_ratios", {})
        financial_ratios = {
            "return_on_equity": key_ratios.get("roe", {}).get("value", "N/A"),
            "return_on_assets": key_ratios.get("roa", {}).get("value", "N/A"),
            "profit_margin": key_ratios.get("net_margin", {}).get("value", "N/A"),
            "current_ratio": key_ratios.get("current_ratio", {}).get("value", "N/A"),
            "debt_to_equity": key_ratios.get("debt_to_equity", {}).get("value", "N/A"),
            "eps": market_metrics.get("eps", "N/A"),
            "pe_ratio": market_metrics.get("pe_ratio", "N/A"),
            "price_to_book": key_ratios.get("price_to_book", {}).get("value", "N/A"),
            "dividend_yield": market_metrics.get("dividend_yield", "N/A"),
            "payout_ratio": key_ratios.get("payout_ratio", {}).get("value", "N/A")
        }

        # Financial Statements
        financial_highlights = stock_data.get("financial_highlights", [])
        
        # Initialize with default values (expanded with critical metrics)
        financial_statements = {
            "income_statement": {
                "total_revenue": "N/A",
                "cost_of_revenue": "N/A",
                "gross_profit": "N/A",
                "operating_income": "N/A",
                "operating_expenses": "N/A",
                "research_and_development": "N/A",
                "selling_general_admin": "N/A",
                "ebitda": "N/A",
                "net_income": "N/A",
                "tax_provision": "N/A",
                "eps_basic": "N/A",
                "eps_diluted": "N/A",
                "shares_outstanding_basic": "N/A",
                "shares_outstanding_diluted": "N/A"
            },
            "balance_sheet": {
                "total_assets": "N/A",
                "total_liabilities": "N/A",
                "total_equity": "N/A",
                "working_capital": "N/A",
                "cash_and_equivalents": "N/A",
                "short_term_investments": "N/A",
                "accounts_receivable": "N/A",
                "inventory": "N/A",
                "short_term_debt": "N/A",
                "long_term_debt": "N/A",
                "total_debt": "N/A",
                "net_debt": "N/A",
                "retained_earnings": "N/A",
                "tangible_book_value": "N/A"
            },
            "cash_flow": {
                "operating_cash_flow": "N/A",
                "capital_expenditure": "N/A",
                "free_cash_flow": "N/A",
                "dividends_paid": "N/A",
                "stock_repurchases": "N/A",
                "debt_repayment": "N/A",
                "net_borrowings": "N/A",
                "cash_from_financing": "N/A",
                "cash_from_investing": "N/A",
                "change_in_cash": "N/A",
                "depreciation_amortization": "N/A"
            }
        }

        # Update with actual data (limit to first 3 statements)
        for statement in financial_highlights[:3]:
            stmt_type = statement.get("statement_type")
            data = statement.get("data", {})
            
            if stmt_type == "Income Statement":
                financial_statements["income_statement"].update({
                    "total_revenue": data.get("Total Revenue", "N/A"),
                    "cost_of_revenue": data.get("Cost Of Revenue", "N/A"),
                    "gross_profit": data.get("Gross Profit", "N/A"),
                    "operating_income": data.get("Operating Income", "N/A"),
                    "operating_expenses": data.get("Operating Expense", "N/A"),
                    "research_and_development": data.get("Research And Development", "N/A"),
                    "selling_general_admin": data.get("Selling General And Administration", "N/A"),
                    "ebitda": data.get("EBITDA", "N/A"),
                    "net_income": data.get("Net Income", "N/A"),
                    "tax_provision": data.get("Tax Provision", "N/A"),
                    "eps_basic": data.get("Basic EPS", "N/A"),
                    "eps_diluted": data.get("Diluted EPS", "N/A"),
                    "shares_outstanding_basic": data.get("Basic Average Shares", "N/A"),
                    "shares_outstanding_diluted": data.get("Diluted Average Shares", "N/A")
                })
            elif stmt_type == "Balance Sheet":
                financial_statements["balance_sheet"].update({
                    "total_assets": data.get("Total Assets", "N/A"),
                    "total_liabilities": data.get("Total Liabilities Net Minority Interest", "N/A"),
                    "total_equity": data.get("Total Equity Gross Minority Interest", "N/A"),
                    "working_capital": data.get("Working Capital", "N/A"),
                    "cash_and_equivalents": data.get("Cash And Cash Equivalents", "N/A"),
                    "short_term_investments": data.get("Cash Cash Equivalents And Short Term Investments", "N/A"),
                    "accounts_receivable": data.get("Accounts Receivable", "N/A"),
                    "inventory": data.get("Inventory", "N/A"),
                    "short_term_debt": data.get("Current Debt", "N/A"),
                    "long_term_debt": data.get("Long Term Debt", "N/A"),
                    "total_debt": data.get("Total Debt", "N/A"),
                    "net_debt": data.get("Net Debt", "N/A"),
                    "retained_earnings": data.get("Retained Earnings", "N/A"),
                    "tangible_book_value": data.get("Tangible Book Value", "N/A")
                })
            elif stmt_type == "Cash Flow":
                financial_statements["cash_flow"].update({
                    "operating_cash_flow": data.get("Operating Cash Flow", "N/A"),
                    "capital_expenditure": data.get("Capital Expenditure", "N/A"),
                    "free_cash_flow": data.get("Free Cash Flow", "N/A"),
                    "dividends_paid": data.get("Common Stock Dividend Paid", "N/A"),
                    "stock_repurchases": data.get("Repurchase Of Capital Stock", "N/A"),
                    "debt_repayment": data.get("Long Term Debt Payments", "N/A"),
                    "net_borrowings": data.get("Net Issuance Payments Of Debt", "N/A"),
                    "cash_from_financing": data.get("Financing Cash Flow", "N/A"),
                    "cash_from_investing": data.get("Investing Cash Flow", "N/A"),
                    "change_in_cash": data.get("Changes In Cash", "N/A"),
                    "depreciation_amortization": data.get("Depreciation And Amortization", "N/A")
                })

        # News & Sentiment
        news_sentiment_data = stock_data.get("news_sentiment", {})
        ticker = company_info.get("ticker", "")
        
        # Get results dictionary first, then get ticker data
        results = news_sentiment_data.get("results", {})
        ticker_sentiment = results.get(ticker, {})
        
        news_sentiment = {
            "sentiment_score": ticker_sentiment.get("sentiment_score", "N/A"),
            "sentiment_label": ticker_sentiment.get("sentiment_label", "N/A"),
            "news": ticker_sentiment.get("news", []),
            "has_error": news_sentiment_data.get("has_error", False),
            "error": news_sentiment_data.get("error", None)
        }

        

        return {
            "company_info": company_info,
            "overview": overview,
            "financial_ratios": financial_ratios,
            "financial_statements": financial_statements,
            "news_sentiment": news_sentiment
        }
    
    except Exception as e:
        logger.error(f"Error transforming data: {str(e)}")
        return {
            "error": f"Error transforming data: {str(e)}"
        }

if __name__ == "__main__":
    ticker = "AAPL"
    overview = get_stock_overview(ticker)
    # print(json.dumps(overview, indent=4))
    # try:
    #     os.makedirs('data_archive', exist_ok=True)
    #     file_path = os.path.join('data_archive', 'output.json')
    #     with open(file_path, 'w') as f:
    #         json.dump(overview, f, indent=4)
    #     logger.info(f"Stock overview data saved to {file_path}")
    # except Exception as e:
    #     logger.error(f"Error saving stock overview data to file: {str(e)}")

    results = get_refined_data(overview)
    try:
        os.makedirs('data_archive', exist_ok=True)
        file_path = os.path.join('data_archive', 'output_refined.json')
        with open(file_path, 'w') as f:
            json.dump(results, f, indent=4)
        logger.info(f"Stock overview data saved to {file_path}")
    except Exception as e:
        logger.error(f"Error saving stock overview data to file: {str(e)}")
            


