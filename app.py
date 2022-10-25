from telegram.ext.updater import Updater
from telegram.update import Update
from telegram.ext.callbackcontext import CallbackContext
from telegram.ext.commandhandler import CommandHandler
from telegram.ext.messagehandler import MessageHandler
from telegram.ext.filters import Filters
from telegram_commands import *
import json, config, requests
from flask import Flask, request, jsonify, render_template
from binance.client import Client
from binance.enums import *
from functions import *
import logging

app = Flask(__name__)

# No need to make client object as no function in this file uses it

# Create and configure logger
logging.basicConfig(filename="log_file.log", level=logging.DEBUG, format='%(asctime)s %(message)s', filemode='w')

# Creating an object
logger = logging.getLogger()


# Resolve server time difference error
# Sending telegram message taking too long


# ----- Routes ------->

@app.route('/')
def home():
    # return render_template("home.html", position=get_my_positions)  
    return "Algorithmic Trading Bot created by @dhyeysherasia"


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

    # Intentionally commented cause it can create error and exception block can be executed
    # order_response = {
    #     "code": "failure",
    #     "message": "Could not even initiate order"
    # }

    trade_opened = False
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
            trade_opened = True

        # If positionAmt > 0, close position by making a 'SELL' order of same quantity.
        elif my_positions > 0 and market_position == 'flat' and side == 'SELL':
            quantity = abs(my_positions)
            order_response = close_trade(side='SELL', symbol="BTCUSDT", quantity=quantity)
            trade_opened = True

        # If positionAmt < 0, close position by making a 'BUY' order of same quantity.
        elif my_positions < 0 and market_position == 'flat' and side == 'BUY':
            quantity = abs(my_positions)
            order_response = close_trade(side='BUY', symbol="BTCUSDT", quantity=quantity)
            trade_opened = True

        # Get remaining usdt
        holdings = get_my_holdings(specific=True, symbol='USDT')
        holdings = str(
            f"{float(holdings[0]['withdrawAvailable']):.3f}")  # Can use 'withdrawAvailable' as balacnce will be same after placing order
        remaining_usdt = float(holdings)
        bot_response = send_telegram_message(f"Remaining Balance: {remaining_usdt} USDT")
        return order_response


    except Exception as e:
        bot_response = send_telegram_message(f"Error: {e}")
        if not trade_opened:
            print(f"Exception occurred while evaluating position: {e}")
            logger.error(f"Exception occurred while evaluating position: {e}")
            bot_response = send_telegram_message(
                f"Failed to initiate trade.\nTV position did not match your current position.\nYour Pos: {my_positions}\nTV Pos: {market_position}\nSide: {side}")

            return {
                'code': 'Failure',
                'message': 'Error occurred while evaluating position and initiating trade'
            }

        return {
            'code': 'Success',
            'message': 'Trade executed successfully'
        }


if __name__ == "__main__":
    app.run(debug=True)

    # Initialize telegram commands
    # print("Initializing telegram commands")
    # updater.start_polling()
    # updater.idle()
