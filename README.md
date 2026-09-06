# 🤖 StockAgent — AI-Based Stock Market Simulation

An educational AI-powered stock market simulation where multiple autonomous agents make simulated trading decisions based on their personalities, market conditions, financial information, and AI-generated reasoning.

> ⚠️ This project is for educational and simulation purposes only. It does not execute real trades, connect to a brokerage account, or provide financial advice.

## 🚀 Features

- 🤖 Multiple autonomous AI trading agents
- 🧠 AI-powered decision making using Google Gemini
- 📊 Simulated stock market with multiple stocks
- 💰 Buying and selling simulation
- 🏦 Loan and repayment mechanism
- 👥 Different agent personalities
- 🔄 Multi-day market simulation
- 📝 Trading and agent activity records
- 📈 CSV and JSON result generation
- 💻 Offline demo mode for testing without an API key

## 🏗️ Project Structure

```text
Stockagent/
│
├── agent.py              # Autonomous trading agent
├── main.py               # Main simulation controller
├── secretary.py          # AI model/API interface
├── stock.py              # Stock and market logic
├── record.py             # Simulation result recording
├── util.py               # Configuration and utilities
├── prompt/
│   └── agent_prompt.py   # AI agent prompts
├── requirements.txt      # Python dependencies
├── .env.example          # Environment variable template
├── .gitignore            # Git ignore rules
└── README.md             # Project documentation
