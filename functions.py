def get_account_info():
    try:
        print("Getting account info")
        # account = client.get_account()
        account = client.futures_account_balance()
    except Exception as e:
        print(f"An exception occured - {e}")
        return {
            "code": "failure",
            "message": "Could not fetch account info"
        }

    return account


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