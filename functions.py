import json, config, requests
from flask import Flask, request, jsonify, render_template
from binance.client import Client
from binance.enums import *
import logging


# Define binance client object
client = Client(config.API_KEY, config.API_SECRET, testnet=True)

# Create and configure logger
logging.basicConfig(filename="log_file.log", level=logging.DEBUG, format='%(asctime)s %(message)s', filemode='w')
logger = logging.getLogger()


# Get how much USDT do I have to buy futures contracts
def get_my_holdings(specific=False, symbol='all'):
    try:
        print("Getting your holdings")
        logger.info("Getting your holdings")
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
        print(f"An exception occurred: {e}")
        logger.error(f"Could not fetch your holdings: {e}")
        bot_response = send_telegram_message("Failure\nCould not fetch your holdings")
        bot_response = send_telegram_message(f"Error: {e}")
        return {
            "code": "failure",
            "message": "Could not fetch your holdings"
        }

    return my_holdings


# Get price of BTCUSDT perpetual contract
def get_futures_symbol_price(symbol):
    try:
        print(f"Getting price for {symbol}")
        logger.info(f"Getting price for {symbol}")
        symbols = client.futures_symbol_ticker()

        for symbol_detail in symbols:
            if symbol_detail['symbol'] == symbol:
                return symbol_detail

    except Exception as e:
        print(f"An exception occurred - {e}")
        logger.error(f"Could not fetch BTCUSDT price: {e}")
        bot_response = send_telegram_message("Failure\nCould not fetch BTCUSDT price")
        bot_response = send_telegram_message(f"Error: {e}")
        return {
            "code": "failure",
            "message": "Could not fetch symbol price"
        }


def get_my_positions(symbol='BTCUSDT'):
    try:
        print("Getting your positions")
        logger.info("Getting your positions")
        account = client.futures_account()['positions']

        for symbols in account:
            if symbols['symbol'] == symbol:
                return float(symbols['positionAmt'])

    except Exception as e:
        print(f"An exception occurred: {e}")
        logger.error(f"Could not fetch your positions: {e}")
        bot_response = send_telegram_message("Failure\nCould not fetch your positions")
        bot_response = send_telegram_message(f"Error: {e}")
        return {
            "code": "failure",
            "message": "Could not fetch your positions"
        }


def send_telegram_message(message):
    try:
        print("Sending message to telegram")
        logging.info("Sending message to telegram")

        bot_token = config.BOT_TOKEN  # Sender bot token
        receiver_id = config.RECEIVER_ID  # Receiver chat account id
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage?chat_id={receiver_id}&text={message}&parse_mode=html"
        bot_response = requests.get(url).json()  # Sending GET request

    except Exception as e:
        print(f"An exception occurred while sending message to telegram: {e}")
        logger.error(f"Could not send message to telegram: {e}")
        return {
            "code": "failure",
            "message": "Could not send message to telegram"
        }

    return bot_response


def open_trade(side, symbol, order_type=ORDER_TYPE_MARKET):
    try:
        # Get available usdt
        holdings = get_my_holdings(specific=True, symbol='USDT')
        available_usdt = float(holdings[0]['withdrawAvailable'])  # Can use 'withdrawAvailable' as balacnce will be same after placing order
        # 'Margin insufficient' error with 100%. Hence used 95%.
        to_trade_usdt = (95/100) * available_usdt  # 95% of available USDT
        print(f"Holdings: {available_usdt} USDT")
        print(f"Tradable: {to_trade_usdt} USDT")
        logger.info(f"Holdings: {available_usdt} USDT")
        logger.info(f"Tradable: {to_trade_usdt} USDT")

        # Get BTCUSDT price
        btcusdt = get_futures_symbol_price("BTCUSDT")
        price_btcusdt = float(btcusdt['price'])
        print(f"BTCUSDT Price: {price_btcusdt}")
        logger.info(f"BTCUSDT Price: {price_btcusdt}")

        # Calculate quantity of BTC with 3 point precision
        quantity = to_trade_usdt / price_btcusdt
        quantity = str(f"{quantity:.3f}")
        quantity = float(quantity)
        print(f"Quantity: {quantity}")
        logger.info(f"Quantity: {quantity}")

    except Exception as e:
        print(f"An exception occurred while calculating quantity: {e}")
        logger.error(f"Could not calculate quantity: {e}")
        bot_response = send_telegram_message("Failure\nCould not calculate quantity")
        bot_response = send_telegram_message(f"Error: {e}")

    if side == 'BUY':
        direction = 'Long'
    elif side == 'SELL':
        direction = 'Short'
    else:
        direction = 'Unknown'
        bot_response = send_telegram_message(f"Failure detecting side\nUnknown side {side}")
        logger.error(f"Failure detecting side. Unknown side {side}")
        return {
            "code": "failure",
            "message": "Unknown direction"
        }
    bot_notification = send_telegram_message(message=f"<b><i>|| {direction} Trade ||</i></b>")

    # Placing order
    try:
        print(f"Sending {order_type} order: {side} {quantity} {symbol}")
        logger.info(f"Sending {order_type} order: {side} {quantity} {symbol}")
        order = client.futures_create_order(symbol=symbol, side=side, quantity=quantity, type=order_type, recvWindow=100000000)

    except Exception as e:
        bot_response = send_telegram_message(f"Failed to OPEN {direction} trade\n{side.lower()} {quantity} {symbol} at {price_btcusdt}\nCurrent position: {get_my_positions()}")
        bot_response = send_telegram_message(f"Error: {e}")
        bot_response = send_telegram_message(f"Order response: {order}")
        print(f"An exception occurred while opening {side} trade: {e}")
        print(f"{side} order failed")
        logger.error(f"{quantity} {symbol} {side} order failed: {e}")
        return {
            "code": f"Failed to OPEN {direction} trade",
            "message": f"{quantity} {symbol} {side} order failed"
        }

    # return this if success
    bot_response = send_telegram_message(f"{direction} trade OPENED successfully\n{side.lower()} {quantity} {symbol} at {price_btcusdt}\nCurrent position: {get_my_positions()}")
    print(f"{side} order placed successfully")
    print("Trade OPENED successfully")
    logger.info(f"{quantity} {symbol} {side} order placed successfully")
    logger.info("Trade OPENED successfully")
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
        logger.error(f"Failure detecting side. Unknown side {side}")
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
        print("An exception occurred while getting BTCUSDT price while closing trade")
        bot_response = send_telegram_message(f"Failure\nCould not get BTCUSDT price while closing trade")
        logger.error("Could not get BTCUSDT price while closing trade")

    try:
        print(f"Sending {order_type} order: {side} {quantity} {symbol}")
        logger.info(f"Sending {order_type} order: {side} {quantity} {symbol}")
        order = client.futures_create_order(symbol=symbol, side=side, quantity=quantity, reduceOnly=True, type=order_type, recvWindow=100000000)

    except Exception as e:
        bot_response = send_telegram_message(f"Failed to CLOSE {direction} trade\n{side.lower()} {quantity} {symbol} at {price_btcusdt}\nCurrent position: {get_my_positions()}")
        bot_response = send_telegram_message(f"Error: {e}")
        bot_response = send_telegram_message(f"Order response: {order}")

        print(f"An exception occurred while closing trade: {e}")
        print(f"{side} order failed")
        logger.error(f"{quantity} {symbol} {side} order failed: {e}\n")
        return {
            "code": f"Failed to CLOSE {direction} trade",
            "message": f"{quantity} {symbol} {side} order failed"
        }

    # return this if success
    bot_response = send_telegram_message(
        f"{direction} trade CLOSED successfully\n{side.lower()} {quantity} {symbol} at {price_btcusdt}\nCurrent position: {get_my_positions()}")
    print(f"{side} order placed successfully")
    print("Trade CLOSED successfully")
    logger.info(f"{quantity} {symbol} {side} order placed successfully")
    logger.info("Trade CLOSED successfully\n")
    return {
        "code": f"{direction} trade CLOSED successfully",
        "message": f"{quantity} {symbol} {side} order placed successfully"
    }



