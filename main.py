import logging 
from datetime import datetime, timedelta
from telegram import Update
from telegram.ext import ApplicationBuilder, CallbackContext, CommandHandler 
import os 
from dotenv import load_dotenv
from functools import wraps
from dateutil.relativedelta import relativedelta
import json

user_dict = {}

load_dotenv()

TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
filters = ['daily', 'monthly', 'yearly']

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)


class Spends:
    index = 1
    category_list = ['food', 'rent', 'education', 'clothes', 'entertainment', 'health']

    def __init__(self, amount: int, category: str, date: datetime = None):
        self.amount = amount
        self.category = category
        self.date = date
        self.position = Spends.index
        Spends.index += 1

    def __repr__(self):
        return f"Spends(amount: {self.amount}, category: {self.category}, date:{self.date})"

    def __str__(self):
        if self.date:
            return f"{self.position}: Spend amount - {self.amount}, in category - {self.category} with date - {self.date.strftime('%Y-%m-%d')}"
        else:
            return f"{self.position}: Spend amount - {self.amount}, in category - {self.category}"


class Earns:
    index = 1

    def __init__(self, amount: int, category: str, date: datetime = None):
        self.amount = amount
        self.category = category
        self.date = date
        self.position = Earns.index
        Earns.index += 1

    def __repr__(self):
        return f"Spends(amount: {self.amount}, category: {self.category}, date:{self.date})"

    def __str__(self):
        if self.date:
            return f"{self.position}: Earn amount - {self.amount}, in category - {self.category} with date - {self.date.strftime('%Y-%m-%d')}"
        else:
            return f"{self.position}: Earn amount - {self.amount}, in category - {self.category}"


def parameter_type(type_of_notice: str):

    def parameters_decorator(func):
        @wraps(func)
        async def wrapper(update: Update, context: CallbackContext, *args, **kwargs):

            if len(context.args) < 2 or len(context.args) >= 4:
                logging.error("Not valid number of arguments")
                await update.message.reply_text("Not correct number of arguments. Example: \n"
                                                "/add_spend amount category [date, Optional]")
                return

            try:
                int(context.args[0])
            except ValueError:
                logging.error("Amount of spends is incorrect type")
                await update.message.reply_text('Amount of spends is incorrect type')
                return

            if context.args[1] not in Spends.category_list and type_of_notice == 'spend':
                logging.error("Category for spends not in category list")
                await update.message.reply_text('Category must be from category list \n'
                                                'Help Command:  \'/list_category\'')
                return

            if len(context.args) > 2:
                try:
                    datetime.strptime(context.args[2].strip(), "%Y-%m-%d")
                except ValueError:
                    logging.error("Date is incorrect type")
                    await update.message.reply_text('Data is invalid type, must be: %Y-%m-%d \n'
                                                    'Example: (2004-11-27)')
                    return

            return await func(update, context, *args, **kwargs)

        return wrapper
    return parameters_decorator


def load_data():
    global user_dict
    try:
        with open('user_data.json', 'r') as file:
            user_dict = json.load(file)
    except FileNotFoundError:
        user_dict = {}
    except json.JSONDecodeError:
        user_dict = {}


def save_data():
    with open('user_data.json', 'w') as file:
        json.dump(user_dict, file, default=str)


async def start(update: Update, context: CallbackContext) -> None:
    await update.message.reply_text("Hi! This is budget tracker bot , for helping"
                                    "Write /help for more information")


async def my_help(update: Update, context: CallbackContext) -> None:
    await update.message.reply_text(
        "All commands:\n"
        "/list_category -> list of all spends categories\n"
        "/add_spend amount category [date] -> Category must be from the list of categories\n"
        "/add_earn amount category [date] -> Category can be anything\n"
        "/list_spend [filter, Optional]  -> show list with all spends\n"
        "Filter must be this keywords: monthly, weekly, daily, yearly, name of category\n"
        "/list_earn [filter, Optional] -> show list with all earns\n"
        "Filter must be this keywords: monthly, weekly, daily, yearly, name of category\n"
        "/del_spend index ->  index from the list of spends, to delete the notice from the list\n"
        "/del_earn index -> index from the list of earns, to delete the notice from the list\n"
    )


async def list_category(update: Update, context: CallbackContext) -> None:
    result = ""
    for index, category in enumerate(Spends.category_list):
        formatted_string = str(index) + " -> " + category
        result += "\n" + formatted_string
    await update.message.reply_text(f"All possible category of spends:\n {result}")


@parameter_type('spend')
async def add_spend(update: Update, context: CallbackContext) -> None:
    user_id = update.message.from_user.id
    logging.info(f'{context.args}')

    date = None
    if len(context.args) > 2 and context.args[2]:
        date = datetime.strptime(context.args[2], "%Y-%m-%d")

    if not user_dict.get(user_id):
        user_dict[user_id] = []

    spend = Spends(context.args[0], context.args[1], date)
    user_dict[user_id].append(spend)
    save_data()
    await update.message.reply_text("Spend was successfully added")


def check_existing_filter(filter_option: str, type_notice: str, user_id: int):

    for option in filters:
        if option == filter_option:
            return option

    if type_notice == 'spend':
        for option in Spends.category_list:
            if option == filter_option:
                return option

    else:
        all_earns_categories = []
        list_with_notices = user_dict[user_id]

        for notice in list_with_notices:
            if isinstance(notice, Earns):
                all_earns_categories.append(notice.category)

        for option in all_earns_categories:
            if option == filter_option:
                return option
    return None


async def list_spend(update: Update, context: CallbackContext):
    result = ""
    user_id = update.message.from_user.id
    filter_option = None
    if len(context.args) == 1:
        filter_option = check_existing_filter(context.args[0], 'spend', user_id)

    if len(context.args) == 1 and filter_option is None:
        await update.message.reply_text(f"Unknown filter is: {context.args[0]}\n"
                                        f"Possible filters:\n"
                                        f"monthly, yearly, daily, category ( write /list_categories )\n")
        return

    if not user_dict.get(user_id):
        await update.message.reply_text('You haven\'t add any notice yet')
        return

    list_with_notices = user_dict[user_id]
    list_with_all_spends = [spend for spend in list_with_notices if isinstance(spend, Spends)]

    if filter_option is not None:
        now = datetime.now()
        match filter_option:
            case 'daily':
                last_24_hours = now - timedelta(days=1)
                for spend in list_with_all_spends:
                    if spend.date is not None and last_24_hours <= spend.date <= now:
                        result += str(spend) + "\n"
            case 'monthly':
                last_month = now - relativedelta(months=1)
                for spend in list_with_all_spends:
                    if spend.date is not None and last_month <= spend.date <= now:
                        result += str(spend) + "\n"
            case 'yearly':
                last_year = now - relativedelta(years=1)
                for spend in list_with_all_spends:
                    if spend.date is not None and last_year <= spend.date <= now:
                        result += str(spend) + "\n"
            case _:
                for spend in list_with_all_spends:
                    if spend.category == filter_option:
                        result += str(spend) + "\n"
    else:
        for spend in list_with_all_spends:
            result += str(spend) + "\n"

    await update.message.reply_text("All spends are: \n"
                                    f"{result}")


@parameter_type('earn')
async def add_earn(update: Update, context: CallbackContext) -> None:
    user_id = update.message.from_user.id
    logging.info(f'{context.args}')

    date = None
    if len(context.args) > 2 and context.args[2]:
        date = context.args[2]

    if not user_dict.get(user_id):
        user_dict[user_id] = []

    earn = Earns(context.args[0], context.args[1], date)
    user_dict[user_id].append(earn)
    save_data()
    await update.message.reply_text("Earn was successfully added")


async def list_earn(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    result = ""

    filter_option = None
    if len(context.args) == 1:
        filter_option = check_existing_filter(context.args[0], 'earn', user_id)

    if len(context.args) == 1 and filter_option is None:
        await update.message.reply_text(f"Unknown filter is: {context.args[0]}\n"
                                        f"Possible filters:\n"
                                        f"monthly, yearly, daily, category ( write /list_categories )\n")
        return

    if not user_dict.get(user_id):
        await update.message.reply_text('You haven\'t add any notice yet')
        return

    list_with_all_notices = user_dict[user_id]
    list_with_all_earns = [earn for earn in list_with_all_notices if isinstance(earn, Earns)]

    if filter_option is not None:
        now = datetime.now()
        match filter_option:
            case 'daily':
                last_24_hours = now - timedelta(days=1)
                for earn in list_with_all_earns:
                    if earn.date is not None and last_24_hours <= earn.date <= now:
                        result += str(earn) + "\n"
            case 'monthly':
                last_month = now - relativedelta(months=1)
                for earn in list_with_all_earns:
                    if earn.date is not None and last_month <= earn.date <= now:
                        result += str(earn) + "\n"
            case 'yearly':
                last_year = now - relativedelta(years=1)
                for earn in list_with_all_earns:
                    if earn.date is not None and last_year <= earn.date <= now:
                        result += str(earn) + "\n"
            case _:
                for earn in list_with_all_earns:
                    if earn.category == filter_option:
                        result += str(earn) + "\n"
    else:
        for earn in list_with_all_earns:
            result += str(earn) + "\n"

    await update.message.reply_text("All earns are: \n"
                                    f"{result}")


async def del_spend(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    logging.info({f'{context.args}'})

    if len(context.args) != 1:
        await update.message.reply_text("Not correct arguments. Example: \n"
                                        "/del_spend 2")
        return

    if not user_dict.get(user_id):
        await update.message.reply_text("Haven\'t added any notice yet")
        return

    try:
        index = int(context.args[0])
    except ValueError:
        await update.message.reply_text("Index must be only an int")
        return

    if index <= 0:
        await update.message.reply_text("Index must be only more than 0")
        return

    list_with_all_notices = user_dict[user_id]
    list_with_all_spends = [spend for spend in list_with_all_notices if isinstance(spend, Spends)]

    found_notice = None
    for spend in list_with_all_spends:
        if spend.position == index:
            found_notice = spend
            break

    if found_notice:
        await update.message.reply_text("Spend notice was successfully deleted")
        list_with_all_notices.remove(found_notice)
        save_data()
    else:
        await update.message.reply_text("Spend with the specified index was not found.")


async def del_earn(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    logging.info({f'{context.args}'})

    if len(context.args) != 1:
        await update.message.reply_text("Not correct arguments. Example: \n"
                                        "/del_spend 2")
        return

    if not user_dict.get(user_id):
        await update.message.reply_text("Haven\'t added any notice yet")
        return

    try:
        index = int(context.args[0])
    except ValueError:
        await update.message.reply_text("Index must be only an int")
        return

    if index <= 0:
        await update.message.reply_text("Index must be only more than 0")
        return

    list_with_all_notices = user_dict[user_id]
    list_with_all_earns = [earn for earn in list_with_all_notices if isinstance(earn, Earns)]

    found_notice = None
    for earn in list_with_all_earns:
        if earn.position == index:
            found_notice = earn
            break

    if found_notice:
        await update.message.reply_text("Earn notice was successfully deleted")
        list_with_all_notices.remove(found_notice)
        save_data()
    else:
        await update.message.reply_text("Earn with the specified index was not found.")


async def stat_spend(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    logging.info(f"{context.args}")

    filter_option = None
    if len(context.args) == 1:
        filter_option = check_existing_filter(context.args[0], 'spend', user_id)

    if len(context.args) == 1 and filter_option is None:
        await update.message.reply_text(f"Unknown filter is: {context.args[0]}\n"
                                        f"Possible filters:\n"
                                        f"monthly, yearly, daily, category ( write /list_categories )\n")
        return

    if len(context.args) != 1 and len(context.args) != 0:
        await update.message.reply_text("Not correct arguments. Example: \n"
                                        "/stat_spend [filter, Optional]"
                                        "Possible filters: [daily, monthly, yearly, category]")
        return

    if not user_dict.get(user_id):
        await update.message.reply_text("Haven\'t added any notice yet")
        return

    list_with_all_notices = user_dict[user_id]
    list_with_all_spends = [spend for spend in list_with_all_notices if isinstance(spend, Spends)]
    list_with_specific_spends = []

    if filter_option is not None:
        now = datetime.now()
        match filter_option:
            case 'daily':
                last_24_hours = now - timedelta(days=1)
                for spend in list_with_all_spends:
                    if spend.date is not None and last_24_hours <= spend.date <= now:
                        list_with_specific_spends.append(spend)

            case 'monthly':
                last_month = now - relativedelta(months=1)
                for spend in list_with_all_spends:
                    if spend.date is not None and last_month <= spend.date <= now:
                        list_with_specific_spends.append(spend)

            case 'yearly':
                last_year = now - relativedelta(years=1)
                for spend in list_with_all_spends:
                    if spend.date is not None and last_year <= spend.date <= now:
                        list_with_specific_spends.append(spend)
            case _:
                for spend in list_with_all_spends:
                    if spend.category == filter_option:
                        list_with_specific_spends.append(spend)
    else:
        for spend in list_with_all_spends:
            list_with_specific_spends.append(spend)

    all_spends = 0

    for spend in list_with_all_spends:
        all_spends += int(spend.amount)

    if filter_option:
        await update.message.reply_text(f"All Money that u spend is: {all_spends}\n"
                                        f"In this filter option: {filter_option}")
    else:
        await update.message.reply_text(f"All money that u spend is {all_spends}\n")


async def stat_earn(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    logging.info(f"{context.args}")

    filter_option = None
    if len(context.args) == 1:
        filter_option = check_existing_filter(context.args[0], 'earn', user_id)

    if len(context.args) == 1 and filter_option is None:
        await update.message.reply_text(f"Unknown filter is: {context.args[0]}\n"
                                        f"Possible filters:\n"
                                        f"monthly, yearly, daily, category ( write /list_categories )\n")
        return

    if len(context.args) != 1 and len(context.args) != 0:
        await update.message.reply_text("Not correct arguments. Example: \n"
                                        "/stat_earn [filter, Optional]"
                                        "Possible filters: [daily, monthly, yearly, category]")
        return

    if not user_dict.get(user_id):
        await update.message.reply_text("Haven\'t added any notice yet")
        return

    list_with_all_notices = user_dict[user_id]
    list_with_all_earns = [earn for earn in list_with_all_notices if isinstance(earn, Earns)]
    list_with_specific_earns = []

    if filter_option is not None:
        now = datetime.now()
        match filter_option:
            case 'daily':
                last_24_hours = now - timedelta(days=1)
                for earn in list_with_all_earns:
                    if earn.date is not None and last_24_hours <= earn.date <= now:
                        list_with_specific_earns.append(earn)

            case 'monthly':
                last_month = now - relativedelta(months=1)
                for earn in list_with_all_earns:
                    if earn.date is not None and last_month <= earn.date <= now:
                        list_with_specific_earns.append(earn)

            case 'yearly':
                last_year = now - relativedelta(years=1)
                for earn in list_with_all_earns:
                    if earn.date is not None and last_year <= earn.date <= now:
                        list_with_specific_earns.append(earn)
            case _:
                for earn in list_with_all_earns:
                    if earn.category == filter_option:
                        list_with_specific_earns.append(earn)
    else:
        for earn in list_with_all_earns:
            list_with_specific_earns.append(earn)

    all_earns = 0

    for earn in list_with_specific_earns:
        all_earns += int(earn.amount)

    if filter_option:
        await update.message.reply_text(f"All Money that u earn is: {all_earns}\n"
                                        f"In this filter option: {filter_option}")
    else:
        await update.message.reply_text(f"All money that u earn is {all_earns}\n")


def run():
    load_data()
    app = ApplicationBuilder().token(TOKEN).build()
    logging.info('Bot start working')

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", my_help))

    app.add_handler(CommandHandler("add_spend", add_spend))
    app.add_handler(CommandHandler("add_earn", add_earn))

    app.add_handler(CommandHandler("list_spend", list_spend))
    app.add_handler(CommandHandler("list_category", list_category))
    app.add_handler(CommandHandler("list_earn", list_earn))

    app.add_handler(CommandHandler("del_spend", del_spend))
    app.add_handler(CommandHandler("del_earn", del_earn))

    app.add_handler(CommandHandler("stat_spend", stat_spend))
    app.add_handler(CommandHandler("stat_earn", stat_earn))

    app.run_polling()


if __name__ == "__main__":
    run()
