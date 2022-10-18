from telegram.ext.updater import Updater
from telegram.update import Update
from telegram.ext.callbackcontext import CallbackContext
from telegram.ext.commandhandler import CommandHandler
from telegram.ext.messagehandler import MessageHandler
from telegram.ext.filters import Filters
from functions import *
import config


bot_token = config.BOT_TOKEN
receiver_id = config.RECEIVER_ID

updater = Updater(bot_token, use_context=True)
dispatcher = updater.dispatcher


def positions(update=Update, context=CallbackContext):
    update.message.reply_text(f"Your positions: {get_my_positions()}")

def holdings(update=Update, context=CallbackContext):
    holdings = get_my_holdings(specific=True, symbol='USDT')
    holdings = str(f"{float(holdings[0]['withdrawAvailable']):.3f}")
    available_usdt = float(holdings)
    update.message.reply_text(f"Your holdings: {available_usdt} USDT")

def long(update=Update, context=CallbackContext):
    my_positions = get_my_positions()
    logger.info(f"Position: {my_positions}")

    if my_positions == 0:
        try:
            order_response = open_trade(side='BUY', symbol="BTCUSDT")
        except Exception as e:
            update.message.reply_text(f"Error: {e}")

    else:
        update.message.reply_text(f"Trade already exists.\nYour current position: {my_positions}")

def short(update=Update, context=CallbackContext):
    my_positions = get_my_positions()
    logger.info(f"Position: {my_positions}")

    if my_positions == 0:
        try:
            order_response = open_trade(side='SELL', symbol="BTCUSDT")
        except Exception as e:
            update.message.reply_text(f"Error: {e}")

    else:
        update.message.reply_text(f"Trade already exists.\nYour current position: {my_positions}")

def close(update=Update, context=CallbackContext):
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


def help(update=Update, context=CallbackContext):
    update.message.reply_text(
    """
    /positions --> Current position
    /holdings --> Current holdings (USDT)
    /long --> Open long trade
    /short --> Open short trade
    /close --> Close any open trade
    /help --> Show all commands
    *Note: Trades will be executed only if the position conditions meet
    (Pyramiding == 1)
    """
    )


def unknown_text(update=Update, context=CallbackContext):
    update.message.reply_text(f"Sorry, unrecognized command given: {update.message.text}\nUse /help to see available commands")
  
  
def unknown(update=Update, context=CallbackContext):
    update.message.reply_text(f"Sorry, unrecognized command given: {update.message.text}\nUse /help to see available commands")


dispatcher.add_handler(CommandHandler('positions', positions))
dispatcher.add_handler(CommandHandler('holdings', holdings))
dispatcher.add_handler(CommandHandler('long', long))
dispatcher.add_handler(CommandHandler('short', short))
dispatcher.add_handler(CommandHandler('close', close))
dispatcher.add_handler(CommandHandler('help', help))

# Filter out unknown commands and messages
dispatcher.add_handler(MessageHandler(Filters.text, unknown))
dispatcher.add_handler(MessageHandler(Filters.command, unknown))
dispatcher.add_handler(MessageHandler(Filters.text, unknown_text))

# Initialize
updater.start_polling()
updater.idle()


