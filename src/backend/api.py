#!/usr/bin/env python3
"""
Paper Trading API Handler
This script provides API endpoints for the frontend to interact with the paper trading system.
"""

import os
import sys
import json
import time
import logging
from datetime import datetime
from flask import Flask, jsonify, request, Blueprint, send_from_directory
from flask_cors import CORS

# Add parent directory to path for imports
parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
sys.path.append(parent_dir)

from src.backend.strategies.paper_trading import PaperTradingStrategy

# Configure logging
log_dir = os.path.join(parent_dir, 'logs')
os.makedirs(log_dir, exist_ok=True)
log_file = os.path.join(log_dir, 'paper_trading_api.log')

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('paper_trading_api')

# Create Blueprint for paper trading API
paper_trading_bp = Blueprint('paper_trading', __name__)

# Initialize the paper trading strategy
config_dir = os.path.join(parent_dir, 'config')
config_file = os.path.join(config_dir, 'trading_config.json')
if not os.path.exists(config_file):
    # Copy default config if not exists
    default_config = os.path.join(config_dir, 'trading_config.default.json')
    if os.path.exists(default_config):
        import shutil
        shutil.copy2(default_config, config_file)
        logger.info(f'Created default configuration file: {config_file}')
    else:
        logger.error(f'Default configuration file not found: {default_config}')

strategy = PaperTradingStrategy(config_file=config_file)

# Initialize strategy instance
trading_thread = None
last_status_update = None

# Path for storing the status JSON
data_dir = os.path.join(parent_dir, 'data')
os.makedirs(data_dir, exist_ok=True)
status_file = os.path.join(data_dir, 'paper_trading_status.json')

def update_status_file():
    """Update the status JSON file for the frontend"""
    global last_status_update
    
    try:
        # Calculate total portfolio value
        total_value = strategy.balance
        holdings_with_value = {}
        
        for symbol, amount in strategy.holdings.items():
            price = strategy.get_current_price(symbol)
            if price:
                value = amount * price
                total_value += value
                holdings_with_value[symbol] = amount
        
        # Prepare trade history entries for the status file
        trade_history = []
        for trade in strategy.trade_history[-strategy.config.get('max_history_items', 100):]:
            trade_history.append({
                'timestamp': trade['timestamp'],
                'symbol': trade['symbol'],
                'side': trade['side'],
                'quantity': trade['quantity'],
                'price': trade['price'],
                'value': trade['value'],
                'balance_after': trade['balance_after'],
                'type': trade.get('type', 'market')
            })
        
        # Create the status object
        status = {
            'is_running': strategy.is_running,
            'mode': strategy.config.get('mode', 'paper'),
            'balance': strategy.balance,
            'holdings': holdings_with_value,
            'base_currency': strategy.config.get('base_currency', 'USDT'),
            'portfolio_value': total_value,
            'performance': {
                'total_trades': len(strategy.trade_history),
                'win_rate': strategy.calculate_win_rate(),
                'profit_loss': strategy.calculate_profit_loss(),
                'return_pct': (strategy.calculate_profit_loss() / strategy.initial_balance) * 100 if strategy.initial_balance > 0 else 0,
                'sharpe_ratio': strategy.calculate_sharpe_ratio(),
                'max_drawdown': strategy.calculate_max_drawdown()
            },
            'trade_history': trade_history,
            'last_prices': strategy.last_prices,
            'last_updated': datetime.now().isoformat(),
            'api_keys_configured': bool(strategy.config.get('api_key')) and bool(strategy.config.get('api_secret'))
        }
        
        # Write to the status file
        with open(status_file, 'w') as f:
            json.dump(status, f, indent=2)
            
        last_status_update = time.time()
        logger.debug(f'Updated status file: {status_file}')
        
    except Exception as e:
        logger.error(f'Error updating status file: {e}')

@paper_trading_bp.route('/paper', methods=['GET'])
def get_status():
    """Get the current paper trading status"""
    try:
        # Update the status file if it doesn't exist or is older than 5 seconds
        if not os.path.exists(status_file) or last_status_update is None or time.time() - last_status_update > 5:
            update_status_file()
        
        # Return a simplified status for faster response
        return jsonify({
            'status': 'success',
            'data': {
                'is_running': strategy.is_running,
                'mode': strategy.config.get('mode', 'paper'),
                'balance': strategy.balance,
                'portfolio_value': strategy.calculate_portfolio_value(),
                'last_updated': datetime.now().isoformat()
            }
        })
    except Exception as e:
        logger.error(f'Error getting status: {e}')
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@paper_trading_bp.route('/paper', methods=['POST'])
def handle_command():
    """Handle paper trading commands from the frontend"""
    global trading_thread
    
    try:
        data = request.json
        if not data:
            return jsonify({
                'status': 'error',
                'message': 'No JSON data provided'
            }), 400
        
        command = data.get('command')
        if not command:
            return jsonify({
                'status': 'error',
                'message': 'No command specified'
            }), 400
        
        logger.info(f'Received command: {command}')
        
        if command == 'start':
            if strategy.is_running:
                return jsonify({
                    'status': 'success',
                    'message': 'Trading already running'
                })
            
            # Check for API keys
            if not strategy.api_keys_configured():
                # Try to recover keys if possible
                if not attempt_to_recover_api_keys():
                    return jsonify({
                        'status': 'error',
                        'message': 'API keys not configured'
                    }), 400
            
            # Start the trading thread
            if trading_thread is None or not trading_thread.is_alive():
                strategy.start()
                update_status_file()
                return jsonify({
                    'status': 'success',
                    'message': 'Trading started'
                })
            else:
                return jsonify({
                    'status': 'error',
                    'message': 'Trading thread already running'
                }), 400
                
        elif command == 'stop':
            if not strategy.is_running:
                return jsonify({
                    'status': 'success',
                    'message': 'Trading already stopped'
                })
            
            strategy.stop()
            update_status_file()
            return jsonify({
                'status': 'success',
                'message': 'Trading stopped'
            })
            
        elif command == 'reset':
            strategy.stop()
            strategy.reset_account()
            update_status_file()
            return jsonify({
                'status': 'success',
                'message': 'Account reset'
            })
            
        elif command == 'buy':
            symbol = data.get('symbol', 'BTCUSDT')
            quantity = float(data.get('quantity', 0.001))
            
            if not strategy.is_running:
                return jsonify({
                    'status': 'error',
                    'message': 'Trading is not running'
                }), 400
            
            success, message = strategy.place_buy_order(symbol, quantity)
            update_status_file()
            
            if success:
                return jsonify({
                    'status': 'success',
                    'message': message
                })
            else:
                return jsonify({
                    'status': 'error',
                    'message': message
                }), 400
                
        elif command == 'sell':
            symbol = data.get('symbol', 'BTCUSDT')
            quantity = float(data.get('quantity', 0.001))
            
            if not strategy.is_running:
                return jsonify({
                    'status': 'error',
                    'message': 'Trading is not running'
                }), 400
                
            success, message = strategy.place_sell_order(symbol, quantity)
            update_status_file()
            
            if success:
                return jsonify({
                    'status': 'success',
                    'message': message
                })
            else:
                return jsonify({
                    'status': 'error',
                    'message': message
                }), 400
                
        elif command == 'api':
            # Update API keys
            api_key = data.get('key', '')
            api_secret = data.get('secret', '')
            
            if not api_key or not api_secret:
                return jsonify({
                    'status': 'error',
                    'message': 'API key and secret are required'
                }), 400
            
            # Update the config
            strategy.update_api_keys(api_key, api_secret)
            update_status_file()
            
            return jsonify({
                'status': 'success',
                'message': 'API keys updated'
            })
            
        else:
            return jsonify({
                'status': 'error',
                'message': f'Unknown command: {command}'
            }), 400
            
    except Exception as e:
        logger.error(f'Error handling command: {e}')
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

def attempt_to_recover_api_keys():
    """Attempt to recover API keys from backup locations if they're missing."""
    try:
        # Check for API keys in environment variables
        api_key = os.environ.get('BINANCE_API_KEY')
        api_secret = os.environ.get('BINANCE_API_SECRET')
        
        if api_key and api_secret:
            strategy.update_api_keys(api_key, api_secret)
            logger.info('Recovered API keys from environment variables')
            return True
            
        # Check for backup file
        backup_file = os.path.join(config_dir, 'api_keys_backup.json')
        if os.path.exists(backup_file):
            try:
                with open(backup_file, 'r') as f:
                    backup_data = json.load(f)
                    if 'api_key' in backup_data and 'api_secret' in backup_data:
                        api_key = backup_data['api_key']
                        api_secret = backup_data['api_secret']
                        if api_key and api_secret:
                            strategy.update_api_keys(api_key, api_secret)
                            logger.info('Recovered API keys from backup file')
                            return True
            except Exception as e:
                logger.error(f'Error reading backup file: {e}')
                
        logger.warning('Could not recover API keys')
        return False
        
    except Exception as e:
        logger.error(f'Error attempting to recover API keys: {e}')
        return False

@paper_trading_bp.route('/api-status', methods=['GET'])
def get_api_status():
    """Get the API keys configuration status"""
    try:
        api_key = strategy.config.get('api_key', '')
        api_secret = strategy.config.get('api_secret', '')
        
        # Test the API connection if keys are configured
        api_working = False
        if api_key and api_secret:
            try:
                # Quick test of API connection
                strategy.test_api_connection()
                api_working = True
            except Exception as e:
                logger.error(f'API connection test failed: {e}')
        
        return jsonify({
            'status': 'success',
            'data': {
                'keys_configured': bool(api_key) and bool(api_secret),
                'api_working': api_working
            }
        })
    except Exception as e:
        logger.error(f'Error getting API status: {e}')
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

# Serve static files from the data directory
@paper_trading_bp.route('/paper_trading_status.json', methods=['GET'])
def serve_status_file():
    """Serve the status JSON file"""
    update_status_file()  # Update before serving
    return send_from_directory(data_dir, 'paper_trading_status.json')

def init_app(app):
    """Initialize the Flask app with the paper trading blueprint"""
    # Register the blueprint with the /trading prefix
    app.register_blueprint(paper_trading_bp, url_prefix='/trading')
    
    # Allow CORS for all domains on all routes for development
    CORS(app)
    
    # Add route to serve trading data files
    @app.route('/trading_data/<path:filename>', methods=['GET'])
    def serve_data_file(filename):
        return send_from_directory(data_dir, filename)


if __name__ == "__main__":
    # This can be run as a standalone service for testing
    app = Flask(__name__)
    init_app(app)
    logger.info('Starting Paper Trading API server on port 5001')
    app.run(host='0.0.0.0', port=5001, debug=True)
