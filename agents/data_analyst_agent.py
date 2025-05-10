import sys
import os
from collections import OrderedDict
import json
import logging
from typing import Dict, Any, List
import pandas as pd
from datetime import datetime
import asyncio



# Get the absolute path to the project root
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

try:
    from agents.dtmac import DTMAC
    from services.stock_data import fetch_stock_basics
    from services.financial_statement import get_company_financials
    from services.ratios import get_financial_ratios
    from services.historic_data import get_historic_data
    from services.earning_call_transcript import get_earnings_call_transcript
    from services.news_sentiment import get_news_sentiment
    from services.economics import get_economic_indicators
    from agents.base_agent import BaseAgent
    from services.stock_data import fetch_stock_basics as stock_data
    from agents.dtmac import MessagePriority, DTMessage
except ImportError as e:
    print(f"Import error: {e}")
    print(f"Python path: {sys.path}")
    raise

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DataAnalystAgent(BaseAgent):
    """
    Data Analyst Agent - Collects, processes, and archives financial data
    from various sources for further analysis.
    """

    def __init__(self, dtmac):
        # Define topics this agent is interested in
        topics = [
            "market_data",
            "analysis_requests",
            "risk_alerts",
            "trading_signals"
        ]
        super().__init__("data_analyst", dtmac, topics)
        
        # Register specific message handlers
        self.dtmac.register_handler(self.agent_id, "new_market_data", self.handle_new_market_data)
        self.dtmac.register_handler(self.agent_id, "analysis_request", self.handle_analysis_request)
        
        # Initialize agent state
        self.current_analysis = {}
        self.last_update = None
        
        self.data_archive = 'data_archive'
        os.makedirs(self.data_archive, exist_ok=True)
        
        # Supported technical indicators
        self.FUNCTIONS = [
            'SMA', 'EMA', 'WMA', 'DEMA', 'TEMA', 'TRIMA', 'KAMA',
            'MAMA', 'T3', 'MACDEXT', 'STOCH', 'STOCHF', 'RSI', 'STOCHRSI',
            'WILLR', 'ADX', 'ADXR', 'APO', 'PPO', 'MOM', 'BOP', 'CCI',
            'CMO', 'ROC', 'ROCR', 'AROON', 'AROONOSC', 'MFI', 'TRIX',
            'ULTOSC', 'DX', 'MINUS_DI', 'PLUS_DI', 'MINUS_DM', 'PLUS_DM',
            'BBANDS', 'MIDPOINT', 'MIDPRICE', 'SAR', 'TRANGE', 'ATR',
            'NATR', 'AD', 'ADOSC', 'OBV', 'HT_TRENDLINE', 'HT_SINE',
            'HT_TRENDMODE', 'HT_DCPERIOD', 'HT_DCPHASE', 'HT_PHASOR'
        ]
        self.INTERVALS = ['1min', '5min', '15min', '30min', '60min', 'daily', 'weekly', 'monthly']

    async def get_status(self) -> Dict[str, Any]:
        return {
            "status": "active",
            "last_update": self.last_update,
            "current_analysis_count": len(self.current_analysis),
            "subscribed_topics": self.get_subscribed_topics()
        }
    
    async def handle_new_market_data(self, message: DTMessage):
        """Handle new market data messages"""
        market_data = message.content
        symbol = market_data.get("symbol")
        
        # Process the data
        analysis = await self.analyze_market_data(market_data)
        
        # Store the analysis
        self.current_analysis[symbol] = analysis
        self.last_update = datetime.now()
        
        # Broadcast analysis results to interested agents
        await self.broadcast_to_topic(
            topic="analysis_results",
            content={
                "symbol": symbol,
                "analysis": analysis,
                "timestamp": self.last_update.isoformat()
            },
            message_type="analysis_complete",
            priority=MessagePriority.HIGH
        )
    
    async def handle_analysis_request(self, message: DTMessage):
        """Handle analysis request messages"""
        request = message.content
        symbol = request.get("symbol")
        
        if symbol in self.current_analysis:
            # Send analysis directly to requester
            await self.send_to_agent(
                recipient=message.sender,
                content={
                    "symbol": symbol,
                    "analysis": self.current_analysis[symbol],
                    "timestamp": self.last_update.isoformat()
                },
                message_type="analysis_response",
                priority=MessagePriority.NORMAL
            )
        else:
            # Request new data if not available
            await self.broadcast_to_topic(
                topic="market_data",
                content={"symbol": symbol, "request_type": "historical"},
                message_type="data_request",
                priority=MessagePriority.HIGH
            )
    
    async def analyze_market_data(self, market_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze market data and generate insights"""
        # Your existing analysis logic here
        # This is where you'd implement your technical analysis, indicators, etc.
        
        # Example analysis
        analysis = {
            "technical_indicators": {
                "rsi": self.calculate_rsi(market_data),
                "macd": self.calculate_macd(market_data),
                "bollinger_bands": self.calculate_bollinger_bands(market_data)
            },
            "trend_analysis": self.analyze_trend(market_data),
            "support_resistance": self.find_support_resistance(market_data),
            "volatility_metrics": self.calculate_volatility(market_data)
        }
        
        return analysis
    
    

    # def fetch_all_data(self, inputs: Dict[str, Any]):
    #     """
    #     Fetch all required data based on the provided inputs and save as JSON.

    #     :param inputs: Dictionary containing 'ticker', 'start_date', 'end_date', 'quarter'
    #     :return: Dictionary containing formatted data for display
    #     """
    #     ticker = inputs.get('ticker', 'TSLA')
    #     start_date = inputs.get('start_date', '2023-01-01')
    #     end_date = inputs.get('end_date', '2023-12-31')
    #     quarter = inputs.get('quarter', '2023Q1')

    #     results = {
    #         "ticker": ticker,
    #         "analysis_date": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
    #         "sections": []
    #     }

    #     # Stock Overview
    #     try:
    #         stock_data = fetch_stock_basics(ticker)
    #         with open(f'{self.data_archive}/{ticker}_stock_data.json', 'w') as f:
    #             json.dump(stock_data, f, indent=4)
            
    #         results["sections"].append({
    #             "title": "Stock Overview",
    #             "data": {
    #                 "Company Name": stock_data.get("Name", "N/A"),
    #                 "Industry": stock_data.get("Industry", "N/A"),
    #                 "Market Cap": stock_data.get("MarketCap", "N/A"),
    #                 "52 Week High": stock_data.get("52WeekHigh", "N/A"),
    #                 "52 Week Low": stock_data.get("52WeekLow", "N/A"),
    #                 "Beta": stock_data.get("Beta", "N/A")
    #             }
    #         })
    #         logger.info(f"Stock data for {ticker} saved and processed")
    #     except Exception as e:
    #         logger.error(f"Error fetching stock data for {ticker}: {e}")
    #         results["sections"].append({
    #             "title": "Stock Overview",
    #             "error": str(e)
    #         })

    #     # Financial Ratios
    #     try:
    #         ratios = get_financial_ratios(ticker)
    #         with open(f'{self.data_archive}/{ticker}_financial_ratios.json', 'w') as f:
    #             json.dump(ratios, f, indent=4)
            
    #         results["sections"].append({
    #             "title": "Financial Ratios",
    #             "data": {
    #                 "P/E Ratio": ratios.get("PE", "N/A"),
    #                 "P/B Ratio": ratios.get("PB", "N/A"),
    #                 "ROE": ratios.get("ROE", "N/A"),
    #                 "ROA": ratios.get("ROA", "N/A"),
    #                 "Current Ratio": ratios.get("CurrentRatio", "N/A"),
    #                 "Debt to Equity": ratios.get("DebtToEquity", "N/A")
    #             }
    #         })
    #         logger.info(f"Financial ratios for {ticker} saved and processed")
    #     except Exception as e:
    #         logger.error(f"Error fetching financial ratios for {ticker}: {e}")
    #         results["sections"].append({
    #             "title": "Financial Ratios",
    #             "error": str(e)
    #         })

    #     # Historic Data Summary
    #     try:
    #         df = get_historic_data(ticker, start_date, end_date)
    #         if df is not None and not df.empty:
    #             # Save historic data
    #             data = df.to_dict(orient='records')
    #             start_clean = start_date.replace('-', '')
    #             end_clean = end_date.replace('-', '')
    #             timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    #             file_path = f'{self.data_archive}/{ticker}_historic_data_{start_clean}_{end_clean}_{timestamp}.json'
                
    #             with open(file_path, 'w') as f:
    #                 json.dump(data, f, indent=4)

    #             # Calculate summary statistics
    #             latest_price = df.iloc[-1]['Close'] if 'Close' in df else None
    #             price_change = df['Close'].pct_change().iloc[-1] * 100 if 'Close' in df else None
    #             avg_volume = df['Volume'].mean() if 'Volume' in df else None
                
    #             results["sections"].append({
    #                 "title": "Historic Data Summary",
    #                 "data": {
    #                     "Latest Price": f"${latest_price:.2f}" if latest_price else "N/A",
    #                     "Price Change": f"{price_change:.2f}%" if price_change else "N/A",
    #                     "Average Volume": f"{avg_volume:,.0f}" if avg_volume else "N/A",
    #                     "Period": f"{start_date} to {end_date}",
    #                     "Data Points": len(df)
    #                 }
    #             })
    #             logger.info(f"Historic data for {ticker} saved and processed")
    #         else:
    #             results["sections"].append({
    #                 "title": "Historic Data Summary",
    #                 "error": "No historic data available"
    #             })
    #     except Exception as e:
    #         logger.error(f"Error processing historic data for {ticker}: {e}")
    #         results["sections"].append({
    #             "title": "Historic Data Summary",
    #             "error": str(e)
    #         })

    #     # News Sentiment
    #     try:
    #         news_sentiment = get_news_sentiment(ticker)
            
    #         # Format dates in news articles
    #         if 'feed' in news_sentiment:
    #             for article in news_sentiment['feed']:
    #                 if 'time_published' in article:
    #                     try:
    #                         # Convert from format "20250428T155900" to datetime
    #                         dt = datetime.strptime(article['time_published'], '%Y%m%dT%H%M%S')
    #                         # Format to human-readable string
    #                         article['time_published'] = dt.strftime('%Y-%m-%d %H:%M:%S')
    #                     except (ValueError, TypeError):
    #                         article['time_published'] = 'N/A'
            
    #         with open(f'{self.data_archive}/{ticker}_news_sentiment.json', 'w') as f:
    #             json.dump(news_sentiment, f, indent=4)
            
    #         results["sections"].append({
    #             "title": "News Sentiment Analysis",
    #             "data": {
    #                 "overall_sentiment": news_sentiment.get("overall_sentiment", "N/A"),
    #                 "positive_articles": news_sentiment.get("positive_count", 0),
    #                 "negative_articles": news_sentiment.get("negative_count", 0),
    #                 "neutral_articles": news_sentiment.get("neutral_count", 0),
    #                 "total_articles": news_sentiment.get("total_articles", 0),
    #                 "articles": news_sentiment.get("feed", [])  # Include formatted articles
    #             }
    #         })
    #         logger.info(f"News sentiment for {ticker} saved and processed")
    #     except Exception as e:
    #         logger.error(f"Error fetching news sentiment for {ticker}: {e}")
    #         results["sections"].append({
    #             "title": "News Sentiment Analysis",
    #             "error": str(e)
    #         })

    #     # Economic Indicators
    #     # try:
    #     #     economic_indicators = get_economic_indicators()
    #     #     with open(f'{self.data_archive}/economic_indicators.json', 'w') as f:
    #     #         json.dump(economic_indicators, f, indent=4)
            
    #     #     results["sections"].append({
    #     #         "title": "Economic Indicators",
    #     #         "data": {
    #     #             "GDP Growth Rate": economic_indicators.get("gdp_growth", "N/A"),
    #     #             "Inflation Rate": economic_indicators.get("inflation_rate", "N/A"),
    #     #             "Unemployment Rate": economic_indicators.get("unemployment_rate", "N/A"),
    #     #             "Interest Rate": economic_indicators.get("interest_rate", "N/A"),
    #     #             "Last Updated": economic_indicators.get("last_updated", "N/A")
    #     #         }
    #     #     })
    #     #     logger.info("Economic indicators saved and processed")
    #     # except Exception as e:
    #     #     logger.error(f"Error fetching economic indicators: {e}")
    #     #     results["sections"].append({
    #     #         "title": "Economic Indicators",
    #     #         "error": str(e)
    #     #     })


    #     # Reddit Sentiment
    #     try:
    #         sentiment_analyzer = RedditSentimentAnalyzer()
    #         sentiment_data = sentiment_analyzer.analyze_sentiment(ticker)

    #         results["sections"].append({
    #             "title": "Reddit Sentiment Analysis",
    #             "data": sentiment_data
    #         })

    #     except Exception as e:
    #         logger.error(f"Error fetching Reddit sentiment for {ticker}: {e}")
    #         results["sections"].append({
    #             "title": "Reddit Sentiment Analysis",
    #             "error": str(e)
    #         })
            
        
    #     return results

    def get_stock_overview(self, ticker_symbol: str) -> Dict[str, Any]:
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

            # Get Reddit sentiment
            # sentiment_analyzer = RedditSentimentAnalyzer()
            # reddit_sentiment = sentiment_analyzer.analyze_sentiment(ticker_symbol)
            
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

                #Reddit Sentiment
                # ('reddit_sentiment', reddit_sentiment),
            ])
                
            return overview
            
        except Exception as e:
            logger.error(f"Error generating stock overview for {ticker_symbol}: {e}")
            return {
                'ticker': ticker_symbol,
                'error': str(e)
            } 
        
    def get_refined_data(self, stock_data):
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

            #Reddit Sentiment
            # reddit_sentiment = stock_data.get("reddit_sentiment", {})
            
            # # Calculate gauge score (0-100)
            # avg_sentiment = reddit_sentiment.get("average_sentiment", 0.0)
            # gauge_score = round((avg_sentiment + 1) * 50)  # Convert -1 to 1 scale to 0-100
            
            # # Determine sentiment label based on distribution
            # sentiment_dist = reddit_sentiment.get("sentiment_distribution", {})
            # pos_count = sentiment_dist.get("positive", 0)
            # neu_count = sentiment_dist.get("neutral", 0)
            # neg_count = sentiment_dist.get("negative", 0)
            
            # # Get the dominant sentiment
            # total_posts = pos_count + neu_count + neg_count
            # if total_posts > 0:
            #     pos_pct = (pos_count / total_posts) * 100
            #     neu_pct = (neu_count / total_posts) * 100
            #     neg_pct = (neg_count / total_posts) * 100
                
            #     if pos_pct > neu_pct and pos_pct > neg_pct:
            #         sentiment_label = "Positive"
            #     elif neg_pct > pos_pct and neg_pct > neu_pct:
            #         sentiment_label = "Negative"
            #     else:
            #         sentiment_label = "Neutral"
            # else:
            #     sentiment_label = "Neutral"

            # reddit_sentiment = {
            #     # Gauge specific data
            #     "gauge_score": gauge_score,  # 0-100 scale for the gauge
            #     "sentiment_label": sentiment_label,  # "Positive", "Neutral", or "Negative"
                
            #     # Original metrics
            #     "success": reddit_sentiment.get("success", False),
            #     "average_sentiment": avg_sentiment,
            #     "positive_posts": pos_count,
            #     "neutral_posts": neu_count,
            #     "negative_posts": neg_count,
                
            #     # Include top posts for detailed view
            #     "top_posts": reddit_sentiment.get("top_posts", [])
            # }

            return {
                "company_info": company_info,
                "overview": overview,
                "financial_ratios": financial_ratios,
                "financial_statements": financial_statements,
                "news_sentiment": news_sentiment,
                # "reddit_sentiment": reddit_sentiment
            }
        
        except Exception as e:
            logger.error(f"Error transforming data: {str(e)}")
            return {
                "error": f"Error transforming data: {str(e)}"
            }

if __name__ == "__main__":
    ticker = "AAPL"
    dtmac = DTMAC()
    data_analyst = DataAnalystAgent(dtmac)

    overview = data_analyst.get_stock_overview(ticker)
    print(json.dumps(overview, indent=4))
    try:
        os.makedirs('data_archive', exist_ok=True)
        file_path = os.path.join('data_archive', 'output.json')
        with open(file_path, 'w') as f:
            json.dump(overview, f, indent=4)
        logger.info(f"Stock overview data saved to {file_path}")
    except Exception as e:
        logger.error(f"Error saving stock overview data to file: {str(e)}")

    results = data_analyst.get_refined_data(overview)
    print(json.dumps(results, indent=4))
    try:
        os.makedirs('data_archive', exist_ok=True)
        file_path = os.path.join('data_archive', 'output_refined.json')
        with open(file_path, 'w') as f:
            json.dump(results, f, indent=4)
        logger.info(f"Stock overview data saved to {file_path}")
    except Exception as e:
        logger.error(f"Error saving stock overview data to file: {str(e)}")
            


