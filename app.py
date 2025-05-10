import os
import json
import logging
import numpy as np
from datetime import datetime, timedelta
from flask import Flask, render_template, request, jsonify, session
import pandas as pd
from flask_socketio import SocketIO

from agents.dtmac import DTMAC
from agents.data_analyst_agent import DataAnalystAgent
from agents.trade_strategy_agent import TradeStrategyAgent
from agents.trade_advisor_agent import TradeAdvisorAgent
from agents.risk_advisor_agent import RiskAdvisorAgent

from services.historic_data import DataArchiver
from services.stock_data import fetch_stock_basics
from services.stock_overview import get_stock_overview, get_refined_data

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "fin_foresight_session_key")
socketio = SocketIO(app, cors_allowed_origins="*")

# Utility function to handle NumPy types in JSON serialization
def np_encoder(obj):
    if isinstance(obj, np.integer):
        return int(obj)
    elif isinstance(obj, np.floating):
        return float(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, datetime):
        return obj.isoformat()
    elif pd.isna(obj):
        return None
    raise TypeError(f"Object of type {type(obj)} is not JSON serializable")

# Add template context processor to provide common variables to all templates
@app.context_processor
def inject_now():
    return {'now': datetime.now()}

# Create data directories
os.makedirs('data_archive', exist_ok=True)
os.makedirs('strategies_archive', exist_ok=True)
os.makedirs('predictions_archive', exist_ok=True)
os.makedirs('risk_archive', exist_ok=True)

# Initialize DTMAC
dtmac = DTMAC()

# Initialize agents with DTMAC
data_analyst = DataAnalystAgent(dtmac)
trade_strategy = TradeStrategyAgent(dtmac)
trade_advisor = TradeAdvisorAgent(dtmac)
risk_advisor = RiskAdvisorAgent(dtmac)

# Default tickers for the dashboard
DEFAULT_TICKERS = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'META', 'TSLA', 'NVDA', 'JPM', 'V', 'WMT']

# Default symbols for top stocks section
DEFAULT_SYMBOLS = ['AAPL', 'AMZN', 'GOOGL', 'JPM', 'META', 'MSFT']

@app.route('/')
def index():
    """Render the main dashboard"""
    return render_template('index.html')

@app.route('/get_stock_data')
def get_stock_data():
    """API endpoint to fetch basic stock data for dashboard"""
    tickers = request.args.get('tickers', ','.join(DEFAULT_TICKERS)).split(',')
    results = {}
    
    for ticker in tickers:
        try:
            stock_data = fetch_stock_basics(ticker)
            if 'error' not in stock_data:
                # Convert NumPy types to Python native types
                for key, value in stock_data.items():
                    if isinstance(value, np.integer):
                        stock_data[key] = int(value)
                    elif isinstance(value, np.floating):
                        stock_data[key] = float(value)
                    elif isinstance(value, np.ndarray):
                        stock_data[key] = value.tolist()
                
                results[ticker] = stock_data
        except Exception as e:
            logger.error(f"Error fetching data for {ticker}: {e}")
    
    print(results.json()) 
    # Use the standard json module with our encoder function
    return app.response_class(
        response=json.dumps(results, default=np_encoder),
        status=200,
        mimetype='application/json'
    )

@app.route('/analyze', methods=['GET', 'POST'])
def analyze():
    """Handle analysis request and render results page"""
    if request.method == 'POST':
        # Get form inputs
        ticker = request.form.get('ticker', 'AAPL')
        start_date = request.form.get('start_date', (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d'))
        end_date = request.form.get('end_date', datetime.now().strftime('%Y-%m-%d'))
        quarter = request.form.get('quarter', '2023Q1')
        
        save_historic_data = DataArchiver()
        historic_data = save_historic_data.archive_historic_data(ticker, start_date, end_date)
        
        # Save inputs to session
        session['analysis_inputs'] = {
            'ticker': ticker,
            'start_date': start_date,
            'end_date': end_date,
            'quarter': quarter,
            'historic_data': historic_data
        }
        
        # Initialize result storage
        session['analysis_results'] = {
            'data_analyst': {'status': 'pending'},
            'trade_strategy': {'status': 'pending'},
            'trade_advisor': {'status': 'pending'},
            'risk_advisor': {'status': 'pending'},
            'current_agent': 'data_analyst'
        }
        
        return render_template('results.html', 
                               inputs=session['analysis_inputs'],
                               results=session['analysis_results'])
    
    return render_template('index.html')

@app.route('/run_agent/<agent_name>', methods=['POST'])
def run_agent(agent_name):
    """Run a specific agent and return its results"""
    if 'analysis_inputs' not in session:
        return jsonify({'error': 'No analysis in progress. Please start a new analysis.'})
    
    inputs = session['analysis_inputs']
    results = session.get('analysis_results', {})
    
    try:
        if agent_name == 'data_analyst':
            logger.info(f"Starting data analysis for {inputs['ticker']}")
            
            # Run data analyst agent
            raw_stock_data = data_analyst.get_stock_overview(inputs['ticker'])
            
            # Initialize the result structure
            results['data_analyst'] = {
                'status': 'processing',  # Start with processing status
                'data': {}
            }
            
            # Handle stock overview errors
            if raw_stock_data is None:
                logger.error("Stock overview returned None")
                results['data_analyst'].update({
                    'status': 'error',
                    'message': 'Failed to fetch stock data',
                    'data': {
                        'company_info': {
                            'ticker': inputs['ticker'],
                            'name': 'N/A',
                            'sector': 'N/A',
                            'industry': 'N/A'
                        },
                        'error': 'Failed to fetch stock data'
                    }
                })
            elif raw_stock_data.get('error'):
                logger.warning(f"Error in stock overview: {raw_stock_data['error']}")
                results['data_analyst'].update({
                    'status': 'error',
                    'message': raw_stock_data['error'],
                    'data': {
                        'company_info': {
                            'ticker': inputs['ticker'],
                            'name': 'N/A',
                            'sector': 'N/A',
                            'industry': 'N/A'
                        },
                        'error': raw_stock_data['error']
                    }
                })
            else:
                # Transform data for frontend
                try:
                    frontend_data = data_analyst.get_refined_data(raw_stock_data)
                    if frontend_data.get('error'):
                        logger.warning(f"Error in data transformation: {frontend_data['error']}")
                        results['data_analyst'].update({
                            'status': 'error',
                            'message': frontend_data['error'],
                            'data': {
                                'company_info': {
                                    'ticker': inputs['ticker'],
                                    'name': raw_stock_data.get('company_info', {}).get('name', 'N/A'),
                                    'sector': raw_stock_data.get('company_info', {}).get('sector', 'N/A'),
                                    'industry': raw_stock_data.get('company_info', {}).get('industry', 'N/A')
                                },
                                'error': frontend_data['error']
                            }
                        })
                    else:
                        results['data_analyst'].update({
                            'status': 'completed',
                            'data': frontend_data
                        })
                except Exception as e:
                    logger.error(f"Error transforming data: {str(e)}")
                    results['data_analyst'].update({
                        'status': 'error',
                        'message': str(e),
                        'data': {
                            'company_info': {
                                'ticker': inputs['ticker'],
                                'name': raw_stock_data.get('company_info', {}).get('name', 'N/A'),
                                'sector': raw_stock_data.get('company_info', {}).get('sector', 'N/A'),
                                'industry': raw_stock_data.get('company_info', {}).get('industry', 'N/A')
                            },
                            'error': f"Error transforming data: {str(e)}"
                        }
                    })
            
            # Always set next agent unless there's a critical error
            if results['data_analyst']['status'] != 'error':
                results['current_agent'] = 'trade_strategy'
            else:
                results['current_agent'] = 'failed'
            
            # Save results to session
            session['analysis_results'] = results
            
            return jsonify({
                'status': 'success',
                'results': results
            })
            
        elif agent_name == 'trade_strategy':
            # Run trade strategy agent
            try:
                # Get both strategies
                ma_strategy = trade_strategy.moving_average_crossover_strategy(inputs['ticker'])
                rsi_strategy = trade_strategy.rsi_strategy(inputs['ticker'])
            
                # Check for errors in either strategy
                if 'error' in ma_strategy or 'error' in rsi_strategy:
                    logger.error("Error in strategy calculation")
                    results['trade_strategy'] = {
                        'status': 'error',
                        'error': 'Strategy calculation failed',
                        'ma_error': ma_strategy.get('error'),
                        'rsi_error': rsi_strategy.get('error')
                    }
                else:
                    # Structure the response as expected by frontend
                    results['trade_strategy'] = {
                            'status': 'completed',
                                'data': {
                            'ma_strategy': ma_strategy,
                            'rsi_strategy': rsi_strategy
                        }
                    }
            
            except Exception as e:
                logger.error(f"Error in trade strategy: {str(e)}")
                results['trade_strategy'] = {
                    'status': 'error',
                    'error': str(e)
                }
            
            if results['trade_strategy']['status'] != 'error':
                results['current_agent'] = 'trade_advisor'
            else:
                results['current_agent'] = 'failed'
            
        elif agent_name == 'trade_advisor':
            logger.info(f"Starting trade advisor analysis for {inputs['ticker']}")
            try:
                # Get trading recommendation
                recommendation = trade_advisor.get_trading_recommendation(inputs['ticker'])
            
                if 'error' in recommendation:
                    logger.error(f"Error in trading recommendation: {recommendation['error']}")
                    results['trade_advisor'] = {
                        'status': 'completed',
                        'recommendation': {
                            'error': recommendation['error'],
                            'ticker': inputs['ticker']
                        }
                    }
                else:
                    logger.info(f"Successfully generated recommendation for {inputs['ticker']}")
                    
                    # Map the signals to sentiment
                    signal_to_sentiment = {
                        'BUY': 'bullish',
                        'SELL': 'bearish',
                        'HOLD': 'neutral'
                    }
                    
                    # Get the technical indicators
                    tech_indicators = recommendation.get('technical_indicators', {})
                    
                    # Calculate confidence based on multiple factors
                    rsi_confidence = abs(tech_indicators.get('rsi', 50) - 50) * 2  # RSI deviation from neutral
                    macd_confidence = 100 if tech_indicators.get('macd', 0) > tech_indicators.get('macd_signal', 0) else 0
                    momentum_confidence = min(abs(tech_indicators.get('momentum', 0) * 100), 100)  # Scale momentum to 0-100
                    
                    # Average confidence
                    confidence = (rsi_confidence + macd_confidence + momentum_confidence) / 3
                    
                    results['trade_advisor'] = {
                        'status': 'completed',
                        'recommendation': {
                            'ticker': inputs['ticker'],
                            'signal': signal_to_sentiment.get(recommendation['overall'], 'neutral'),
                            'confidence': round(confidence, 2),
                            'technical_analysis': {
                                'current_price': round(tech_indicators.get('close', 0), 2),
                                'RSI': round(tech_indicators.get('rsi', 0), 2),
                                'MA20': None,  # Add if available
                                'MA50': None,  # Add if available
                                'MA200': None,  # Add if available
                                'overall_signal': recommendation['overall']
                            },
                            'sentiment_analysis': {
                                'sentiment': 'neutral',  # Add actual sentiment if available
                                'sentiment_score': 0,  # Add actual score if available
                                'articles_count': 0  # Add actual count if available
                            },
                            'price_momentum': {
                                'momentum': tech_indicators.get('momentum', 0),
                                'error': None
                            },
                            'earnings_analysis': {
                                'quarter': recommendation.get('timestamp', '').split('T')[0],
                                'summary': "Latest technical analysis indicates " + 
                                         f"RSI at {round(tech_indicators.get('rsi', 0), 2)}, " +
                                         f"MACD at {round(tech_indicators.get('macd', 0), 2)}, " +
                                         f"with {round(tech_indicators.get('momentum', 0) * 100, 2)}% momentum.",
                                'error': None
                            }
                        }
                    }
            except Exception as e:
                logger.error(f"Error in trade advisor: {str(e)}", exc_info=True)
                results['trade_advisor'] = {
                    'status': 'completed',
                    'recommendation': {
                        'error': str(e),
                        'ticker': inputs['ticker']
                    }
                }
            
            if results['trade_advisor']['status'] != 'error':
                results['current_agent'] = 'risk_advisor'
            else:
                results['current_agent'] = 'failed'
            
        elif agent_name == 'risk_advisor':
            # Run risk advisor agent
            try:
                risk_assessment = risk_advisor.analyze_risk(inputs['ticker'])
            except Exception as e:
                logger.error(f"Error in risk assessment: {str(e)}")
                risk_assessment = {'error': str(e)}
            
            results['risk_advisor'] = {
                'status': 'completed',
                'risk_assessment': risk_assessment
            }
            results['current_agent'] = 'completed'
            
        # Save results to session
        session['analysis_results'] = results
        
        return jsonify({
                'status': 'success',
                'results': results
        })
        
    except Exception as e:
        logger.error(f"Error running {agent_name}: {str(e)}")
        error_message = f"Error running {agent_name}: {str(e)}"
        
        # Update the specific agent's status
        results[agent_name] = {
            'status': 'error',
            'message': error_message,
            'data': {
                'company_info': {
                    'ticker': inputs['ticker'],
                    'name': 'N/A',
                    'sector': 'N/A',
                    'industry': 'N/A'
                },
                'error': error_message
            }
        }
        
        # Save to session
        session['analysis_results'] = results
        
        return jsonify({
                'status': 'error',
            'message': error_message,
                'results': results
        })


@app.route('/technical_indicators', methods=['GET', 'POST'])
def technical_indicators():
    """Handle technical indicators page"""
    from services.technical_indicator import fetch_indicator
    
    # Define available functions and intervals
    functions = [
        'SMA', 'EMA', 'WMA', 'DEMA', 'TEMA', 'TRIMA', 'KAMA',
        'MAMA', 'T3', 'MACD', 'MACDEXT', 'STOCH', 'STOCHF', 'RSI', 'STOCHRSI',
        'WILLR', 'ADX', 'ADXR', 'APO', 'PPO', 'MOM', 'BOP', 'CCI',
        'CMO', 'ROC', 'ROCR', 'AROON', 'AROONOSC', 'MFI', 'TRIX',
        'ULTOSC', 'DX', 'MINUS_DI', 'PLUS_DI', 'MINUS_DM', 'PLUS_DM',
        'BBANDS', 'MIDPOINT', 'MIDPRICE', 'SAR', 'TRANGE', 'ATR',
        'NATR', 'AD', 'ADOSC', 'OBV', 'HT_TRENDLINE', 'HT_SINE',
        'HT_TRENDMODE', 'HT_DCPERIOD', 'HT_DCPHASE', 'HT_PHASOR'
    ]
    
    intervals = [
        'daily', 'weekly', 'monthly', '60min', '30min', '15min', '5min', '1min'
    ]
    
    # If it's a GET request, just render the form
    if request.method == 'GET':
        return render_template('technical_indicators.html', 
                              functions=functions, 
                              intervals=intervals)
    
    # Handle POST request (form submission)
    symbol = request.form.get('symbol', '')
    function = request.form.get('function', '')
    interval = request.form.get('interval', 'daily')
    time_period = request.form.get('time_period', 14)
    series_type = request.form.get('series_type', 'close')
    days_to_show = int(request.form.get('days', 30))
    
    # Validate inputs
    if not symbol or not function:
        return render_template('technical_indicators.html', 
                              functions=functions, 
                              intervals=intervals,
                              error="Please provide both symbol and indicator function")
    
    try:
        # Try to get API key from environment or ask user for it
        api_key = os.environ.get('ALPHA_VANTAGE_API_KEY')
        if not api_key:
            logger.warning("Alpha Vantage API key not set. Using demo mode with limited functionality.")
            # You could redirect to a page asking for API key here
        
        # Fetch the indicator data
        results = fetch_indicator(symbol, function, interval, time_period, series_type, api_key)
        
        # Check for errors
        if "Error Message" in results or "Information" in results:
            error_msg = results.get("Error Message") or results.get("Information")
            return render_template('technical_indicators.html', 
                                  functions=functions, 
                                  intervals=intervals,
                                  error=error_msg)
            
        # Process results for display
        # Sort by timestamp (most recent first)
        sorted_results = dict(sorted(results.items(), reverse=True)[:days_to_show])
        
        # Extract keys for the table headers (different indicators have different data keys)
        if sorted_results:
            first_entry = next(iter(sorted_results.values()))
            result_keys = list(first_entry.keys())
        else:
            result_keys = []
            
        # Prepare chart data
        chart_data = {
            'timestamps': [],
            'values': []
        }
        
        # Reverse for chart (oldest first)
        for timestamp, values in reversed(list(sorted_results.items())):
            if result_keys:  # Use the first data key for the chart
                key = result_keys[0]
                try:
                    value = float(values[key])
                    chart_data['timestamps'].append(timestamp)
                    chart_data['values'].append(value)
                except (ValueError, TypeError):
                    # Skip non-numeric values
                    pass
        
        return render_template('technical_indicators.html',
                              functions=functions,
                              intervals=intervals,
                              results=sorted_results,
                              result_keys=result_keys,
                              chart_data=chart_data,
                              symbol=symbol,
                              function=function,
                              interval=interval)
                              
    except Exception as e:
        logger.error(f"Error fetching technical indicator: {str(e)}")
        return render_template('technical_indicators.html', 
                              functions=functions, 
                              intervals=intervals,
                              error=f"An error occurred: {str(e)}")

@app.errorhandler(404)
def page_not_found(e):
    return render_template('index.html'), 404

@app.route('/api/top_stocks')
def top_stocks_api():
    try:
        from services.stock_data import fetch_stock_basics
        import concurrent.futures
        import yfinance as yf
        
        logger.info("Fetching top stocks data...")
        stocks_list = []
        
        # Fetch basic data for each stock
        for symbol in DEFAULT_SYMBOLS:
            try:
                # Get basic ticker data
                stock_data = fetch_stock_basics(symbol)
                
                # Get company info
                ticker = yf.Ticker(symbol)
                info = ticker.info
                
                # Create complete stock data including company name and sector
                stock_obj = {
                    'ticker': symbol,
                    'company_name': info.get('shortName', 'Unknown'),
                    'sector': info.get('sector', 'Unknown'),
                    'industry': info.get('industry', 'Unknown'),
                    'close': stock_data.get('close', 0),
                    'previous_close': info.get('previousClose', 0),
                    'volume': stock_data.get('volume', 0),
                    'avg_volume': info.get('averageVolume', 0),
                    'market_cap': info.get('marketCap', 0),
                    'pe_ratio': info.get('trailingPE', None),
                    'eps': info.get('trailingEps', None),
                    'dividend_yield': info.get('dividendYield', 0),
                    '50day_ma': info.get('fiftyDayAverage', 0),
                    '200day_ma': info.get('twoHundredDayAverage', 0)
                }
                
                # Calculate percent change
                if stock_obj['previous_close'] and stock_obj['previous_close'] > 0:
                    stock_obj['percent_change'] = ((stock_obj['close'] - stock_obj['previous_close']) / 
                                                stock_obj['previous_close']) * 100
                else:
                    stock_obj['percent_change'] = 0
                    
                # Get recent price history for mini charts (7 days)
                history = ticker.history(period="10d")
                if not history.empty:
                    recent_prices = []
                    for date, row in history.iterrows():
                        recent_prices.append({
                            'date': date.strftime('%Y-%m-%d'),
                            'close': row['Close']
                        })
                    stock_obj['recent_prices'] = recent_prices
                
                # Get 52 week range
                stock_obj['52_week_range'] = f"{info.get('fiftyTwoWeekLow', 0):.2f} - {info.get('fiftyTwoWeekHigh', 0):.2f}"
                
                stocks_list.append(stock_obj)
                logger.info(f"Added {symbol} to top stocks list")
                
            except Exception as e:
                logger.error(f"Error processing {symbol}: {e}")
                # Still add the stock with minimum data to prevent frontend errors
                stocks_list.append({
                    'ticker': symbol,
                    'company_name': symbol,
                    'sector': 'N/A',
                    'close': 0,
                    'percent_change': 0,
                    'market_cap': 0,
                    'pe_ratio': None,
                    'error': str(e)
                })
        
        # Use the standard json module with our encoder function
        return app.response_class(
            response=json.dumps(stocks_list, default=np_encoder),
            status=200,
            mimetype='application/json'
        )
    except Exception as e:
        logger.error(f"Error fetching top stocks: {e}")
        return app.response_class(
            response=json.dumps({"error": str(e)}, default=np_encoder),
            status=500,
            mimetype='application/json'
        )

@app.errorhandler(500)
def server_error(e):
    logger.error(f"Server error: {str(e)}")
    return render_template('index.html', error="An internal server error occurred."), 500

@socketio.on('connect')
def handle_connect():
    logger.info('Client connected')

@socketio.on('disconnect')
def handle_disconnect():
    logger.info('Client disconnected')

@app.route('/about')
def about():
    return render_template('about.html')

if __name__ == '__main__':
    socketio.run(app, debug=True)

