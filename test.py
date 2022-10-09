import json, config
from binance.client import Client
from binance.enums import *
from flask import Flask, request, jsonify, render_template

# app = Flask(__name__)

client = Client(config.API_KEY, config.API_SECRET, testnet=False)

def my_holdings():
    try:
        print("Getting your holdings")
        account_info = client.get_account()
        all_assets = account_info['balances']

        my_holdings = []
        for asset_detail in all_assets:
            if float(asset_detail['free']) > 0:
                my_holdings.append(asset_detail)

    except Exception as e:
        print(f"An exception occured: {e}")
        return {
            "code": "failure",
            "message": "Could not fetch your holdings"
        }
    
    return my_holdings


def get_asset_balance(asset):
    try:
        print(f"Getting balance for {asset}")
        balance = client.get_asset_balance(asset=asset)
    except Exception as e:
        print(f"An exception occured - {e}")
        return {
            "code": "failure",
            "message": "Could not fetch asset balance"
        }

    return balance

def get_futures_symbol_price(symbol):
    try:
        print(f"Getting price for {symbol}")
        symbols = client.futures_symbol_ticker()
        for symbol_detail in symbols:
            if symbol_detail['symbol'] == symbol:
                return symbol_detail

    except Exception as e:
        print(f"An exception occured - {e}")
        return {
            "code": "failure",
            "message": "Could not fetch symbol price"
        }


# symbol_info = get_futures_symbol_price("BTCUSDT")
# print(f"Symbol info: {symbol_info}")


# my_holdings = get_symbol_info('BTCUSDT')
# print(my_holdings)

# asset_balance = get_asset_balance('USDT')
# print(asset_balance)


balance = client.futures_account_balance()
print(balance)


