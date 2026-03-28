# https://github.com/odysseusmax/animated-lamp/blob/master/bot/database/database.py
import motor.motor_asyncio
from info import DATABASE_NAME, DATABASE_URI, IMDB, IMDB_TEMPLATE, MELCOW_NEW_USERS, P_TTI_SHOW_OFF, SINGLE_BUTTON, SPELL_CHECK_REPLY, PROTECT_CONTENT, AUTO_DELETE, MAX_BTN, AUTO_FFILTER, SHORTLINK_API, SHORTLINK_URL, IS_SHORTLINK, TUTORIAL, IS_TUTORIAL
import datetime
import pytz

class Database:

    def __init__(self, uri, database_name):
        self._client = motor.motor_asyncio.AsyncIOMotorClient(uri)
        self.db = self._client[database_name]
        self.col = self.db.users
        self.grp = self.db.groups
        self.users = self.db.uersz
        self.req = self.db.requests
        self.redeem_codes = self.db.redeem_codes

    async def find_join_req(self, id):
        return bool(await self.req.find_one({'id': id}))

    async def add_join_req(self, id):
        await self.req.insert_one({'id': id})
    async def del_join_req(self):
        await self.req.drop()

    def new_user(self, id, name):
        return dict(
            id = id,
            name = name,
            ban_status=dict(
                is_banned=False,
                ban_reason="",
            ),
        )


    def new_group(self, id, title):
        return dict(
            id = id,
            title = title,
            chat_status=dict(
                is_disabled=False,
                reason="",
            ),
        )

    async def add_user(self, id, name):
        user = self.new_user(id, name)
        await self.col.insert_one(user)

    async def is_user_exist(self, id):
        user = await self.col.find_one({'id':int(id)})
        return bool(user)

    async def total_users_count(self):
        count = await self.col.count_documents({})
        return count

    async def remove_ban(self, id):
        ban_status = dict(
            is_banned=False,
            ban_reason=''
        )
        await self.col.update_one({'id': id}, {'$set': {'ban_status': ban_status}})

    async def ban_user(self, user_id, ban_reason="No Reason"):
        ban_status = dict(
            is_banned=True,
            ban_reason=ban_reason
        )
        await self.col.update_one({'id': user_id}, {'$set': {'ban_status': ban_status}})

    async def get_ban_status(self, id):
        default = dict(
            is_banned=False,
            ban_reason=''
        )
        user = await self.col.find_one({'id':int(id)})
        if not user:
            return default
        return user.get('ban_status', default)

    async def get_all_users(self):
        return self.col.find({})


    async def delete_user(self, user_id):
        await self.col.delete_many({'id': int(user_id)})


    async def get_banned(self):
        users = self.col.find({'ban_status.is_banned': True})
        chats = self.grp.find({'chat_status.is_disabled': True})
        b_chats = [chat['id'] async for chat in chats]
        b_users = [user['id'] async for user in users]
        return b_users, b_chats



    async def add_chat(self, chat, title):
        chat = self.new_group(chat, title)
        await self.grp.insert_one(chat)


    async def get_chat(self, chat):
        chat = await self.grp.find_one({'id':int(chat)})
        return False if not chat else chat.get('chat_status')


    async def re_enable_chat(self, id):
        chat_status=dict(
            is_disabled=False,
            reason="",
            )
        await self.grp.update_one({'id': int(id)}, {'$set': {'chat_status': chat_status}})

    async def update_settings(self, id, settings):
        await self.grp.update_one({'id': int(id)}, {'$set': {'settings': settings}})


    async def get_settings(self, id):
        default = {
            'button': SINGLE_BUTTON,
            'botpm': P_TTI_SHOW_OFF,
            'file_secure': PROTECT_CONTENT,
            'imdb': IMDB,
            'spell_check': SPELL_CHECK_REPLY,
            'welcome': MELCOW_NEW_USERS,
            'auto_delete': AUTO_DELETE,
            'auto_ffilter': AUTO_FFILTER,
            'max_btn': MAX_BTN,
            'template': IMDB_TEMPLATE,
            'shortlink': SHORTLINK_URL,
            'shortlink_api': SHORTLINK_API,
            'is_shortlink': IS_SHORTLINK,
            'tutorial': TUTORIAL,
            'is_tutorial': IS_TUTORIAL
        }
        chat = await self.grp.find_one({'id':int(id)})
        if chat:
            return chat.get('settings', default)
        return default


    async def disable_chat(self, chat, reason="No Reason"):
        chat_status=dict(
            is_disabled=True,
            reason=reason,
            )
        await self.grp.update_one({'id': int(chat)}, {'$set': {'chat_status': chat_status}})


    async def total_chat_count(self):
        count = await self.grp.count_documents({})
        return count


    async def get_all_chats(self):
        return self.grp.find({})


    async def get_db_size(self):
        return (await self.db.command("dbstats"))['dataSize']

    async def get_user(self, user_id):
        user_data = await self.users.find_one({"id": user_id})
        return user_data
    async def update_user(self, user_data):
        await self.users.update_one({"id": user_data["id"]}, {"$set": user_data}, upsert=True)

    async def has_premium_access(self, user_id):
        """Check if user has active premium access (not expired)"""
        user_data = await self.get_user(user_id)
        if user_data:
            expiry_time = user_data.get("expiry_time")
            if expiry_time is None:
                return False
            elif isinstance(expiry_time, datetime.datetime) and datetime.datetime.now() <= expiry_time:
                return True
            # Note: We don't clear expiry_time here anymore
            # Let the notification system handle expired users properly
        return False

    async def is_premium_expired(self, user_id):
        """Check if user's premium has expired (for notification purposes)"""
        user_data = await self.get_user(user_id)
        if user_data:
            expiry_time = user_data.get("expiry_time")
            if expiry_time is None:
                return False  # Never had premium or lifetime
            elif isinstance(expiry_time, datetime.datetime) and datetime.datetime.now() > expiry_time:
                return True
        return False

    async def clear_expired_premium(self, user_id):
        """Clear premium access after notification has been sent"""
        return await self.update_one(
            {"id": user_id}, {"$set": {"expiry_time": None}}
        )

    async def update_user(self, user_data):
        await self.users.update_one({"id": user_data["id"]}, {"$set": user_data}, upsert=True)

    async def update_one(self, filter_query, update_data):
        try:
            result = await self.users.update_one(filter_query, update_data)
            return result.matched_count == 1
        except Exception as e:
            print(f"Error updating document: {e}")
            return False

    async def get_expired(self, current_time):
        expired_users = []
        if data := self.users.find({"expiry_time": {"$lt": current_time}}):
            async for user in data:
                expired_users.append(user)
        return expired_users

    async def remove_premium_access(self, user_id):
        return await self.update_one(
            {"id": user_id}, {"$set": {"expiry_time": None}}
        )

    async def check_trial_status(self, user_id):
        user_data = await self.get_user(user_id)
        if user_data:
            return user_data.get("has_free_trial", False)
        return False

    async def give_free_trial(self, user_id):
        user_id = user_id
        seconds = 5*60         
        expiry_time = datetime.datetime.now() + datetime.timedelta(seconds=seconds)
        user_data = {"id": user_id, "expiry_time": expiry_time, "has_free_trial": True}
        await self.users.update_one({"id": user_id}, {"$set": user_data}, upsert=True)

    # ==================== REDEEM CODE METHODS ====================

    async def add_redeem_code(self, redeem_data: dict):
        """Add a new redeem code to the database"""
        try:
            await self.redeem_codes.insert_one(redeem_data)
            return True
        except Exception as e:
            print(f"Error adding redeem code: {e}")
            return False

    async def get_redeem_code(self, code: str):
        """Get redeem code data by code - also cleans up expired codes first"""
        try:
            await self.delete_expired_redeem_codes()
            return await self.redeem_codes.find_one({"code": code})
        except Exception as e:
            print(f"Error getting redeem code: {e}")
            return None

    async def update_redeem_code(self, code: str, update_data: dict):
        """Update redeem code data"""
        try:
            await self.redeem_codes.update_one(
                {"code": code},
                {"$set": update_data}
            )
            return True
        except Exception as e:
            print(f"Error updating redeem code: {e}")
            return False

    async def delete_redeem_code(self, code: str):
        """Delete a redeem code from the database"""
        try:
            await self.redeem_codes.delete_one({"code": code})
            return True
        except Exception as e:
            print(f"Error deleting redeem code: {e}")
            return False

    async def delete_expired_redeem_codes(self):
        """Delete redeem codes whose expiry_time has passed (expired premium)"""
        try:
            current_time = datetime.datetime.now()
            result = await self.redeem_codes.delete_many({
                "expiry_time": {"$lt": current_time}
            })
            if result.deleted_count > 0:
                print(f"[Redeem Codes] Deleted {result.deleted_count} expired redeem code(s)")
            return result.deleted_count
        except Exception as e:
            print(f"Error deleting expired redeem codes: {e}")
            return 0

    async def get_all_redeem_codes(self, status_filter: str = None):
        """Get all non-expired redeem codes with optional status filter"""
        try:
            await self.delete_expired_redeem_codes()

            current_time = datetime.datetime.now()
            query = {
                "$or": [
                    {"expiry_time": None},
                    {"expiry_time": {"$gte": current_time}}
                ]
            }

            if status_filter == "redeemed":
                query["is_redeemed"] = True
            elif status_filter == "available":
                query["is_redeemed"] = False

            cursor = self.redeem_codes.find(query)
            return cursor
        except Exception as e:
            print(f"Error getting redeem codes: {e}")
            return []

    async def get_redeem_stats(self):
        """Get statistics about non-expired redeem codes only"""
        try:
            await self.delete_expired_redeem_codes()

            current_time = datetime.datetime.now()
            base_query = {
                "$or": [
                    {"expiry_time": None},
                    {"expiry_time": {"$gte": current_time}}
                ]
            }

            total = await self.redeem_codes.count_documents(base_query)
            redeemed = await self.redeem_codes.count_documents({**base_query, "is_redeemed": True})
            available = await self.redeem_codes.count_documents({**base_query, "is_redeemed": False})
            return {
                "total": total,
                "redeemed": redeemed,
                "available": available
            }
        except Exception as e:
            print(f"Error getting redeem stats: {e}")
            return {"total": 0, "redeemed": 0, "available": 0}

    async def get_all_premium_users(self):
        """Get all users with premium access"""
        try:
            return self.users.find({"expiry_time": {"$ne": None}})
        except Exception as e:
            print(f"Error getting premium users: {e}")
            return []

    # ==================== EXPIRY NOTIFICATION METHODS ====================

    async def get_expired_users_not_notified(self):
        """Get all users whose premium has expired but haven't been notified yet"""
        try:
            current_time = datetime.datetime.now()
            query = {
                "expiry_time": {"$lt": current_time},
                "$or": [
                    {"expiry_notified": {"$exists": False}},
                    {"expiry_notified": False}
                ]
            }
            return self.users.find(query)
        except Exception as e:
            print(f"Error getting expired users: {e}")
            return []

    async def mark_expiry_notified(self, user_id):
        """Mark that a user has been notified about premium expiration"""
        try:
            await self.users.update_one(
                {"id": user_id},
                {"$set": {"expiry_notified": True, "expiry_notified_at": datetime.datetime.now()}}
            )
            return True
        except Exception as e:
            print(f"Error marking expiry notified: {e}")
            return False

    async def reset_expiry_notification(self, user_id):
        """Reset notification status when user gets new premium"""
        try:
            await self.users.update_one(
                {"id": user_id},
                {"$set": {"expiry_notified": False, "expiry_notified_at": None}}
            )
            return True
        except Exception as e:
            print(f"Error resetting expiry notification: {e}")
            return False

db = Database(DATABASE_URI, DATABASE_NAME)
