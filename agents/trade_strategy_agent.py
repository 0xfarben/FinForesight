import os
import json
import logging
import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional
import matplotlib.pyplot as plt
from datetime import datetime
import asyncio
from .base_agent import BaseAgent
from .dtmac import MessagePriority, DTMessage

logger = logging.getLogger(__name__)

class TradeStrategyAgent(BaseAgent):
    """
    Trade Strategy Agent - Develops and optimizes trading strategies based on
    analyzed data and market trends.
    """

    def __init__(self, dtmac):
        # Define topics this agent is interested in
        topics = [
            "analysis_results",
            "market_data",
            "risk_alerts",
            "trading_signals"
        ]
        super().__init__("trade_strategy", dtmac, topics)
        
        # Register specific message handlers
        self.dtmac.register_handler(self.agent_id, "analysis_complete", self.handle_analysis)
        self.dtmac.register_handler(self.agent_id, "risk_alert", self.handle_risk_alert)
        
        # Initialize agent state
        self.strategies = {}
        self.last_update = None
        
        self.data_archive = 'data_archive'
        self.strategies_archive = 'strategies_archive'
        os.makedirs(self.data_archive, exist_ok=True)
        os.makedirs(self.strategies_archive, exist_ok=True)
        
    async def get_status(self) -> Dict[str, Any]:
        return {
            "status": "active",
            "last_update": self.last_update,
            "active_strategies": len(self.strategies),
            "subscribed_topics": self.get_subscribed_topics()
        }
    
    async def handle_analysis(self, message: DTMessage):
        """Handle analysis results from data analyst"""
        analysis = message.content
        symbol = analysis.get("symbol")
        
        # Generate trading strategies based on analysis
        strategies = await self.generate_strategies(analysis)
        
        # Store strategies
        self.strategies[symbol] = strategies
        self.last_update = datetime.now()
        
        # Broadcast strategies to interested agents
        await self.broadcast_to_topic(
            topic="trading_signals",
            content={
                "symbol": symbol,
                "strategies": strategies,
                "timestamp": self.last_update.isoformat()
            },
            message_type="strategy_update",
            priority=MessagePriority.HIGH
        )
    
    async def handle_risk_alert(self, message: DTMessage):
        """Handle risk alerts from risk advisor"""
        risk_data = message.content
        symbol = risk_data.get("symbol")
        
        # Adjust strategies based on risk
        if symbol in self.strategies:
            adjusted_strategies = await self.adjust_strategies_for_risk(
                self.strategies[symbol],
                risk_data
            )
            
            # Update stored strategies
            self.strategies[symbol] = adjusted_strategies
            
            # Notify other agents of adjusted strategies
            await self.broadcast_to_topic(
                topic="trading_signals",
                content={
                    "symbol": symbol,
                    "strategies": adjusted_strategies,
                    "risk_adjusted": True,
                    "timestamp": datetime.now().isoformat()
                },
                message_type="strategy_update",
                priority=MessagePriority.HIGH
            )
    
    async def generate_strategies(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Generate trading strategies based on analysis"""
        # Your existing strategy generation logic here
        strategies = {
            "entry_points": self.calculate_entry_points(analysis),
            "exit_points": self.calculate_exit_points(analysis),
            "stop_loss": self.calculate_stop_loss(analysis),
            "position_sizing": self.calculate_position_size(analysis),
            "timeframes": self.determine_timeframes(analysis)
        }
        return strategies
    
    async def adjust_strategies_for_risk(self, 
                                       strategies: Dict[str, Any], 
                                       risk_data: Dict[str, Any]) -> Dict[str, Any]:
        """Adjust strategies based on risk assessment"""
        # Your existing risk adjustment logic here
        adjusted = strategies.copy()
        
        # Adjust position sizing based on risk
        adjusted["position_sizing"] = self.adjust_position_size(
            strategies["position_sizing"],
            risk_data["risk_score"]
        )
        
        # Adjust stop loss based on volatility
        adjusted["stop_loss"] = self.adjust_stop_loss(
            strategies["stop_loss"],
            risk_data["volatility"]
        )
        
        return adjusted
    
    # Your existing strategy calculation methods
    def calculate_entry_points(self, analysis: Dict[str, Any]) -> List[float]:
        # Implement entry point calculation
        pass
    
    def calculate_exit_points(self, analysis: Dict[str, Any]) -> List[float]:
        # Implement exit point calculation
        pass
    
    def calculate_stop_loss(self, analysis: Dict[str, Any]) -> float:
        # Implement stop loss calculation
        pass
    
    def calculate_position_size(self, analysis: Dict[str, Any]) -> float:
        # Implement position sizing calculation
        pass
    
    def determine_timeframes(self, analysis: Dict[str, Any]) -> List[str]:
        # Implement timeframe determination
        pass
    
    def adjust_position_size(self, original_size: float, risk_score: float) -> float:
        # Implement position size adjustment
        pass
    
    def adjust_stop_loss(self, original_stop: float, volatility: float) -> float:
        # Implement stop loss adjustment
        pass
    
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
            
            logger.info(f"Found {len(files)} historical data files for {ticker}: {files}")
            
            # Sort files by timestamp (last part of filename before .json)
            files.sort(key=lambda x: x.split('_')[-1].replace('.json', ''), reverse=True)
            latest_file = files[0]
            file_path = os.path.join(self.data_archive, latest_file)
            
            logger.info(f"Loading most recent file: {latest_file}")
            
            with open(file_path, 'r') as f:
                data = json.load(f)
            
            # Convert to DataFrame
            df = pd.DataFrame(data)
            
            logger.info(f"Loaded DataFrame with columns: {df.columns.tolist()}")
            
            # Create a mapping of current column names to lowercase
            column_mapping = {col: col.lower() for col in df.columns}
            
            # Rename columns to lowercase
            df.rename(columns=column_mapping, inplace=True)
            
            logger.info(f"Converted columns to lowercase: {df.columns.tolist()}")
            
            # Convert date column to datetime
            if 'Date' in df.columns:
                df.rename(columns={'Date': 'date'}, inplace=True)
            
            df['date'] = pd.to_datetime(df['date'])
            df.set_index('date', inplace=True)
            
            # Convert numeric columns to float
            numeric_columns = ['open', 'high', 'low', 'close', 'volume']
            for col in numeric_columns:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce')
                else:
                    logger.warning(f"Missing expected column: {col}")
            
            # Sort by index (date) to ensure chronological order
            df.sort_index(inplace=True)
            
            # Verify required columns exist
            required_columns = ['close']  # Add other required columns as needed
            missing_columns = [col for col in required_columns if col not in df.columns]
            if missing_columns:
                logger.error(f"Missing required columns: {missing_columns}")
                return None
            
            logger.info(f"Successfully loaded data for {ticker} with shape {df.shape}")
            return df
            
        except Exception as e:
            logger.error(f"Error loading historical data for {ticker}: {str(e)}", exc_info=True)
            return None
    
    def moving_average_crossover_strategy(self, ticker: str, short_window: int = 20, long_window: int = 50) -> Dict:
        """
        Generate trading signals using moving average crossover strategy
        """
        try:
            logger.info(f"Generating moving average crossover signals for {ticker}")
            
            # Load historical data
            df = self.load_historical_data(ticker)
            if df is None:
                logger.error("No historical data available for MA strategy")
                return {"error": f"No historical data found for {ticker}"}
                
            # Calculate moving averages
            df['ma_short'] = df['close'].rolling(window=short_window).mean()
            df['ma_long'] = df['close'].rolling(window=long_window).mean()
            
            # Generate signals
            df['signal'] = 0
            df.loc[df['ma_short'] > df['ma_long'], 'signal'] = 1    # Buy signal
            df.loc[df['ma_short'] < df['ma_long'], 'signal'] = -1   # Sell signal
            
            # Calculate returns and metrics
            df['returns'] = df['close'].pct_change()
            df['strategy_returns'] = df['returns'] * df['signal'].shift(1)
            df['cumulative_returns'] = (1 + df['returns']).cumprod()
            df['strategy_cumulative_returns'] = (1 + df['strategy_returns']).cumprod()
            
            # Drop rows with NaN values
            df = df.dropna()
            
            # Calculate performance metrics
            total_trades = len(df[df['signal'] != df['signal'].shift(1)])  # Count actual trade signals
            profitable_trades = len(df[(df['signal'] != df['signal'].shift(1)) & (df['strategy_returns'] > 0)])
            win_rate = profitable_trades / total_trades if total_trades > 0 else 0
            
            # Get recent data for display
            recent_df = df.tail(30).copy()
            recent_df.reset_index(inplace=True)
            
            # Format signals for output
            signals = []
            for _, row in recent_df.iterrows():
                signal_dict = {
                    "date": row['date'].strftime('%Y-%m-%d'),
                    "price": float(row['close']),
                    "short_ma": float(row['ma_short']),
                    "long_ma": float(row['ma_long']),
                    "signal": int(row['signal'])
                }
                signals.append(signal_dict)
            
            logger.info(f"Generated MA signals. Total signals: {len(signals)}")
            logger.debug(f"Signal distribution: {df['signal'].value_counts().to_dict()}")
            
            return {
                "ticker": ticker,
                "strategy_type": "Moving Average Crossover",
                "parameters": {
                    "short_window": short_window,
                    "long_window": long_window
                },
                "performance": {
                    "total_trades": total_trades,
                    "profitable_trades": profitable_trades,
                    "win_rate": float(win_rate),
                    "current_signal": "BUY" if df['signal'].iloc[-1] == 1 else "SELL" if df['signal'].iloc[-1] == -1 else "HOLD",
                    "current_short_ma": float(df['ma_short'].iloc[-1]),
                    "current_long_ma": float(df['ma_long'].iloc[-1]),
                    "cumulative_return": float(df['strategy_cumulative_returns'].iloc[-1]),
                    "sharpe_ratio": float(df['strategy_returns'].mean() / df['strategy_returns'].std() * np.sqrt(252)) if len(df) > 0 else 0
                },
                "signals": signals
            }
            
        except Exception as e:
            logger.error(f"Error in moving average strategy: {str(e)}", exc_info=True)
            return {"error": f"Error calculating MA strategy: {str(e)}"}
            
    def rsi_strategy(self, ticker: str, rsi_period: int = 14, overbought: int = 70, oversold: int = 30) -> Dict:
        """
        Generate trading signals using RSI strategy
        """
        try:
            logger.info(f"Generating RSI signals for {ticker}")
            
            # Load historical data
            df = self.load_historical_data(ticker)
            if df is None:
                logger.error("No historical data available for RSI strategy")
                return {"error": f"No historical data found for {ticker}"}
            
            # Calculate RSI
            delta = df['close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=rsi_period).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=rsi_period).mean()
            
            rs = gain / loss
            df['rsi'] = 100 - (100 / (1 + rs))
            
            # Generate signals
            df['signal'] = 0
            df.loc[df['rsi'] < oversold, 'signal'] = 1     # Oversold - Buy signal
            df.loc[df['rsi'] > overbought, 'signal'] = -1  # Overbought - Sell signal
            
            # Calculate returns and metrics
            df['returns'] = df['close'].pct_change()
            df['strategy_returns'] = df['returns'] * df['signal'].shift(1)
            df['cumulative_returns'] = (1 + df['returns']).cumprod()
            df['strategy_cumulative_returns'] = (1 + df['strategy_returns']).cumprod()
            
            # Drop rows with NaN values
            df = df.dropna()
            
            # Calculate performance metrics
            total_trades = len(df[df['signal'] != df['signal'].shift(1)])  # Count actual trade signals
            profitable_trades = len(df[(df['signal'] != df['signal'].shift(1)) & (df['strategy_returns'] > 0)])
            win_rate = profitable_trades / total_trades if total_trades > 0 else 0
            
            # Get recent data for display
            recent_df = df.tail(30).copy()
            recent_df.reset_index(inplace=True)
            
            # Format signals for output
            signals = []
            for _, row in recent_df.iterrows():
                signal_dict = {
                    "date": row['date'].strftime('%Y-%m-%d'),
                    "price": float(row['close']),
                    "rsi": float(row['rsi']),
                    "signal": int(row['signal'])
                }
                signals.append(signal_dict)
            
            logger.info(f"Generated RSI signals. Total signals: {len(signals)}")
            logger.debug(f"Signal distribution: {df['signal'].value_counts().to_dict()}")
            
            return {
                "ticker": ticker,
                "strategy_type": "RSI",
                "parameters": {
                    "rsi_period": rsi_period,
                    "overbought": overbought,
                    "oversold": oversold
                },
                "performance": {
                    "total_trades": total_trades,
                    "profitable_trades": profitable_trades,
                    "win_rate": float(win_rate),
                    "current_signal": "BUY" if df['signal'].iloc[-1] == 1 else "SELL" if df['signal'].iloc[-1] == -1 else "HOLD",
                    "current_rsi": float(df['rsi'].iloc[-1]),
                    "cumulative_return": float(df['strategy_cumulative_returns'].iloc[-1]),
                    "sharpe_ratio": float(df['strategy_returns'].mean() / df['strategy_returns'].std() * np.sqrt(252)) if len(df) > 0 else 0
                },
                "signals": signals
            }
            
        except Exception as e:
            logger.error(f"Error in RSI strategy: {str(e)}", exc_info=True)
            return {"error": f"Error calculating RSI strategy: {str(e)}"}
        
    def get_available_strategies(self, ticker: str = None) -> List[Dict]:
        """
        Get a list of available strategies for a ticker
        """
        try:
            strategies = []
            for file in os.listdir(self.strategies_archive):
                if ticker is None or file.startswith(f"{ticker}_"):
                    file_path = os.path.join(self.strategies_archive, file)
                    with open(file_path, 'r') as f:
                        strategy = json.load(f)
                        strategies.append({
                            "ticker": strategy.get("ticker"),
                            "strategy": strategy.get("strategy"),
                            "parameters": strategy.get("parameters"),
                            "metrics": strategy.get("metrics"),
                            "latest_signal": strategy.get("latest_signal"),
                            "file": file
                        })
            return sorted(strategies, key=lambda x: x.get("metrics", {}).get("cumulative_return", 0), reverse=True)
        except Exception as e:
            logger.error(f"Error getting available strategies: {e}")
            return []

    def analyze(self, ticker: str, strategy_type: str = 'moving_average') -> Dict:
        """
        Analyze the stock data using the specified strategy
        """
        try:
            logger.info(f"Starting analysis for {ticker} using {strategy_type} strategy")
            
            # Generate both MA and RSI strategies
            ma_strategy = self.moving_average_crossover_strategy(ticker)
            rsi_strategy = self.rsi_strategy(ticker)
            
            # Check for errors in either strategy
            if 'error' in ma_strategy or 'error' in rsi_strategy:
                logger.error("Error in one or both strategies")
                return {
                    "error": "Strategy calculation failed",
                    "ma_error": ma_strategy.get('error'),
                    "rsi_error": rsi_strategy.get('error')
                }
            
            # Structure the response for the frontend
            response = {
                "status": "completed",
                "data": {
                    "ma_strategy": ma_strategy,
                    "rsi_strategy": rsi_strategy
                }
            }
            
            logger.info(f"Analysis completed successfully")
            logger.debug(f"MA Strategy signals: {len(ma_strategy['signals'])} points")
            logger.debug(f"RSI Strategy signals: {len(rsi_strategy['signals'])} points")
            
            return response
            
        except Exception as e:
            logger.error(f"Error in analysis: {str(e)}", exc_info=True)
            return {
                "error": f"Analysis failed: {str(e)}",
                "status": "error"
            }

    def save_and_plot_analysis(self, ticker: str, strategy_type: str = 'moving_average') -> None:
        """
        Analyze stock data, save results to JSON, and create a plot
        """
        try:
            # Get analysis results
            results = self.analyze(ticker, strategy_type)
            
            # Save results to JSON
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            json_filename = f"{ticker}_{strategy_type}_{timestamp}.json"
            json_path = os.path.join('data', 'analysis_results', json_filename)
            
            # Ensure directory exists
            os.makedirs(os.path.dirname(json_path), exist_ok=True)
            
            with open(json_path, 'w') as f:
                json.dump(results, f, indent=2)
            print(f"Analysis results saved to {json_path}")

            # Create plot
            if 'signals' in results and results['signals']:
                signals = results['signals']
                
                # Extract data for plotting
                dates = [signal['date'] for signal in signals]
                prices = [signal['price'] for signal in signals]
                
                plt.figure(figsize=(12, 6))
                
                if strategy_type == 'moving_average':
                    short_ma = [signal['short_ma'] for signal in signals]
                    long_ma = [signal['long_ma'] for signal in signals]
                    
                    plt.plot(dates, prices, label='Price', color='blue')
                    plt.plot(dates, short_ma, label='Short MA', color='green')
                    plt.plot(dates, long_ma, label='Long MA', color='red')
                    
                elif strategy_type == 'rsi':
                    rsi = [signal['rsi'] for signal in signals]
                    
                    # Create two subplots
                    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8), height_ratios=[2, 1])
                    
                    # Price plot
                    ax1.plot(dates, prices, label='Price', color='blue')
                    ax1.set_title(f'{ticker} Price')
                    ax1.legend()
                    
                    # RSI plot
                    ax2.plot(dates, rsi, label='RSI', color='purple')
                    ax2.axhline(y=70, color='r', linestyle='--')
                    ax2.axhline(y=30, color='g', linestyle='--')
                    ax2.set_title('RSI')
                    ax2.legend()
                
                plt.title(f'{ticker} {strategy_type.upper()} Strategy Analysis')
                plt.xlabel('Date')
                plt.ylabel('Price')
                plt.xticks(rotation=45)
                plt.legend()
                plt.tight_layout()
                
                # Save plot
                plot_filename = f"{ticker}_{strategy_type}_{timestamp}.png"
                plot_path = os.path.join('data', 'analysis_plots', plot_filename)
                os.makedirs(os.path.dirname(plot_path), exist_ok=True)
                plt.savefig(plot_path)
                print(f"Plot saved to {plot_path}")
                
                # Display plot
                plt.show()
                
        except Exception as e:
            print(f"Error in save_and_plot_analysis: {str(e)}")

if __name__ == "__main__":
    agent = TradeStrategyAgent()
    agent.save_and_plot_analysis("TSLA", "moving_average")
    agent.save_and_plot_analysis("TSLA", "rsi")
    
    

