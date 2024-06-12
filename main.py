import logging 
from datetime import datetime, timedelta
from telegram import Update
from telegram.ext import ApplicationBuilder, CallbackContext, CommandHandler 
import os 
from dotenv import load_dotenv


load_dotenv()

TOKEN =  os.getenv('TELEGRAM_BOT_TOKEN')


logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

async def start(update: Update, context: CallbackContext):
    pass


def run():
    logging.info('program start working')

if __name__ == "__main__":
    run()