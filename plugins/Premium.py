# REDEEM CODE FEATURE ADDED - FULLY TRACKED
# EXPIRY NOTIFICATION FEATURE ADDED - AUTOMATIC
# AUTO-DELETE MESSAGES FEATURE ADDED

from datetime import timedelta
import pytz
import datetime, time
import random
import string
import asyncio
from Script import script
from info import ADMINS, PREMIUM_LOGS
from utils import get_seconds
from database.users_chats_db import db
from pyrogram import Client, filters
from pyrogram.errors.exceptions.bad_request_400 import MessageTooLong
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup

# ==================== CONFIGURATION ====================

# Auto-delete timer in seconds (set to 0 to disable auto-delete)
AUTO_DELETE_TIMER = 60  # Messages will be deleted after set timer

# ==================== HELPER FUNCTIONS ====================

async def auto_delete_message(message, reply_msg=None, timer=None):
    """Auto-delete command message and reply after specified timer"""
    if timer is None:
        timer = AUTO_DELETE_TIMER

    if timer <= 0:
        return  # Auto-delete is disabled

    await asyncio.sleep(timer)

    try:
        # Delete the command message
        await message.delete()
    except Exception as e:
        pass  # Message might already be deleted

    try:
        # Delete the reply message if provided
        if reply_msg:
            await reply_msg.delete()
    except Exception as e:
        pass  # Message might already be deleted


async def delete_redeem_code_message(client, chat_id, code):
    """Delete the message containing the redeem code from chat history"""
    try:
        # Search for messages containing the redeem code in the chat
        # This will try to delete any message containing the code
        async for msg in client.search_messages(chat_id, query=code, limit=10):
            try:
                await msg.delete()
            except:
                pass
    except Exception as e:
        print(f"[Redeem Code Cleanup] Could not delete code message: {e}")


# ==================== REDEEM CODE FEATURE ====================

def generate_redeem_code():
    """Generate an80-digit alphanumeric redeem code"""
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))

@Client.on_message(filters.command("gen_code") & filters.user(ADMINS))
async def generate_redeem_code_handler(client, message):
    """Admin command to generate redeem codes for premium access"""
    reply_msg = None

    if len(message.command) < 3:
        reply_msg = await message.reply_text(
            "**Uꜱᴀɢᴇ:** `/gen_code <duration> <quantity>`\n\n"
            "**Exᴀᴍᴘʟᴇꜱ:**\n"
            "`/gen_code 1day 5` - Gᴇɴᴇʀᴀᴛᴇ 5 Cᴏᴅᴇꜱ Fᴏʀ 1 Dᴀʏ\n"
            "`/gen_code 1month 10` - Gᴇɴᴇʀᴀᴛᴇ 10 Cᴏᴅᴇꜱ Fᴏʀ 1 Mᴏɴᴛʜ\n"
            "`/gen_code 1year 3` - Gᴇɴᴇʀᴀᴛᴇ 3 Cᴏᴅᴇꜱ Fᴏʀ 1 Yᴇᴀʀ\n\n"
            "**Sᴜᴘᴘᴏʀᴛᴇᴅ Dᴜʀᴀᴛɪᴏɴꜱ:** day, days, week, weeks, month, months, year, years"
        )
        asyncio.create_task(auto_delete_message(message, reply_msg))
        return

    duration_str = message.command[1].lower()
    try:
        quantity = int(message.command[2])
        if quantity < 1 or quantity > 50:
            reply_msg = await message.reply_text("❌ Qᴜᴀɴᴛɪᴛʏ Mᴜꜱᴛ Bᴇ Bᴇᴛᴡᴇᴇɴ 1 Aɴᴅ 50!")
            asyncio.create_task(auto_delete_message(message, reply_msg))
            return
    except ValueError:
        reply_msg = await message.reply_text("❌ Qᴜᴀɴᴛɪᴛʏ ɪɴᴠᴀʟɪᴅ! ᴘʟᴇᴀꜱᴇ ᴇɴᴛᴇʀ ᴀ ɴᴜᴍʙᴇʀ.")
        asyncio.create_task(auto_delete_message(message, reply_msg))
        return

    # Handle lifetime separately
    if duration_str in ["lifetime", "life"]:
        seconds = -1  # Special value for lifetime
        duration_display = "Lifetime"
    else:
        seconds = await get_seconds(duration_str)
        if seconds <= 0:
            reply_msg = await message.reply_text("❌ Invalid duration format!")
            asyncio.create_task(auto_delete_message(message, reply_msg))
            return
        duration_display = duration_str

    # Generate codes
    generated_codes = []
    time_zone = datetime.datetime.now(pytz.timezone("Asia/Kolkata"))
    generated_time = time_zone.strftime("%d-%m-%Y %I:%M:%S %p")

    for _ in range(quantity):
        code = generate_redeem_code()
        redeem_data = {
            "code": code,
            "duration": duration_str,
            "seconds": seconds,
            "generated_by": message.from_user.id,
            "generated_by_name": message.from_user.mention,
            "generated_at": datetime.datetime.now(),
            "is_redeemed": False,
            "redeemed_by": None,
            "redeemed_at": None,
            "expiry_time": None
        }
        await db.add_redeem_code(redeem_data)
        generated_codes.append(code)

    # Create response message
    codes_text = "\n".join([f"`{code}`" for code in generated_codes])
    response = (
        f"✅ **Rᴇᴅᴇᴇᴍ Cᴏᴅᴇꜱ Gᴇɴᴇʀᴀᴛᴇᴅ!**\n\n"
        f"📊 **Qᴜᴀɴᴛɪᴛʏ :** {quantity}\n"
        f"⏰ **Dᴜʀᴀᴛɪᴏɴ :** {duration_display}\n"
        f"🕐 **Gᴇɴᴇʀᴀᴛᴇᴅ Aᴛ :** {generated_time}\n\n"
        f"📋 **Cᴏᴅᴇꜱ :**\n{codes_text}\n\n"
        f"🤖 **Bᴏᴛ Uꜱᴇʀɴᴀᴍᴇ :** <b><a href='https://t.me/Your_Movie_Search_Bot'>Rᴇᴅᴇᴇᴍ Hᴇʀᴇ</a></b>\n"
        f"💡 **Sᴛᴀʀᴛ Tʜᴇ Bᴏᴛ :** `/redeem`\n\n"
        f"✨ **Eɴᴊᴏʏ ʏᴏᴜʀ ᴘʀᴇᴍɪᴜᴍ ᴀᴄᴄᴇꜱꜱ!**"
    )

    # Send as file if too many codes
    if len(response) > 4000:
        separator = "=" * 50
        file_content = f"Rᴇᴅᴇᴇᴍ Cᴏᴅᴇꜱ Gᴇɴᴇʀᴀᴛᴇᴅ\n{separator}\n"
        file_content += f"Dᴜʀᴀᴛɪᴏɴ: {duration_display}\n"
        file_content += f"Qᴜᴀɴᴛɪᴛʏ: {quantity}\n"
        file_content += f"Gᴇɴᴇʀᴀᴛᴇᴅ Aᴛ: {generated_time}\n"
        file_content += f"{separator}\n\n"
        file_content += "Codes:\n" + "\n".join(generated_codes)

        with open('redeem_codes.txt', 'w') as f:
            f.write(file_content)

        reply_msg = await message.reply_document(
            'redeem_codes.txt',
            caption=f"✅ Gᴇɴᴇʀᴀᴛᴇᴅ {quantity} ᴄᴏᴅᴇꜱ ꜰᴏʀ {duration_display}"
        )
    else:
        reply_msg = await message.reply_text(response)

    # Log to premium logs
    await client.send_message(
        PREMIUM_LOGS,
        f"#Nᴇᴡ_ʀᴇᴅᴇᴇᴍ_ᴄᴏᴅᴇꜱ_ɢᴇɴᴇʀᴀᴛᴇᴅ\n\n"
        f"🆔 **Aᴅᴍɪɴ ɪᴅ:** `{message.from_user.id}`\n"
        f"📊 **Qᴜᴀɴᴛɪᴛʏ:** {quantity}\n"
        f"⏰ **Dᴜʀᴀᴛɪᴏɴ:** {duration_display}\n"
        f"🕐 **Tɪᴍᴇ:** {generated_time}"
    )

    # Auto-delete messages
    asyncio.create_task(auto_delete_message(message, reply_msg))

@Client.on_message(filters.command("redeem"))
async def redeem_code_handler(client, message):
    """User command to redeem a premium code"""
    reply_msg = None

    if len(message.command) != 2:
        reply_msg = await message.reply_text(
            "**Uꜱᴀɢᴇ:** `/redeem <code>`\n\n"
            "Exᴀᴍᴘʟᴇ: `/redeem ABCDE12345`\n\n"
            "Eɴᴛᴇʀ Yᴏᴜʀ Rᴇᴅᴇᴇᴍ Cᴏᴅᴇ Hᴇʀᴇ Tᴏ Gᴇᴛ Pʀᴇᴍɪᴜᴍ Aᴄᴄᴇꜱꜱ!"
        )
        asyncio.create_task(auto_delete_message(message, reply_msg))
        return

    code = message.command[1].upper().strip()
    user_id = message.from_user.id
    user = message.from_user.mention

    # Validate code format
    if len(code) != 8 or not all(c in string.ascii_uppercase + string.digits for c in code):
        reply_msg = await message.reply_text("❌ Iɴᴠᴀʟɪᴅ ᴄᴏᴅᴇ ꜰᴏʀᴍᴀᴛ! ᴄᴏᴅᴇ ᴍᴜꜱᴛ ʙᴇ 8 ᴄʜᴀʀᴀᴄᴛᴇʀꜱ (ᴀ-ᴢ, 0-9).")
        asyncio.create_task(auto_delete_message(message, reply_msg))
        return

    # Check if user already has premium
    if await db.has_premium_access(user_id):
        data = await db.get_user(user_id)
        expiry = data.get("expiry_time") if data else None
        if expiry:
            expiry_str = expiry.astimezone(pytz.timezone("Asia/Kolkata")).strftime("%d-%m-%Y %I:%M:%S %p")
            reply_msg = await message.reply_text(
                f"⚠️ **Yᴏᴜ ᴀʟʀᴇᴀᴅʏ ʜᴀᴠᴇ ᴀɴ ᴀᴄᴛɪᴠᴇ ᴘʀᴇᴍɪᴜᴍ ᴘʟᴀɴ!**\n\n"
                f"⏰ Exᴘɪʀᴇꜱ ᴏɴ: `{expiry_str}`\n\n"
                f"Uꜱᴇ `/myplan` ᴛᴏ ᴄʜᴇᴄᴋ ʏᴏᴜʀ ᴘʟᴀɴ ᴅᴇᴛᴀɪʟꜱ."
            )
        else:
            reply_msg = await message.reply_text(
                f"⚠️ **Yᴏᴜ ᴀʟʀᴇᴀᴅʏ ʜᴀᴠᴇ ʟɪꜰᴇᴛɪᴍᴇ ᴘʀᴇᴍɪᴜᴍ ᴀᴄᴄᴇꜱꜱ!**\n\n"
                f"Uꜱᴇ `/myplan` ᴛᴏ ᴄʜᴇᴄᴋ ʏᴏᴜʀ ᴘʟᴀɴ ᴅᴇᴛᴀɪʟꜱ."
            )
        asyncio.create_task(auto_delete_message(message, reply_msg))
        return

    # Verify code in database
    redeem_data = await db.get_redeem_code(code)

    if not redeem_data:
        reply_msg = await message.reply_text("❌ Iɴᴠᴀʟɪᴅ ʀᴇᴅᴇᴇᴍ ᴄᴏᴅᴇ! ᴘʟᴇᴀꜱᴇ ᴄʜᴇᴄᴋ ᴀɴᴅ ᴛʀʏ ᴀɢᴀɪɴ.")
        asyncio.create_task(auto_delete_message(message, reply_msg))
        return

    if redeem_data.get("is_redeemed", False):
        redeemed_by = redeem_data.get("redeemed_by")
        if redeemed_by == user_id:
            reply_msg = await message.reply_text("⚠️ Yᴏᴜ ʜᴀᴠᴇ ᴀʟʀᴇᴀᴅʏ ʀᴇᴅᴇᴇᴍᴇᴅ ᴛʜɪꜱ ᴄᴏᴅᴇ!")
        else:
            reply_msg = await message.reply_text("❌ Tʜɪꜱ ᴄᴏᴅᴇ ʜᴀꜱ ᴀʟʀᴇᴀᴅʏ ʙᴇᴇɴ ʀᴇᴅᴇᴇᴍᴇᴅ ʙʏ ꜱᴏᴍᴇᴏɴᴇ ᴇʟꜱᴇ!")
        asyncio.create_task(auto_delete_message(message, reply_msg))
        return

    # Redeem the code
    time_zone = datetime.datetime.now(pytz.timezone("Asia/Kolkata"))
    current_time = time_zone.strftime("%d-%m-%Y\n⏱️ Jᴏɪɴɪɴɢ ᴛɪᴍᴇ : %I:%M:%S %p")
    redeemed_at = datetime.datetime.now()

    seconds = redeem_data.get("seconds", 0)
    duration = redeem_data.get("duration", "Unknown")

    # Calculate expiry
    if seconds == -1:  # Lifetime
        expiry_time = None
        expiry_str = "Lifetime"
        time_left_str = "Lifetime"
    else:
        expiry_time = datetime.datetime.now() + datetime.timedelta(seconds=seconds)
        expiry_ist = expiry_time.astimezone(pytz.timezone("Asia/Kolkata"))
        expiry_str = expiry_ist.strftime("%d-%m-%Y\n⏱️ Exᴘɪʀʏ ᴛɪᴍᴇ : %I:%M:%S %p")
        time_left_str = duration

    # Update user premium data - also reset expiry notification status
    user_data = {
        "id": user_id,
        "expiry_time": expiry_time,
        "redeemed_code": code,
        "premium_source": "redeem_code",
        "expiry_notified": False,
        "expiry_notified_at": None
    }
    await db.update_user(user_data)

    # Update redeem code data
    await db.update_redeem_code(code, {
        "is_redeemed": True,
        "redeemed_by": user_id,
        "redeemed_by_name": message.from_user.mention,
        "redeemed_at": redeemed_at,
        "expiry_time": expiry_time
    })

    # Send success message to user
    reply_msg = await message.reply_text(
        f"🎉 **Cᴏᴅᴇ Rᴇᴅᴇᴇᴍᴇᴅ Sᴜᴄᴄᴇꜱꜱꜰᴜʟʟʏ!**\n\n"
        f"👤 **Uꜱᴇʀ:** {user}\n"
        f"⚡ **Uꜱᴇʀ ɪᴅ:** `{user_id}`\n"
        f"🎟️ **Rᴇᴅᴇᴇᴍ ᴄᴏᴅᴇ:** `{code}`\n"
        f"⏰ **Dᴜʀᴀᴛɪᴏɴ:** {duration}\n"
        f"⏳ **Jᴏɪɴɪɴɢ ᴛɪᴍᴇ:** {current_time}\n"
        f"⌛️ **Exᴘɪʀʏ ᴛɪᴍᴇ:** {expiry_str}\n\n"
        f"✨ Eɴᴊᴏʏ ʏᴏᴜʀ ᴘʀᴇᴍɪᴜᴍ ᴀᴄᴄᴇꜱꜱ!"
    )

    # Delete any messages containing the redeem code
    asyncio.create_task(delete_redeem_code_message(client, message.chat.id, code))

    # Log to premium logs
    await client.send_message(
        PREMIUM_LOGS,
        f"#Pʀᴇᴍɪᴜᴍ_ʀᴇᴅᴇᴇᴍᴇᴅ\n\n"
        f"👤 **Uꜱᴇʀ:** {user}\n"
        f"⚡ **Uꜱᴇʀ ɪᴅ:** `{user_id}`\n"
        f"🎟️ **Rᴇᴅᴇᴇᴍ ᴄᴏᴅᴇ:** `{code}`\n"
        f"⏰ **Dᴜʀᴀᴛɪᴏɴ:** {duration}\n"
        f"⏳ **Jᴏɪɴɪɴɢ ᴛɪᴍᴇ:** {current_time}\n"
        f"⌛️ **Exᴘɪʀʏ ᴛɪᴍᴇ:** {expiry_str}\n\n"
    )

    # Auto-delete messages
    asyncio.create_task(auto_delete_message(message, reply_msg))

@Client.on_message(filters.command("code_status") & filters.user(ADMINS))
async def redeem_status_handler(client, message):
    """Admin command to check status of redeem codes"""
    reply_msg = None

    if len(message.command) == 2:
        # Check specific code
        code = message.command[1].upper().strip()
        redeem_data = await db.get_redeem_code(code)

        if not redeem_data:
            reply_msg = await message.reply_text("❌ Cᴏᴅᴇ ɴᴏᴛ ꜰᴏᴜɴᴅ ɪɴ ᴅᴀᴛᴀʙᴀꜱᴇ!")
            asyncio.create_task(auto_delete_message(message, reply_msg))
            return

        status = "✅ Redeemed" if redeem_data.get("is_redeemed") else "⏳ Available"
        generated_at = redeem_data.get("generated_at")
        generated_at_str = generated_at.astimezone(pytz.timezone("Asia/Kolkata")).strftime("%d-%m-%Y %I:%M:%S %p") if generated_at else "Unknown"

        response = (
            f"📋 **Cᴏᴅᴇ ꜱᴛᴀᴛᴜꜱ: `{code}`**\n\n"
            f"📊 **Sᴛᴀᴛᴜꜱ:** {status}\n"
            f"⏰ **Dᴜʀᴀᴛɪᴏɴ:** {redeem_data.get('duration', 'Unknown')}\n"
            f"🕐 **Gᴇɴᴇʀᴀᴛᴇᴅ ᴀᴛ:** {generated_at_str}\n"
        )

        if redeem_data.get("is_redeemed"):
            redeemed_at = redeem_data.get("redeemed_at")
            redeemed_at_str = redeemed_at.astimezone(pytz.timezone("Asia/Kolkata")).strftime("%d-%m-%Y %I:%M:%S %p") if redeemed_at else "Unknown"
            expiry = redeem_data.get("expiry_time")
            expiry_str = expiry.astimezone(pytz.timezone("Asia/Kolkata")).strftime("%d-%m-%Y %I:%M:%S %p") if expiry else "Lifetime"

            response += (
                f"🙋 **Rᴇᴅᴇᴇᴍᴇᴅ ʙʏ:** {redeem_data.get('redeemed_by_name', 'Unknown')}\n"
                f"🆔 **Rᴇᴅᴇᴇᴍᴇʀ ɪᴅ:** `{redeem_data.get('redeemed_by', 'N/A')}`\n"
                f"🕐 **Rᴇᴅᴇᴇᴍᴇᴅ ᴀᴛ:** {redeemed_at_str}\n"
                f"⌛️ **Exᴘɪʀᴇᴅ ᴀᴛ:** {expiry_str}"
            )

        reply_msg = await message.reply_text(response)
    else:
        # Show overall statistics
        stats = await db.get_redeem_stats()
        total = stats.get("total", 0)
        redeemed = stats.get("redeemed", 0)
        available = stats.get("available", 0)

        reply_msg = await message.reply_text(
            f"📊 **Rᴇᴅᴇᴇᴍ ᴄᴏᴅᴇ ꜱᴛᴀᴛɪꜱᴛɪᴄꜱ**\n\n"
            f"📋 **Tᴏᴛᴀʟ ᴄᴏᴅᴇꜱ:** {total}\n"
            f"✅ **Tᴏᴛᴀʟ ʀᴇᴅᴇᴇᴍᴇᴅ:** {redeemed}\n"
            f"⏳ **Nᴏᴛ ʀᴇᴅᴇᴇᴍᴇᴅ:** {available}\n\n"
            f"Cʜᴇᴄᴋ ꜱᴘᴇᴄɪꜰɪᴄ ᴄᴏᴅᴇ: `/code_status <code>`"
        )

    # Auto-delete messages
    asyncio.create_task(auto_delete_message(message, reply_msg))

@Client.on_message(filters.command("code_list") & filters.user(ADMINS))
async def list_redeem_codes_handler(client, message):
    """Admin command to list all redeem codes"""
    status_filter = None
    if len(message.command) == 2:
        arg = message.command[1].lower()
        if arg in ["redeemed", "used"]:
            status_filter = "redeemed"
        elif arg in ["available", "unused"]:
            status_filter = "available"

    aa = await message.reply_text("<i>Fᴇᴛᴄʜɪɴɢ ʀᴇᴅᴇᴇᴍ ᴄᴏᴅᴇꜱ...</i>")

    codes = await db.get_all_redeem_codes(status_filter)

    if not codes:
        reply_msg = await aa.edit_text("Nᴏ ʀᴇᴅᴇᴇᴍ ᴄᴏᴅᴇꜱ ꜰᴏᴜɴᴅ!")
        asyncio.create_task(auto_delete_message(message, reply_msg))
        return

    new = f"🎟️ **Rᴇᴅᴇᴇᴍ Cᴏᴅᴇꜱ Lɪꜱᴛ**\n\n"
    code_count = 1

    async for code_data in codes:
        code = code_data.get("code", "Unknown")
        duration = code_data.get("duration", "Unknown")
        is_redeemed = code_data.get("is_redeemed", False)

        if is_redeemed:
            redeemed_by = code_data.get("redeemed_by_name", "Unknown")
            status = f"✅ Bʏ {redeemed_by}"
        else:
            status = "⏳ Aᴠᴀɪʟᴀʙʟᴇ"

        new += f"{code_count}. `{code}` | {duration} | {status}\n"
        code_count += 1

    try:
        reply_msg = await aa.edit_text(new)
    except MessageTooLong:
        with open('redeem_codes_list.txt', 'w+') as outfile:
            outfile.write(new)
        reply_msg = await message.reply_document('redeem_codes_list.txt', caption="Rᴇᴅᴇᴇᴍ Cᴏᴅᴇꜱ Lɪꜱᴛ:")

    # Auto-delete messages
    asyncio.create_task(auto_delete_message(message, reply_msg))

@Client.on_message(filters.command("del_code") & filters.user(ADMINS))
async def revoke_redeem_code_handler(client, message):
    """Admin command to revoke a redeem code"""
    reply_msg = None

    if len(message.command) != 2:
        reply_msg = await message.reply_text("**Uꜱᴀɢᴇ:** `/del_code <code>`\n\nDᴇʟᴇᴛᴇ ᴀ ʀᴇᴅᴇᴇᴍ ᴄᴏᴅᴇ.")
        asyncio.create_task(auto_delete_message(message, reply_msg))
        return

    code = message.command[1].upper().strip()
    redeem_data = await db.get_redeem_code(code)

    if not redeem_data:
        reply_msg = await message.reply_text("❌ Cᴏᴅᴇ ɴᴏᴛ ꜰᴏᴜɴᴅ ɪɴ ᴅᴀᴛᴀʙᴀꜱᴇ!")
        asyncio.create_task(auto_delete_message(message, reply_msg))
        return

    if redeem_data.get("is_redeemed", False):
        reply_msg = await message.reply_text("❌ Cᴀɴɴᴏᴛ ʀᴇᴠᴏᴋᴇ! ᴛʜɪꜱ ᴄᴏᴅᴇ ʜᴀꜱ ᴀʟʀᴇᴀᴅʏ ʙᴇᴇɴ ʀᴇᴅᴇᴇᴍᴇᴅ.")
        asyncio.create_task(auto_delete_message(message, reply_msg))
        return

    await db.delete_redeem_code(code)
    reply_msg = await message.reply_text(f"✅ Cᴏᴅᴇ `{code}` ʜᴀꜱ ʙᴇᴇɴ ᴅᴇʟᴇᴛᴇ ꜱᴜᴄᴄᴇꜱꜱꜰᴜʟʟʏ!")

    await client.send_message(
        PREMIUM_LOGS,
        f"#Rᴇᴅᴇᴇᴍ_ᴄᴏᴅᴇ_ᴅᴇʟᴇᴛᴇᴅ\n\n"
        f"🎟️ **Cᴏᴅᴇ:** `{code}`\n"
        f"👤 **Dᴇʟᴇᴛᴇᴅ ʙʏ:** {message.from_user.mention}\n"
        f"🕐 **Tɪᴍᴇ:** {datetime.datetime.now(pytz.timezone('Asia/Kolkata')).strftime('%d-%m-%Y %I:%M:%S %p')}"
    )

    # Auto-delete messages
    asyncio.create_task(auto_delete_message(message, reply_msg))

# ==================== AUTOMATIC EXPIRY NOTIFICATION FEATURE ====================

async def notify_expired_user(client, user_id, user_mention=None):
    """Send expiry notification to a user"""
    try:
        # Get user data
        user_data = await db.get_user(user_id)
        if not user_data:
            return False, "User not found"

        # Check if already notified
        if user_data.get("expiry_notified", False):
            # Already notified, clear the expired premium data
            await db.clear_expired_premium(user_id)
            return False, "Already notified"

        # Get premium source for personalized message
        premium_source = user_data.get("premium_source", "admin")
        redeemed_code = user_data.get("redeemed_code", None)

        # Build notification message
        if premium_source == "redeem_code" and redeemed_code:
            source_text = f"🎟️ **Rᴇᴅᴇᴇᴍᴇᴅ ᴄᴏᴅᴇ:** `{redeemed_code}`"
        else:
            source_text = "👑 **Pʀᴇᴍɪᴜᴍ ꜱᴏᴜʀᴄᴇ:** Aᴅᴍɪɴ ᴀᴅᴅᴇᴅ"

        notification_text = (
            f"⏰ **Pʀᴇᴍɪᴜᴍ Exᴘɪʀᴇᴅ Nᴏᴛɪꜰɪᴄᴀᴛɪᴏɴ** ⏰\n\n"
            f"👋 Hᴇʟʟᴏ {user_mention or 'User'},\n\n"
            f"💔 Yᴏᴜʀ ᴘʀᴇᴍɪᴜᴍ ᴀᴄᴄᴇꜱꜱ ʜᴀꜱ **Exᴘɪʀᴇᴅ**.\n\n"
            f"{source_text}\n\n"
            f"✨ **Wᴀɴᴛ ᴛᴏ ᴄᴏɴᴛɪɴᴜᴇ ᴘʀᴇᴍɪᴜᴍ?**\n"
            f"👑 Uꜱᴇ /plan ᴛᴏ ᴘᴜʀᴄʜᴀꜱᴇ ᴀ ɴᴇᴡ ᴘʟᴀɴ!\n\n"
            f"😊 **Tʜᴀɴᴋ ʏᴏᴜ ꜰᴏʀ ᴜꜱɪɴɢ ᴏᴜʀ ꜱᴇʀᴠɪᴄᴇ!**"
        )

        # Send notification to user
        await client.send_message(
            chat_id=user_id,
            text=notification_text,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("💸 Cʜᴇᴄᴋᴏᴜᴛ Pʀᴇᴍɪᴜᴍ Pʟᴀɴꜱ", callback_data="seeplans")],
                [InlineKeyboardButton("📞 Cᴏɴᴛᴀᴄᴛ Aᴅᴍɪɴ", url="https://t.me/sujan_chh")]
            ])
        )

        # Mark user as notified and clear expired premium data
        await db.mark_expiry_notified(user_id)
        await db.clear_expired_premium(user_id)

        return True, "Notification sent successfully"

    except Exception as e:
        return False, f"Error: {str(e)}"


async def auto_notify_expired_users(client):
    """Background task to automatically notify expired users"""
    await asyncio.sleep(60)  # Wait 60 seconds for bot to fully start

    while True:
        try:
            # Get all expired users who haven't been notified
            expired_users = await db.get_expired_users_not_notified()

            notified_count = 0
            failed_count = 0

            async for user_data in expired_users:
                user_id = user_data.get("id")
                try:
                    # Try to get user info for mention
                    try:
                        user = await client.get_users(user_id)
                        user_mention = user.mention
                    except:
                        user_mention = f"User {user_id}"

                    success, result = await notify_expired_user(client, user_id, user_mention)
                    if success:
                        notified_count += 1
                    else:
                        failed_count += 1

                except Exception as e:
                    failed_count += 1
                    print(f"Error notifying user {user_id}: {e}")

            # Log summary if any notifications were sent
            if notified_count > 0 or failed_count > 0:
                print(f"[Auto Notify] Notified: {notified_count}, Failed: {failed_count}")

                # Send log to PREMIUM_LOGS channel
                try:
                    await client.send_message(
                        PREMIUM_LOGS,
                        f"#Aᴜᴛᴏ_ᴇxᴘɪʀʏ_ɴᴏᴛɪꜰɪᴄᴀᴛɪᴏɴ\n\n"
                        f"✅ **Sᴜᴄᴄᴇꜱꜱꜰᴜʟʟʏ ɴᴏᴛɪꜰɪᴇᴅ:** {notified_count}\n"
                        f"❌ **Fᴀɪʟᴇᴅ ɴᴏᴛɪꜰɪᴇᴅ:** {failed_count}\n"
                        f"🕐 **Tɪᴍᴇ:** {datetime.datetime.now(pytz.timezone('Asia/Kolkata')).strftime('%d-%m-%Y %I:%M:%S %p')}"
                    )
                except:
                    pass

        except Exception as e:
            print(f"Eʀʀᴏʀ ɪɴ ᴀᴜᴛᴏ_ɴᴏᴛɪꜰʏ_ᴇxᴘɪʀᴇᴅ_ᴜꜱᴇʀꜱ: {e}")

        # Check every 5 minutes
        await asyncio.sleep(300)


# ==================== EXISTING PREMIUM FEATURES ====================

@Client.on_message(filters.command("remove_premium") & filters.user(ADMINS))
async def remove_premium(client, message):
    reply_msg = None

    if len(message.command) == 2:
        user_id = int(message.command[1])
        user = await client.get_users(user_id)
        if await db.remove_premium_access(user_id):
            reply_msg = await message.reply_text("Uꜱᴇʀ ʀᴇᴍᴏᴠᴇᴅ ꜱᴜᴄᴄᴇꜱꜱꜰᴜʟʟʏ !")
            await client.send_message(
                chat_id=user_id,
                text=f"<b>Hᴇʏ {user.mention},\n\nYᴏᴜʀ Pʀᴇᴍɪᴜᴍ Aᴄᴄᴇss Hᴀs Bᴇᴇɴ Rᴇᴍᴏᴠᴇᴅ.\nTʜᴀɴᴋ Yᴏᴜ Fᴏʀ Usɪɴɢ Oᴜʀ Sᴇʀᴠɪᴄᴇ 😊\nCʟɪᴄᴋ Oɴ /myplan Tᴏ Cʜᴇᴄᴋ Oᴜᴛ Oᴛʜᴇʀ Pʟᴀɴꜱ.</b>"
            )
        else:
            reply_msg = await message.reply_text("Uɴᴀʙʟᴇ ᴛᴏ ʀᴇᴍᴏᴠᴇ ᴜꜱᴇᴅ !\nᴀʀᴇ ʏᴏᴜ ꜱᴜʀᴇ, ɪᴛ ᴡᴀꜱ ᴀ ᴘʀᴇᴍɪᴜᴍ ᴜꜱᴇʀ ɪᴅ ?")
    else:
        reply_msg = await message.reply_text("Uꜱᴀɢᴇ : /remove_premium user_id")

    # Auto-delete messages
    if reply_msg:
        asyncio.create_task(auto_delete_message(message, reply_msg))
    else:
        asyncio.create_task(auto_delete_message(message))

@Client.on_message(filters.command("myplan"))
async def myplan(client, message):
    user = message.from_user.mention
    user_id = message.from_user.id
    reply_msg = None

    # Check if user has active premium
    if await db.has_premium_access(user_id):
        # User has active premium - show plan details
        data = await db.get_user(user_id)
        expiry = data.get("expiry_time") if data else None
        redeemed_code = data.get("redeemed_code", None)
        premium_source = data.get("premium_source", "admin")  # Default to admin if not set

        if not expiry:
            # Lifetime premium
            plan_info = f"⚜️ Pʀᴇᴍɪᴜᴍ Uꜱᴇʀ Dᴀᴛᴀ :\n\n👤 Uꜱᴇʀ : {user}\n⚡ Uꜱᴇʀ ɪᴅ : <code>{user_id}</code>\n⏰ Tɪᴍᴇ ʟᴇꜰᴛ : ʟɪꜰᴇᴛɪᴍᴇ"
            # Show premium source based on how it was obtained
            if premium_source == "redeem_code" and redeemed_code:
                plan_info += f"\n🎟️ Rᴇᴅᴇᴇᴍᴇᴅ ᴄᴏᴅᴇ : <code>{redeemed_code}</code>"
            else:
                plan_info += f"\n👑 Pʀᴇᴍɪᴜᴍ ꜱᴏᴜʀᴄᴇ : ᴀᴅᴍɪɴ ᴀᴅᴅᴇᴅ"
            reply_msg = await message.reply_text(plan_info)
            asyncio.create_task(auto_delete_message(message, reply_msg))
            return

        # Calculate time left
        expiry_ist = expiry.astimezone(pytz.timezone("Asia/Kolkata"))
        expiry_str_in_ist = expiry_ist.strftime("%d-%m-%Y\n⏱️ Exᴘɪʀʏ ᴛɪᴍᴇ : %I:%M:%S %p")
        current_time = datetime.datetime.now(pytz.timezone("Asia/Kolkata"))
        time_left = expiry_ist - current_time

        days = time_left.days
        hours, remainder = divmod(time_left.seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        time_left_str = f"{days} Dᴀʏꜱ, {hours} Hʀꜱ, {minutes} Mɪɴ"

        plan_info = f"⚜️ Pʀᴇᴍɪᴜᴍ Uꜱᴇʀ Dᴀᴛᴀ :\n\n👤 Uꜱᴇʀ : {user}\n⚡ Uꜱᴇʀ ɪᴅ : <code>{user_id}</code>\n⏰ Tɪᴍᴇ ʟᴇꜰᴛ : {time_left_str}\n⌛️ Exᴘɪʀʏ ᴅᴀᴛᴇ : {expiry_str_in_ist}"
        # Show premium source based on how it was obtained
        if premium_source == "redeem_code" and redeemed_code:
            plan_info += f"\n🎟️ Rᴇᴅᴇᴇᴍᴇᴅ ᴄᴏᴅᴇ : <code>{redeemed_code}</code>"
        else:
            plan_info += f"\n👑 Rʀᴇᴍɪᴜᴍ ꜱᴏᴜʀᴄᴇ : ᴀᴅᴍɪɴ ᴀᴅᴅᴇᴅ"

        reply_msg = await message.reply_text(plan_info)
        asyncio.create_task(auto_delete_message(message, reply_msg))
        return

    # Check if premium expired (but not yet cleared)
    if await db.is_premium_expired(user_id):
        # Premium has expired - show expired message
        data = await db.get_user(user_id)
        expiry = data.get("expiry_time") if data else None
        redeemed_code = data.get("redeemed_code", None)

        expired_text = (
            f"⏰ **Pʀᴇᴍɪᴜᴍ Exᴘɪʀᴇᴅ** ⏰\n\n"
            f"Hᴇʏ {user},\n\n"
            f"Yᴏᴜʀ ᴘʀᴇᴍɪᴜᴍ ᴀᴄᴄᴇꜱꜱ ʜᴀꜱ **Exᴘɪʀᴇᴅ**.\n\n"
        )
        if expiry:
            expiry_ist = expiry.astimezone(pytz.timezone("Asia/Kolkata"))
            expiry_str = expiry_ist.strftime("%d-%m-%Y %I:%M:%S %p")
            expired_text += f"⌛️ **Exᴘɪʀᴇᴅ ᴛɪᴍᴇ:** `{expiry_str}`\n\n"

        expired_text += (
            f"✨ **Wᴀɴᴛ ᴛᴏ ᴄᴏɴᴛɪɴᴜᴇ ᴘʀᴇᴍɪᴜᴍ?**\n"
        )

        reply_msg = await message.reply_text(
            expired_text,
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("💸 Cʜᴇᴄᴋᴏᴜᴛ Pʀᴇᴍɪᴜᴍ Pʟᴀɴꜱ 💸", callback_data="seeplans")],
                [InlineKeyboardButton("📞 Cᴏɴᴛᴀᴄᴛ Aᴅᴍɪɴ", url="https://t.me/sujan_chh")]]
            )
        )
        asyncio.create_task(auto_delete_message(message, reply_msg))
        return

    # No premium at all
    reply_msg = await message.reply_text(
        f"Hᴇʏ {user},\n\nYᴏᴜ Dᴏ Nᴏᴛ Hᴀᴠᴇ Aɴʏ Aᴄᴛɪᴠᴇ Pʀᴇᴍɪᴜᴍ Pʟᴀɴs, Iꜰ Yᴏᴜ Wᴀɴᴛ Tᴏ Tᴀᴋᴇ Pʀᴇᴍɪᴜᴍ Tʜᴇɴ Cʟɪᴄᴋ Oɴ Bᴇʟᴏᴡ Bᴜᴛᴛᴏɴ 👇",
        reply_markup=InlineKeyboardMarkup(
            [[InlineKeyboardButton("💸 Cʜᴇᴄᴋᴏᴜᴛ Pʀᴇᴍɪᴜᴍ Pʟᴀɴꜱ 💸", callback_data="seeplans")]]
        )
    )
    asyncio.create_task(auto_delete_message(message, reply_msg))
@Client.on_message(filters.command("add_premium") & filters.user(ADMINS))
async def give_premium_cmd_handler(client, message):
    reply_msg = None

    if len(message.command) == 4:
        time_zone = datetime.datetime.now(pytz.timezone("Asia/Kolkata"))
        current_time = time_zone.strftime("%d-%m-%Y\n⏱️ Jᴏɪɴɪɴɢ ᴛɪᴍᴇ : %I:%M:%S %p") 
        user_id = int(message.command[1])  # Convert the user_id to integer
        user = await client.get_users(user_id)
        time = message.command[2]+" "+message.command[3]
        seconds = await get_seconds(time)
        if seconds > 0:
            expiry_time = datetime.datetime.now() + datetime.timedelta(seconds=seconds)
            # Reset expiry notification status when adding new premium
            user_data = {
                "id": user_id, 
                "expiry_time": expiry_time,
                "premium_source": "admin",
                "expiry_notified": False,
                "expiry_notified_at": None
            }
            await db.update_user(user_data)  # Use the update_user method to update or insert user data
            data = await db.get_user(user_id)
            expiry = data.get("expiry_time")   
            expiry_str_in_ist = expiry.astimezone(pytz.timezone("Asia/Kolkata")).strftime("%d-%m-%Y\n⏱️ ᴇxᴘɪʀʏ ᴛɪᴍᴇ : %I:%M:%S %p")         
            reply_msg = await message.reply_text(f"Pʀᴇᴍɪᴜᴍ Aᴅᴅᴇᴅ Sᴜᴄᴄᴇꜱꜱꜰᴜʟʟʏ ✅\n\n👤 Uꜱᴇʀ : {user.mention}\n⚡ Uꜱᴇʀ ɪᴅ : <code>{user_id}</code>\n⏰ Pʀᴇᴍɪᴜᴍ ᴀᴄᴄᴇꜱꜱ : <code>{time}</code>\n\n⏳ Jᴏɪɴɪɴɢ ᴅᴀᴛᴇ : {current_time}\n\n⌛️ Exᴘɪʀʏ ᴅᴀᴛᴇ : {expiry_str_in_ist}", disable_web_page_preview=True)
            await client.send_message(
                chat_id=user_id,
                text=f"👋 Hᴇʏ {user.mention},\n\nTʜᴀɴᴋ ʏᴏᴜ ꜰᴏʀ ᴘᴜʀᴄʜᴀsɪɴɢ ᴘʀᴇᴍɪᴜᴍ.✨🎉\n\n⏰ Pʀᴇᴍɪᴜᴍ ᴀᴄᴄᴇꜱꜱ : <code>{time}</code>\n⏳ Jᴏɪɴɪɴɢ ᴅᴀᴛᴇ : {current_time}\n\n⌛️ Exᴘɪʀʏ ᴅᴀᴛᴇ : {expiry_str_in_ist}", disable_web_page_preview=True              
            )    
            await client.send_message(PREMIUM_LOGS, text=f"#Aᴅᴅᴇᴅ_ᴘʀᴇᴍɪᴜᴍ\n\n👤 Uꜱᴇʀ : {user.mention}\n⚡ Uꜱᴇʀ ɪᴅ : <code>{user_id}</code>\n⏰ Pʀᴇᴍɪᴜᴍ ᴀᴄᴄᴇꜱꜱ : <code>{time}</code>\n\n⏳ Jᴏɪɴɪɴɢ ᴅᴀᴛᴇ : {current_time}\n\n⌛️ Exᴘɪʀʏ ᴅᴀᴛᴇ : {expiry_str_in_ist}", disable_web_page_preview=True)

        else:
            reply_msg = await message.reply_text("Iɴᴠᴀʟɪᴅ ᴛɪᴍᴇ ꜰᴏʀᴍᴀᴛ. ᴘʟᴇᴀꜱᴇ ᴜꜱᴇ '1 day for days', '1 hour for hours', or '1 min for minutes', or '1 month for months' or '1 year for year'")
    else:
        reply_msg = await message.reply_text("Uꜱᴀɢᴇ : /add_premium user_id ᴛɪᴍᴇ (e.g., '1 day for days', '1 hour for hours', or '1 min for minutes', or '1 month for months' or '1 year for year')")

    # Auto-delete messages
    if reply_msg:
        asyncio.create_task(auto_delete_message(message, reply_msg))
    else:
        asyncio.create_task(auto_delete_message(message))

@Client.on_message(filters.command("premium_users") & filters.user(ADMINS))
async def premium_user(client, message):
    aa = await message.reply_text("<i>Fᴇᴛᴄʜɪɴɢ...</i>")
    new = f"⚜️ Pʀᴇᴍɪᴜᴍ Uꜱᴇʀꜱ Lɪꜱᴛ :\n\n"
    user_count = 1
    users = await db.get_all_premium_users()
    async for user in users:
        if not await db.has_premium_access(user['id']):
            continue
        data = await db.get_user(user['id'])
        expiry = data.get("expiry_time") if data else None
        if not expiry:
            new += f"{user_count}. {(await client.get_users(user['id'])).mention}\n👤 Uꜱᴇʀ ɪᴅ : {user['id']}\n⏰ Tɪᴍᴇ ʟᴇꜰᴛ : ʟɪꜰᴇᴛɪᴍᴇ\n"
            user_count += 1
            continue

        expiry_ist = expiry.astimezone(pytz.timezone("Asia/Kolkata"))
        expiry_str_in_ist = expiry_ist.strftime("%d-%m-%Y\n⏱️ Exᴘɪʀʏ ᴛɪᴍᴇ : %I:%M:%S %p")            
        current_time = datetime.datetime.now(pytz.timezone("Asia/Kolkata"))
        time_left = expiry_ist - current_time
        if time_left.total_seconds() <= 0:
            await db.remove_premium_access(user['id'])
            continue
        days = time_left.days
        hours, remainder = divmod(time_left.seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        time_left_str = f"{days} days, {hours} hours, {minutes} minutes"	 
        new += f"{user_count}. {(await client.get_users(user['id'])).mention}\n👤 Uꜱᴇʀ ɪᴅ : {user['id']}\n⏳ Exᴘɪʀʏ ᴅᴀᴛᴇ : {expiry_str_in_ist}\n⏰ Tɪᴍᴇ ʟᴇꜰᴛ : {time_left_str}\n"
        user_count += 1
    try:    
        reply_msg = await aa.edit_text(new)
    except MessageTooLong:
        with open('usersplan.txt', 'w+') as outfile:
            outfile.write(new)
        reply_msg = await message.reply_document('usersplan.txt', caption="Paid Users:")

    # Auto-delete messages
    asyncio.create_task(auto_delete_message(message, reply_msg))

@Client.on_message(filters.command("plan"))
async def plan(client, message):
    user_id = message.from_user.id 
    users = message.from_user.mention 
    btn = [[

        InlineKeyboardButton("📲 Sᴇɴᴅ Pᴀʏᴍᴇɴᴛ Sᴄʀᴇᴇɴꜱʜᴏᴛ", user_id=int(5123039648))],[InlineKeyboardButton("❌ ᴄʟᴏꜱᴇ ❌", callback_data="close_data")
    ]]
    reply_msg = await message.reply_photo(photo="https://iili.io/fmFvFN1.jpg", caption=script.PREMIUM_TEXT.format(message.from_user.mention), reply_markup=InlineKeyboardMarkup(btn))

    # Auto-delete messages
    asyncio.create_task(auto_delete_message(message, reply_msg))
