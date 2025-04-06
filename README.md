# CryptoBot - Cryptocurrency Trading Bot

A complete cryptocurrency trading bot with paper trading capabilities and a modern web interface.

## Features

- **Paper Trading Mode**: Safely practice trading strategies without risking real money
- **Real-time Market Data**: Connect to live market data from Binance
- **Advanced Technical Indicators**: Includes RSI, MACD, Moving Averages, and more
- **Interactive Dashboard**: Monitor your portfolio, trading history, and market data
- **Customizable Strategies**: Configure your trading parameters through a simple JSON file
- **Backtesting**: Test your strategies against historical data to measure performance

## Requirements

- Python 3.8 or higher
- Node.js 14 or higher
- npm 6 or higher

## Directory Structure

```
cryptobot-package/
├── config/                 # Configuration files
├── data/                   # Data storage
├── logs/                   # Log files
├── scripts/                # Utility scripts
├── src/                    # Source code
│   ├── backend/            # Python backend code
│   ├── frontend/           # React frontend code
│   └── shared/             # Shared utilities
├── install.sh              # Installation script
├── README.md               # This file
└── requirements.txt        # Python dependencies
```

## Quick Start

1. Clone or download this repository:
   ```
   git clone <repository-url>
   cd cryptobot-package
   ```

2. Run the installation script:
   ```
   chmod +x install.sh
   ./install.sh
   ```

3. Start the trading bot:
   ```
   ./scripts/start.sh
   ```

4. Open your browser and navigate to:
   ```
   http://localhost:5173
   ```

## Configuration

The main configuration file is located at `config/trading_config.json`. You can edit this file to:

- Set your API keys (required for live data)
- Configure trading strategy parameters
- Select cryptocurrency pairs to trade
- Set trading timeframes
- Adjust indicator settings

## API Keys

To use real market data, you need to obtain API keys from Binance:

1. Create an account on [Binance](https://www.binance.com)
2. Go to API Management in your account settings
3. Create a new API key (read-only permissions are sufficient for paper trading)
4. Add the keys to your configuration file:
   ```json
   {
     "api_key": "YOUR_API_KEY",
     "api_secret": "YOUR_API_SECRET"
   }
   ```

## Development

### Backend Development

The backend is built with Flask and uses the Binance API for market data:

```
cd src/backend
python api.py
```

### Frontend Development

The frontend is built with React, TypeScript, and Vite:

```
cd src/frontend
npm install
npm run dev
```

## Troubleshooting

- Check the log files in the `logs/` directory for errors
- Make sure your API keys are correctly configured
- Verify that ports 5001 and 5173 are not in use by other applications

## License

MIT License

## Acknowledgements

- [Binance API](https://github.com/binance/binance-spot-api-docs)
- [React](https://reactjs.org/)
- [Vite](https://vitejs.dev/)
- [Flask](https://flask.palletsprojects.com/)
