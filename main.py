import telebot
from datetime import datetime, timedelta
import config
import text_constants
from database_communication import DataBase


# from time import sleep


def log_message(user_id, message: str, is_from_user: bool, encoding="utf-8"):
    f = open(f"./logs_chat/{user_id}.txt", "a", )
    time = str((datetime.now() + timedelta(hours=config.TIME_OFFSET)).strftime("%d.%m.%Y %H:%M"))
    text = time + " "
    if is_from_user:
        text += "USER "
    else:
        text += "BOT "
    if message is not None:
        text += message.replace("\n", " || ").replace("\r", " || ") + "\n"
    else:
        text += text_constants.MESSAGE_FOR_LOG_WITHOUT_TEXT + "\n"
    f.write(text)


def check_user_status(user_id):
    global users_in_processing
    if user_id in users_in_processing:
        return False
    else:
        users_in_processing.add(user_id)
        return True


def del_user_from_checking_arr(user_id):
    global users_in_processing
    if user_id in users_in_processing:
        users_in_processing.remove(user_id)


def get_and_update_user_info(db: DataBase, user_id, username, first_name, last_name):
    user_info = db.update_userinfo_user(user_id, username, first_name, last_name)
    return user_info


def get_server_info(db: DataBase):
    settings = db.get_bot_settings()
    return {
        "is_logging_chat": settings["is_logging_chat"],
        "is_enabled_for_users_bot": settings["is_enabled_for_users_bot"]
    }


# Далее функции по обработки сообщений и запросов к боту

def get_main_menu(user_object):
    keyboard = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    if user_object["user_id"] in config.MAIN_ADMINS or user_object["is_admin"] or user_object["is_moderator"]:
        keyboard.add(telebot.types.KeyboardButton(text_constants.ADMIN_MENU))
    return keyboard


def get_admin_menu(user_object, bot_settings):
    keyboard = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add(text_constants.ITEM_LIST_OF_USERS)
    keyboard.add(text_constants.ITEM_SEND_MESSAGE_FOR_ALL)
    if bot_settings["is_enabled_for_users_bot"]:
        keyboard.add(text_constants.ITEM_DISABLE_BOT_USERS)
    else:
        keyboard.add(text_constants.ITEM_ENABLE_BOT_USERS)
    if bot_settings["is_logging_chat"]:
        keyboard.add(text_constants.ITEM_DISABLE_LOGGING_CHAT)
    else:
        keyboard.add(text_constants.ITEM_ENABLE_LOGGING_CHAT)
    keyboard.add(telebot.types.KeyboardButton(text_constants.BACK_TO_MAIN_MENU))

    return keyboard


def get_moderator_menu(user_object, bot_settings):
    keyboard = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add(text_constants.ITEM_LIST_OF_USERS)
    keyboard.add(telebot.types.KeyboardButton(text_constants.BACK_TO_MAIN_MENU))
    return keyboard


def post_status_writing(user_id):
    bot.send_chat_action(user_id, "typing", timeout=7)


def gen_message_for_user_profile(viewing_user_id, viewing_user_info):
    # обновление сообщения
    message_text_from_bot = f"*Профиль пользователя @{viewing_user_info['username']}*\n"
    message_text_from_bot += f"*Последняя активность*: {viewing_user_info['last_activity']}\n"
    if viewing_user_info["is_banned"]:
        message_text_from_bot += f"Пользователь *забанен*\n"
    if viewing_user_info["is_moderator"] or viewing_user_info["is_admin"]:
        message_text_from_bot += f"*Администратор/Модератор*\n"
    message_text_from_bot += f"*Telegram id*: {viewing_user_info['user_id']}\n"
    #  message_text_from_bot += f"Баланс: {viewing_user_info['balance']}"
    message_text_from_bot += f"*Дата регистрации*: {viewing_user_info['reg_date']}\n"
    return message_text_from_bot


def get_user_profile_keyboard(user_object, viewing_user_object):
    keyboard = telebot.types.InlineKeyboardMarkup()
    row = []
    if viewing_user_object["is_banned"] and (user_object["is_admin"] or user_object["user_id"] in config.MAIN_ADMINS):
        row.append(
            telebot.types.InlineKeyboardButton(text=text_constants.ITEM_UNBAN_USER, callback_data="user_unban"))
    elif not viewing_user_object["is_banned"] and (
            user_object["is_admin"] or user_object["user_id"] in config.MAIN_ADMINS):
        row.append(
            telebot.types.InlineKeyboardButton(text=text_constants.ITEM_BAN_USER, callback_data="user_ban"))
    if viewing_user_object["is_admin"] and (user_object["is_admin"] or user_object["user_id"] in config.MAIN_ADMINS):
        row.append(
            telebot.types.InlineKeyboardButton(text=text_constants.ITEM_TAKEAWAY_ADMIN,
                                               callback_data="user_takeaway_admin"))
    elif not viewing_user_object["is_admin"] and (
            user_object["is_admin"] or user_object["user_id"] in config.MAIN_ADMINS):
        row.append(
            telebot.types.InlineKeyboardButton(text=text_constants.ITEM_GIVE_ADMIN, callback_data="user_give_admin"))
    if viewing_user_object["is_moderator"] and (
            user_object["is_admin"] or user_object["user_id"] in config.MAIN_ADMINS):
        row.append(
            telebot.types.InlineKeyboardButton(text=text_constants.ITEM_TAKEAWAY_MODERATOR,
                                               callback_data="user_takeaway_moderator"))
    elif not viewing_user_object["is_moderator"] and (
            user_object["is_admin"] or user_object["user_id"] in config.MAIN_ADMINS):
        row.append(
            telebot.types.InlineKeyboardButton(text=text_constants.ITEM_GIVE_MODERATOR,
                                               callback_data="user_give_moderator"))
    try:
        keyboard.add(*row)
    except:
        pass
    row = []
    row.append(telebot.types.InlineKeyboardButton(text_constants.ITEM_VIEW_CHAT_LOGS, callback_data="chat_logs_view"))
    row.append(telebot.types.InlineKeyboardButton(text_constants.ITEM_CLEAR_CHAT_LOGS, callback_data="chat_logs_clear"))
    try:
        keyboard.add(*row)
    except:
        pass
    return keyboard


users_in_processing = set()

bot = telebot.TeleBot(token=config.BOT_TOKEN)



@bot.message_handler(commands=[config.CONFIGURATEDB_COMMAND])
def configurate_db(message: telebot.types.Message):
    if message.from_user.id in config.MAIN_ADMINS:
        try:
            db = DataBase()
            db.configurate_db()
            bot.send_message(message.chat.id, "База данных настроена")
        except:
            bot.send_message(message.chat.id, "Ошибка")


@bot.message_handler(commands=["start"])
def start(message: telebot.types.Message):
    if not check_user_status(message.from_user.id): return 0
    post_status_writing(message.from_user.id)
    db_object = DataBase()
    bot_settings = get_server_info(db_object)
    if not bot_settings["is_enabled_for_users_bot"] and message.from_user.id not in config.MAIN_ADMINS:
        bot.send_message(message.chat.id, text_constants.BOT_STATUS_MESSAGE)
        del_user_from_checking_arr(message.from_user.id)
        db_object.close_connection()
        return 0

    if bot_settings["is_logging_chat"]:
        log_message(user_id=message.chat.id, message=message.text, is_from_user=True)
    user_info = get_and_update_user_info(db_object, message.from_user.id, message.from_user.username,
                                         message.from_user.first_name, message.from_user.last_name)
    if user_info["is_banned"]:
        del_user_from_checking_arr(message.from_user.id)
        db_object.close_connection()
        return 0
    message_text_from_bot = ""
    """START OF PROCESSING MESSAGES"""
    if len(message.text.split()) == 1:
        message_text_from_bot = text_constants.WELCOME_MESSAGE
        bot.send_message(message.from_user.id, message_text_from_bot,
                         parse_mode="MARKDOWN", reply_markup=get_main_menu(user_info))
    elif len(message.text.split()) == 2 and len(message.text.split()[1]) >= 8 and message.text.split()[1].startswith(
            "profile") and (user_info["is_admin"] or user_info["is_moderator"]
                            or message.from_user.id in config.MAIN_ADMINS):
        viewing_user_id = int(message.text.split()[1].split("profile")[1])
        viewing_user_info = db_object.check_user_is_registered(viewing_user_id)
        if not user_info:
            del_user_from_checking_arr(message.from_user.id)
            db_object.close_connection()
            return 0
        message_text_from_bot = gen_message_for_user_profile(viewing_user_id, viewing_user_info)
        bot.send_message(message.from_user.id, message_text_from_bot, parse_mode="MARKDOWN",
                         reply_markup=get_user_profile_keyboard(user_info, viewing_user_info))

    """END OF PROCESSING MESSAGES"""
    if bot_settings["is_logging_chat"]:
        log_message(user_id=message.chat.id, message=message_text_from_bot, is_from_user=False)
    del_user_from_checking_arr(message.from_user.id)
    db_object.close_connection()


@bot.message_handler(content_types=["text"])
def text_messages(message: telebot.types.Message):
    if not check_user_status(message.from_user.id): return 0
    post_status_writing(message.from_user.id)
    db_object = DataBase()
    bot_settings = get_server_info(db_object)
    if not bot_settings["is_enabled_for_users_bot"] and message.chat.id not in config.MAIN_ADMINS:
        del_user_from_checking_arr(message.from_user.id)
        db_object.close_connection()
        bot.send_message(message.chat.id, text_constants.BOT_STATUS_MESSAGE)
        return 0
    if bot_settings["is_logging_chat"]:
        log_message(user_id=message.chat.id, message=message.text, is_from_user=True)
    user_info = get_and_update_user_info(db_object, message.from_user.id, message.from_user.username,
                                         message.from_user.first_name, message.from_user.last_name)
    if user_info["is_banned"]:
        del_user_from_checking_arr(message.from_user.id)
        db_object.close_connection()
        return 0
    message_text_from_bot = ""
    """START OF PROCESSING ALL TEXT MESSAGES"""
    """START OF ADMIN MENU"""
    if message.text == text_constants.ADMIN_MENU and (user_info["is_admin"]
                                                      or message.from_user.id in config.MAIN_ADMINS):  # меню для админов
        message_text_from_bot = text_constants.ADMIN_MENU_OPENED_TEXT
        bot.send_message(message.from_user.id, message_text_from_bot, parse_mode="MARKDOWN",
                         reply_markup=get_admin_menu(user_info, bot_settings))
    elif message.text == text_constants.ADMIN_MENU and user_info["is_moderator"]:  # меню для модеров
        message_text_from_bot = text_constants.MODERATOR_MENU_OPENED_TEXT
        bot.send_message(message.from_user.id, message_text_from_bot, parse_mode="MARKDOWN",
                         reply_markup=get_moderator_menu(user_info, bot_settings))

    elif message.text == text_constants.ITEM_DISABLE_BOT_USERS and (user_info["is_admin"]
                                                                    or message.from_user.id in config.MAIN_ADMINS):
        db_object.set_bot_settings(False, bot_settings["is_logging_chat"])
        message_text_from_bot = text_constants.MESSAGE_BOT_DISABLED
        bot.send_message(message.from_user.id, message_text_from_bot,
                         reply_markup=get_admin_menu(user_info, {"is_enabled_for_users_bot": False,
                                                                 "is_logging_chat": bot_settings["is_logging_chat"]}))
    elif message.text == text_constants.ITEM_ENABLE_BOT_USERS and (user_info["is_admin"]
                                                                   or message.from_user.id in config.MAIN_ADMINS):
        db_object.set_bot_settings(True, bot_settings["is_logging_chat"])
        bot.send_message(message.from_user.id, text_constants.MESSAGE_BOT_ENABLED,
                         reply_markup=get_admin_menu(user_info, {"is_enabled_for_users_bot": True,
                                                                 "is_logging_chat": bot_settings["is_logging_chat"]}))
    elif message.text == text_constants.ITEM_DISABLE_LOGGING_CHAT and (user_info["is_admin"]
                                                                       or message.from_user.id in config.MAIN_ADMINS):
        db_object.set_bot_settings(bot_settings["is_enabled_for_users_bot"], False)
        message_text_from_bot = text_constants.MESSAGE_LOGGING_DISABLED
        bot.send_message(message.from_user.id, message_text_from_bot,
                         reply_markup=get_admin_menu(user_info, {
                             "is_enabled_for_users_bot": bot_settings["is_enabled_for_users_bot"],
                             "is_logging_chat": False}))
    elif message.text == text_constants.ITEM_ENABLE_LOGGING_CHAT and (user_info["is_admin"]
                                                                      or message.from_user.id in config.MAIN_ADMINS):
        db_object.set_bot_settings(bot_settings["is_enabled_for_users_bot"], True)
        message_text_from_bot = text_constants.MESSAGE_LOGGING_ENABLED
        bot.send_message(message.from_user.id, message_text_from_bot,
                         reply_markup=get_admin_menu(user_info, {
                             "is_enabled_for_users_bot": bot_settings["is_enabled_for_users_bot"],
                             "is_logging_chat": True}))
    elif message.text == text_constants.ITEM_SEND_MESSAGE_FOR_ALL and (user_info["is_admin"]
                                                                       or message.from_user.id in config.MAIN_ADMINS):
        message_text_from_bot = text_constants.MESSAGE_REPLY_ON_THIS_FOR_SEND_MESSAGE_FOR_ALL
        bot.send_message(message.from_user.id, message_text_from_bot, parse_mode="MARKDOWN",
                         reply_markup=telebot.types.ForceReply(), disable_web_page_preview=True)
    elif message.reply_to_message is not None \
            and message.reply_to_message.text == text_constants.MESSAGE_REPLY_ON_THIS_FOR_SEND_MESSAGE_FOR_ALL_WITHOUT_FORMAT \
            and (user_info["is_admin"] or message.from_user.id in config.MAIN_ADMINS):
        message_text_for_send = message.text
        errors = 0
        counter = 0
        for user in db_object.get_all_users():
            try:
                bot.send_message(user["user_id"], message_text_for_send, disable_web_page_preview=True,
                                 parse_mode="MARKDOWN")
            except:
                errors += 1
            counter += 1
        message_text_from_bot = f"Сообщение отправлено пользователям ({counter - errors}/{counter})"
        bot.send_message(message.from_user.id, message_text_from_bot,
                         reply_markup=get_admin_menu(user_info, bot_settings))
    elif message.text == text_constants.ITEM_LIST_OF_USERS and (user_info["is_admin"] or user_info["is_moderator"]
                                                                or message.from_user.id in config.MAIN_ADMINS):
        all_users = db_object.get_all_users()
        message_text_from_bot = f"*Всего пользователей:* {len(all_users)}\n"
        user_counter = 1
        for user in all_users:
            message_text_from_bot += f"{user_counter}) @{user['username']} | [{text_constants.VIEW_USER_PROFILE}](https://t.me/{config.BOT_USERNAME}?start=profile{user['user_id']})\n"
            if user_counter == 10:
                break
            user_counter += 1
        message_text_from_bot += f"_Страница 1 из {(len(all_users) + 9) // 10}_"
        buttons_arr = [telebot.types.InlineKeyboardButton(text="Страница 1", callback_data="page_number")]
        if len(all_users) > 10:
            buttons_arr.append(
                telebot.types.InlineKeyboardButton(text=text_constants.NEXT_PAGE, callback_data="next_page_users"))
            keyboard = telebot.types.InlineKeyboardMarkup(row_width=len(buttons_arr))
            keyboard.add(buttons_arr[0], buttons_arr[1])
        else:
            keyboard = telebot.types.InlineKeyboardMarkup(row_width=len(buttons_arr))
            keyboard.add(buttons_arr[0])

        bot.send_message(message.from_user.id, message_text_from_bot, reply_markup=keyboard,
                         disable_web_page_preview=True, parse_mode="MARKDOWN")
    """END OF ADMIN MENU"""
    if message.text == text_constants.BACK_TO_MAIN_MENU:  # возвращение в главное меню
        message_text_from_bot = text_constants.WELCOME_MESSAGE
        bot.send_message(message.from_user.id, message_text_from_bot,
                         parse_mode="MARKDOWN", reply_markup=get_main_menu(user_info))
    """END OF PROCESSING ALL TEXT MESSAGES"""
    if bot_settings["is_logging_chat"]:
        log_message(user_id=message.chat.id, message=message_text_from_bot, is_from_user=False)
    del_user_from_checking_arr(message.from_user.id)
    db_object.close_connection()


@bot.callback_query_handler(func=lambda call: True)
def callback_inline(call: telebot.types.CallbackQuery):
    if not check_user_status(call.from_user.id): return 0
    db_object = DataBase()
    bot_settings = get_server_info(db_object)
    if not bot_settings["is_enabled_for_users_bot"] and call.from_user.id not in config.MAIN_ADMINS:
        bot.send_message(call.from_user.id, text_constants.BOT_STATUS_MESSAGE)
        del_user_from_checking_arr(call.from_user.id)
        db_object.close_connection()
        return 0

    if bot_settings["is_logging_chat"]:
        log_message(user_id=call.from_user.id, message=f"QUERY {call.data}", is_from_user=True)
    user_info = get_and_update_user_info(db_object, call.from_user.id, call.from_user.username,
                                         call.from_user.first_name, call.from_user.last_name)
    if user_info["is_banned"]:
        del_user_from_checking_arr(call.from_user.id)
        db_object.close_connection()
        return 0
    """START OF PROCESSING QUERIES"""
    message_text_from_bot = ""
    if call.data == "next_page_users" and (user_info["is_admin"] or user_info["is_moderator"]
                                           or call.from_user.id in config.MAIN_ADMINS):
        tmp_data_pages = call.message.text[call.message.text.find("Страница"):].split()
        page_now = int(tmp_data_pages[1])
        page_max = int(tmp_data_pages[3])
        if page_now + 1 > page_max:
            del_user_from_checking_arr(call.from_user.id)
            db_object.close_connection()
            return 0
        all_users = db_object.get_all_users()
        message_text_from_bot = f"*Всего пользователей:* {len(all_users)}\n"

        user_counter = page_now * 10 + 1
        for user in all_users[page_now * 10:]:
            message_text_from_bot += f"{user_counter}) @{user['username']} | [{text_constants.VIEW_USER_PROFILE}](https://t.me/{config.BOT_USERNAME}?start=profile{user['user_id']})\n"
            if user_counter == page_now * 10 + 10:
                break
            user_counter += 1
        message_text_from_bot += f"_Страница {page_now + 1} из {page_max}_"
        buttons_arr = [telebot.types.InlineKeyboardButton(text=f"Страница {page_now + 1}", callback_data="page_number")]
        if page_now + 1 < page_max:
            buttons_arr.append(
                telebot.types.InlineKeyboardButton(text=text_constants.NEXT_PAGE, callback_data="next_page_users"))
            buttons_arr.append(
                telebot.types.InlineKeyboardButton(text=text_constants.PREV_PAGE, callback_data="prev_page_users"))
            keyboard = telebot.types.InlineKeyboardMarkup(row_width=len(buttons_arr))
            keyboard.add(buttons_arr[2], buttons_arr[0], buttons_arr[1])
        else:
            buttons_arr.append(
                telebot.types.InlineKeyboardButton(text=text_constants.PREV_PAGE, callback_data="prev_page_users"))
            keyboard = telebot.types.InlineKeyboardMarkup(row_width=len(buttons_arr))
            keyboard.add(buttons_arr[1], buttons_arr[0])
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                              text=message_text_from_bot, reply_markup=keyboard, parse_mode="MARKDOWN")
    if call.data == "prev_page_users" and (user_info["is_admin"] or user_info["is_moderator"]
                                           or call.from_user.id in config.MAIN_ADMINS):
        tmp_data_pages = call.message.text[call.message.text.find("Страница"):].split()
        page_now = int(tmp_data_pages[1])
        page_max = int(tmp_data_pages[3])
        if page_now - 1 < 1:
            del_user_from_checking_arr(call.from_user.id)
            db_object.close_connection()
            return 0
        all_users = db_object.get_all_users()
        message_text_from_bot = f"*Всего пользователей:* {len(all_users)}\n"
        user_counter = (page_now - 2) * 10 + 1
        for user in all_users[(page_now - 2) * 10:]:
            message_text_from_bot += f"{user_counter}) @{user['username']} | [{text_constants.VIEW_USER_PROFILE}](https://t.me/{config.BOT_USERNAME}?start=profile{user['user_id']})\n"
            if user_counter == (page_now - 2) * 10 + 10:
                break
            user_counter += 1
        message_text_from_bot += f"_Страница {page_now - 1} из {page_max}_"
        buttons_arr = [telebot.types.InlineKeyboardButton(text=f"Страница {page_now - 1}", callback_data="page_number")]
        if page_now - 1 > 1:
            buttons_arr.append(
                telebot.types.InlineKeyboardButton(text=text_constants.PREV_PAGE, callback_data="prev_page_users"))
            buttons_arr.append(
                telebot.types.InlineKeyboardButton(text=text_constants.NEXT_PAGE, callback_data="next_page_users"))
            keyboard = telebot.types.InlineKeyboardMarkup(row_width=len(buttons_arr))
            keyboard.add(buttons_arr[1], buttons_arr[0], buttons_arr[2])
        else:
            buttons_arr.append(
                telebot.types.InlineKeyboardButton(text=text_constants.NEXT_PAGE, callback_data="next_page_users"))
            keyboard = telebot.types.InlineKeyboardMarkup(row_width=len(buttons_arr))
            keyboard.add(buttons_arr[0], buttons_arr[1])
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                              text=message_text_from_bot, reply_markup=keyboard, parse_mode="MARKDOWN")
    if str(call.data).startswith("user") and (user_info["is_admin"] or call.from_user.id in config.MAIN_ADMINS):
        if call.data == "user_ban" and int(call.message.text.split("Telegram id:")[1].split()[0]):
            object_for_update_user = {"user_id": int(call.message.text.split("Telegram id:")[1].split()[0]),
                                      "is_banned": True}
            if int(call.message.text.split("Telegram id:")[1].split()[0]) not in config.MAIN_ADMINS:
                db_object.update_userinfo_for_admin_by_object(object_for_update_user)
            else:
                if bot_settings["is_logging_chat"]:
                    log_message(user_id=call.from_user.id, message=message_text_from_bot, is_from_user=False)
                del_user_from_checking_arr(call.from_user.id)
                db_object.close_connection()
                bot.answer_callback_query(str(call.id))
                return 0
        if call.data == "user_unban":
            object_for_update_user = {"user_id": int(call.message.text.split("Telegram id:")[1].split()[0]),
                                      "is_banned": False}
            db_object.update_userinfo_for_admin_by_object(object_for_update_user)
        if call.data == "user_takeaway_admin":
            object_for_update_user = {"user_id": int(call.message.text.split("Telegram id:")[1].split()[0]),
                                      "is_admin": False}
            db_object.update_userinfo_for_admin_by_object(object_for_update_user)
        if call.data == "user_give_admin":
            object_for_update_user = {"user_id": int(call.message.text.split("Telegram id:")[1].split()[0]),
                                      "is_admin": True}
            db_object.update_userinfo_for_admin_by_object(object_for_update_user)
        if call.data == "user_takeaway_moderator":
            object_for_update_user = {"user_id": int(call.message.text.split("Telegram id:")[1].split()[0]),
                                      "is_moderator": False}
            db_object.update_userinfo_for_admin_by_object(object_for_update_user)
        if call.data == "user_give_moderator":
            object_for_update_user = {"user_id": int(call.message.text.split("Telegram id:")[1].split()[0]),
                                      "is_moderator": True}
            db_object.update_userinfo_for_admin_by_object(object_for_update_user)
        viewing_user_id = int(call.message.text.split("Telegram id:")[1].split()[0])
        viewing_user_info = db_object.check_user_is_registered(viewing_user_id)
        message_text_from_bot = gen_message_for_user_profile(viewing_user_id, viewing_user_info)
        bot.edit_message_text(chat_id=call.from_user.id, message_id=call.message.message_id, text=message_text_from_bot,
                              parse_mode="MARKDOWN",
                              reply_markup=get_user_profile_keyboard(user_info, viewing_user_info))
    if str(call.data).startswith("chat_logs") and (
            user_info["is_admin"] or user_info["is_moderator"] or call.from_user.id in config.MAIN_ADMINS):
        viewing_user_id = int(call.message.text.split("Telegram id:")[1].split()[0])
        if call.data == "chat_logs_view":
            try:
                message_text_from_bot = f"FILE: ./logs_chat/{viewing_user_id}.txt"
                with open(f"./logs_chat/{viewing_user_id}.txt") as tmp_f:
                    bot.send_document(call.from_user.id, data=tmp_f)
            except:
                message_text_from_bot = text_constants.ERROR_SEND_FILE
                bot.send_message(call.from_user.id, message_text_from_bot, parse_mode="MARKDOWN")
        elif call.data == "chat_logs_clear":
            message_text_from_bot = f"CLEARED FILE: ./logs_chat/{viewing_user_id}.txt"
            with open(f"./logs_chat/{viewing_user_id}.txt", "w") as tmp_f:
                tmp_f.write("")
    """END OF PROCESSING QUERIES"""
    if bot_settings["is_logging_chat"]:
        log_message(user_id=call.from_user.id, message=message_text_from_bot, is_from_user=False)
    del_user_from_checking_arr(call.from_user.id)
    db_object.close_connection()
    bot.answer_callback_query(str(call.id))


@bot.message_handler(content_types=["photo"])
def photo_messages(message: telebot.types.Message):
    if not check_user_status(message.from_user.id): return 0
    post_status_writing(message.from_user.id)
    db_object = DataBase()
    bot_settings = get_server_info(db_object)
    if not bot_settings["is_enabled_for_users_bot"] and message.from_user.id not in config.MAIN_ADMINS:
        bot.send_message(message.chat.id, text_constants.BOT_STATUS_MESSAGE)
        del_user_from_checking_arr(message.from_user.id)
        db_object.close_connection()
        return 0

    if bot_settings["is_logging_chat"]:
        log_message(user_id=message.chat.id, message=message.text, is_from_user=True)
    user_info = get_and_update_user_info(db_object, message.from_user.id, message.from_user.username,
                                         message.from_user.first_name, message.from_user.last_name)
    if user_info["is_banned"]:
        del_user_from_checking_arr(message.from_user.id)
        db_object.close_connection()
        return 0
    message_text_from_bot = ""
    """START OF PROCESSING MESSAGES"""
    photo_id = message.photo[-1].file_id
    if message.reply_to_message is not None \
            and message.reply_to_message.text == text_constants.MESSAGE_REPLY_ON_THIS_FOR_SEND_MESSAGE_FOR_ALL_WITHOUT_FORMAT \
            and (user_info["is_admin"] or message.from_user.id in config.MAIN_ADMINS):
        message_text_for_send = message.caption
        errors = 0
        counter = 0
        for user in db_object.get_all_users():
            try:
                bot.send_photo(chat_id=user["user_id"], photo=photo_id, caption=message_text_for_send,
                               parse_mode="MARKDOWN")
            except:
                errors += 1
            counter += 1
        message_text_from_bot = f"Сообщение отправлено пользователям ({counter - errors}/{counter})"
        bot.send_message(message.from_user.id, message_text_from_bot,
                         reply_markup=get_admin_menu(user_info, bot_settings))
    """END OF PROCESSING MESSAGES"""
    if bot_settings["is_logging_chat"]:
        log_message(user_id=message.chat.id, message=message_text_from_bot, is_from_user=False)
    del_user_from_checking_arr(message.from_user.id)
    db_object.close_connection()


while True:
    bot.polling()
