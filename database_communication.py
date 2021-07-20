import pymongo
import config
import random
import string
from datetime import datetime, timedelta


def generate_alphanum_random_string(length):
    letters_and_digits = string.ascii_letters + string.digits
    rand_string = ''.join(random.sample(letters_and_digits, length))
    return rand_string


class DataBase:
    def __init__(self):
        self.client = pymongo.MongoClient(config.DB_CONNECT_LINK)
        self.db = self.client.TelegramBotBS

    def update_userinfo_user(self, user_id, username, first_name, last_name):
        user_data = self.check_user_is_registered(user_id)
        if user_data:
            user = {
                "user_id": user_id,
                "username": username,
                "first_name": first_name,
                "last_name": last_name,
                "last_activity": str((datetime.now() + timedelta(hours=config.TIME_OFFSET)).strftime("%d.%m.%Y %H:%M"))
            }
        else:
            user = {
                "user_id": user_id,
                "username": username,
                "first_name": first_name,
                "last_name": last_name,
                "reg_date": str((datetime.now() + timedelta(hours=config.TIME_OFFSET)).strftime("%d.%m.%Y %H:%M")),
                "last_activity": str((datetime.now() + timedelta(hours=config.TIME_OFFSET)).strftime("%d.%m.%Y %H:%M")),
                "is_banned": False,
                "is_admin": False,
                "is_moderator": False
            }
            user_data = user
        self.db.users.update_one({"user_id": user_id}, {'$set': user}, upsert=True)
        return user_data

    def update_userinfo_for_admin_by_object(self, data):
        self.db.users.update_one({"user_id": data["user_id"]}, {'$set': data}, upsert=True)

    def get_all_users(self):
        cursor = self.db.users.find()
        return list(cursor)

    def check_user_is_registered(self, user_id):
        cursor = self.db.users.find_one({"user_id": user_id})
        if cursor is not None and cursor:
            return cursor
        else:
            return False

    def get_bot_settings(self):
        cursor = list(self.db.bot_settings.find())[0]
        return cursor

    def set_bot_settings(self, is_enabled_for_users_bot, is_logging_chat):
        settings = {
            "is_enabled_for_users_bot": is_enabled_for_users_bot,
            "is_logging_chat": is_logging_chat
        }
        self.db.bot_settings.update_one({"setting_id": 0}, {'$set': settings}, upsert=True)

    def configurate_db(self):
        db.set_bot_settings(True, True)

    def close_connection(self):
        self.client.close()



if __name__ == "__main__":
    db = DataBase()
    db.set_bot_settings(True, True)
    """product_id = db.insert_product(category="Пятёрочка", product_name="100-200",
                                   image_id="AgACAgIAAxkBAAIG8WDscBQzfZldARgj_aLy-9VkE_eGAAIKuDEbLzVgS0YivakP3UtFAQADAgADeAADIAQ",
                                   text="Промокод пятёрочки на сумму от 100 до 200 бонусов", is_service=False, added_by_id=391257848,
                                   is_individual=False, price=60, amount=14, is_eproduct=True, is_display=False)["product_id"]"""
