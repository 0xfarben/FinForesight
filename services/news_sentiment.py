import logging
import requests
import os
from datetime import datetime
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

def get_news_sentiment(tickers):
    """
    Get news sentiment for specified tickers
    
    Args:
        tickers (str): Comma-separated list of stock ticker symbols
        
    Returns:
        dict: News sentiment data with whatever was successfully fetched
    """
    try:
        # Split tickers if provided as comma-separated string
        if isinstance(tickers, str):
            ticker_list = [t.strip().upper() for t in tickers.split(',')]
        else:
            ticker_list = [tickers.strip().upper()]
        
        # Check for Alpha Vantage API key
        api_key = os.getenv('ALPHA_VANTAGE_API_KEY')
        if not api_key:
            error_msg = "Alpha Vantage API key not set. Please set ALPHA_VANTAGE_API_KEY in your environment variables."
            logger.error(error_msg)
            return {
                "error": error_msg,
                "has_error": True,
                "results": {}
            }
        
        # Fetch sentiment for each ticker
        results = {}
        has_error = False
        error_message = None
        
        for ticker in ticker_list:
            logger.info(f"Fetching news sentiment for {ticker}")
            url = f"https://www.alphavantage.co/query?function=NEWS_SENTIMENT&tickers={ticker}&apikey={api_key}"
            
            try:
                response = requests.get(url)
                response.raise_for_status()
                
                data = response.json()
                logger.debug(f"Response for {ticker}: {data}")
                
                # Check if we got valid data
                if 'feed' not in data:
                    if 'Note' in data:
                        # API limit reached - log it but continue with what we have
                        error_msg = f"API limit reached: {data['Note']}"
                        logger.warning(error_msg)
                        has_error = True
                        error_message = error_msg
                        continue
                    elif 'Information' in data:
                        # Other API information - log it but continue with what we have
                        error_msg = f"API information: {data['Information']}"
                        logger.warning(error_msg)
                        has_error = True
                        error_message = error_msg
                        continue
                    else:
                        logger.warning(f"No news data found for {ticker}. Response: {data}")
                        continue
                
                # Process the news feed
                news_feed = data['feed']
                sentiment_scores = []
                relevance_scores = []
                ticker_news = []
                
                for article in news_feed:
                    ticker_sentiment = None
                    
                    # Find the sentiment for this specific ticker
                    for ticker_sentiment_item in article.get('ticker_sentiment', []):
                        if ticker_sentiment_item.get('ticker') == ticker:
                            ticker_sentiment = ticker_sentiment_item
                            break
                    
                    if not ticker_sentiment:
                        continue
                    
                    try:
                        sentiment_score = float(ticker_sentiment.get('ticker_sentiment_score', 0))
                        relevance_score = float(ticker_sentiment.get('relevance_score', 0))
                    except (ValueError, TypeError) as e:
                        logger.warning(f"Error parsing sentiment scores for {ticker}: {e}")
                        continue
                    
                    sentiment_scores.append(sentiment_score)
                    relevance_scores.append(relevance_score)
                    
                    # Keep the article if it's relevant enough (relevance > 0.2)
                    if relevance_score > 0.2:  # Lowered threshold to get more news
                        ticker_news.append({
                            'title': article.get('title', 'No title'),
                            'summary': article.get('summary', 'No summary'),
                            'sentiment_score': sentiment_score,
                            'relevance_score': relevance_score,
                            'url': article.get('url', ''),
                            'time_published': article.get('time_published', ''),
                            'authors': article.get('authors', []),
                            'source': article.get('source', 'Unknown')
                        })
                
                if sentiment_scores:
                    # Calculate average sentiment
                    avg_sentiment = sum(sentiment_scores) / len(sentiment_scores)
                    
                    # Classify overall sentiment
                    sentiment_label = "Neutral"
                    if avg_sentiment > 0.25:
                        sentiment_label = "Bullish"
                    elif avg_sentiment > 0.1:
                        sentiment_label = "Somewhat Bullish"
                    elif avg_sentiment < -0.25:
                        sentiment_label = "Bearish"
                    elif avg_sentiment < -0.1:
                        sentiment_label = "Somewhat Bearish"
                    
                    # Save results
                    results[ticker] = {
                        'sentiment_score': avg_sentiment,
                        'sentiment_label': sentiment_label,
                        'news_count': len(ticker_news),
                        'news': sorted(ticker_news, key=lambda x: x['relevance_score'], reverse=True)[:10]  # Top 10 most relevant news
                    }
                    
                    logger.info(f"Successfully processed news sentiment for {ticker}")
                
            except requests.exceptions.RequestException as e:
                error_msg = f"Error fetching data for {ticker}: {str(e)}"
                logger.error(error_msg)
                has_error = True
                error_message = error_msg
                continue  # Continue with other tickers
        
        # Return both results and error status
        return {
            "has_error": has_error,
            "error": error_message if has_error else None,
            "results": results
        }
        
    except Exception as e:
        error_msg = f"Error getting news sentiment: {str(e)}"
        logger.error(error_msg)
        return {
            "has_error": True,
            "error": error_msg,
            "results": {}
        }

if __name__ == "__main__":
    # Test the function
    tickers = "AAPL"
    sentiment_data = get_news_sentiment(tickers)
    
    # Print any errors
    if sentiment_data["has_error"]:
        print(f"\nWarning: {sentiment_data['error']}")
    
    # Print results if we have any
    if sentiment_data["results"]:
        print("\nSuccessfully fetched results:")
        for ticker, data in sentiment_data["results"].items():
            print(f"\nResults for {ticker}:")
            print(f"Sentiment Score: {data['sentiment_score']:.2f}")
            print(f"Sentiment Label: {data['sentiment_label']}")
            print(f"Number of news items: {data['news_count']}")
            if data['news']:
                print("\nTop news items:")
                for news in data['news']:
                    print(f"\nTitle: {news['title']}")
                    print(f"Sentiment: {news['sentiment_score']:.2f}")
                    print(f"Relevance: {news['relevance_score']:.2f}")
    else:
        print("\nNo results were successfully fetched.")