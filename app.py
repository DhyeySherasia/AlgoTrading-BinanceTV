import json, config, requests
from flask import Flask, request, jsonify, render_template
from binance.client import Client
from binance.enums import *


app = Flask(__name__)


# Define binance client object
client = Client(config.API_KEY, config.API_SECRET, testnet=False)


# Get how much USDT do I have to buy futures contracts
def get_my_holdings(specific=False, symbol='all'):
    try:
        print("Getting your holdings")
        all_assets = client.futures_account_balance()

        my_holdings = []
        for asset_detail in all_assets:
            if specific:
                if asset_detail['asset'] == symbol:
                    my_holdings.append(asset_detail)
                    break
    
            elif not specific:
                if float(asset_detail['balance']) > 0:
                    my_holdings.append(asset_detail)

    except Exception as e:
        print(f"An exception occured: {e}")
        bot_response = send_telegram_message("Failure\nCould not fetch your holdings")
        return {
            "code": "failure",
            "message": "Could not fetch your holdings"
        }

    return my_holdings


# Get price of BTCUSDT perpetual contract
def get_futures_symbol_price(symbol):
    try:
        print(f"Getting price for {symbol}")
        symbols = client.futures_symbol_ticker()

        for symbol_detail in symbols:
            if symbol_detail['symbol'] == symbol:
                return symbol_detail

    except Exception as e:
        print(f"An exception occured - {e}")
        bot_response = send_telegram_message("Failure\nCould not fetch BTCUSDT price")
        return {
            "code": "failure",
            "message": "Could not fetch symbol price"
        }    


def get_my_positions(symbol='BTCUSDT'):
    try:
        print("Getting your positions")
        account = client.futures_account()['positions']

        for symbols in account:
            if symbols['symbol'] == symbol:
                return float(symbols['positionAmt'])

    except Exception as e:
        print(f"An exception occured: {e}")
        bot_response = send_telegram_message("Failure\nCould not fetch your positions")
        return {
            "code": "failure",
            "message": "Could not fetch your positions"
        }


def send_telegram_message(message):
    try:
        print("Sending message to telegram")

        bot_token = config.BOT_TOKEN  # Sender bot token
        receiver_id = config.RECEIVER_ID  # Receiver chat account id
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage?chat_id={receiver_id}&text={message}&parse_mode=html"
        bot_response = requests.get(url).json()  # Sending GET request

    except Exception as e:
        print(f"An exception occured while sending message to telegram: {e}")
        return {
            "code": "failure",
            "message": "Could not send message to telegram"
        }

    return bot_response


def open_trade(side, symbol, order_type=ORDER_TYPE_MARKET):
    
    try:
        # Get available usdt
        holdings = get_my_holdings(specific=True, symbol='USDT')
        available_usdt = float(holdings[0]['balance'])  # Can use 'withdrawAvailable' as balacnce will be same after placing order
        to_trade_usdt = (80/100) * available_usdt  # 80% of available USDT
        print(f"Holdings: {available_usdt} USDT")
        print(f"Tradable: {to_trade_usdt} USDT")

        # Get BTCUSDT price
        btcusdt = get_futures_symbol_price("BTCUSDT")
        price_btcusdt = float(btcusdt['price'])
        print(f"BTCUSDT Price: {price_btcusdt}")

        # Calculate quantity of BTC with 3 point precision
        quantity = to_trade_usdt / price_btcusdt
        quantity = str(f"{quantity:.3f}")
        quantity = float(quantity)
        print(f"Quantity: {quantity}")

    except Exception as e:
        print(f"An exception occured while calculating quantity: {e}")
        bot_response = send_telegram_message("Failure\nCould not calculate quantity")


    if side == 'BUY':
        direction = 'Long'
    elif side == 'SELL':
        direction = 'Short'
    else:
        direction = 'Unknown'
        bot_response = send_telegram_message(f"Failure detecting side\nUnknown side {side}")
        return {
            "code": "failure",
            "message": "Unknown direction"
        }
    bot_notification = send_telegram_message(message=f"<b><i>|| {direction} Trade ||</i></b>")

    # Placing order
    try:
        print(f"Sending {order_type} order: {side} {quantity} {symbol}")
        order = client.futures_create_order(symbol=symbol, side=side, quantity=quantity, type=order_type, recvWindow=59999)

    except Exception as e:
        bot_response = send_telegram_message(f"Failed to OPEN {direction} trade\n{side.lower()} {quantity} {symbol} at {price_btcusdt}\nCurrent position: {get_my_positions()}")
        print(f"An exception occured while opening {side} trade: {e}")
        print(f"{side} order failed")
        return {
            "code": f"Failed to OPEN {direction} trade",
            "message": f"{quantity} {symbol} {side} order failed"
        }


    # return this if success
    bot_response = send_telegram_message(f"{direction} trade OPENED successfully\n{side.lower()} {quantity} {symbol} at {price_btcusdt}\nCurrent position: {get_my_positions()}")
    print(f"{side} order placed successfully")
    print("Trade OPENED successfully")
    return {
        "code": f"{direction} trade OPENED successfully",
        "message": f"{quantity} {symbol} {side} order placed successfully"
    }


def close_trade(side, symbol, quantity, order_type=ORDER_TYPE_MARKET):

    if side == 'BUY':
        direction = 'Short'
    elif side == 'SELL':
        direction = 'Long'
    else:
        direction = 'Unknown'
        bot_response = send_telegram_message(f"Failure detecting side\nUnknown side {side}")
        return {
            "code": "failure",
            "message": "Unknown direction"
        }
    
    # Get BTCUSDT price
    price_btcusdt = '\'Could not fetch\''
    try:
        btcusdt = get_futures_symbol_price("BTCUSDT")
        price_btcusdt = float(btcusdt['price'])
    except Exception as e:
        print("An exception occured while getting BTCUSDT price while closing trade")
    
    try:
        print(f"Sending {order_type} order: {side} {quantity} {symbol}")
        order = client.futures_create_order(symbol=symbol, side=side, quantity=quantity, reduceOnly=True, type=order_type, recvWindow=59999)
    
    except Exception as e:
        bot_response = send_telegram_message(f"Failed to CLOSE {direction} trade\n{side.lower()} {quantity} {symbol} at {price_btcusdt}\nCurrent position: {get_my_positions()}")
        print(f"An exception occured while closing trade: {e}")
        print(f"{side} order failed")
        return {
            "code": f"Failed to CLOSE {direction} trade",
            "message": f"{quantity} {symbol} {side} order failed"
        }


    # return this if success
    bot_response = send_telegram_message(f"{direction} trade CLOSED successfully\n{side.lower()} {quantity} {symbol} at {price_btcusdt}\nCurrent position: {get_my_positions()}")
    print(f"{side} order placed successfully")
    print("Trade CLOSED successfully")
    return {
        "code": f"{direction} trade CLOSED successfully",
        "message": f"{quantity} {symbol} {side} order placed successfully"
    }



# Resolve server time difference error
# Sending telegram message taking too long



# ----- Routes ------->

@app.route('/')
def home():
    return "AlgoTrading Bot created by @dhyeysherasia"


# Request received from tradingview
@app.route('/webhook', methods=['POST'])
def webhook():

    # Convert to python dictionary
    data = request.data
    data = json.loads(data)

    # Check Passphrase to validate user
    if data['passphrase'] != config.PASSPHRASE:
        bot_response = send_telegram_message("Login attempt: Invalid passphrase")
        return {
            "code": "failure",
            "message": "Incorrect passphrase"
        }


    try:
        my_positions = get_my_positions()
        print(f"Position: {my_positions}")

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

        return order_response


    except Exception as e:
        print(f"Exception occured while evaluating position: {e}")
        bot_response = send_telegram_message(f"Failed to initiate trade.\nTV position did not match your current position.\nYour Pos: {my_positions}\nTV Pos: {market_position}\nSide: {side}")
        return {
            'code': 'Failure',
            'message': 'Error occured while evaluating position and initiating trade'
        }
        


if __name__ == "__main__":
    app.run(debug=True)

    