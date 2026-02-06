from datetime import timedelta
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
    new = f"⚜️ ᴘʀᴇᴍɪᴜᴍ ᴜꜱᴇʀꜱ ʟɪꜱᴛ :\n\n"
    user_count = 1
    users = await db.get_all_users()
    async for user in users:
        data = await db.get_user(user['id'])
        if data and data.get("expiry_time"):
            expiry = data.get("expiry_time") 
            expiry_ist = expiry.astimezone(pytz.timezone("Asia/Kolkata"))
            expiry_str_in_ist = expiry.astimezone(pytz.timezone("Asia/Kolkata")).strftime("%d-%m-%Y\n⏱️ ᴇxᴘɪʀʏ ᴛɪᴍᴇ : %I:%M:%S %p")            
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
        return await message.reply_text("Usage : /gen_redeem <time> (e.g., '1 hour', '1 day', '1 month' or '1 year')")
    time_value = " ".join(message.command[1:]).strip()
    seconds = await get_seconds(time_value)
    if seconds <= 0:
        return await message.reply_text("Invalid time format. Use '1 day', '2 hour', '30 min', '1 month', or '1 year'")
    code = await generate_unique_redeem_code()
    await db.create_redeem_code(code, seconds, message.from_user.id)
    duration_text = format_duration(seconds)
    await message.reply_text(
        f"✅ *Rᴇᴅᴇᴇᴍ Cᴏᴅᴇ Gᴇɴᴇʀᴀᴛᴇᴅ!*\n\n"
		f"⏰ Pʀᴇᴍɪᴜᴍ Aᴄᴄᴇꜱꜱ: <code>{duration_text}</code>"
        f"🧾 Redeem Cᴏᴅᴇ: <code>{code}</code>\n"
    )
    await client.send_message(
        PREMIUM_LOGS,
        text=f"#RedeemCodeGenerated\n\n👤 Aᴅᴍɪɴ: {message.from_user.mention}\n🧾 Cᴏᴅᴇ: <code>{code}</code>\n⏰ Pʀᴇᴍɪᴜᴍ Aᴄᴄᴇꜱꜱ: <code>{duration_text}</code>"
    )

@Client.on_message(filters.command("redeem"))
async def redeem_code(client, message):
    if len(message.command) != 2:
        return await message.reply_text("Usage : /redeem <code>")
    code = message.command[1].strip().upper()
    redeem_data = await db.get_redeem_code(code)
    if not redeem_data:
        return await message.reply_text("❌ Iɴᴠᴀʟɪᴅ Rᴇᴅᴇᴇᴍ Cᴏᴅᴇ.")
    if redeem_data.get("redeemed_by"):
        return await message.reply_text("⚠️ Tʜɪꜱ Cᴏᴅᴇ Aʟʀᴇᴀᴅʏ Rᴇᴅᴇᴇᴍ.")
    seconds = redeem_data.get("premium_seconds", 0)
    if seconds <= 0:
        return await message.reply_text("❌ Tʜɪꜱ Rᴇᴅᴇᴇᴍ Cᴏᴅᴇ Iꜱ Nᴏᴛ Vᴀʟɪᴅ.")
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
    await db.update_user({"id": user_id, "expiry_time": new_expiry})
    if not await db.mark_redeemed(code, user_id):
        return await message.reply_text("⚠️ Uɴᴀʙʟᴇ Tᴏ Rᴇᴅᴇᴇᴍ Tʜɪꜱ Cᴏᴅᴇ. Pʟᴇᴀꜱᴇ Tʀʏ Aɢᴀɪɴ.")
    duration_text = format_duration(seconds)
    await message.reply_text(
        f"✅ Rᴇᴅᴇᴇᴍ Sᴜᴄᴄᴇꜱꜱꜰᴜʟ!\n\n"
		f"⏰ Pʀᴇᴍɪᴜᴍ Aᴄᴄᴇꜱꜱ: <code>{duration_text}</code>"
        f"🧾 Cᴏᴅᴇ: <code>{code}</code>\n"
    )
    await client.send_message(
        PREMIUM_LOGS,
        text=f"#RedeemCodeUsed\n\n👤 Uꜱᴇʀ: {message.from_user.mention}\n🧾 Cᴏᴅᴇ: <code>{code}</code>\n⏰ Pʀᴇᴍɪᴜᴍ Aᴄᴄᴇꜱꜱ: <code>{duration_text}</code>"
    )

@Client.on_message(filters.command("redeem_codes") & filters.user(ADMINS))
async def redeem_codes_list(client, message):
    show_all = len(message.command) > 1 and message.command[1].lower() == "all"
    data = await db.list_redeem_codes(include_redeemed=show_all)
    output = "🎟️ Rᴇᴅᴇᴇᴍ Cᴏᴅᴇꜱ:\n\n"
    idx = 1
    async for item in data:
        duration_text = format_duration(item.get("premium_seconds", 0))
        redeemed_by = item.get("redeemed_by")
        status = f"Rᴇᴅᴇᴇᴍ Bʏ <code>{redeemed_by}</code>" if redeemed_by else "Not used"
        output += (
            f"{idx}. <code>{item.get('code')}</code>\n"
            f"⏰ Pʀᴇᴍɪᴜᴍ: <code>{duration_text}</code>\n"
            f"📌 Sᴛᴀᴛᴜꜱ: {status}\n\n"
        )
        idx += 1
    if idx == 1:
        output = "Nᴏ Rᴇᴅᴇᴇᴍ Cᴏᴅᴇꜱ Fᴏᴜɴᴅ."
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
    if await db.delete_redeem_code(code):
        await message.reply_text(f"✅ Rᴇᴅᴇᴇᴍ Cᴏᴅᴇ <code>{code}</code> deleted.")
        await client.send_message(
            PREMIUM_LOGS,
            text=f"#RedeemCodeDeleted\n\n👤 Aᴅᴍɪɴ: {message.from_user.mention}\n🧾 Cᴏᴅᴇ: <code>{code}</code>"
        )
    else:
        await message.reply_text("❌ Rᴇᴅᴇᴇᴍ Cᴏᴅᴇ Nᴏᴛ Fᴏᴜɴᴅ.")
		
@Client.on_message(filters.command("plan"))
async def plan(client, message):
    user_id = message.from_user.id 
    users = message.from_user.mention 
    btn = [[
	
        InlineKeyboardButton("📲 Sᴇɴᴅ Pᴀʏᴍᴇɴᴛ Sᴄʀᴇᴇɴꜱʜᴏᴛ", user_id=int(5123039648))],[InlineKeyboardButton("❌ ᴄʟᴏꜱᴇ ❌", callback_data="close_data")
    ]]
    await message.reply_photo(photo="https://graph.org/file/7d8b428734782477158d4.jpg", caption=script.PREMIUM_TEXT.format(message.from_user.mention), reply_markup=InlineKeyboardMarkup(btn))
