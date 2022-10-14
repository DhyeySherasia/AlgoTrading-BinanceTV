import json, config, requests
from flask import Flask, request, jsonify, render_template
from binance.client import Client
from binance.enums import *
from functions import *
import logging


app = Flask(__name__)

# No need to make client object as no function in this file uses it

# Create and configure logger
logging.basicConfig(filename="log_file.log", level=logging.DEBUG, format='%(asctime)s %(levelname)s %(message)s', filemode='w')

# Creating an object
logger = logging.getLogger()


# Resolve server time difference error
# Sending telegram message taking too long


# ----- Routes ------->

@app.route('/')
def home():
    return "AgloTrading Bot created by @dhyeysherasia. Logging to log_file.log""     


# Request received from tradingview
@app.route('/webhook', methods=['POST'])
def webhook():

    # Convert to python dictionary
    data = request.data
    data = json.loads(data)

    # Check Passphrase to validate user
    if data['passphrase'] != config.PASSPHRASE:
        bot_response = send_telegram_message("Login attempt: Invalid passphrase")
        logger.warning("Login attempt: Invalid passphrase")
        return {
            "code": "failure",
            "message": "Incorrect passphrase"
        }

    order_response = {
        "code": "failure",
        "message": "Could not even initiate order"
    }

    try:
        my_positions = get_my_positions()
        print(f"Position: {my_positions}")
        logger.info(f"Position: {my_positions}")

        # Get 'market_position' from post request
        # 'flat' --> Closing trade
        # 'long/short' --> Opening trade
        market_position = data['strategy']['market_position'].lower()

        # Buy/Sell 
        side = data['strategy']['order_action'].upper()  # Binance requires upper case

        # Open position if positionAmt == 0.
        if my_positions == 0 and market_position != 'flat':
            order_response = open_trade(side=side, symbol="BTCUSDT")  # Quantity is cal. inside the function

        # If positionAmt > 0, close position by making a 'SELL' order of same quantity.
        elif my_positions > 0 and market_position == 'flat' and side == 'SELL':
            quantity = abs(my_positions)
            order_response = close_trade(side='SELL', symbol="BTCUSDT", quantity=quantity)
            
        # If positionAmt < 0, close position by making a 'BUY' order of same quantity.
        elif my_positions < 0 and market_position == 'flat' and side == 'BUY':
            quantity = abs(my_positions)
            order_response = close_trade(side='BUY', symbol="BTCUSDT", quantity=quantity)
        
        
        # Get remaining usdt
        holdings = get_my_holdings(specific=True, symbol='USDT')
        remaining_usdt = float(holdings[0]['withdrawAvailable'])  # Can use 'withdrawAvailable' as balacnce will be same after placing order
        bot_response = send_telegram_message(f"Remaining Balance: {remaining_usdt}")
        return order_response


    except Exception as e:
        print(f"Exception occured while evaluating position: {e}")
        logger.error(f"Exception occured while evaluating position: {e}")
        bot_response = send_telegram_message(f"Failed to initiate trade.\nTV position did not match your current position.\nYour Pos: {my_positions}\nTV Pos: {market_position}\nSide: {side}")
        bot_response = send_telegram_message(f"Error: {e}")
        return {
            'code': 'Failure',
            'message': 'Error occured while evaluating position and initiating trade'
        }
        


if __name__ == "__main__":
    app.run(debug=True)

    
