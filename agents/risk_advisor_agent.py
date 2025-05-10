import os
import json
import logging
import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional
from datetime import datetime
import asyncio
from .base_agent import BaseAgent
from .dtmac import MessagePriority, DTMessage

logger = logging.getLogger(__name__)

class RiskAdvisorAgent(BaseAgent):
    """
    Risk Advisor Agent - Assesses investment risks, calculates risk metrics,
    and provides risk management recommendations.
    """

    def __init__(self, dtmac):
        # Define topics this agent is interested in
        topics = [
            "market_data",
            "analysis_results",
            "trading_signals",
            "economic_data"
        ]
        super().__init__("risk_advisor", dtmac, topics)
        
        # Register specific message handlers
        self.dtmac.register_handler(self.agent_id, "new_market_data", self.handle_market_data)
        self.dtmac.register_handler(self.agent_id, "analysis_complete", self.handle_analysis)
        self.dtmac.register_handler(self.agent_id, "economic_update", self.handle_economic_update)
        
        # Initialize agent state
        self.risk_assessments = {}
        self.last_update = None
        
        self.data_archive = 'data_archive'
        self.risk_archive = 'risk_archive'
        os.makedirs(self.data_archive, exist_ok=True)
        os.makedirs(self.risk_archive, exist_ok=True)
    
    async def get_status(self) -> Dict[str, Any]:
        return {
            "status": "active",
            "last_update": self.last_update,
            "active_assessments": len(self.risk_assessments),
            "subscribed_topics": self.get_subscribed_topics()
        }
    
    async def handle_market_data(self, message: DTMessage):
        """Handle new market data"""
        market_data = message.content
        symbol = market_data.get("symbol")
        
        # Calculate risk metrics
        risk_metrics = await self.calculate_risk_metrics(market_data)
        
        # Store risk assessment
        self.risk_assessments[symbol] = risk_metrics
        self.last_update = datetime.now()
        
        # Broadcast risk alert if necessary
        if risk_metrics["risk_score"] > 0.7:  # High risk threshold
            await self.broadcast_to_topic(
                topic="risk_alerts",
                content={
                    "symbol": symbol,
                    "risk_metrics": risk_metrics,
                    "timestamp": self.last_update.isoformat()
                },
                message_type="risk_alert",
                priority=MessagePriority.HIGH
            )
    
    async def handle_analysis(self, message: DTMessage):
        """Handle analysis results"""
        analysis = message.content
        symbol = analysis.get("symbol")
        
        if symbol in self.risk_assessments:
            # Update risk assessment with analysis
            updated_metrics = await self.update_risk_metrics(
                self.risk_assessments[symbol],
                analysis
            )
            
            # Store updated assessment
            self.risk_assessments[symbol] = updated_metrics
            
            # Broadcast risk alert if necessary
            if updated_metrics["risk_score"] > 0.7:
                await self.broadcast_to_topic(
                    topic="risk_alerts",
                    content={
                        "symbol": symbol,
                        "risk_metrics": updated_metrics,
                        "timestamp": datetime.now().isoformat()
                    },
                    message_type="risk_alert",
                    priority=MessagePriority.HIGH
                )
    
    async def handle_economic_update(self, message: DTMessage):
        """Handle economic data updates"""
        economic_data = message.content
        
        # Update all risk assessments based on economic conditions
        for symbol, current_metrics in self.risk_assessments.items():
            updated_metrics = await self.adjust_risk_metrics(
                current_metrics,
                economic_data
            )
            
            # Store updated assessment
            self.risk_assessments[symbol] = updated_metrics
            
            # Broadcast risk alert if necessary
            if updated_metrics["risk_score"] > 0.7:
                await self.broadcast_to_topic(
                    topic="risk_alerts",
                    content={
                        "symbol": symbol,
                        "risk_metrics": updated_metrics,
                        "timestamp": datetime.now().isoformat()
                    },
                    message_type="risk_alert",
                    priority=MessagePriority.HIGH
                )
    
    async def calculate_risk_metrics(self, market_data: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate risk metrics based on market data"""
        metrics = {
            "volatility": self.calculate_volatility(market_data),
            "liquidity": self.assess_liquidity(market_data),
            "market_correlation": self.calculate_market_correlation(market_data),
            "risk_score": self.calculate_risk_score(market_data),
            "risk_factors": self.identify_risk_factors(market_data)
        }
        return metrics
    
    async def update_risk_metrics(self, 
                                current_metrics: Dict[str, Any], 
                                analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Update risk metrics based on new analysis"""
        updated = current_metrics.copy()
        
        # Update volatility based on technical analysis
        updated["volatility"] = self.update_volatility(
            current_metrics["volatility"],
            analysis["technical_indicators"]
        )
        
        # Update risk score
        updated["risk_score"] = self.update_risk_score(
            current_metrics["risk_score"],
            analysis
        )
        
        return updated
    
    async def adjust_risk_metrics(self, 
                                metrics: Dict[str, Any], 
                                economic_data: Dict[str, Any]) -> Dict[str, Any]:
        """Adjust risk metrics based on economic conditions"""
        adjusted = metrics.copy()
        
        # Adjust risk score based on economic indicators
        adjusted["risk_score"] = self.adjust_risk_score(
            metrics["risk_score"],
            economic_data
        )
        
        # Update risk factors
        adjusted["risk_factors"] = self.update_risk_factors(
            metrics["risk_factors"],
            economic_data
        )
        
        return adjusted
    
    def load_historical_data(self, ticker: str) -> Optional[pd.DataFrame]:
        """
        Load the most recent historical data for a ticker from data_archive
        """
        try:
            # Find all historic data files for this ticker
            files = [f for f in os.listdir(self.data_archive) 
                    if f.startswith(f"{ticker}_historic_data_") and f.endswith('.json')]
            
            if not files:
                logger.error(f"No historical data found for {ticker}")
                return None
            
            # Sort files by timestamp (last part of filename before .json)
            files.sort(key=lambda x: x.split('_')[-1].replace('.json', ''), reverse=True)
            latest_file = files[0]
            file_path = os.path.join(self.data_archive, latest_file)
            
            logger.info(f"Loading file: {file_path}")
            
            with open(file_path, 'r') as f:
                data = json.load(f)
            
            if not isinstance(data, list):
                logger.error(f"Invalid data format in {file_path}")
                return None
            
            # Convert to DataFrame
            df = pd.DataFrame(data)
            
            if df.empty:
                logger.error(f"Empty DataFrame created from {file_path}")
                return None
            
            # Create a mapping of current column names to lowercase
            column_mapping = {col: col.lower() for col in df.columns}
            
            # Rename columns to lowercase
            df.rename(columns=column_mapping, inplace=True)
            
            logger.info(f"Loaded DataFrame with columns: {df.columns.tolist()}")
            
            # Convert date column to datetime and set as index
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

    def calculate_volatility(self, market_data: Dict[str, Any]) -> float:
        """Calculate volatility based on historical data"""
        try:
            df = market_data.get("data")
            if df is None or 'close' not in df.columns:
                return 0.0
            
            # Calculate daily returns
            returns = df['close'].pct_change().dropna()
            
            # Calculate annualized volatility
            volatility = returns.std() * np.sqrt(252)  # Annualize daily volatility
            
            return float(volatility)
        except Exception as e:
            logger.error(f"Error calculating volatility: {e}")
            return 0.0
    
    def assess_liquidity(self, market_data: Dict[str, Any]) -> float:
        # Implement liquidity assessment
        pass
    
    def calculate_market_correlation(self, market_data: Dict[str, Any]) -> float:
        # Implement market correlation calculation
        pass
    
    def calculate_risk_score(self, market_data: Dict[str, Any]) -> float:
        # Implement risk score calculation
        pass
    
    def identify_risk_factors(self, market_data: Dict[str, Any]) -> List[str]:
        # Implement risk factor identification
        pass
    
    def update_volatility(self, 
                         current_volatility: float, 
                         technical_indicators: Dict[str, Any]) -> float:
        # Implement volatility update
        pass
    
    def update_risk_score(self, 
                         current_score: float, 
                         analysis: Dict[str, Any]) -> float:
        # Implement risk score update
        pass
    
    def adjust_risk_score(self, 
                         current_score: float, 
                         economic_data: Dict[str, Any]) -> float:
        # Implement risk score adjustment
        pass
    
    def update_risk_factors(self, 
                          current_factors: List[str], 
                          economic_data: Dict[str, Any]) -> List[str]:
        # Implement risk factors update
        pass

    def calculate_value_at_risk(self, ticker: str, confidence_level: float = 0.95, time_horizon: int = 1) -> Dict[str, Any]:
        """
        Calculate Value at Risk (VaR) for a ticker
        
        Args:
            ticker: Stock ticker symbol
            confidence_level: Confidence level for VaR (default: 95%)
            time_horizon: Time horizon in days (default: 1 day)
        """
        df = self.load_historical_data(ticker)
        if df is None or df.empty:
            return {"error": f"No historical data found for {ticker}"}
        
        # Calculate daily returns
        df['daily_return'] = df['close'].pct_change().dropna()
        
        # Calculate VaR using historical method
        var_percentile = 1 - confidence_level
        daily_var = np.percentile(df['daily_return'].dropna(), var_percentile * 100)
        
        # Scale to the time horizon
        var = daily_var * np.sqrt(time_horizon)
        
        # Calculate dollar VaR for a hypothetical $10,000 investment
        investment_amount = 10000
        dollar_var = investment_amount * var
        
        return {
            "ticker": ticker,
            "confidence_level": confidence_level * 100,
            "time_horizon": time_horizon,
            "var_percentage": round(var * 100, 2),  # as percentage
            "dollar_var": round(dollar_var, 2),
            "interpretation": f"With {confidence_level*100}% confidence, the maximum loss over {time_horizon} day(s) will not exceed {abs(round(var*100, 2))}% of the investment.",
            "timestamp": datetime.now().isoformat()
        }
    
    def calculate_max_drawdown(self, ticker: str) -> Dict[str, Any]:
        """
        Calculate maximum drawdown for a ticker
        """
        df = self.load_historical_data(ticker)
        if df is None or df.empty:
            return {"error": f"No historical data found for {ticker}"}
        
        # Calculate running maximum
        df['running_max'] = df['close'].cummax()
        
        # Calculate drawdown
        df['drawdown'] = (df['close'] - df['running_max']) / df['running_max']
        
        # Find maximum drawdown
        max_drawdown = df['drawdown'].min()
        max_drawdown_date = df['drawdown'].idxmin()
        
        # Find current drawdown
        current_drawdown = df['drawdown'].iloc[-1]
        
        drawdown_risk = "low"
        if current_drawdown < -0.2:
            drawdown_risk = "high"
        elif current_drawdown < -0.1:
            drawdown_risk = "medium"
        
        return {
            "ticker": ticker,
            "max_drawdown": round(max_drawdown * 100, 2),  # as percentage
            "max_drawdown_date": max_drawdown_date.strftime('%Y-%m-%d') if not pd.isna(max_drawdown_date) else "N/A",
            "current_drawdown": round(current_drawdown * 100, 2),  # as percentage
            "drawdown_risk": drawdown_risk,
            "timestamp": datetime.now().isoformat()
        }
    
    def calculate_beta(self, ticker: str, market_ticker: str = "SPY") -> Dict[str, Any]:
        """
        Calculate beta (market risk) for a ticker
        """
        # Load ticker data
        df = self.load_historical_data(ticker)
        if df is None or df.empty:
            return {"error": f"No historical data found for {ticker}"}
        
        # Load market data
        market_df = self.load_historical_data(market_ticker)
        if market_df is None or market_df.empty:
            return {"error": f"No historical data found for market index {market_ticker}"}
        
        # Calculate daily returns
        df['daily_return'] = df['close'].pct_change().dropna()
        market_df['daily_return'] = market_df['close'].pct_change().dropna()
        
        # Align dates
        common_dates = df.index.intersection(market_df.index)
        if len(common_dates) < 30:
            return {"error": f"Insufficient overlapping data between {ticker} and {market_ticker}"}
        
        # Calculate beta
        ticker_returns = df.loc[common_dates, 'daily_return']
        market_returns = market_df.loc[common_dates, 'daily_return']
        
        # Beta = covariance(ticker returns, market returns) / variance(market returns)
        covariance = np.cov(ticker_returns, market_returns)[0, 1]
        market_variance = np.var(market_returns)
        beta = covariance / market_variance if market_variance != 0 else 0
        
        # Interpret beta
        beta_interpretation = "neutral (market)"
        if beta > 1.5:
            beta_interpretation = "very aggressive (high volatility)"
        elif beta > 1.1:
            beta_interpretation = "aggressive (above market)"
        elif beta < 0.9:
            beta_interpretation = "defensive (below market)"
        elif beta < 0.5:
            beta_interpretation = "very defensive (low volatility)"
        
        return {
            "ticker": ticker,
            "market_index": market_ticker,
            "beta": round(beta, 2),
            "interpretation": beta_interpretation,
            "timestamp": datetime.now().isoformat()
        }
    
    def analyze_risk(self, ticker: str) -> Dict[str, Any]:
        """
        Comprehensive risk analysis for a ticker
        """
        try:
            logger.info(f"Starting risk analysis for {ticker}")
            
            # Initialize default risk metrics
            risk_score = 0
            risk_factors = []
            
            # Load historical data first
            df = self.load_historical_data(ticker)
            if df is None:
                return {
                    "ticker": ticker,
                    "error": f"No historical data available for {ticker}",
                    "timestamp": datetime.now().isoformat()
                }
            
            # Calculate volatility
            volatility = self.calculate_volatility({"symbol": ticker, "data": df})
            if volatility:
                if volatility > 0.2:  # 20% volatility threshold
                    risk_score += 30
                    risk_factors.append("High volatility")
                elif volatility > 0.1:  # 10% volatility threshold
                    risk_score += 15
                    risk_factors.append("Medium volatility")
            
            # Calculate max drawdown
            max_drawdown = self.calculate_max_drawdown(ticker)
            if not isinstance(max_drawdown, dict) or 'error' in max_drawdown:
                max_drawdown = {
                    'max_drawdown': 0,
                    'current_drawdown': 0,
                    'drawdown_risk': 'unknown'
                }
            
            if max_drawdown.get('drawdown_risk') == 'high':
                risk_score += 30
                risk_factors.append("Significant drawdown")
            elif max_drawdown.get('drawdown_risk') == 'medium':
                risk_score += 15
                risk_factors.append("Moderate drawdown")
            
            # Calculate Value at Risk
            var_metrics = self.calculate_value_at_risk(ticker)
            if not isinstance(var_metrics, dict) or 'error' in var_metrics:
                var_metrics = {
                    'var_percentage': 0,
                    'dollar_var': 0
                }
            
            # Calculate Beta
            beta_metrics = self.calculate_beta(ticker)
            if not isinstance(beta_metrics, dict) or 'error' in beta_metrics:
                beta_metrics = {
                    'beta': 1.0,
                    'interpretation': 'neutral (market)'
                }
            
            if beta_metrics.get('beta', 1.0) > 1.5:
                risk_score += 25
                risk_factors.append("Very aggressive beta")
            elif beta_metrics.get('beta', 1.0) > 1.1:
                risk_score += 15
                risk_factors.append("Above-market beta")
            
            # Calculate overall risk level
            risk_level = "Low"
            if risk_score >= 50:
                risk_level = "High"
            elif risk_score >= 25:
                risk_level = "Medium"
            
            # Generate recommendations
            recommendations = []
            if "High volatility" in risk_factors or "Very aggressive beta" in risk_factors:
                recommendations.append("Consider reducing position size due to high volatility.")
            if "Significant drawdown" in risk_factors:
                recommendations.append("Set strict stop-loss orders to limit potential losses.")
            if beta_metrics.get('beta', 1.0) > 1.3:
                recommendations.append("Hedge with defensive assets to balance portfolio risk.")
            if not recommendations:
                recommendations.append("Current risk levels are manageable. Maintain standard position sizing.")
            
            # Create comprehensive risk report
            risk_report = {
                "ticker": ticker,
                "risk_summary": {
                    "risk_score": risk_score,
                    "risk_level": risk_level,
                    "key_risk_factors": risk_factors,
                    "recommendations": recommendations
                },
                "detailed_metrics": {
                    "volatility": volatility,
                    "maximum_drawdown": max_drawdown,
                    "value_at_risk": var_metrics,
                    "beta": beta_metrics
                },
                "timestamp": datetime.now().isoformat()
            }
            
            # Save risk report
            try:
                timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
                file_path = os.path.join(self.risk_archive, f"{ticker}_risk_analysis_{timestamp}.json")
                with open(file_path, 'w') as f:
                    json.dump(risk_report, f, indent=4)
                logger.info(f"Risk analysis for {ticker} saved to {file_path}")
            except Exception as e:
                logger.error(f"Error saving risk analysis for {ticker}: {e}")
            
            return risk_report
            
        except Exception as e:
            logger.error(f"Error in risk analysis for {ticker}: {e}")
            return {
                "ticker": ticker,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }

# if __name__ == "__main__":
#     agent = RiskAdvisorAgent()
#     risk_report = agent.analyze_risk('TSLA')
#     print(risk_report)