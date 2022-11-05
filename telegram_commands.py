from telegram.ext.updater import Updater
from telegram.update import Update
from telegram.ext.callbackcontext import CallbackContext
from telegram.ext.commandhandler import CommandHandler
from telegram.ext.messagehandler import MessageHandler
from telegram.ext.filters import Filters
from functions import *
import logging
import config


# Create and configure logger
logging.basicConfig(filename="log_file.log", level=logging.DEBUG, format='%(asctime)s %(message)s', filemode='w')
logger = logging.getLogger()


# Bot configs
bot_token = config.BOT_TOKEN
receiver_id = int(config.RECEIVER_ID)

updater = Updater(bot_token, use_context=True)
dispatcher = updater.dispatcher


# User verification
def verified_user(update=Update, context=CallbackContext):
    user_id = update.effective_user.id
    print(f"User id: {user_id}")
    if user_id == receiver_id:
        logger.info(f"{update.effective_user.first_name}_{user_id} sent a telegram command")
        return True
    else:
        bot_response = send_telegram_message(f"{update.effective_user.first_name} tried to access the AlgoTrading bot\nUser id: {update.effective_user.id}")
        logger.warning(f"{update.effective_user.first_name}_{user_id} tried to access the AlgoTrading bot")
        update.message.reply_text("Sorry, this command is restricted to the bot owner.")
        return False


def positions(update=Update, context=CallbackContext):
    if verified_user(update=update):
        update.message.reply_text(f"Your positions: {get_my_positions()}")


def holdings(update=Update, context=CallbackContext):
    if verified_user(update=update):
        holdings = get_my_holdings(specific=True, symbol='USDT')
        holdings = str(f"{float(holdings[0]['withdrawAvailable']):.3f}")
        available_usdt = float(holdings)
        update.message.reply_text(f"Your holdings: {available_usdt} USDT")


def long(update=Update, context=CallbackContext):
    if verified_user(update=update):
        my_positions = get_my_positions()
        logger.info(f"Position: {my_positions}")

        if my_positions == 0:
            try:
                order_response = open_trade(side='BUY', symbol="BTCUSDT")
            except Exception as e:
                update.message.reply_text(f"Error: {e}")

        else:
            update.message.reply_text(f"Trade already exists.\nYour current position: {my_positions}")

        # Get remaining usdt
        holdings = get_my_holdings(specific=True, symbol='USDT')
        holdings = str(f"{float(holdings[0]['withdrawAvailable']):.3f}")  # Can use 'withdrawAvailable' as balacnce will be same after placing order
        remaining_usdt = float(holdings)
        update.message.reply_text(f"Remaining Balance: {remaining_usdt} USDT")


def short(update=Update, context=CallbackContext):
    if verified_user(update=update):
        my_positions = get_my_positions()
        logger.info(f"Position: {my_positions}")

        if my_positions == 0:
            try:
                order_response = open_trade(side='SELL', symbol="BTCUSDT")
            except Exception as e:
                update.message.reply_text(f"Error: {e}")

        else:
            update.message.reply_text(f"Trade already exists.\nYour current position: {my_positions}")
        
        # Get remaining usdt
        holdings = get_my_holdings(specific=True, symbol='USDT')
        holdings = str(f"{float(holdings[0]['withdrawAvailable']):.3f}")  # Can use 'withdrawAvailable' as balacnce will be same after placing order
        remaining_usdt = float(holdings)
        update.message.reply_text(f"Remaining Balance: {remaining_usdt} USDT")


def close(update=Update, context=CallbackContext):
    if verified_user(update=update):
        my_positions = get_my_positions()
        logger.info(f"Position: {my_positions}")

        # Close long position
        if my_positions > 0:
            try:
                quantity = abs(my_positions)
                order_response = close_trade(side='SELL', symbol="BTCUSDT", quantity=quantity)
            except Exception as e:
                update.message.reply_text(f"Error: {e}")

        # Close short position
        elif my_positions < 0:
            try:
                quantity = abs(my_positions)
                order_response = close_trade(side='BUY', symbol="BTCUSDT", quantity=quantity)
            except Exception as e:
                update.message.reply_text(f"Error: {e}")

        else:
            update.message.reply_text(f"No open trade found.\nYour current position: {my_positions}")

        # Get remaining usdt
        holdings = get_my_holdings(specific=True, symbol='USDT')
        holdings = str(f"{float(holdings[0]['withdrawAvailable']):.3f}")  # Can use 'withdrawAvailable' as balacnce will be same after placing order
        remaining_usdt = float(holdings)
        update.message.reply_text(f"Remaining Balance: {remaining_usdt} USDT")


def pnl(update=Update, context=CallbackContext):
    if verified_user(update=update):
        pnl = get_pnl()
        if pnl['pos'] != 0:
            update.message.reply_text(f"Your PnL: {pnl['pnl']} USDT\nPnL percentage: {pnl['pnl_percentage']} %")
        
        elif pnl['pos'] == 0:
            update.message.reply_text(f"No open trade found")
            update.message.reply_text(f"Recent trade PnL:\n{pnl['pnl']} USDT\n{pnl['pnl_percentage']} %\nNote: Excluding trade fees.")
            
            # Get remaining usdt
            holdings = get_my_holdings(specific=True, symbol='USDT')
            holdings = str(f"{float(holdings[0]['withdrawAvailable']):.3f}")  # Can use 'withdrawAvailable' as balacnce will be same after placing order
            remaining_usdt = float(holdings)
            update.message.reply_text(f"Remaining Balance: {remaining_usdt} USDT")


def help(update=Update, context=CallbackContext):
    if verified_user(update=update):
        update.message.reply_text("/positions --> Current position\n/holdings --> Current holdings (USDT)\n/long --> Open long trade\n/short --> Open short trade\n/close --> Close any open trade\n/pnl --> Current PnL\n/start --> Welcome message\n/help --> Show all commands\n*Note: Trades will be executed only if the position conditions meet (Pyramiding == 1)")
    else:
        update.message.reply_text("/positions --> Current position\n/holdings --> Current holdings (USDT)\n/long --> Open long trade\n/short --> Open short trade\n/close --> Close any open trade\n/pnl --> Current PnL\n/start --> Welcome message\n/help --> Show all commands\n*Note: Trades will be executed only if the position conditions meet (Pyramiding == 1)")


def start(update=Update, context=CallbackContext):
    if verified_user(update=update):
        update.message.reply_text(f"Hello {update.effective_user.first_name} !!\nWelcome to the AlgoTrading bot developed by @dhyeySherasia\nUse /help to see available commands.")
    else:
        update.message.reply_text(f"Hello {update.effective_user.first_name} !!\nWe can automate your binance trades using tradingview webhook alerts.\nYou can also manage your trades using simple bot commands. Use /help to see available commands.\nCurrently this bot is restricted to the bot owner only. Contact @dhyeySherasia for more info.")


def unknown_text(update=Update, context=CallbackContext):
    if verified_user(update=update):
        update.message.reply_text(f"Sorry, unrecognized command given: {update.message.text}\nUse /help to see available commands")


def unknown(update=Update, context=CallbackContext):
    if verified_user(update=update):
        update.message.reply_text(f"Sorry, unrecognized command given: {update.message.text}\nUse /help to see available commands")


def main():

    print("Inside main")

    dispatcher.add_handler(CommandHandler('positions', positions))
    dispatcher.add_handler(CommandHandler('holdings', holdings))
    dispatcher.add_handler(CommandHandler('long', long))
    dispatcher.add_handler(CommandHandler('short', short))
    dispatcher.add_handler(CommandHandler('close', close))
    dispatcher.add_handler(CommandHandler('pnl', pnl))
    dispatcher.add_handler(CommandHandler('help', help))
    dispatcher.add_handler(CommandHandler('start', start))

    # Filter out unknown commands and messages
    dispatcher.add_handler(MessageHandler(Filters.text, unknown))
    dispatcher.add_handler(MessageHandler(Filters.command, unknown))
    dispatcher.add_handler(MessageHandler(Filters.text, unknown_text))

    # Initialize
    updater.start_polling()
    updater.idle()




    
