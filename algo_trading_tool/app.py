from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO, emit
import logging
from datetime import datetime
import threading
import json
import os

from config.config import config
from src.data_sources.data_manager import DataManager
from src.strategies.strategy_manager import StrategyManager
from src.brokers.broker_manager import BrokerManager
from src.backtesting.backtest_engine import BacktestEngine
from src.risk_management.risk_manager import RiskManager
from src.utils.logger import setup_logger

# Initialize Flask app
app = Flask(__name__)
app.config.from_object(config['development'])

# Initialize SocketIO for real-time updates
socketio = SocketIO(app, cors_allowed_origins="*")

# Setup logging
logger = setup_logger()

# Initialize core components
data_manager = DataManager()
strategy_manager = StrategyManager()
broker_manager = BrokerManager()
backtest_engine = BacktestEngine()
risk_manager = RiskManager()

# Global variables for trading state
trading_active = False
current_positions = {}
trading_thread = None

@app.route('/')
def index():
    """Main dashboard page"""
    return render_template('dashboard.html')

@app.route('/api/start_trading', methods=['POST'])
def start_trading():
    """Start automated trading"""
    global trading_active, trading_thread
    
    try:
        config_data = request.json
        trading_active = True
        
        # Start trading in a separate thread
        trading_thread = threading.Thread(
            target=run_trading_loop,
            args=(config_data,)
        )
        trading_thread.start()
        
        logger.info("Trading started successfully")
        return jsonify({
            'status': 'success',
            'message': 'Trading started successfully'
        })
    
    except Exception as e:
        logger.error(f"Error starting trading: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f'Error starting trading: {str(e)}'
        }), 500

@app.route('/api/stop_trading', methods=['POST'])
def stop_trading():
    """Stop automated trading"""
    global trading_active
    
    try:
        trading_active = False
        logger.info("Trading stopped")
        
        return jsonify({
            'status': 'success',
            'message': 'Trading stopped successfully'
        })
    
    except Exception as e:
        logger.error(f"Error stopping trading: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f'Error stopping trading: {str(e)}'
        }), 500

@app.route('/api/backtest', methods=['POST'])
def run_backtest():
    """Run backtesting on historical data"""
    try:
        backtest_config = request.json
        
        # Validate required fields
        required_fields = ['start_date', 'end_date', 'strategy', 'symbol']
        for field in required_fields:
            if field not in backtest_config:
                return jsonify({
                    'status': 'error',
                    'message': f'Missing required field: {field}'
                }), 400
        
        # Run backtest
        results = backtest_engine.run_backtest(backtest_config)
        
        return jsonify({
            'status': 'success',
            'results': results
        })
    
    except Exception as e:
        logger.error(f"Error running backtest: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f'Error running backtest: {str(e)}'
        }), 500

@app.route('/api/positions')
def get_positions():
    """Get current positions"""
    try:
        positions = broker_manager.get_positions()
        return jsonify({
            'status': 'success',
            'positions': positions
        })
    
    except Exception as e:
        logger.error(f"Error getting positions: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f'Error getting positions: {str(e)}'
        }), 500

@app.route('/api/market_data/<symbol>')
def get_market_data(symbol):
    """Get current market data for a symbol"""
    try:
        data = data_manager.get_real_time_data(symbol)
        return jsonify({
            'status': 'success',
            'data': data
        })
    
    except Exception as e:
        logger.error(f"Error getting market data: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f'Error getting market data: {str(e)}'
        }), 500

@socketio.on('connect')
def handle_connect():
    """Handle client connection"""
    emit('connected', {'message': 'Connected to trading server'})
    logger.info("Client connected")

@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection"""
    logger.info("Client disconnected")

def run_trading_loop(config_data):
    """Main trading loop that runs in a separate thread"""
    global trading_active, current_positions
    
    logger.info("Starting trading loop")
    
    while trading_active:
        try:
            # Get market data
            symbols = config_data.get('symbols', ['NIFTY', 'BANKNIFTY'])
            
            for symbol in symbols:
                if not trading_active:
                    break
                
                # Get current market data
                market_data = data_manager.get_real_time_data(symbol)
                
                if market_data:
                    # Run strategy analysis
                    signals = strategy_manager.analyze_symbol(symbol, market_data)
                    
                    # Process signals
                    for signal in signals:
                        if not trading_active:
                            break
                        
                        # Check risk management
                        if risk_manager.can_take_position(signal):
                            # Execute trade
                            result = broker_manager.place_order(signal)
                            
                            if result['status'] == 'success':
                                # Update positions
                                current_positions[signal['symbol']] = signal
                                
                                # Emit update to clients
                                socketio.emit('trade_executed', {
                                    'signal': signal,
                                    'result': result,
                                    'timestamp': datetime.now().isoformat()
                                })
                                
                                logger.info(f"Trade executed: {signal}")
                
                # Check existing positions for exit signals
                positions_to_check = list(current_positions.keys())
                for position_symbol in positions_to_check:
                    if not trading_active:
                        break
                    
                    position = current_positions[position_symbol]
                    exit_signal = strategy_manager.check_exit_conditions(
                        position_symbol, position
                    )
                    
                    if exit_signal:
                        # Execute exit
                        result = broker_manager.place_order(exit_signal)
                        
                        if result['status'] == 'success':
                            # Remove from positions
                            del current_positions[position_symbol]
                            
                            # Emit update to clients
                            socketio.emit('position_closed', {
                                'signal': exit_signal,
                                'result': result,
                                'timestamp': datetime.now().isoformat()
                            })
                            
                            logger.info(f"Position closed: {exit_signal}")
            
            # Sleep for a short interval before next iteration
            import time
            time.sleep(1)  # 1 second interval
            
        except Exception as e:
            logger.error(f"Error in trading loop: {str(e)}")
            # Emit error to clients
            socketio.emit('trading_error', {
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            })
    
    logger.info("Trading loop stopped")

if __name__ == '__main__':
    # Create logs directory if it doesn't exist
    os.makedirs('logs', exist_ok=True)
    
    # Run the application
    socketio.run(app, debug=app.config['DEBUG'], host='0.0.0.0', port=5000)