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


def help(update=Update, context=CallbackContext):
    update.message.reply_text(
    """
    /positions --> Get your current position
    /holdings --> Get your current holdings
    /long --> Open long position of predefined portfolio percentage
    /short --> Open short position of predefined portfolio percentage
    /close --> Close any open trade
    /help --> Show available commands
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
dispatcher.add_handler(CommandHandler('help', help))

# Filter out unknown commands and messages
dispatcher.add_handler(MessageHandler(Filters.text, unknown))
dispatcher.add_handler(MessageHandler(Filters.command, unknown))
dispatcher.add_handler(MessageHandler(Filters.text, unknown_text))

# Initialize
updater.start_polling()
updater.idle()


