import os
import json
import time
import logging
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from binance.client import Client
from binance.exceptions import BinanceAPIException
from binance.enums import *
import threading

# Configure logging
log_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../logs'))
os.makedirs(log_dir, exist_ok=True)
log_file = os.path.join(log_dir, 'paper_trading.log')

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("paper_trading")

class PaperTradingStrategy:
    """
    Paper trading strategy for Binance that can be easily switched to live trading.
    This class simulates trading with virtual funds while using real market data.
    """
    def __init__(self, config_file='trading_config.json'):
        """
        Initialize the paper trading strategy with configuration.
        
        Args:
            config_file (str): Path to the JSON configuration file
        """
        self.config_file = config_file
        self.load_config()
        
        # Initialize account state
        self.reset_account()
        
        # Initialize runtime variables
        self.is_running = False
        self.thread = None
        self.orders = []
        
        # Keep API key state at startup
        self._last_api_key = self.config.get('api_key', '')
        self._last_api_secret = self.config.get('api_secret', '')
        self.trade_history = []
        
        # Initialize prices dictionary
        self.last_prices = {}
        
        # Create client if API keys are configured
        self.client = None
        if self.config.get('api_key') and self.config.get('api_secret'):
            self.create_client()
        
    def load_config(self):
        """Load the configuration from the JSON file"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    self.config = json.load(f)
                logger.info(f'Loaded configuration from {self.config_file}')
            else:
                logger.warning(f'Config file not found: {self.config_file}')
                self.config = self.get_default_config()
                
                # Create the config file with default values
                os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
                with open(self.config_file, 'w') as f:
                    json.dump(self.config, f, indent=2)
                logger.info(f'Created default config file: {self.config_file}')
        except Exception as e:
            logger.error(f'Error loading config: {e}')
            self.config = self.get_default_config()
        
    def get_default_config(self):
        """Return default configuration values"""
        return {
            'mode': 'paper',
            'balance': 10000,
            'base_currency': 'USDT',
            'api_key': '',
            'api_secret': '',
            'symbols': ['BTCUSDT', 'ETHUSDT', 'ADAUSDT', 'SOLUSDT', 'DOTUSDT', 'XRPUSDT'],
            'strategy_settings': {
                'buy_threshold': 1.5,
                'sell_threshold': -1.0,
                'stop_loss': -2.5,
                'take_profit': 3.0,
                'max_positions': 5,
                'position_size': 0.1,
                'trailing_stop': True,
                'trailing_stop_pct': 1.0
            },
            'timeframes': ['1m', '5m', '15m', '1h', '4h', '1d'],
            'indicators': {
                'ma_fast': 8,
                'ma_slow': 21,
                'rsi_period': 14,
                'rsi_overbought': 70,
                'rsi_oversold': 30,
                'macd_fast': 12,
                'macd_slow': 26,
                'macd_signal': 9
            },
            'update_interval': '1m',
            'log_level': 'INFO',
            'enable_thoughts': True,
            'max_history_items': 100
        }
    
    def save_config(self):
        """Save the current configuration to the JSON file"""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.config, f, indent=2)
            logger.info(f'Saved configuration to {self.config_file}')
        except Exception as e:
            logger.error(f'Error saving config: {e}')
    
    def reset_account(self):
        """Reset the paper trading account to initial state"""
        self.balance = self.config.get('balance', 10000)
        self.initial_balance = self.balance
        self.holdings = {}
        self.trades = []
        self.trade_history = []
        self.orders = []
        self.open_orders = []
        self.last_prices = {}
        self.performance_data = {
            'balance_history': [(datetime.now().isoformat(), self.balance)],
            'trades': []
        }
        logger.info(f'Reset account with balance {self.balance} {self.config.get("base_currency", "USDT")}')
    
    def create_client(self):
        """Create the Binance API client if keys are configured"""
        api_key = self.config.get('api_key', '')
        api_secret = self.config.get('api_secret', '')
        
        if api_key and api_secret:
            try:
                self.client = Client(api_key, api_secret)
                # Test connection
                self.client.ping()
                logger.info('Connected to Binance API')
            except Exception as e:
                logger.error(f'Failed to create Binance client: {e}')
                self.client = None
        else:
            logger.warning('API keys not configured')
            self.client = None
    
    def test_api_connection(self):
        """Test the Binance API connection"""
        if not self.client:
            self.create_client()
        
        if self.client:
            try:
                self.client.ping()
                server_time = self.client.get_server_time()
                logger.info(f'API connection successful. Server time: {server_time}')
                return True
            except Exception as e:
                logger.error(f'API connection test failed: {e}')
                return False
        else:
            logger.warning('No API client available to test connection')
            return False
    
    def api_keys_configured(self):
        """Check if API keys are configured"""
        return (self.config.get('api_key') and self.config.get('api_secret'))
    
    def update_api_keys(self, api_key, api_secret):
        """Update the API keys in the configuration"""
        self.config['api_key'] = api_key
        self.config['api_secret'] = api_secret
        
        # Save API keys to backup file for recovery if needed
        backup_dir = os.path.dirname(self.config_file)
        backup_file = os.path.join(backup_dir, 'api_keys_backup.json')
        
        try:
            with open(backup_file, 'w') as f:
                json.dump({
                    'api_key': api_key,
                    'api_secret': api_secret
                }, f, indent=2)
        except Exception as e:
            logger.error(f'Failed to save API keys backup: {e}')
        
        # Re-create the client with new keys
        self.create_client()
        
        # Save the updated config
        self.save_config()
        logger.info('Updated API keys')
    
    def get_current_price(self, symbol):
        """
        Get the current price for a symbol.
        Tries to use the Binance API if available, otherwise uses cached values.
        """
        try:
            # If we have a client, try to get a real-time price
            if self.client:
                ticker = self.client.get_symbol_ticker(symbol=symbol)
                price = float(ticker['price'])
                self.last_prices[symbol] = price
                return price
            
            # If no client or API call fails, use the last known price
            if symbol in self.last_prices:
                return self.last_prices[symbol]
            
            # If we don't have a price, simulate one (for development without API)
            # This is just a placeholder, real implementations should use actual market data
            if symbol == 'BTCUSDT':
                return 46700 + (np.random.random() * 100 - 50)
            elif symbol == 'ETHUSDT':
                return 3220 + (np.random.random() * 20 - 10)
            elif symbol == 'ADAUSDT':
                return 0.35 + (np.random.random() * 0.01 - 0.005)
            elif symbol == 'SOLUSDT':
                return 142 + (np.random.random() * 3 - 1.5)
            elif symbol == 'DOTUSDT':
                return 7.5 + (np.random.random() * 0.2 - 0.1)
            elif symbol == 'XRPUSDT':
                return 0.53 + (np.random.random() * 0.01 - 0.005)
            else:
                return 100  # Default price for unknown symbols
            
        except Exception as e:
            logger.error(f'Error getting price for {symbol}: {e}')
            
            # Return last known price if available
            if symbol in self.last_prices:
                return self.last_prices[symbol]
            
            return None
