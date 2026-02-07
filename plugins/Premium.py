# SPECIAL THANKS TO [Rishikesh Sharma] @Rk_botowner FOR THESE AMAZING CODES
# SPECIAL THANKS TO @DeletedFromEarth FOR MODIFYING THESE AMAZING CODES
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
    """Generate an 8-digit alphanumeric redeem code"""
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))

@Client.on_message(filters.command("gen_redeem") & filters.user(ADMINS))
async def generate_redeem_code_handler(client, message):
    """Admin command to generate redeem codes for premium access"""
    reply_msg = None

    if len(message.command) < 3:
        reply_msg = await message.reply_text(
            "**Usage:** `/gen_redeem <duration> <quantity>`\n\n"
            "**Examples:**\n"
            "`/gen_redeem 1day 5` - Generate 5 codes for 1 day\n"
            "`/gen_redeem 1month 10` - Generate 10 codes for 1 month\n"
            "`/gen_redeem 1year 3` - Generate 3 codes for 1 year\n"
            "`/gen_redeem lifetime 1` - Generate 1 lifetime code\n\n"
            "**Supported durations:** day, days, week, weeks, month, months, year, years, lifetime"
        )
        asyncio.create_task(auto_delete_message(message, reply_msg))
        return

    duration_str = message.command[1].lower()
    try:
        quantity = int(message.command[2])
        if quantity < 1 or quantity > 50:
            reply_msg = await message.reply_text("❌ Quantity must be between 1 and 50!")
            asyncio.create_task(auto_delete_message(message, reply_msg))
            return
    except ValueError:
        reply_msg = await message.reply_text("❌ Invalid quantity! Please enter a number.")
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
        f"✅ **Redeem Codes Generated Successfully!**\n\n"
        f"📊 **Quantity:** {quantity}\n"
        f"⏰ **Duration:** {duration_display}\n"
        f"👤 **Generated By:** {message.from_user.mention}\n"
        f"🕐 **Generated At:** {generated_time}\n\n"
        f"📋 **Codes:**\n{codes_text}\n\n"
        f"💡 Users can redeem with: `/redeem <code>`"
    )

    # Send as file if too many codes
    if len(response) > 4000:
        separator = "=" * 50
        file_content = f"Redeem Codes Generated\n{separator}\n"
        file_content += f"Duration: {duration_display}\n"
        file_content += f"Quantity: {quantity}\n"
        file_content += f"Generated By: {message.from_user.mention}\n"
        file_content += f"Generated At: {generated_time}\n"
        file_content += f"{separator}\n\n"
        file_content += "Codes:\n" + "\n".join(generated_codes)

        with open('redeem_codes.txt', 'w') as f:
            f.write(file_content)

        reply_msg = await message.reply_document(
            'redeem_codes.txt',
            caption=f"✅ Generated {quantity} codes for {duration_display}"
        )
    else:
        reply_msg = await message.reply_text(response)

    # Log to premium logs
    await client.send_message(
        PREMIUM_LOGS,
        f"#New_Redeem_Codes_Generated\n\n"
        f"👤 **Generated By:** {message.from_user.mention}\n"
        f"🆔 **Admin ID:** `{message.from_user.id}`\n"
        f"📊 **Quantity:** {quantity}\n"
        f"⏰ **Duration:** {duration_display}\n"
        f"🕐 **Time:** {generated_time}"
    )

    # Auto-delete messages
    asyncio.create_task(auto_delete_message(message, reply_msg))

@Client.on_message(filters.command("redeem"))
async def redeem_code_handler(client, message):
    """User command to redeem a premium code"""
    reply_msg = None

    if len(message.command) != 2:
        reply_msg = await message.reply_text(
            "**Usage:** `/redeem <code>`\n\n"
            "Example: `/redeem ABCD1234`\n\n"
            "Enter your 8-digit redeem code to get premium access!"
        )
        asyncio.create_task(auto_delete_message(message, reply_msg))
        return

    code = message.command[1].upper().strip()
    user_id = message.from_user.id
    user = message.from_user.mention

    # Validate code format
    if len(code) != 8 or not all(c in string.ascii_uppercase + string.digits for c in code):
        reply_msg = await message.reply_text("❌ Invalid code format! Code must be 8 characters (A-Z, 0-9).")
        asyncio.create_task(auto_delete_message(message, reply_msg))
        return

    # Check if user already has premium
    if await db.has_premium_access(user_id):
        data = await db.get_user(user_id)
        expiry = data.get("expiry_time") if data else None
        if expiry:
            expiry_str = expiry.astimezone(pytz.timezone("Asia/Kolkata")).strftime("%d-%m-%Y %I:%M:%S %p")
            reply_msg = await message.reply_text(
                f"⚠️ **You already have an active premium plan!**\n\n"
                f"⏰ Expires on: `{expiry_str}`\n\n"
                f"Use `/myplan` to check your plan details."
            )
        else:
            reply_msg = await message.reply_text(
                f"⚠️ **You already have lifetime premium access!**\n\n"
                f"Use `/myplan` to check your plan details."
            )
        asyncio.create_task(auto_delete_message(message, reply_msg))
        return

    # Verify code in database
    redeem_data = await db.get_redeem_code(code)

    if not redeem_data:
        reply_msg = await message.reply_text("❌ Invalid redeem code! Please check and try again.")
        asyncio.create_task(auto_delete_message(message, reply_msg))
        return

    if redeem_data.get("is_redeemed", False):
        redeemed_by = redeem_data.get("redeemed_by")
        if redeemed_by == user_id:
            reply_msg = await message.reply_text("⚠️ You have already redeemed this code!")
        else:
            reply_msg = await message.reply_text("❌ This code has already been redeemed by someone else!")
        asyncio.create_task(auto_delete_message(message, reply_msg))
        return

    # Redeem the code
    time_zone = datetime.datetime.now(pytz.timezone("Asia/Kolkata"))
    current_time = time_zone.strftime("%d-%m-%Y\n⏱️ ᴊᴏɪɴɪɴɢ ᴛɪᴍᴇ : %I:%M:%S %p")
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
        expiry_str = expiry_ist.strftime("%d-%m-%Y\n⏱️ ᴇxᴘɪʀʏ ᴛɪᴍᴇ : %I:%M:%S %p")
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
        f"🎉 **Premium Redeemed Successfully!**\n\n"
        f"👤 **User:** {user}\n"
        f"⚡ **User ID:** `{user_id}`\n"
        f"🎟️ **Code:** `{code}`\n"
        f"⏰ **Duration:** {duration}\n"
        f"⏳ **Joining Date:** {current_time}\n"
        f"⌛️ **Expiry Date:** {expiry_str}\n\n"
        f"✨ Enjoy your premium access!"
    )

    # Delete any messages containing the redeem code
    asyncio.create_task(delete_redeem_code_message(client, message.chat.id, code))

    # Log to premium logs
    await client.send_message(
        PREMIUM_LOGS,
        f"#Premium_Redeemed\n\n"
        f"👤 **User:** {user}\n"
        f"🆔 **User ID:** `{user_id}`\n"
        f"🎟️ **Code:** `{code}`\n"
        f"⏰ **Duration:** {duration}\n"
        f"🕐 **Redeemed At:** {redeemed_at.astimezone(pytz.timezone('Asia/Kolkata')).strftime('%d-%m-%Y %I:%M:%S %p')}\n"
        f"👑 **Generated By:** {redeem_data.get('generated_by_name', 'Unknown')}\n"
        f"⏳ **Joining Date:** {current_time}\n"
        f"⌛️ **Expiry Date:** {expiry_str}"
    )

    # Auto-delete messages
    asyncio.create_task(auto_delete_message(message, reply_msg))

@Client.on_message(filters.command("redeem_status") & filters.user(ADMINS))
async def redeem_status_handler(client, message):
    """Admin command to check status of redeem codes"""
    reply_msg = None

    if len(message.command) == 2:
        # Check specific code
        code = message.command[1].upper().strip()
        redeem_data = await db.get_redeem_code(code)

        if not redeem_data:
            reply_msg = await message.reply_text("❌ Code not found in database!")
            asyncio.create_task(auto_delete_message(message, reply_msg))
            return

        status = "✅ Redeemed" if redeem_data.get("is_redeemed") else "⏳ Available"
        generated_at = redeem_data.get("generated_at")
        generated_at_str = generated_at.astimezone(pytz.timezone("Asia/Kolkata")).strftime("%d-%m-%Y %I:%M:%S %p") if generated_at else "Unknown"

        response = (
            f"📋 **Code Status: `{code}`**\n\n"
            f"📊 **Status:** {status}\n"
            f"⏰ **Duration:** {redeem_data.get('duration', 'Unknown')}\n"
            f"👤 **Generated By:** {redeem_data.get('generated_by_name', 'Unknown')}\n"
            f"🕐 **Generated At:** {generated_at_str}\n"
        )

        if redeem_data.get("is_redeemed"):
            redeemed_at = redeem_data.get("redeemed_at")
            redeemed_at_str = redeemed_at.astimezone(pytz.timezone("Asia/Kolkata")).strftime("%d-%m-%Y %I:%M:%S %p") if redeemed_at else "Unknown"
            expiry = redeem_data.get("expiry_time")
            expiry_str = expiry.astimezone(pytz.timezone("Asia/Kolkata")).strftime("%d-%m-%Y %I:%M:%S %p") if expiry else "Lifetime"

            response += (
                f"🙋 **Redeemed By:** {redeem_data.get('redeemed_by_name', 'Unknown')}\n"
                f"🆔 **Redeemer ID:** `{redeem_data.get('redeemed_by', 'N/A')}`\n"
                f"🕐 **Redeemed At:** {redeemed_at_str}\n"
                f"⌛️ **Expiry Date:** {expiry_str}"
            )

        reply_msg = await message.reply_text(response)
    else:
        # Show overall statistics
        stats = await db.get_redeem_stats()
        total = stats.get("total", 0)
        redeemed = stats.get("redeemed", 0)
        available = stats.get("available", 0)

        reply_msg = await message.reply_text(
            f"📊 **Redeem Code Statistics**\n\n"
            f"📋 **Total Codes:** {total}\n"
            f"✅ **Redeemed:** {redeemed}\n"
            f"⏳ **Available:** {available}\n\n"
            f"Check specific code: `/redeem_status <code>`"
        )

    # Auto-delete messages
    asyncio.create_task(auto_delete_message(message, reply_msg))

@Client.on_message(filters.command("list_redeem") & filters.user(ADMINS))
async def list_redeem_codes_handler(client, message):
    """Admin command to list all redeem codes"""
    status_filter = None
    if len(message.command) == 2:
        arg = message.command[1].lower()
        if arg in ["redeemed", "used"]:
            status_filter = "redeemed"
        elif arg in ["available", "unused"]:
            status_filter = "available"

    aa = await message.reply_text("<i>Fetching redeem codes...</i>")

    codes = await db.get_all_redeem_codes(status_filter)

    if not codes:
        reply_msg = await aa.edit_text("No redeem codes found!")
        asyncio.create_task(auto_delete_message(message, reply_msg))
        return

    new = f"🎟️ **Redeem Codes List**\n\n"
    code_count = 1

    async for code_data in codes:
        code = code_data.get("code", "Unknown")
        duration = code_data.get("duration", "Unknown")
        is_redeemed = code_data.get("is_redeemed", False)

        if is_redeemed:
            redeemed_by = code_data.get("redeemed_by_name", "Unknown")
            status = f"✅ Redeemed by {redeemed_by}"
        else:
            status = "⏳ Available"

        new += f"{code_count}. `{code}` | {duration} | {status}\n"
        code_count += 1

    try:
        reply_msg = await aa.edit_text(new)
    except MessageTooLong:
        with open('redeem_codes_list.txt', 'w+') as outfile:
            outfile.write(new)
        reply_msg = await message.reply_document('redeem_codes_list.txt', caption="Redeem Codes List:")

    # Auto-delete messages
    asyncio.create_task(auto_delete_message(message, reply_msg))

@Client.on_message(filters.command("revoke_redeem") & filters.user(ADMINS))
async def revoke_redeem_code_handler(client, message):
    """Admin command to revoke a redeem code"""
    reply_msg = None

    if len(message.command) != 2:
        reply_msg = await message.reply_text("**Usage:** `/revoke_redeem <code>`\n\nRevokes a redeem code (only if not yet redeemed).")
        asyncio.create_task(auto_delete_message(message, reply_msg))
        return

    code = message.command[1].upper().strip()
    redeem_data = await db.get_redeem_code(code)

    if not redeem_data:
        reply_msg = await message.reply_text("❌ Code not found in database!")
        asyncio.create_task(auto_delete_message(message, reply_msg))
        return

    if redeem_data.get("is_redeemed", False):
        reply_msg = await message.reply_text("❌ Cannot revoke! This code has already been redeemed.")
        asyncio.create_task(auto_delete_message(message, reply_msg))
        return

    await db.delete_redeem_code(code)
    reply_msg = await message.reply_text(f"✅ Code `{code}` has been revoked successfully!")

    await client.send_message(
        PREMIUM_LOGS,
        f"#Redeem_Code_Revoked\n\n"
        f"🎟️ **Code:** `{code}`\n"
        f"👤 **Revoked By:** {message.from_user.mention}\n"
        f"🕐 **Time:** {datetime.datetime.now(pytz.timezone('Asia/Kolkata')).strftime('%d-%m-%Y %I:%M:%S %p')}"
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
            source_text = f"🎟️ **Redeemed Code:** `{redeemed_code}`"
        else:
            source_text = "👑 **Premium Source:** Admin Added"

        notification_text = (
            f"⏰ **Premium Expired Notification** ⏰\n\n"
            f"👋 Hello {user_mention or 'User'},\n\n"
            f"Your premium access has **expired**.\n\n"
            f"{source_text}\n\n"
            f"💔 You no longer have access to premium features.\n\n"
            f"✨ **Want to continue enjoying premium?**\n"
            f"Contact admins or use `/plan` to purchase a new plan!\n\n"
            f"Thank you for using our service! 😊"
        )

        # Send notification to user
        await client.send_message(
            chat_id=user_id,
            text=notification_text,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("💸 Check Premium Plans", callback_data="seeplans")],
                [InlineKeyboardButton("📞 Contact Support", url="https://t.me/your_support_link")]
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
                        f"#Auto_Expiry_Notification\n\n"
                        f"✅ **Successfully Notified:** {notified_count}\n"
                        f"❌ **Failed:** {failed_count}\n"
                        f"🕐 **Time:** {datetime.datetime.now(pytz.timezone('Asia/Kolkata')).strftime('%d-%m-%Y %I:%M:%S %p')}"
                    )
                except:
                    pass

        except Exception as e:
            print(f"Error in auto_notify_expired_users: {e}")

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
            reply_msg = await message.reply_text("ᴜꜱᴇʀ ʀᴇᴍᴏᴠᴇᴅ ꜱᴜᴄᴄᴇꜱꜱꜰᴜʟʟʏ !")
            await client.send_message(
                chat_id=user_id,
                text=f"<b>Hᴇʏ {user.mention},\n\nYᴏᴜʀ Pʀᴇᴍɪᴜᴍ Aᴄᴄᴇss Hᴀs Bᴇᴇɴ Rᴇᴍᴏᴠᴇᴅ.\nTʜᴀɴᴋ Yᴏᴜ Fᴏʀ Usɪɴɢ Oᴜʀ Sᴇʀᴠɪᴄᴇ 😊\nCʟɪᴄᴋ Oɴ /myplan Tᴏ Cʜᴇᴄᴋ Oᴜᴛ Oᴛʜᴇʀ Pʟᴀɴꜱ.</b>"
            )
        else:
            reply_msg = await message.reply_text("ᴜɴᴀʙʟᴇ ᴛᴏ ʀᴇᴍᴏᴠᴇ ᴜꜱᴇᴅ !\nᴀʀᴇ ʏᴏᴜ ꜱᴜʀᴇ, ɪᴛ ᴡᴀꜱ ᴀ ᴘʀᴇᴍɪᴜᴍ ᴜꜱᴇʀ ɪᴅ ?")
    else:
        reply_msg = await message.reply_text("ᴜꜱᴀɢᴇ : /remove_premium user_id")

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
            plan_info = f"⚜️ ᴘʀᴇᴍɪᴜᴍ ᴜꜱᴇʀ ᴅᴀᴛᴀ :\n\n👤 ᴜꜱᴇʀ : {user}\n⚡ ᴜꜱᴇʀ ɪᴅ : <code>{user_id}</code>\n⏰ ᴛɪᴍᴇ ʟᴇꜰᴛ : ʟɪꜰᴇᴛɪᴍᴇ"
            # Show premium source based on how it was obtained
            if premium_source == "redeem_code" and redeemed_code:
                plan_info += f"\n🎟️ ʀᴇᴅᴇᴇᴍᴇᴅ ᴄᴏᴅᴇ : <code>{redeemed_code}</code>"
            else:
                plan_info += f"\n👑 ᴘʀᴇᴍɪᴜᴍ ꜱᴏᴜʀᴄᴇ : ᴀᴅᴍɪɴ ᴀᴅᴅᴇᴅ"
            reply_msg = await message.reply_text(plan_info)
            asyncio.create_task(auto_delete_message(message, reply_msg))
            return

        # Calculate time left
        expiry_ist = expiry.astimezone(pytz.timezone("Asia/Kolkata"))
        expiry_str_in_ist = expiry_ist.strftime("%d-%m-%Y\n⏱️ ᴇxᴘɪʀʏ ᴛɪᴍᴇ : %I:%M:%S %p")
        current_time = datetime.datetime.now(pytz.timezone("Asia/Kolkata"))
        time_left = expiry_ist - current_time

        days = time_left.days
        hours, remainder = divmod(time_left.seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        time_left_str = f"{days} ᴅᴀʏꜱ, {hours} ʜᴏᴜʀꜱ, {minutes} ᴍɪɴᴜᴛᴇꜱ"

        plan_info = f"⚜️ ᴘʀᴇᴍɪᴜᴍ ᴜꜱᴇʀ ᴅᴀᴛᴀ :\n\n👤 ᴜꜱᴇʀ : {user}\n⚡ ᴜꜱᴇʀ ɪᴅ : <code>{user_id}</code>\n⏰ ᴛɪᴍᴇ ʟᴇꜰᴛ : {time_left_str}\n⌛️ ᴇxᴘɪʀʏ ᴅᴀᴛᴇ : {expiry_str_in_ist}"
        # Show premium source based on how it was obtained
        if premium_source == "redeem_code" and redeemed_code:
            plan_info += f"\n🎟️ ʀᴇᴅᴇᴇᴍᴇᴅ ᴄᴏᴅᴇ : <code>{redeemed_code}</code>"
        else:
            plan_info += f"\n👑 ᴘʀᴇᴍɪᴜᴍ ꜱᴏᴜʀᴄᴇ : ᴀᴅᴍɪɴ ᴀᴅᴅᴇᴅ"

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
            f"⏰ **Premium Expired** ⏰\n\n"
            f"Hᴇʏ {user},\n\n"
            f"Your premium access has **expired**.\n\n"
        )
        if expiry:
            expiry_ist = expiry.astimezone(pytz.timezone("Asia/Kolkata"))
            expiry_str = expiry_ist.strftime("%d-%m-%Y %I:%M:%S %p")
            expired_text += f"⌛️ **Expired On:** `{expiry_str}`\n\n"

        expired_text += (
            f"✨ **Want to continue enjoying premium?**\n"
        )

        reply_msg = await message.reply_text(
            expired_text,
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("💸 Cʜᴇᴄᴋᴏᴜᴛ Pʀᴇᴍɪᴜᴍ Pʟᴀɴꜱ 💸", callback_data="seeplans")]]
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
        current_time = time_zone.strftime("%d-%m-%Y\n⏱️ ᴊᴏɪɴɪɴɢ ᴛɪᴍᴇ : %I:%M:%S %p") 
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
            reply_msg = await message.reply_text(f"ᴘʀᴇᴍɪᴜᴍ ᴀᴅᴅᴇᴅ ꜱᴜᴄᴄᴇꜱꜱꜰᴜʟʟʏ ✅\n\n👤 ᴜꜱᴇʀ : {user.mention}\n⚡ ᴜꜱᴇʀ ɪᴅ : <code>{user_id}</code>\n⏰ ᴘʀᴇᴍɪᴜᴍ ᴀᴄᴄᴇꜱꜱ : <code>{time}</code>\n\n⏳ ᴊᴏɪɴɪɴɢ ᴅᴀᴛᴇ : {current_time}\n\n⌛️ ᴇxᴘɪʀʏ ᴅᴀᴛᴇ : {expiry_str_in_ist}", disable_web_page_preview=True)
            await client.send_message(
                chat_id=user_id,
                text=f"👋 ʜᴇʏ {user.mention},\nᴛʜᴀɴᴋ ʏᴏᴜ ꜰᴏʀ ᴘᴜʀᴄʜᴀsɪɴɢ ᴘʀᴇᴍɪᴜᴍ.\nᴇɴᴊᴏʏ !! ✨🎉\n\n⏰ ᴘʀᴇᴍɪᴜᴍ ᴀᴄᴄᴇꜱꜱ : <code>{time}</code>\n⏳ ᴊᴏɪɴɪɴɢ ᴅᴀᴛᴇ : {current_time}\n\n⌛️ ᴇxᴘɪʀʏ ᴅᴀᴛᴇ : {expiry_str_in_ist}", disable_web_page_preview=True              
            )    
            await client.send_message(PREMIUM_LOGS, text=f"#Added_Premium\n\n👤 ᴜꜱᴇʀ : {user.mention}\n⚡ ᴜꜱᴇʀ ɪᴅ : <code>{user_id}</code>\n⏰ ᴘʀᴇᴍɪᴜᴍ ᴀᴄᴄᴇꜱꜱ : <code>{time}</code>\n\n⏳ ᴊᴏɪɴɪɴɢ ᴅᴀᴛᴇ : {current_time}\n\n⌛️ ᴇxᴘɪʀʏ ᴅᴀᴛᴇ : {expiry_str_in_ist}", disable_web_page_preview=True)

        else:
            reply_msg = await message.reply_text("Invalid time format. Please use '1 day for days', '1 hour for hours', or '1 min for minutes', or '1 month for months' or '1 year for year'")
    else:
        reply_msg = await message.reply_text("Usage : /add_premium user_id time (e.g., '1 day for days', '1 hour for hours', or '1 min for minutes', or '1 month for months' or '1 year for year')")

    # Auto-delete messages
    if reply_msg:
        asyncio.create_task(auto_delete_message(message, reply_msg))
    else:
        asyncio.create_task(auto_delete_message(message))

@Client.on_message(filters.command("premium_users") & filters.user(ADMINS))
async def premium_user(client, message):
    aa = await message.reply_text("<i>ꜰᴇᴛᴄʜɪɴɢ...</i>")
    new = f"⚜️ ᴘʀᴇᴍɪᴜᴍ ᴜꜱᴇʀꜱ ʟɪꜱᴛ :\n\n"
    user_count = 1
    users = await db.get_all_premium_users()
    async for user in users:
        if not await db.has_premium_access(user['id']):
            continue
        data = await db.get_user(user['id'])
        expiry = data.get("expiry_time") if data else None
        if not expiry:
            new += f"{user_count}. {(await client.get_users(user['id'])).mention}\n👤 ᴜꜱᴇʀ ɪᴅ : {user['id']}\n⏰ ᴛɪᴍᴇ ʟᴇꜰᴛ : ʟɪꜰᴇᴛɪᴍᴇ\n"
            user_count += 1
            continue

        expiry_ist = expiry.astimezone(pytz.timezone("Asia/Kolkata"))
        expiry_str_in_ist = expiry_ist.strftime("%d-%m-%Y\n⏱️ ᴇxᴘɪʀʏ ᴛɪᴍᴇ : %I:%M:%S %p")            
        current_time = datetime.datetime.now(pytz.timezone("Asia/Kolkata"))
        time_left = expiry_ist - current_time
        if time_left.total_seconds() <= 0:
            await db.remove_premium_access(user['id'])
            continue
        days = time_left.days
        hours, remainder = divmod(time_left.seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        time_left_str = f"{days} days, {hours} hours, {minutes} minutes"	 
        new += f"{user_count}. {(await client.get_users(user['id'])).mention}\n👤 ᴜꜱᴇʀ ɪᴅ : {user['id']}\n⏳ ᴇxᴘɪʀʏ ᴅᴀᴛᴇ : {expiry_str_in_ist}\n⏰ ᴛɪᴍᴇ ʟᴇꜰᴛ : {time_left_str}\n"
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
    reply_msg = await message.reply_photo(photo="https://graph.org/file/7d8b428734782477158d4.jpg", caption=script.PREMIUM_TEXT.format(message.from_user.mention), reply_markup=InlineKeyboardMarkup(btn))

    # Auto-delete messages
    asyncio.create_task(auto_delete_message(message, reply_msg))

# SPECIAL THANKS TO [Rishikesh Sharma] @Rk_botowner FOR THESE AMAZING CODES
# SPECIAL THANKS TO @DeletedFromEarth FOR MODIFYING THESE AMAZING CODES 
