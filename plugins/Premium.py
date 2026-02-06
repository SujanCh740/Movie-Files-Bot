from datetime import timedelta
import asyncio
import secrets
import string
import pytz
import datetime, time
from Script import script 
from info import ADMINS, PREMIUM_LOGS
from utils import get_seconds
from database.users_chats_db import db 
from pyrogram import Client, filters 
from pyrogram.errors.exceptions.bad_request_400 import MessageTooLong
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup

def format_duration(total_seconds):
    days, remainder = divmod(total_seconds, 86400)
    hours, remainder = divmod(remainder, 3600)
    minutes, seconds = divmod(remainder, 60)
    parts = []
    if days:
        parts.append(f"{days} day(s)")
    if hours:
        parts.append(f"{hours} hour(s)")
    if minutes:
        parts.append(f"{minutes} minute(s)")
    if seconds and not parts:
        parts.append(f"{seconds} second(s)")
    return ", ".join(parts) if parts else "0 seconds"

async def send_redeem_expiry_notice(client, user_id, expiry_time):
    delay = (expiry_time - datetime.datetime.now()).total_seconds()
    if delay > 0:
        await asyncio.sleep(delay)
    user_data = await db.get_user(user_id)
    if not user_data:
        return
    current_expiry = user_data.get("expiry_time")
    if not isinstance(current_expiry, datetime.datetime):
        return
    if current_expiry > datetime.datetime.now():
        return
    if user_data.get("premium_source") != "redeem":
        return
    if user_data.get("redeem_expiry_notice_sent"):
        return
    await db.update_user(
        {
            "id": user_id,
            "expiry_time": None,
            "premium_source": None,
            "redeem_expiry_notice_sent": True,
        }
    )
    try:
        await client.send_message(
            chat_id=user_id,
            text=(
                "⚠️ Rᴇᴅᴇᴇᴍ Pʀᴇᴍɪᴜᴍ Exᴘɪʀᴇᴅ\n\n"
                "Yᴏᴜʀ Pʀᴇᴍɪᴜᴍ Aᴄᴄᴇss Fʀᴏᴍ A Rᴇᴅᴇᴇᴍ Cᴏᴅᴇ Hᴀs Exᴘɪʀᴇᴅ.\n"
                "Uꜱᴇ /myplan Tᴏ Cʜᴇᴄᴋ Pʟᴀɴs Aɴᴅ Rᴇɴᴇᴡ."
            ),
        )
    except Exception:
        pass
		
async def generate_unique_redeem_code(length=10):
    charset = string.ascii_uppercase + string.digits
    for _ in range(10):
        code = "".join(secrets.choice(charset) for _ in range(length))
        if not await db.get_redeem_code(code):
            return code
    raise RuntimeError("Unable to generate unique redeem code")

@Client.on_message(filters.command("remove_premium") & filters.user(ADMINS))
async def remove_premium(client, message):
    if len(message.command) == 2:
        user_id = int(message.command[1])  # Convert the user_id to integer
        user = await client.get_users(user_id)
        if await db.remove_premium_access(user_id):
            await message.reply_text("ᴜꜱᴇʀ ʀᴇᴍᴏᴠᴇᴅ ꜱᴜᴄᴄᴇꜱꜱꜰᴜʟʟʏ !")
            await client.send_message(
                chat_id=user_id,
                text=f"<b>Hᴇʏ {user.mention},\n\nYᴏᴜʀ Pʀᴇᴍɪᴜᴍ Aᴄᴄᴇss Hᴀs Bᴇᴇɴ Rᴇᴍᴏᴠᴇᴅ.\nTʜᴀɴᴋ Yᴏᴜ Fᴏʀ Usɪɴɢ Oᴜʀ Sᴇʀᴠɪᴄᴇ 😊\nCʟɪᴄᴋ Oɴ /myplan Tᴏ Cʜᴇᴄᴋ Oᴜᴛ Oᴛʜᴇʀ Pʟᴀɴꜱ.</b>"
            )
        else:
            await message.reply_text("ᴜɴᴀʙʟᴇ ᴛᴏ ʀᴇᴍᴏᴠᴇ ᴜꜱᴇᴅ !\nᴀʀᴇ ʏᴏᴜ ꜱᴜʀᴇ, ɪᴛ ᴡᴀꜱ ᴀ ᴘʀᴇᴍɪᴜᴍ ᴜꜱᴇʀ ɪᴅ ?")
    else:
        await message.reply_text("ᴜꜱᴀɢᴇ : /remove_premium user_id") 

@Client.on_message(filters.command("myplan"))
async def myplan(client, message):
    user = message.from_user.mention 
    user_id = message.from_user.id
    data = await db.get_user(message.from_user.id)  # Convert the user_id to integer
    if data and data.get("expiry_time"):
        #expiry_time = datetime.datetime.now() + datetime.timedelta(seconds=data)
        expiry = data.get("expiry_time") 
        expiry_ist = expiry.astimezone(pytz.timezone("Asia/Kolkata"))
        expiry_str_in_ist = expiry.astimezone(pytz.timezone("Asia/Kolkata")).strftime("%d-%m-%Y\n⏱️ ᴇxᴘɪʀʏ ᴛɪᴍᴇ : %I:%M:%S %p")            
        # Calculate time difference
        current_time = datetime.datetime.now(pytz.timezone("Asia/Kolkata"))
        time_left = expiry_ist - current_time
            
        # Calculate days, hours, and minutes
        days = time_left.days
        hours, remainder = divmod(time_left.seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
            
        # Format time left as a string
        time_left_str = f"{days} ᴅᴀʏꜱ, {hours} ʜᴏᴜʀꜱ, {minutes} ᴍɪɴᴜᴛᴇꜱ"
        await message.reply_text(f"⚜️ Pʀᴇᴍɪᴜᴍ Uꜱᴇʀ Dᴀᴛᴀ :\n\n👤 Uꜱᴇʀ : {user}\n⚡ Uꜱᴇʀ Iᴅ : <code>{user_id}</code>\n⏰ Tɪᴍᴇ Lᴇꜰᴛ : {time_left_str}\n⌛️ Exᴘɪʀʏ Dᴀᴛᴇ : {expiry_str_in_ist}")   
    else:
        await message.reply_text(f"Hᴇʏ {user},\n\nYᴏᴜ Dᴏ Nᴏᴛ Hᴀᴠᴇ Aɴʏ Aᴄᴛɪᴠᴇ Pʀᴇᴍɪᴜᴍ Pʟᴀɴs, Iꜰ Yᴏᴜ Wᴀɴᴛ Tᴏ Tᴀᴋᴇ Pʀᴇᴍɪᴜᴍ Tʜᴇɴ Cʟɪᴄᴋ Oɴ Bᴇʟᴏᴡ Bᴜᴛᴛᴏɴ 👇",
	reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("💸 Cʜᴇᴄᴋᴏᴜᴛ Pʀᴇᴍɪᴜᴍ Pʟᴀɴꜱ 💸", callback_data='seeplans')]]))			 

@Client.on_message(filters.command("get_premium") & filters.user(ADMINS))
async def get_premium(client, message):
    if len(message.command) == 2:
        user_id = int(message.command[1])
        user = await client.get_users(user_id)
        data = await db.get_user(user_id)  # Convert the user_id to integer
        if data and data.get("expiry_time"):
            #expiry_time = datetime.datetime.now() + datetime.timedelta(seconds=data)
            expiry = data.get("expiry_time") 
            expiry_ist = expiry.astimezone(pytz.timezone("Asia/Kolkata"))
            expiry_str_in_ist = expiry.astimezone(pytz.timezone("Asia/Kolkata")).strftime("%d-%m-%Y\n⏱️ ᴇxᴘɪʀʏ ᴛɪᴍᴇ : %I:%M:%S %p")            
            # Calculate time difference
            current_time = datetime.datetime.now(pytz.timezone("Asia/Kolkata"))
            time_left = expiry_ist - current_time
            
            # Calculate days, hours, and minutes
            days = time_left.days
            hours, remainder = divmod(time_left.seconds, 3600)
            minutes, seconds = divmod(remainder, 60)
            
            # Format time left as a string
            time_left_str = f"{days} days, {hours} hours, {minutes} minutes"
            await message.reply_text(f"⚜️ Pʀᴇᴍɪᴜᴍ uꜱᴇʀ Dᴀᴛᴀ :\n\n👤 Uꜱᴇʀ : {user.mention}\n⚡ Uꜱᴇʀ Iᴅ : <code>{user_id}</code>\n⏰ Tɪᴍᴇ Lᴇꜰᴛ : {time_left_str}\n⌛️ Exᴘɪʀʏ Dᴀᴛᴇ : {expiry_str_in_ist}")
        else:
            await message.reply_text("Nᴏ Aɴʏ Pʀᴇᴍɪᴜᴍ Dᴀᴛᴀ Oꜰ Tʜᴇ Wᴀꜱ Fᴏᴜɴᴅ Iɴ Dᴀᴛᴀʙᴀꜱᴇ !")
    else:
        await message.reply_text("ᴜꜱᴀɢᴇ : /get_premium user_id")

@Client.on_message(filters.command("add_premium") & filters.user(ADMINS))
async def give_premium_cmd_handler(client, message):
    if len(message.command) == 4:
        time_zone = datetime.datetime.now(pytz.timezone("Asia/Kolkata"))
        current_time = time_zone.strftime("%d-%m-%Y\n⏱️ Jᴏɪɴɪɴɢ Tɪᴍᴇ : %I:%M:%S %p") 
        user_id = int(message.command[1])  # Convert the user_id to integer
        user = await client.get_users(user_id)
        time = message.command[2]+" "+message.command[3]
        seconds = await get_seconds(time)
        if seconds > 0:
            expiry_time = datetime.datetime.now() + datetime.timedelta(seconds=seconds)
            user_data = {"id": user_id, "expiry_time": expiry_time}  # Using "id" instead of "user_id"  
            await db.update_user(user_data)  # Use the update_user method to update or insert user data
            data = await db.get_user(user_id)
            expiry = data.get("expiry_time")   
            expiry_str_in_ist = expiry.astimezone(pytz.timezone("Asia/Kolkata")).strftime("%d-%m-%Y\n⏱️ Exᴘɪʀʏ Tɪᴍᴇ : %I:%M:%S %p")         
            await message.reply_text(f"Pʀᴇᴍɪᴜᴍ Aᴅᴅᴇᴅ Sᴜᴄᴄᴇꜱꜱꜰᴜʟʟʏ ✅\n\n👤 Uꜱᴇʀ : {user.mention}\n⚡ Uꜱᴇʀ Iᴅ : <code>{user_id}</code>\n⏰ Pʀᴇᴍɪᴜᴍ Aᴄᴄᴇꜱꜱ : <code>{time}</code>\n\n⏳ Jᴏɪɴɪɴɢ Dᴀᴛᴇ : {current_time}\n\n⌛️ Exᴘɪʀʏ Dᴀᴛᴇ : {expiry_str_in_ist}", disable_web_page_preview=True)
            await client.send_message(
                chat_id=user_id,
                text=f"👋 Hᴇʏ {user.mention},\n\nTʜᴀɴᴋ Yᴏᴜ Fᴏʀ Pᴜʀᴄʜᴀꜱɪɴɢ Pʀᴇᴍɪᴜᴍ ✨🎉\n\n⏰ Pʀᴇᴍɪᴜᴍ Aᴄᴄᴇꜱꜱ : <code>{time}</code>\n⏳ Jᴏɪɴɪɴɢ Dᴀᴛᴇ : {current_time}\n\n⌛️ Exᴘɪʀʏ Dᴀᴛᴇ : {expiry_str_in_ist}", disable_web_page_preview=True              
            )    
            await client.send_message(PREMIUM_LOGS, text=f"#Added_Premium\n\n👤 Uꜱᴇʀ : {user.mention}\n⚡ Uꜱᴇʀ Iᴅ : <code>{user_id}</code>\n⏰ Pʀᴇᴍɪᴜᴍ Aᴄᴄᴇꜱꜱ : <code>{time}</code>\n\n⏳ Jᴏɪɴɪɴɢ Dᴀᴛᴇ : {current_time}\n\n⌛️ Exᴘɪʀʏ Dᴀᴛᴇ : {expiry_str_in_ist}", disable_web_page_preview=True)
                    
        else:
            await message.reply_text("Invalid time format. Please use '1 day for days', '1 hour for hours', or '1 min for minutes', or '1 month for months' or '1 year for year'")
    else:
        await message.reply_text("Usage : /add_premium user_id time (e.g., '1 day for days', '1 hour for hours', or '1 min for minutes', or '1 month for months' or '1 year for year')")

@Client.on_message(filters.command("premium_users") & filters.user(ADMINS))
async def premium_user(client, message):
    aa = await message.reply_text("<i>ꜰᴇᴛᴄʜɪɴɢ...</i>")
    new = f"⚜️ Pʀᴇᴍɪᴜᴍ Uꜱᴇʀꜱ Lɪꜱᴛ :\n\n"
    user_count = 1
    users = await db.get_all_users()
    async for user in users:
        data = await db.get_user(user['id'])
        if data and data.get("expiry_time"):
            expiry = data.get("expiry_time") 
            expiry_ist = expiry.astimezone(pytz.timezone("Asia/Kolkata"))
            expiry_str_in_ist = expiry.astimezone(pytz.timezone("Asia/Kolkata")).strftime("%d-%m-%Y\n⏱️ Exᴘɪʀʏ Tɪᴍᴇ : %I:%M:%S %p")            
            current_time = datetime.datetime.now(pytz.timezone("Asia/Kolkata"))
            time_left = expiry_ist - current_time
            days = time_left.days
            hours, remainder = divmod(time_left.seconds, 3600)
            minutes, seconds = divmod(remainder, 60)
            time_left_str = f"{days} days, {hours} hours, {minutes} minutes"	 
            new += f"{user_count}. {(await client.get_users(user['id'])).mention}\n👤 Uꜱᴇʀ Iᴅ : {user['id']}\n⏳ Exᴘɪʀʏ Dᴀᴛᴇ : {expiry_str_in_ist}\n⏰ Tɪᴍᴇ Lᴇꜰᴛ : {time_left_str}\n"
            user_count += 1
        else:
            pass
    try:    
        await aa.edit_text(new)
    except MessageTooLong:
        with open('usersplan.txt', 'w+') as outfile:
            outfile.write(new)
        await message.reply_document('usersplan.txt', caption="Paid Users:")
		
@Client.on_message(filters.command("gen_redeem") & filters.user(ADMINS))
async def generate_redeem_code(client, message):
    if len(message.command) < 2:
        return await message.reply_text("Usage : /gen_redeem <time> (e.g., '1 day', '2 hour', '30 min')")
    time_value = " ".join(message.command[1:]).strip()
    seconds = await get_seconds(time_value)
    if seconds <= 0:
        return await message.reply_text("Invalid time format. Use '1 day', '2 hour', '30 min', '1 month', or '1 year'.")
    code = await generate_unique_redeem_code()
    await db.create_redeem_code(code, seconds, message.from_user.id)
    duration_text = format_duration(seconds)
    await message.reply_text(
        f"✅ Redeem code generated!\n\n"
        f"Code: <code>{code}</code>\n"
        f"Premium Access: <code>{duration_text}</code>"
    )
    await client.send_message(
        PREMIUM_LOGS,
        text=f"#RedeemCodeGenerated\n\n👤 Admin: {message.from_user.mention}\n🧾 Code: <code>{code}</code>\n⏰ Premium Access: <code>{duration_text}</code>"
    )

@Client.on_message(filters.command("redeem"))
async def redeem_code(client, message):
    if len(message.command) != 2:
        return await message.reply_text("Usage : /redeem <code>")
    code = message.command[1].strip().upper()
    redeem_data = await db.redeem_code(code, message.from_user.id)
    if not redeem_data:
        existing = await db.get_redeem_code(code)
        if not existing:
            return await message.reply_text("❌ Invalid redeem code.")
        if existing.get("redeemed_by"):
            return await message.reply_text("⚠️ This redeem code has already been used.")
        return await message.reply_text("⚠️ Unable to redeem this code. Please try again.")
    seconds = redeem_data.get("premium_seconds", 0)
    if seconds <= 0:
        return await message.reply_text("❌ This redeem code is not valid.")
    now = datetime.datetime.now()
    user_id = message.from_user.id
    user_data = await db.get_user(user_id)
    current_expiry = None
    if user_data:
        current_expiry = user_data.get("expiry_time")
    if isinstance(current_expiry, datetime.datetime) and current_expiry > now:
        new_expiry = current_expiry + datetime.timedelta(seconds=seconds)
    else:
        new_expiry = now + datetime.timedelta(seconds=seconds)
     await db.update_user(
        {
            "id": user_id,
            "expiry_time": new_expiry,
            "premium_source": "redeem",
            "redeem_expiry_notice_sent": False,
        }
    )
    asyncio.create_task(send_redeem_expiry_notice(client, user_id, new_expiry))
    duration_text = format_duration(seconds)
    await message.reply_text(
        f"✅ Redeem successful!\n\n"
        f"Code: <code>{code}</code>\n"
        f"Premium Access Added: <code>{duration_text}</code>"
    )
    await client.send_message(
        PREMIUM_LOGS,
        text=f"#RedeemCodeUsed\n\n👤 User: {message.from_user.mention}\n🧾 Code: <code>{code}</code>\n⏰ Premium Access: <code>{duration_text}</code>"
    )

@Client.on_message(filters.command("redeem_codes") & filters.user(ADMINS))
async def redeem_codes_list(client, message):
    show_unused_only = len(message.command) > 1 and message.command[1].lower() == "unused"
    data = await db.list_redeem_codes(include_redeemed=not show_unused_only)
    output = "🎟️ Redeem Codes:\n\n"
    idx = 1
    async for item in data:
        duration_text = format_duration(item.get("premium_seconds", 0))
        redeemed_by = item.get("redeemed_by")
        status = f"Used by <code>{redeemed_by}</code>" if redeemed_by else "Not used"
        output += (
            f"{idx}. <code>{item.get('code')}</code>\n"
            f"⏰ Premium: <code>{duration_text}</code>\n"
            f"📌 Status: {status}\n\n"
        )
        idx += 1
    if idx == 1:
        output = "No redeem codes found."
    try:
        await message.reply_text(output)
    except MessageTooLong:
        with open('redeem_codes.txt', 'w+') as outfile:
            outfile.write(output)
        await message.reply_document('redeem_codes.txt', caption="Redeem codes list")

@Client.on_message(filters.command("del_redeem") & filters.user(ADMINS))
async def delete_redeem_code(client, message):
    if len(message.command) != 2:
        return await message.reply_text("Usage : /del_redeem <code>")
    code = message.command[1].strip().upper()
    existing = await db.get_redeem_code(code)
    if not existing:
        return await message.reply_text("❌ Redeem code not found.")
    if await db.delete_redeem_code(code):
        redeemed_by = existing.get("redeemed_by")
        if redeemed_by:
            await db.remove_premium_access(redeemed_by)
        await message.reply_text(f"✅ Redeem code <code>{code}</code> deleted.")
        await client.send_message(
            PREMIUM_LOGS,
            text=f"#RedeemCodeDeleted\n\n👤 Admin: {message.from_user.mention}\n🧾 Code: <code>{code}</code>"
        )
    else:
        await message.reply_text("❌ Redeem code not found.")
		
@Client.on_message(filters.command("plan"))
async def plan(client, message):
    user_id = message.from_user.id 
    users = message.from_user.mention 
    btn = [[
	
        InlineKeyboardButton("📲 Sᴇɴᴅ Pᴀʏᴍᴇɴᴛ Sᴄʀᴇᴇɴꜱʜᴏᴛ", user_id=int(5123039648))],[InlineKeyboardButton("❌ ᴄʟᴏꜱᴇ ❌", callback_data="close_data")
    ]]
    await message.reply_photo(photo="https://graph.org/file/7d8b428734782477158d4.jpg", caption=script.PREMIUM_TEXT.format(message.from_user.mention), reply_markup=InlineKeyboardMarkup(btn))
