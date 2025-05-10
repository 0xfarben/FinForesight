import os
import json
import logging
import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import re
import asyncio
from .base_agent import BaseAgent
from .dtmac import MessagePriority, DTMessage

logger = logging.getLogger(__name__)

class TradeAdvisorAgent(BaseAgent):
    """
    Trade Advisor Agent - Uses predictive analytics and machine learning to
    forecast market trends and provide trading recommendations.
    """

    def __init__(self, dtmac):
        # Define topics this agent is interested in
        topics = [
            "trading_signals",
            "analysis_results",
            "economic_data",
            "risk_alerts"
        ]
        super().__init__("trade_advisor", dtmac, topics)
        
        # Register specific message handlers
        self.dtmac.register_handler(self.agent_id, "strategy_update", self.handle_strategy_update)
        self.dtmac.register_handler(self.agent_id, "economic_update", self.handle_economic_update)
        self.dtmac.register_handler(self.agent_id, "risk_alert", self.handle_risk_alert)
        
        # Initialize agent state
        self.advice = {}
        self.last_update = None
        
        self.data_archive = 'data_archive'
        self.predictions_archive = 'predictions_archive'
        os.makedirs(self.data_archive, exist_ok=True)
        os.makedirs(self.predictions_archive, exist_ok=True)
    
    async def get_status(self) -> Dict[str, Any]:
        return {
            "status": "active",
            "last_update": self.last_update,
            "active_advice": len(self.advice),
            "subscribed_topics": self.get_subscribed_topics()
        }
    
    async def handle_strategy_update(self, message: DTMessage):
        """Handle strategy updates from trade strategy agent"""
        strategy_data = message.content
        symbol = strategy_data.get("symbol")
        
        # Generate trading advice based on strategy
        advice = await self.generate_advice(strategy_data)
        
        # Store advice
        self.advice[symbol] = advice
        self.last_update = datetime.now()
        
        # Send advice to UI
        await self.send_to_agent(
            recipient="ui_agent",
            content={
                "symbol": symbol,
                "advice": advice,
                "timestamp": self.last_update.isoformat()
            },
            message_type="trading_advice",
            priority=MessagePriority.HIGH
        )
    
    async def handle_economic_update(self, message: DTMessage):
        """Handle economic data updates"""
        economic_data = message.content
        
        # Update advice based on economic conditions
        for symbol, current_advice in self.advice.items():
            updated_advice = await self.adjust_advice_for_economics(
                current_advice,
                economic_data
            )
            
            # Update stored advice
            self.advice[symbol] = updated_advice
            
            # Send updated advice to UI
            await self.send_to_agent(
                recipient="ui_agent",
                content={
                    "symbol": symbol,
                    "advice": updated_advice,
                    "economic_adjusted": True,
                    "timestamp": datetime.now().isoformat()
                },
                message_type="trading_advice",
                priority=MessagePriority.NORMAL
            )
    
    async def handle_risk_alert(self, message: DTMessage):
        """Handle risk alerts"""
        risk_data = message.content
        symbol = risk_data.get("symbol")
        
        if symbol in self.advice:
            # Adjust advice based on risk
            updated_advice = await self.adjust_advice_for_risk(
                self.advice[symbol],
                risk_data
            )
            
            # Update stored advice
            self.advice[symbol] = updated_advice
            
            # Send updated advice to UI
            await self.send_to_agent(
                recipient="ui_agent",
                content={
                    "symbol": symbol,
                    "advice": updated_advice,
                    "risk_adjusted": True,
                    "timestamp": datetime.now().isoformat()
                },
                message_type="trading_advice",
                priority=MessagePriority.HIGH
            )
    
    async def generate_advice(self, strategy_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate trading advice based on strategy and market conditions"""
        advice = {
            "recommendation": self.determine_recommendation(strategy_data),
            "confidence_score": self.calculate_confidence(strategy_data),
            "time_horizon": self.determine_time_horizon(strategy_data),
            "key_factors": self.identify_key_factors(strategy_data),
            "risk_level": self.assess_risk_level(strategy_data)
        }
        return advice
    
    async def adjust_advice_for_economics(self, 
                                        advice: Dict[str, Any], 
                                        economic_data: Dict[str, Any]) -> Dict[str, Any]:
        """Adjust advice based on economic conditions"""
        adjusted = advice.copy()
        
        # Adjust recommendation based on economic indicators
        adjusted["recommendation"] = self.adjust_recommendation(
            advice["recommendation"],
            economic_data
        )
        
        # Update confidence score
        adjusted["confidence_score"] = self.update_confidence(
            advice["confidence_score"],
            economic_data
        )
        
        return adjusted
    
    async def adjust_advice_for_risk(self, 
                                   advice: Dict[str, Any], 
                                   risk_data: Dict[str, Any]) -> Dict[str, Any]:
        """Adjust advice based on risk assessment"""
        adjusted = advice.copy()
        
        # Update risk level
        adjusted["risk_level"] = self.update_risk_level(
            advice["risk_level"],
            risk_data
        )
        
        # Adjust recommendation if necessary
        if risk_data["risk_score"] > 0.7:  # High risk threshold
            adjusted["recommendation"] = self.conservative_recommendation(
                advice["recommendation"]
            )
        
        return adjusted
    
    def load_historical_data(self, ticker: str) -> Optional[pd.DataFrame]:
        """
        Load the most recent historical data for a ticker from data_archive
        """
        try:
            logger.info(f"Loading historical data for {ticker}")
            
            # Find all historic data files for this ticker
            files = [f for f in os.listdir(self.data_archive) 
                    if f.startswith(f"{ticker}_historic_data_") and f.endswith('.json')]
            
            if not files:
                logger.error(f"No historical data files found for {ticker} in {self.data_archive}")
                return None
            
            # Sort files by timestamp and get the latest one
            latest_file = sorted(files)[-1]
            file_path = os.path.join(self.data_archive, latest_file)
            logger.info(f"Loading most recent file: {latest_file}")
            
            with open(file_path, 'r') as f:
                data = json.load(f)
            
            # Convert to DataFrame
            df = pd.DataFrame(data)
            logger.info(f"Loaded DataFrame with columns: {df.columns.tolist()}")
            
            # Create a mapping of current column names to lowercase
            column_mapping = {col: col.lower() for col in df.columns}
            df.rename(columns=column_mapping, inplace=True)
            logger.info(f"Converted columns to lowercase: {df.columns.tolist()}")
            
            # Convert date column to datetime
            if 'Date' in df.columns:
                df.rename(columns={'Date': 'date'}, inplace=True)
            
            if 'date' not in df.columns:
                logger.error("No date column found in DataFrame")
                return None
            
            df['date'] = pd.to_datetime(df['date'])
            df.set_index('date', inplace=True)
            
            # Convert numeric columns to float
            numeric_columns = ['open', 'high', 'low', 'close', 'volume']
            for col in numeric_columns:
                if col in df.columns:
                    df[col] = df[col].astype(float)
                else:
                    logger.warning(f"Expected column {col} not found in DataFrame")
            
            # Verify required columns exist
            required_columns = ['close', 'high', 'low']  # Required for technical analysis
            missing_columns = [col for col in required_columns if col not in df.columns]
            if missing_columns:
                logger.error(f"Missing required columns: {missing_columns}")
                return None
            
            return df
            
        except Exception as e:
            logger.error(f"Error loading historical data for {ticker}: {str(e)}")
            logger.exception(e)
            return None

    def calculate_price_momentum(self, df: pd.DataFrame, window: int = 14) -> float:
        """
        Calculate price momentum using percentage change
        """
        try:
            if not isinstance(df, pd.DataFrame):
                logger.error(f"Invalid input type for df: {type(df)}")
                return 0.0
                
            if df is None or df.empty:
                logger.error("No data provided for momentum calculation")
                return 0.0
                
            if 'close' not in df.columns:
                logger.error("Close price data not found in DataFrame")
                return 0.0
                
            momentum = df['close'].pct_change(periods=window).iloc[-1]
            return float(momentum) if not np.isnan(momentum) else 0.0
            
        except Exception as e:
            logger.error(f"Error calculating momentum: {str(e)}", exc_info=True)
            return 0.0
    
    def analyze_sentiment(self, ticker: str) -> Dict[str, Any]:
        """
        Analyze news sentiment for a ticker
        """
        try:
            # Look for latest sentiment file
            files = [f for f in os.listdir(self.data_archive) if f == f"{ticker}_news_sentiment.json"]
            if not files:
                return {"error": f"No sentiment data found for {ticker}"}
            
            file_path = os.path.join(self.data_archive, files[0])
            with open(file_path, 'r') as f:
                data = json.load(f)
            
            if 'feed' not in data:
                return {"error": "Invalid sentiment data format"}
            
            feed = data.get('feed', [])
            if not feed:
                return {"ticker": ticker, "sentiment": "neutral", "sentiment_score": 0, "articles_count": 0}
            
            # Calculate average sentiment score
            sentiment_scores = []
            titles = []
            urls = []
            timestamps = []
            
            for article in feed[:10]:  # Analyze the latest 10 articles
                sentiment_score = article.get('overall_sentiment_score', 0)
                sentiment_scores.append(sentiment_score)
                titles.append(article.get('title', ''))
                urls.append(article.get('url', ''))
                timestamps.append(article.get('time_published', ''))
            
            avg_sentiment = sum(sentiment_scores) / len(sentiment_scores) if sentiment_scores else 0
            
            # Determine sentiment label
            sentiment_label = "neutral"
            if avg_sentiment > 0.25:
                sentiment_label = "bullish"
            elif avg_sentiment < -0.25:
                sentiment_label = "bearish"
            
            return {
                "ticker": ticker,
                "sentiment": sentiment_label,
                "sentiment_score": round(avg_sentiment, 2),
                "articles_count": len(feed),
                "recent_articles": [
                    {
                        "title": title,
                        "url": url,
                        "time": timestamp,
                        "sentiment_score": round(score, 2)
                    } for title, url, timestamp, score in zip(titles, urls, timestamps, sentiment_scores)
                ]
            }
            
        except Exception as e:
            logger.error(f"Error analyzing sentiment for {ticker}: {e}")
            return {"error": f"Error analyzing sentiment: {str(e)}"}
    
    def analyze_earnings_transcript(self, ticker: str, quarter: str = None) -> Dict[str, Any]:
        """
        Analyze earnings call transcript for a ticker
        """
        try:
            # If quarter not specified, look for the most recent transcript
            if quarter is None:
                files = [f for f in os.listdir(self.data_archive) if f.startswith(f"{ticker}_earnings_transcript_") and f.endswith('.json')]
                if not files:
                    return {"error": f"No earnings transcript found for {ticker}"}
                
                file_path = os.path.join(self.data_archive, sorted(files)[-1])
            else:
                quarter_clean = quarter.replace(' ', '_').replace('/', '_')
                file_path = os.path.join(self.data_archive, f"{ticker}_earnings_transcript_{quarter_clean}.json")
                if not os.path.exists(file_path):
                    return {"error": f"No earnings transcript found for {ticker} {quarter}"}
            
            with open(file_path, 'r') as f:
                data = json.load(f)
            
            if 'transcript' not in data:
                return {"error": "Invalid transcript data format"}
            
            transcript = data.get('transcript', '')
            # Handle case where transcript might be a list
            if isinstance(transcript, list):
                transcript = ' '.join(transcript)
            quarter_info = data.get('quarter', '')
            year = data.get('year', '')
            
            # Simple text analysis for key metrics and outlook
            key_phrases = {
                "revenue": r"revenue.{0,50}(increased|decreased|grew|declined).{0,50}(\d+\.?\d*%?)",
                "profit": r"(net income|profit|earnings).{0,50}(increased|decreased|grew|declined).{0,50}(\d+\.?\d*%?)",
                "outlook": r"(outlook|guidance|forecast).{0,100}(positive|negative|optimistic|cautious|challenging)",
                "growth": r"growth.{0,50}(\d+\.?\d*%)",
                "margin": r"(gross|operating|profit) margin.{0,50}(\d+\.?\d*%)",
                "challenges": r"(challenges|headwinds|difficulties).{0,100}"
            }
            
            # Extract matches
            insights = {}
            for key, pattern in key_phrases.items():
                matches = re.findall(pattern, transcript, re.IGNORECASE)
                if matches:
                    insights[key] = matches
            
            # Extract a summary (first 500 characters of the transcript)
            summary = transcript[:500] + "..." if len(transcript) > 500 else transcript
            
            return {
                "ticker": ticker,
                "quarter": quarter_info,
                "year": year,
                "insights": insights,
                "summary": summary,
                "full_transcript_available": True
            }
            
        except Exception as e:
            logger.error(f"Error analyzing earnings transcript for {ticker}: {e}")
            return {"error": f"Error analyzing earnings transcript: {str(e)}"}
    
    def get_technical_signals(self, df: pd.DataFrame) -> Dict[str, float]:
        """
        Calculate technical indicators and return their values
        """
        try:
            if not isinstance(df, pd.DataFrame):
                logger.error(f"Invalid input type for df: {type(df)}")
                return {}
                
            if df is None or df.empty:
                logger.error("No data provided for technical analysis")
                return {}
                
            if 'close' not in df.columns:
                logger.error("Close price data not found in DataFrame")
                return {}
            
            # Calculate RSI
            delta = df['close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))
            
            # Calculate MACD
            exp1 = df['close'].ewm(span=12, adjust=False).mean()
            exp2 = df['close'].ewm(span=26, adjust=False).mean()
            macd = exp1 - exp2
            signal = macd.ewm(span=9, adjust=False).mean()
            
            # Calculate Bollinger Bands
            sma = df['close'].rolling(window=20).mean()
            std = df['close'].rolling(window=20).std()
            upper_band = sma + (std * 2)
            lower_band = sma - (std * 2)
            
            # Get latest values
            latest_close = float(df['close'].iloc[-1])
            latest_rsi = float(rsi.iloc[-1]) if not np.isnan(rsi.iloc[-1]) else 50.0
            latest_macd = float(macd.iloc[-1]) if not np.isnan(macd.iloc[-1]) else 0.0
            latest_signal = float(signal.iloc[-1]) if not np.isnan(signal.iloc[-1]) else 0.0
            latest_upper = float(upper_band.iloc[-1]) if not np.isnan(upper_band.iloc[-1]) else latest_close
            latest_lower = float(lower_band.iloc[-1]) if not np.isnan(lower_band.iloc[-1]) else latest_close
            
            return {
                'rsi': latest_rsi,
                'macd': latest_macd,
                'macd_signal': latest_signal,
                'bb_upper': latest_upper,
                'bb_lower': latest_lower,
                'close': latest_close
            }
            
        except Exception as e:
            logger.error(f"Error calculating technical signals: {str(e)}", exc_info=True)
            return {}
    
    def get_trading_recommendation(self, ticker: str) -> Dict[str, Any]:
        """
        Generate trading recommendation based on technical analysis
        """
        try:
            # Load historical data
            df = self.load_historical_data(ticker)
            if df is None:
                return {'error': f'No historical data available for {ticker}'}
            
            # Calculate technical signals
            signals = self.get_technical_signals(df)
            if not signals:
                return {'error': 'Failed to calculate technical signals'}
            
            # Calculate momentum
            momentum = self.calculate_price_momentum(df)
            
            # Generate recommendation
            recommendation = {
                'ticker': ticker,
                'timestamp': datetime.now().isoformat(),
                'close_price': signals['close'],
                'technical_indicators': {
                    'rsi': signals['rsi'],
                    'macd': signals['macd'],
                    'macd_signal': signals['macd_signal'],
                    'momentum': momentum,
                    'bb_upper': signals['bb_upper'],
                    'bb_lower': signals['bb_lower']
                },
                'signals': {}
            }
            
            # RSI signals
            if signals['rsi'] > 70:
                recommendation['signals']['rsi'] = 'SELL'
            elif signals['rsi'] < 30:
                recommendation['signals']['rsi'] = 'BUY'
            else:
                recommendation['signals']['rsi'] = 'HOLD'
            
            # MACD signals
            if signals['macd'] > signals['macd_signal']:
                recommendation['signals']['macd'] = 'BUY'
            else:
                recommendation['signals']['macd'] = 'SELL'
            
            # Bollinger Bands signals
            if signals['close'] > signals['bb_upper']:
                recommendation['signals']['bollinger'] = 'SELL'
            elif signals['close'] < signals['bb_lower']:
                recommendation['signals']['bollinger'] = 'BUY'
            else:
                recommendation['signals']['bollinger'] = 'HOLD'
            
            # Momentum signals
            if momentum > 0.02:  # 2% positive momentum
                recommendation['signals']['momentum'] = 'BUY'
            elif momentum < -0.02:  # 2% negative momentum
                recommendation['signals']['momentum'] = 'SELL'
            else:
                recommendation['signals']['momentum'] = 'HOLD'
            
            # Overall recommendation based on signal majority
            buy_signals = sum(1 for signal in recommendation['signals'].values() if signal == 'BUY')
            sell_signals = sum(1 for signal in recommendation['signals'].values() if signal == 'SELL')
            
            if buy_signals > sell_signals:
                recommendation['overall'] = 'BUY'
            elif sell_signals > buy_signals:
                recommendation['overall'] = 'SELL'
            else:
                recommendation['overall'] = 'HOLD'
            
            logger.info(f"Generated recommendation for {ticker}: {recommendation['overall']}")
            return recommendation
            
        except Exception as e:
            logger.error(f"Error generating trading recommendation: {str(e)}", exc_info=True)
            return {'error': str(e)}

    def determine_recommendation(self, strategy_data: Dict[str, Any]) -> str:
        # Implement recommendation determination
        pass
    
    def calculate_confidence(self, strategy_data: Dict[str, Any]) -> float:
        # Implement confidence calculation
        pass
    
    def determine_time_horizon(self, strategy_data: Dict[str, Any]) -> str:
        # Implement time horizon determination
        pass
    
    def identify_key_factors(self, strategy_data: Dict[str, Any]) -> List[str]:
        # Implement key factor identification
        pass
    
    def assess_risk_level(self, strategy_data: Dict[str, Any]) -> str:
        # Implement risk level assessment
        pass
    
    def adjust_recommendation(self, 
                            original_recommendation: str, 
                            economic_data: Dict[str, Any]) -> str:
        # Implement recommendation adjustment
        pass
    
    def update_confidence(self, 
                         original_confidence: float, 
                         economic_data: Dict[str, Any]) -> float:
        # Implement confidence update
        pass
    
    def update_risk_level(self, 
                         original_risk: str, 
                         risk_data: Dict[str, Any]) -> str:
        # Implement risk level update
        pass
    
    def conservative_recommendation(self, original_recommendation: str) -> str:
        # Implement conservative recommendation adjustment
        pass

# if __name__ == "__main__":
#     agent = TradeAdvisorAgent()
#     df = agent.get_trading_recommendation('TSLA')
#     print(df)

