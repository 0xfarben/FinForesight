# Financial Analysis and Trading Platform

A sophisticated financial analysis and trading platform that combines multiple AI agents for comprehensive market analysis, trading strategies, and risk management.

## 🚀 Features

- **Multi-Agent System**: Coordinated AI agents for different aspects of financial analysis
- **Real-time Data Processing**: Live stock data analysis and processing
- **Technical Analysis**: Advanced technical indicators and market analysis
- **Risk Management**: Comprehensive risk assessment and management
- **Trading Strategies**: AI-powered trading strategy development
- **Data Archiving**: Systematic storage of historical data and analysis
- **WebSocket Support**: Real-time updates and notifications
- **AI Chatbot**: Groq-powered chatbot for real-time market queries and analysis [FinBot](chat.finforesight.dev)

## 🛠️ Technology Stack

- **Backend**: Python/Flask
- **Data Processing**: Pandas, NumPy
- **Real-time Communication**: Flask-SocketIO
- **Data Storage**: Local file system with structured archiving
- **AI/ML**: Custom AI agents for different analysis aspects

## 📋 Prerequisites

- Python 3.8+
- pip (Python package manager)
- Git

## 🔧 Installation

1. Clone the repository:
```bash
git clone https://github.com/0xfarben/FinForesight.git
cd FinForesight
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r setup.txt
```

4. Set up environment variables:
```bash
export SESSION_SECRET="your-secret-key"  # On Windows: set SESSION_SECRET=your-secret-key
export ALPHA_VANTAGE_API_KEY="your-api-key"  # On Windows: set ALPHA_VANTAGE_API_KEY=your-api-key
```

## 🏗️ Project Structure

```
├── agents/                 # AI agent implementations
|   ├── base_agent.py  
│   ├── dtmac.py           # DTMAC coordination system
|   ├── orchestrator.py  
│   ├── data_analyst_agent.py
│   ├── trade_strategy_agent.py
│   ├── trade_advisor_agent.py
│   └── risk_advisor_agent.py
├── services/              # Core services
│   ├── historic_data.py           # Historical data management
│   ├── historic_data_original.py  # Original historical data implementation
│   ├── stock_data.py             # Stock data fetching and processing
│   ├── stock_overview.py         # Stock overview and analysis
│   ├── technical_indicator.py    # Technical analysis indicators
│   ├── ratios.py                 # Financial ratios calculations
│   ├── financial_statement.py    # Financial statement analysis
│   ├── economics.py             # Economic indicators and analysis
│   ├── news_sentiment.py        # News sentiment analysis
│   ├── news_sentiment_backup.py # Backup of news sentiment analysis
│   └── earning_call_transcript.py # Earnings call analysis
├── templates/            # HTML templates
├── static/              # Static assets
├── data_archive/        # Historical data storage
├── strategies_archive/  # Trading strategies storage
├── predictions_archive/ # Market predictions storage
├── risk_archive/        # Risk analysis storage
├── app.py              # Main application file
└── setup.txt    # Python dependencies
```

## 🚀 Usage

1. Start the application:
```bash
python app.py
```

2. Access the web interface at `http://localhost:5000`

3. Key endpoints:
   - `/`: Main dashboard
   - `/analyze`: Stock analysis interface
   - `/technical_indicators`: Technical analysis tools
   - `/api/top_stocks`: Top performing stocks API

## 🤖 AI Agents

### Data Analyst Agent
- Performs comprehensive stock data analysis
- Generates market insights
- Processes historical data

### Trade Strategy Agent
- Develops trading strategies
- Analyzes market patterns
- Generates trading signals

### Trade Advisor Agent
- Provides trading recommendations
- Evaluates trading opportunities
- Suggests entry/exit points

### Risk Advisor Agent
- Assesses market risks
- Provides risk management strategies
- Monitors portfolio risk levels

## 📊 Data Management

The platform maintains several archive directories:
- `data_archive/`: Historical stock data
- `strategies_archive/`: Trading strategies
- `predictions_archive/`: Market predictions
- `risk_archive/`: Risk analysis reports

## 🔒 Security

- Session-based authentication
- Environment variable configuration
- Secure data handling practices

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 📞 Support

For support, please open an issue in the repository or contact the development team. 
