# Financial Analysis and Trading Platform (FinForesight)

A sophisticated financial analysis and trading platform leveraging multiple AI agents for market analysis, trading strategies, and risk management, integrated with **DTMAC** (Distributed Targeted Multi Agent Communication) for seamless multi-agent collaboration.

<p align="center">
  <img src="https://github.com/user-attachments/assets/208f772b-0143-4a53-99fe-56587192b128" alt="FinForesight Logo" width="650"/>
</p>

## 🚀 Features

- **Multi-Agent System**: AI agents performing distinct roles like stock analysis, strategy development, and risk management.
- **DTMAC Integration**: Advanced coordination system that enhances agent interaction and collaboration.
- **Real-time Data Processing**: Live stock data fetching and analysis with immediate feedback.
- **Technical Analysis**: Incorporation of advanced technical indicators and market analysis techniques.
- **Risk Management**: Advanced strategies to assess, minimize, and manage market risk.
- **Trading Strategies**: Development of AI-powered algorithms for trading decision-making.
- **Data Archiving**: Comprehensive storage and management of historical data and analysis.
- **WebSocket Support**: Real-time updates, trading signals, and alerts.
- **AI Chatbot**: **FinBot** – A Groq-powered chatbot that provides real-time market insights and answers.
  - [GitHub: FinBot](https://github.com/0xfarben/FinBot.git)

## 🛠️ Technology Stack

- **Backend**: Python, Flask
- **Data Processing**: Pandas, NumPy
- **Real-time Communication**: Flask-SocketIO
- **Data Storage**: Local file system with structured archiving
- **AI/ML**: Custom AI agents for market analysis and decision-making
- **Coordination System**: DTMAC (Dynamic Task Management and Coordination)

## 🛠️ Technology Stack
- Homepage
![47-6](https://github.com/user-attachments/assets/097a64c0-6b75-4115-a7db-6b5fe6fa6e68)

- Our Agents
![48-8](https://github.com/user-attachments/assets/be5d5647-403d-4f26-8c21-29fbf705b518)

- Anlayzer Block
![48-7](https://github.com/user-attachments/assets/8ab1d058-4ddc-4da1-bb42-1306f483d6fc)

- Display of Top Performace Stocks
![49-9](https://github.com/user-attachments/assets/cdeb075a-8b26-414b-ad44-030958d4075d)

- Agents Execution Flow
![50-11](https://github.com/user-attachments/assets/41cf0525-be4f-4046-bcd0-bcb38f824978)

- Data Analyzer Agent
![50-10](https://github.com/user-attachments/assets/b75560f4-397b-40a1-832b-8f5b8b65e3d5)

- Trade Strategy Developer Agent
![51-13](https://github.com/user-attachments/assets/6b47b465-68dd-4473-98c0-8b0dc6d61f60)

- Trade Advisor Agent
![51-12](https://github.com/user-attachments/assets/e7049071-e704-4f4f-9dac-893101486865)

- Risk Advisor Agent (coming soon..)

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

4. Set up environment variables [.env file (in root) can also be used]:
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
│   ├── stock_data.py             # Stock data fetching and processing
│   ├── stock_overview.py         # Stock overview and analysis
│   ├── technical_indicator.py    # Technical analysis indicators
│   ├── ratios.py                 # Financial ratios calculations
│   ├── financial_statement.py    # Financial statement analysis
│   ├── economics.py             # Economic indicators and analysis
│   ├── news_sentiment.py        # News sentiment analysis
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

## 🧠 DTMAC - Dynamic Task Management and Coordination
The DTMAC system is a coordination framework that helps manage and synchronize tasks between multiple AI agents, enabling them to communicate and collaborate seamlessly. DTMAC enhances the platform by ensuring that each agent can work independently while contributing to a unified strategy.

- Task Assignment: Automatically assigns tasks to agents based on real-time analysis and needs.
- Data Sharing: Facilitates data exchange between agents for more informed decision-making.
- Collaboration: Ensures smooth collaboration between agents with minimal conflicts.

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
