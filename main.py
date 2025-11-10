from telethon import TelegramClient, events
from telethon.tl.types import MessageEntityTextUrl, DocumentAttributeAudio
from telethon import functions
from telethon import types
from googletrans import Translator
import asyncio
import os
import pytesseract
from PIL import Image
from datetime import datetime
import requests
import json
import sys
import time
import math
import random
import qrcode

# تنظیمات اتصال
api_id = '###'  # Replace with your API ID
api_hash = '######'  # Replace with your API hash
session_name = 'session'

# Create client with connection parameters
client = TelegramClient(session_name, api_id, api_hash)

# Custom phone callback function for more reliable authentication
async def phone_callback(phone_requested):
    # Read the phone number from a file - will be set during setup
    try:
        phone_file = os.path.join(os.path.dirname(__file__), 'phone.txt')
        if os.path.exists(phone_file):
            with open(phone_file, 'r') as f:
                phone = f.read().strip()
                return phone
    except Exception as e:
        print(f"Error reading phone number: {e}")
    
    # Fallback to a default number if the file doesn't exist
    return None

# Set the phone callback on the client
client.phone_callback = phone_callback

translator = Translator()

# ذخیره موزیک و ویدئو
saved_media = {'music': {}, 'video': {}}
card_number = None
card_name = None
typing_list = set()
typing_all_list = set()
pm_messages = {}
pm_all_messages = {}
filtered_words = set()
allowed_words = set()

# Add these global variables at the top with other global variables
silent_users = set()  # For Silent command
watched_users = set()  # For Eyes command
anti_login = False  # For AntiLogin command
monshi_text = None  # For monshi command
monshi_enabled = False  # For monshi command
ad_tasks = {}  # For AdsPM command
secret_mode = False  # For secret mode

def save_media_data():
    with open('media_data.json', 'w', encoding='utf-8') as f:
        json.dump({
            'media': saved_media,
            'card': card_number,
            'card_name': card_name,
            'typing_list': list(typing_list),
            'typing_all_list': list(typing_all_list),
            'pm_messages': pm_messages,
            'pm_all_messages': pm_all_messages,
            'filtered_words': list(filtered_words),
            'allowed_words': list(allowed_words),
            'silent_users': list(silent_users),
            'watched_users': list(watched_users),
            'anti_login': anti_login,
            'monshi_text': monshi_text,
            'monshi_enabled': monshi_enabled,
            'ad_tasks': ad_tasks,
            'secret_mode': secret_mode
        }, f, ensure_ascii=False)

def load_media_data():
    global saved_media, card_number, card_name, typing_list, typing_all_list, pm_messages, pm_all_messages, filtered_words, allowed_words, silent_users, watched_users, anti_login, monshi_text, monshi_enabled, ad_tasks, secret_mode
    try:
        with open('media_data.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
            saved_media = data.get('media', {'music': {}, 'video': {}})
            card_number = data.get('card', None)
            card_name = data.get('card_name', None)
            typing_list = set(data.get('typing_list', []))
            typing_all_list = set(data.get('typing_all_list', []))
            pm_messages = data.get('pm_messages', {})
            pm_all_messages = data.get('pm_all_messages', {})
            filtered_words = set(data.get('filtered_words', []))
            allowed_words = set(data.get('allowed_words', []))
            silent_users = set(data.get('silent_users', []))
            watched_users = set(data.get('watched_users', []))
            anti_login = data.get('anti_login', False)
            monshi_text = data.get('monshi_text', None)
            monshi_enabled = data.get('monshi_enabled', False)
            ad_tasks = data.get('ad_tasks', {})
            secret_mode = data.get('secret_mode', False)
    except FileNotFoundError:
        saved_media = {'music': {}, 'video': {}}
        card_number = None
        card_name = None
        typing_list = set()
        typing_all_list = set()
        pm_messages = {}
        pm_all_messages = {}
        filtered_words = set()
        allowed_words = set()
        silent_users = set()
        watched_users = set()
        anti_login = False
        monshi_text = None
        monshi_enabled = False
        ad_tasks = {}
        secret_mode = False

@client.on(events.NewMessage(outgoing=True, pattern=r'^Str (.+)'))
async def translate_text(event):
    if event.is_reply:
        reply = await event.get_reply_message()
        dest = event.pattern_match.group(1)
        translated = translator.translate(reply.text, dest=dest)
        await event.reply(f"🌍 ترجمه:\n{translated.text}")
    else:
        await event.reply("لطفا روی یک پیام ریپلای کنید.")

@client.on(events.NewMessage(outgoing=True, pattern=r'^SEditName (.+)'))
async def edit_name(event):
    if event.is_reply:
        reply = await event.get_reply_message()
        new_name = event.pattern_match.group(1)
        if reply.file:
            file = await reply.download_media()
            await event.respond(file=file, file_name=new_name)
            os.remove(file)
        else:
            await event.reply("فقط روی فایل ریپلای کنید.")

@client.on(events.NewMessage(outgoing=True, pattern=r'^SWeather (.+)$'))
async def weather(event):
    city = event.pattern_match.group(1)
    try:
        response = requests.get(f'https://wttr.in/{city}?format=%l+%c+%t+%w+%h+%p', headers={'User-Agent': 'curl'})
        if response.status_code == 200:
            weather_info = response.text.strip()
            await event.reply(f"🌤 آب و هوای {city}:\n{weather_info}")
        else:
            await event.reply("❌ شهر پیدا نشد.")
    except Exception as e:
        await event.reply("❌ خطا در دریافت اطلاعات آب و هوا.")

@client.on(events.NewMessage(outgoing=True, pattern=r'^S(Photo|Sticker|Gif|Voice)$'))
async def file_convert(event):
    command = event.pattern_match.group(1).lower()
    if event.is_reply:
        reply = await event.get_reply_message()
        file = await reply.download_media()
        if command == 'photo' and reply.file.mime_type.startswith('image/webp'):
            await event.respond(file=file)
        elif command == 'sticker' and reply.file.mime_type.startswith('image/'):
            await event.respond(file=file, force_document=False, mime_type='image/webp')
        elif command == 'gif' and reply.video_note:
            await event.respond(file=file, attributes=[DocumentAttributeAnimated()])
        elif command == 'voice' and (reply.file.mime_type.startswith('audio') or reply.file.mime_type.startswith('video')):
            await event.respond(file=file, attributes=[DocumentAttributeAudio(voice=True)])
        os.remove(file)
    else:
        await event.reply("ریپلای کن روی فایل مورد نظر.")

@client.on(events.NewMessage(outgoing=True, pattern=r'(?i)^ChInfo (.+)$'))
async def channel_info(event):
    channel_id = event.pattern_match.group(1)
    entity = await client.get_entity(channel_id)
    await event.reply(f"📄 نام: {entity.title}\n🆔 آیدی: {entity.id}\n🔗 یوزرنیم: @{entity.username}")

@client.on(events.NewMessage(outgoing=True, pattern=r'(?i)^BackUpChat$'))
async def backup_chat(event):
    messages = []
    async for msg in client.iter_messages(event.chat_id, limit=1500):
        messages.append(f"{msg.sender_id}: {msg.text}")
    file = '\n'.join(messages)
    with open('backup.txt', 'w', encoding='utf-8') as f:
        f.write(file)
    await client.send_file('me', 'backup.txt', caption="📄 بکاپ چت")

@client.on(events.NewMessage(outgoing=True, pattern=r'(?i)^SRank (.+)$'))
async def set_rank(event):
    if event.is_reply:
        replied = await event.get_reply_message()
        await client(functions.contacts.EditNameRequest(
            user_id=replied.sender_id,
            first_name=event.pattern_match.group(1),
            last_name=""
        ))
        await event.reply("✅ لقب تنظیم شد.")
    else:
        await event.reply("⚠️ لطفاً روی پیام کاربر ریپلای کنید.")

@client.on(events.NewMessage(outgoing=True, pattern=r'(?i)^CreateGP (.+)$'))
async def create_group(event):
    name = event.pattern_match.group(1)
    await client(functions.messages.CreateChatRequest(
        users=[],
        title=name
    ))
    await event.reply(f"✅ گروه '{name}' ساخته شد.")

@client.on(events.NewMessage(outgoing=True, pattern=r'(?i)^CreateCH (.+)$'))
async def create_channel(event):
    name = event.pattern_match.group(1)
    await client(functions.channels.CreateChannelRequest(
        title=name,
        about="ساخته شده توسط ربات",
        megagroup=False
    ))
    await event.reply(f"✅ کانال '{name}' ساخته شد.")

@client.on(events.NewMessage(outgoing=True, pattern=r'(?i)^AddProfile$'))
async def add_profile_photo(event):
    if event.is_reply:
        replied = await event.get_reply_message()
        if replied.photo:
            path = await replied.download_media()
            await client(functions.photos.UploadProfilePhotoRequest(file=await client.upload_file(path)))
            await event.reply("✅ عکس پروفایل آپلود شد.")
    else:
        await event.reply("⚠️ روی عکس ریپلای کنید.")

@client.on(events.NewMessage(outgoing=True, pattern=r'(?i)^Time$'))
async def time_command(event):
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    await event.reply(f"🕰 زمان فعلی:\n{now}")

@client.on(events.NewMessage(outgoing=True, pattern=r'(?i)^GetContacts$'))
async def get_contacts(event):
    contacts = await client(functions.contacts.GetContactsRequest(hash=0))
    lines = [f"{user.phone}\t{user.first_name}" for user in contacts.users]
    file = '\n'.join(lines)
    with open('contacts.txt', 'w', encoding='utf-8') as f:
        f.write(file)
    await client.send_file('me', 'contacts.txt', caption="📇 لیست مخاطبین شما")

@client.on(events.NewMessage(outgoing=True, pattern=r'(?i)^Ping$'))
async def ping_command(event):
    await event.reply("✅ ربات آنلاین است!")

@client.on(events.NewMessage(outgoing=True, pattern=r'(?i)^Reload$'))
async def reload_command(event):
    await event.reply("🔄 در حال بارگذاری مجدد...")
    os.execv(sys.executable, ['python'] + sys.argv)

@client.on(events.NewMessage(outgoing=True, pattern=r'(?i)^SetName (.+)$'))
async def set_name(event):
    name = event.pattern_match.group(1)
    await client(functions.account.UpdateProfileRequest(
        first_name=name
    ))
    await event.reply("✅ نام شما تغییر کرد.")

@client.on(events.NewMessage(outgoing=True, pattern=r'(?i)^SetBio (.+)$'))
async def set_bio(event):
    bio = event.pattern_match.group(1)
    await client(functions.account.UpdateProfileRequest(
        about=bio
    ))
    await event.reply("✅ بیوگرافی شما تغییر کرد.")

@client.on(events.NewMessage(outgoing=True, pattern=r'(?i)^SaveMusic (.+)$'))
async def save_music(event):
    if event.is_reply:
        replied = await event.get_reply_message()
        if replied.audio or replied.voice:
            name = event.pattern_match.group(1)
            file = await replied.download_media()
            saved_media['music'][name] = file
            save_media_data()
            await event.reply(f"✅ موزیک '{name}' ذخیره شد.")
        else:
            await event.reply("⚠️ روی موزیک یا ویس ریپلای کنید.")
    else:
        await event.reply("⚠️ لطفاً روی موزیک ریپلای کنید.")

@client.on(events.NewMessage(outgoing=True, pattern=r'(?i)^DelMusic (.+)$'))
async def del_music(event):
    name = event.pattern_match.group(1)
    if name in saved_media['music']:
        os.remove(saved_media['music'][name])
        del saved_media['music'][name]
        save_media_data()
        await event.reply(f"✅ موزیک '{name}' حذف شد.")
    else:
        await event.reply("⚠️ موزیک مورد نظر یافت نشد.")

@client.on(events.NewMessage(outgoing=True, pattern=r'(?i)^GetMusic (.+)$'))
async def get_music(event):
    name = event.pattern_match.group(1)
    if name in saved_media['music']:
        await client.send_file(event.chat_id, saved_media['music'][name])
    else:
        await event.reply("⚠️ موزیک مورد نظر یافت نشد.")

@client.on(events.NewMessage(outgoing=True, pattern=r'(?i)^Musics$'))
async def list_musics(event):
    if saved_media['music']:
        text = "🎵 موزیک‌های ذخیره شده:\n\n"
        for name in saved_media['music']:
            text += f"• {name}\n"
        await event.reply(text)
    else:
        await event.reply("⚠️ هیچ موزیکی ذخیره نشده است.")

@client.on(events.NewMessage(outgoing=True, pattern=r'(?i)^Clean Musics$'))
async def clean_musics(event):
    for file in saved_media['music'].values():
        try:
            os.remove(file)
        except:
            pass
    saved_media['music'] = {}
    save_media_data()
    await event.reply("✅ لیست موزیک‌ها پاک شد.")

@client.on(events.NewMessage(outgoing=True, pattern=r'(?i)^SaveVideo (.+)$'))
async def save_video(event):
    if event.is_reply:
        replied = await event.get_reply_message()
        if replied.video:
            name = event.pattern_match.group(1)
            file = await replied.download_media()
            saved_media['video'][name] = file
            save_media_data()
            await event.reply(f"✅ ویدئو '{name}' ذخیره شد.")
        else:
            await event.reply("⚠️ روی ویدئو ریپلای کنید.")
    else:
        await event.reply("⚠️ لطفاً روی ویدئو ریپلای کنید.")

@client.on(events.NewMessage(outgoing=True, pattern=r'(?i)^DelVideo (.+)$'))
async def del_video(event):
    name = event.pattern_match.group(1)
    if name in saved_media['video']:
        os.remove(saved_media['video'][name])
        del saved_media['video'][name]
        save_media_data()
        await event.reply(f"✅ ویدئو '{name}' حذف شد.")
    else:
        await event.reply("⚠️ ویدئو مورد نظر یافت نشد.")

@client.on(events.NewMessage(outgoing=True, pattern=r'(?i)^GetVideo (.+)$'))
async def get_video(event):
    name = event.pattern_match.group(1)
    if name in saved_media['video']:
        await client.send_file(event.chat_id, saved_media['video'][name])
    else:
        await event.reply("⚠️ ویدئو مورد نظر یافت نشد.")

@client.on(events.NewMessage(outgoing=True, pattern=r'(?i)^Videos$'))
async def list_videos(event):
    if saved_media['video']:
        text = "🎥 ویدئو‌های ذخیره شده:\n\n"
        for name in saved_media['video']:
            text += f"• {name}\n"
        await event.reply(text)
    else:
        await event.reply("⚠️ هیچ ویدئویی ذخیره نشده است.")

@client.on(events.NewMessage(outgoing=True, pattern=r'(?i)^Clean Videos$'))
async def clean_videos(event):
    for file in saved_media['video'].values():
        try:
            os.remove(file)
        except:
            pass
    saved_media['video'] = {}
    save_media_data()
    await event.reply("✅ لیست ویدئو‌ها پاک شد.")

@client.on(events.NewMessage(outgoing=True, pattern=r'(?i)^Say (.+)$'))
async def say_command(event):
    text = event.pattern_match.group(1)
    words = text.split()
    for word in words:
        await event.reply(word)
        await asyncio.sleep(0.5)

@client.on(events.NewMessage(outgoing=True, pattern=r'(?i)^SetCard (\d+) (.+)$'))
async def set_card(event):
    global card_number, card_name
    card_number = event.pattern_match.group(1)
    card_name = event.pattern_match.group(2)
    save_media_data()
    await event.reply(f"✅ شماره کارت ذخیره شد:\n`{card_number}`\nبه نام: {card_name}")

@client.on(events.NewMessage(outgoing=True, pattern=r'(?i)^Card$'))
async def get_card(event):
    if card_number:
        await event.reply(f"شماره کارت:\n`{card_number}`\nبه نام: {card_name}")
    else:
        await event.reply("⚠️ شماره کارتی ذخیره نشده است.")

@client.on(events.NewMessage(outgoing=True, pattern=r'(?i)^DelCard$'))
async def del_card(event):
    global card_number
    card_number = None
    save_media_data()
    await event.reply("✅ شماره کارت حذف شد.")

@client.on(events.NewMessage(outgoing=True, pattern=r'(?i)^calc (.+)$'))
async def calculator(event):
    try:
        expression = event.pattern_match.group(1)
        result = eval(expression)
        await event.reply(f"🧮 نتیجه:\n{result}")
    except:
        await event.reply("❌ خطا در محاسبه")

@client.on(events.NewMessage(outgoing=True, pattern=r'(?i)^Age (.+)$'))
async def age_command(event):
    try:
        days, months, years = map(int, event.pattern_match.group(1).split('/'))
        total_days = days + (months * 30) + (years * 365)
        total_months = total_days / 30
        total_years = total_days / 365
        
        await event.reply(
            f"📅 اطلاعات سن:\n"
            f"• روز: {total_days}\n"
            f"• ماه: {math.floor(total_months)}\n"
            f"• سال: {math.floor(total_years)}"
        )
    except:
        await event.reply("❌ فرمت اشتباه. از فرمت Rooz/Mah/Sal استفاده کنید.")

@client.on(events.NewMessage(outgoing=True, pattern=r'(?i)^Sinfo$'))
async def user_info(event):
    if event.is_reply:
        replied = await event.get_reply_message()
        user = await client.get_entity(replied.sender_id)
        
        # Get mutual groups count
        mutual_groups = 0
        async for dialog in client.iter_dialogs():
            if dialog.is_group and dialog.entity.id in [p.id for p in await client.get_participants(dialog.id)]:
                mutual_groups += 1
        
        # Get user's status
        status = "آنلاین" if user.status else "آفلاین"
        if hasattr(user.status, 'was_online'):
            status = f"اخیراً ({user.status.was_online.strftime('%Y-%m-%d %H:%M:%S')})"
        
        # Get profile photos count
        photos = await client.get_profile_photos(user.id)
        photos_count = len(photos)
        
        await event.reply(
            f"👤 اطلاعات کاربر:\n"
            f"نام: ({user.first_name} {user.last_name or ''})\n"
            f"شناسه: ({user.id})\n"
            f"نام کاربری: (@{user.username or 'ندارد'})\n"
            f"تعداد پروفایل: ({photos_count})\n"
            f"وضعیت: ({status})\n"
            f"گروه های مشترک: ({mutual_groups})\n"
            f"بیوگرافی: ({user.about or 'ندارد'})"
        )
    else:
        await event.reply("⚠️ لطفاً روی پیام کاربر ریپلای کنید.")

@client.on(events.NewMessage(outgoing=True, pattern=r'(?i)^Addc$'))
async def add_contact(event):
    if event.is_reply:
        try:
            replied = await event.get_reply_message()
            user = await client.get_entity(replied.sender_id)
            await client(functions.contacts.AddContactRequest(
                id=user.id,
                first_name=user.first_name,
                last_name=user.last_name or "",
                phone=user.phone or ""
            ))
            await event.reply("✅ مخاطب ذخیره شد.")
        except Exception as e:
            await event.reply("❌ خطا در ذخیره مخاطب.")
    else:
        await event.reply("⚠️ لطفاً روی پیام کاربر ریپلای کنید.")

@client.on(events.NewMessage(outgoing=True, pattern=r'(?i)^Share$'))
async def share_phone(event):
    me = await client.get_me()
    if me.phone:
        await event.reply(f"📱 شماره من:\n{me.phone}")
    else:
        await event.reply("⚠️ شماره تلفن یافت نشد.")

@client.on(events.NewMessage(outgoing=True, pattern=r'(?i)^Del$'))
async def delete_message(event):
    if event.is_reply:
        replied = await event.get_reply_message()
        await client.delete_messages(event.chat_id, [replied.id])
        await event.reply("✅ پیام حذف شد.")
    else:
        await event.reply("⚠️ لطفاً روی پیام مورد نظر ریپلای کنید.")

@client.on(events.NewMessage(outgoing=True, pattern=r'(?i)^Save$'))
async def save_message(event):
    if event.is_reply:
        replied = await event.get_reply_message()
        await client.forward_messages('me', [replied.id], event.chat_id)
        await event.reply("✅ پیام ذخیره شد.")
    else:
        await event.reply("⚠️ لطفاً روی پیام مورد نظر ریپلای کنید.")

@client.on(events.NewMessage(outgoing=True, pattern=r'(?i)^id$'))
async def get_id_reply(event):
    if event.is_reply:
        replied = await event.get_reply_message()
        await event.reply(f"🆔 شناسه کاربر: {replied.sender_id}")
    else:
        await event.reply("⚠️ لطفاً روی پیام کاربر ریپلای کنید.")

@client.on(events.NewMessage(outgoing=True, pattern=r'(?i)^id @(.+)$'))
async def get_id_username(event):
    username = event.pattern_match.group(1)
    try:
        user = await client.get_entity(username)
        await event.reply(f"🆔 شناسه کاربر: {user.id}")
    except Exception as e:
        await event.reply("❌ کاربر یافت نشد.")

@client.on(events.NewMessage(outgoing=True, pattern=r'(?i)^whois (.+)$'))
async def get_username(event):
    user_id = event.pattern_match.group(1)
    try:
        user = await client.get_entity(int(user_id))
        await event.reply(f"👤 یوزرنیم: @{user.username or 'ندارد'}")
    except:
        await event.reply("❌ کاربر یافت نشد.")

@client.on(events.NewMessage(outgoing=True, pattern=r'(?i)^Myid$'))
async def get_my_id(event):
    me = await client.get_me()
    await event.reply(f"🆔 شناسه شما: {me.id}")

@client.on(events.NewMessage(outgoing=True, pattern=r'(?i)^gpid$'))
async def get_group_id(event):
    await event.reply(f"🆔 شناسه گروه: {event.chat_id}")

@client.on(events.NewMessage(outgoing=True, pattern=r'(?i)^MyName$'))
async def get_my_name(event):
    me = await client.get_me()
    await event.reply(f"👤 نام شما: {me.first_name} {me.last_name or ''}")

@client.on(events.NewMessage(outgoing=True, pattern=r'(?i)^MyPhone$'))
async def get_my_phone(event):
    me = await client.get_me()
    if me.phone:
        await event.reply(f"📱 شماره شما: {me.phone}")
    else:
        await event.reply("⚠️ شماره تلفن یافت نشد.")

@client.on(events.NewMessage(outgoing=True, pattern=r'(?i)^SPm (.+)$'))
async def send_pm(event):
    if event.is_reply:
        try:
            replied = await event.get_reply_message()
            text = event.pattern_match.group(1)
            await client.send_message(replied.sender_id, text)
            await event.reply("✅ پیام ارسال شد.")
        except Exception as e:
            await event.reply("❌ امکان ارسال پیام وجود ندارد.")
    else:
        await event.reply("⚠️ لطفاً روی پیام کاربر ریپلای کنید.")

@client.on(events.NewMessage(outgoing=True, pattern=r'(?i)^Block$'))
async def block_user(event):
    if event.is_reply:
        replied = await event.get_reply_message()
        try:
            await client(functions.contacts.BlockRequest(id=replied.sender_id))
            await event.reply("✅ کاربر بلاک شد.")
        except:
            await event.reply("❌ خطا در بلاک کردن کاربر.")
    else:
        await event.reply("⚠️ لطفاً روی پیام کاربر ریپلای کنید.")

@client.on(events.NewMessage(outgoing=True, pattern=r'(?i)^UnBlock$'))
async def unblock_user(event):
    if event.is_reply:
        replied = await event.get_reply_message()
        try:
            await client(functions.contacts.UnblockRequest(id=replied.sender_id))
            await event.reply("✅ بلاک کاربر لغو شد.")
        except:
            await event.reply("❌ خطا در لغو بلاک کاربر.")
    else:
        await event.reply("⚠️ لطفاً روی پیام کاربر ریپلای کنید.")

@client.on(events.NewMessage(outgoing=True, pattern=r'(?i)^Typing$'))
async def add_typing(event):
    if event.is_reply:
        replied = await event.get_reply_message()
        typing_list.add(replied.sender_id)
        save_media_data()
        await event.reply("✅ کاربر به لیست تایپینگ اضافه شد.")
    else:
        await event.reply("⚠️ لطفاً روی پیام کاربر ریپلای کنید.")

@client.on(events.NewMessage(outgoing=True, pattern=r'(?i)^UnTyping$'))
async def remove_typing(event):
    if event.is_reply:
        replied = await event.get_reply_message()
        typing_list.discard(replied.sender_id)
        save_media_data()
        await event.reply("✅ کاربر از لیست تایپینگ حذف شد.")
    else:
        await event.reply("⚠️ لطفاً روی پیام کاربر ریپلای کنید.")

@client.on(events.NewMessage(outgoing=True, pattern=r'(?i)^TypingList$'))
async def show_typing_list(event):
    if typing_list:
        text = "📝 لیست تایپینگ:\n\n"
        for user_id in typing_list:
            try:
                user = await client.get_entity(user_id)
                text += f"• @{user.username or 'ندارد'} ({user_id})\n"
            except:
                text += f"• {user_id}\n"
        await event.reply(text)
    else:
        await event.reply("⚠️ لیست تایپینگ خالی است.")

@client.on(events.NewMessage(outgoing=True, pattern=r'(?i)^Clean TypingList$'))
async def clean_typing_list(event):
    typing_list.clear()
    save_media_data()
    await event.reply("✅ لیست تایپینگ پاک شد.")

@client.on(events.NewMessage(outgoing=True, pattern=r'(?i)^TypingAll$'))
async def add_typing_all(event):
    if event.is_reply:
        replied = await event.get_reply_message()
        typing_all_list.add(replied.sender_id)
        save_media_data()
        await event.reply("✅ کاربر به لیست تایپینگ همه‌گانی اضافه شد.")
    else:
        await event.reply("⚠️ لطفاً روی پیام کاربر ریپلای کنید.")

@client.on(events.NewMessage(outgoing=True, pattern=r'(?i)^UnTypingAll$'))
async def remove_typing_all(event):
    if event.is_reply:
        replied = await event.get_reply_message()
        typing_all_list.discard(replied.sender_id)
        save_media_data()
        await event.reply("✅ کاربر از لیست تایپینگ همه‌گانی حذف شد.")
    else:
        await event.reply("⚠️ لطفاً روی پیام کاربر ریپلای کنید.")

@client.on(events.NewMessage(outgoing=True, pattern=r'(?i)^TypingAllList$'))
async def show_typing_all_list(event):
    if typing_all_list:
        text = "📝 لیست تایپینگ همه‌گانی:\n\n"
        for user_id in typing_all_list:
            try:
                user = await client.get_entity(user_id)
                text += f"• @{user.username or 'ندارد'} ({user_id})\n"
            except:
                text += f"• {user_id}\n"
        await event.reply(text)
    else:
        await event.reply("⚠️ لیست تایپینگ همه‌گانی خالی است.")

@client.on(events.NewMessage(incoming=True))
async def handle_typing_and_pm(event):
    # Handle typing
    if event.sender_id in typing_list:
        await client.action(event.chat_id, 'typing')
    if event.sender_id in typing_all_list:
        await client.action(event.chat_id, 'typing')
    
    # Handle PM auto-reply
    if event.sender_id in pm_messages and pm_messages[event.sender_id]:
        await asyncio.sleep(1)
        await event.reply(random.choice(pm_messages[event.sender_id]))
    
    if event.sender_id in pm_all_messages and pm_all_messages[event.sender_id]:
        await asyncio.sleep(1)
        await event.reply(random.choice(pm_all_messages[event.sender_id]))

@client.on(events.NewMessage(outgoing=True, pattern=r'(?i)^SHelp$'))
async def help_command(event):
    help_texts = [
        """
🎯 دستورات پایه و رسانه (قسمت 1):

📌 دستورات اطلاعات:
⚡️ `ChInfo` شناسه کانال
💠 نمایش اطلاعات شناسه یک کانال
━━━━━━━━━━━━━━━━━━━━
⚡️ `Str` زبان با ریپلی!
💠 نمایش ترجمه یک متن با ریپلی
━━━━━━━━━━━━━━━━━━━━
⚡️ `SEditName` نام جدید با ریپلی!
💠 تغییر نام اهنگ یا فایل 
💎 در بخش نام جدید باید نام جدید همراه با فرمت نوشته شود.
━━━━━━━━━━━━━━━━━━━━
⚡️ `SWeather` نام شهر
💠 نمایش اب و هوای شهر
━━━━━━━━━━━━━━━━━━━━

📌 دستورات تبدیل رسانه:
⚡️ `SPhoto` با ریپلی!
💠 تبدیل استیکر به عکس با ریپلی
━━━━━━━━━━━━━━━━━━━━
⚡️ `SSticker` با ریپلی!
💠 تبدیل عکس به استیکر با ریپلی
━━━━━━━━━━━━━━━━━━━━
⚡️ `SGif` با ریپلی!
💠 تبدیل فیلم به گیف با ریپلی
━━━━━━━━━━━━━━━━━━━━
⚡️ `SVoice` با ریپلی!
💠 تبدیل ویدئو و موزیک به ویس
━━━━━━━━━━━━━━━━━━━━

📌 دستورات مدیریت:
⚡️ `BackUpChat`
💠 دریافت 1500 چت اخیر در قالب فایل.
━━━━━━━━━━━━━━━━━━━━
⚡️ `SRank` لقب با ریپلی!
💠 تنظیم لقب برای یک فرد ، با ریپلی
━━━━━━━━━━━━━━━━━━━━
⚡️ `CreateGP` نام
💠 ایجاد گروه
━━━━━━━━━━━━━━━━━━━━
🔥 `CreateCH` نام
💠 ایجاد کانال
━━━━━━━━━━━━━━━━━━━━
⚡️ `AddProfile` با ریپلی!
💠 افزودن تصویر به پروفایل
━━━━━━━━━━━━━━━━━━━━
⚡️ `Time`
💠 دریافت زمان و تاریخ
━━━━━━━━━━━━━━━━━━━━
⚡️ `GetContacts`
💠 دریافت لیست مخاطبین شما و ارسال به پی وی شما
💎 فرمت فایل طوری است که در صورت کلیک بر روی آن مخاطبین در مخاطبین گوشی شما ذخیره میشود.
━━━━━━━━━━━━━━━━━━━━
⚡️ `Ping`
💠 تست آنلاینی سلف.
━━━━━━━━━━━━━━━━━━━━
⚡️ `Reload`
💠 بارگذاری سلف
━━━━━━━━━━━━━━━━━━━━
⚡️ `SetName` نام
💠 تنظیم نام اکانت شما
━━━━━━━━━━━━━━━━━━━━
⚡️ `SetBio` متن
💠 تنظیم بیوگرافی اکانت شما
""",
        """
🎯 دستورات پایه و رسانه (قسمت 2):

📌 دستورات موزیک:
⚡️ `SaveMusic` نام
💠 ذخیره موزیک در حافظه سلف 
━━━━━━━━━━━━━━━━━━━━
🔥 `DelMusic` نام
💠 حذف موزیک از حافظه سلف
━━━━━━━━━━━━━━━━━━━━
🔥 `GetMusic` نام
💠 دریافت موزیک از حافظه سلف
━━━━━━━━━━━━━━━━━━━━
🔥 `Musics`
💠 نمایش موزیک های ذخیره شده
━━━━━━━━━━━━━━━━━━━━
🔥 `Clean Musics`
💠 پاکسازی لیست موزیک های ذخیره شده
━━━━━━━━━━━━━━━━━━━━

📌 دستورات ویدئو:
⚡️ `SaveVideo` نام
💠 ذخیره ویدئو در حافظه سلف
━━━━━━━━━━━━━━━━━━━━
🔥 `DelVideo` نام
💠 حذف ویدئو از حافظه سلف
━━━━━━━━━━━━━━━━━━━━
🔥 `GetVideo` نام
💠 دریافت ویدئو از حافظه سلف
━━━━━━━━━━━━━━━━━━━━
🔥 `Videos`
💠 نمایش ویدئو های ذخیره شده
━━━━━━━━━━━━━━━━━━━━
🔥 `Clean Videos`
💠 پاکسازی لیست ویدئو های ذخیره شده
━━━━━━━━━━━━━━━━━━━━

📌 دستورات کاربردی:
⚡️ `Say` متن
💠 ارسال متن به صورت کلمه به کلمه
━━━━━━━━━━━━━━━━━━━━
⚡️ `SetCard` شماره کارت TEXT
⚡️ Ex: setcard 123456789123 مالک کارت
💠 تنظیم شماره کارت
💎 به جای TEXT میتوانید نام صاحب حساب قرار دهید.
━━━━━━━━━━━━━━━━━━━━
🔥 `Card`
💠 دریافت شماره کارت
━━━━━━━━━━━━━━━━━━━━
🔥 `DelCard`
💠 حذف شماره کارت
━━━━━━━━━━━━━━━━━━━━
⚡️ `calc` مسئله
💠 ماشین حساب سلف
💎 برای تقسیم از / استفاده کنید.
💎 برای ضرب از * استفاده کنید.
━━━━━━━━━━━━━━━━━━━━
⚡️ `Age` Rooz/Mah/Sal
💠 دریافت اطلاعات سن
━━━━━━━━━━━━━━━━━━━━
⚡️ `Sinfo` با ریپلی
💠 دریافت اطلاعات کاربر
━━━━━━━━━━━━━━━━━━━━
⚡️ `Addc` با ریپلی
💠 ذخیره کردن مخاطب با ریپلای
━━━━━━━━━━━━━━━━━━━━
⚡️ `Share`
💠 به اشتراک گذاری شماره شما.
━━━━━━━━━━━━━━━━━━━━
⚡️ `Del` با ریپلی
💠 حذف یک پیام با ریپلی روی آن
━━━━━━━━━━━━━━━━━━━━
⚡️ `Save` با ریپلی
💠 فووارد پیام به پی وی
━━━━━━━━━━━━━━━━━━━━
⚡️ `id` با ریپلی!
💠 دریافت شناسه کاربر
━━━━━━━━━━━━━━━━━━━━
🔥 `id` @نام کاربری
💠 دریافت شناسه کاربر
━━━━━━━━━━━━━━━━━━━━
🔥 `whois` شناسه
💠 دریافت یوزرنیم کاربر
━━━━━━━━━━━━━━━━━━━━
⚡️ `Myid`
💠 دریافت شناسه شما
━━━━━━━━━━━━━━━━━━━━
⚡️ `gpid`
💠 دریافت شناسه گروه
━━━━━━━━━━━━━━━━━━━━
⚡️ `MyName`
💠 دریافت نام شما
━━━━━━━━━━━━━━━━━━━━
⚡️ `MyPhone`
💠 دریافت شماره شما
""",
        """
💬 دستورات پیام و تایپینگ:

📌 دستورات پیام خصوصی:
⚡️ `SPm` متن با ریپلی!
💠 ارسال پیام به پیوی کاربر
━━━━━━━━━━━━━━━━━━━━
⚡️ `Block` با ریپلی
💠 بلاک کردن یک کاربر
💎 شما میتوانید جلوی ریپلی شناسه یا یوزرنیم کاربر را قرار دهید.
━━━━━━━━━━━━━━━━━━━━
🔥 `UnBlock` با ریپلی
💠 لغو بلاک یک کاربر
💎 شما میتوانید جلوی ریپلی شناسه یا یوزرنیم کاربر را قرار دهید.
━━━━━━━━━━━━━━━━━━━━

📌 دستورات تایپینگ:
⚡️ `Typing` با ریپلی
💠 افزودن کاربر به لیست تایپینگ
💎 شما میتوانید جلوی دستور یوزرنیم یا شناسه کاربر را قرار دهید.
💎 در این قابلیت هر وقت کاربر پیامی ارسال کند شما در حال تایپ نمایش داده میشوید.
━━━━━━━━━━━━━━━━━━━━
⚡️ `UnTyping` با ریپلی
💠 حذف کاربر از لیست تایپینگ
💎 شما میتوانید جلوی دستور یوزرنیم یا شناسه کاربر را قرار دهید.
━━━━━━━━━━━━━━━━━━━━
⚡️ `TypingList`
💠 نمایش لیست تایپینگ
━━━━━━━━━━━━━━━━━━━━
⚡️ `Clean TypingList`
💠 پاکسازی لیست تایپینگ
━━━━━━━━━━━━━━━━━━━━
⚡️ `TypingAll` با ریپلی
💠 افزودن کاربر به لیست تایپینگ همه گانی
💎 شما میتوانید جلوی دستور یوزرنیم یا شناسه کاربر را قرار دهید.
💎 در این قابلیت هر وقت کاربر پیامی ارسال کند شما در حال تایپ نمایش داده میشوید.
━━━━━━━━━━━━━━━━━━━━
⚡️ `UnTypingAll` با ریپلی
💠 حذف کاربر از لیست تایپینگ همه گانی
💎 شما میتوانید جلوی دستور یوزرنیم یا شناسه کاربر را قرار دهید.
━━━━━━━━━━━━━━━━━━━━
⚡️ `TypingAllList`
💠 نمایش لیست تایپینگ همه گانی
━━━━━━━━━━━━━━━━━━━━
⚡️ `Clean TypingListAll`
💠 پاکسازی لیست تایپینگ همه گانی
""",
        """
💬 دستورات پیام و تایپینگ (قسمت 2):

⚡️ `SetPm` متن با ریپلی!
💠 افزودن متن جدید به حالت پیام
💎 در این حالت هر زمان کاربر پیام ارسال کند یکی از پیام های تنظیم شده به صورت تصادفی ارسال خواهد شد.
-----------
⚡️ `DelPm` متن با ریپلی!
💠 حذف متن از لیست ییام ها
-----------
⚡️ `PmList` با ریپلی!
💠 نمایش لیست پیام های تنظیم شده.
-----------
⚡️ `Clean Pms` با ریپلی!
💠 پاکسازی پیام های تنظیم شده روی کاربر.
-----------
⚡️ `SetPmAll` متن با ریپلی!
💠 افزودن متن جدید به حالت پیام همه گانی
💎 در این حالت هر زمان کاربر پیام ارسال کند یکی از پیام های تنظیم شده به صورت تصادفی ارسال خواهد شد.
-----------
⚡️ `DelPmAll` متن با ریپلی!
💠 حذف پیام از لیست پیام های همه گانی
-----------
⚡️ `PmAllList` با ریپلی!
💠 نمایش لیست پیام های تنظیم شده.
-----------
⚡️ `Clean PmAllList` با ریپلی!
💠 پاکسازی پیام های همه گانی تنظیم شده روی کاربر
""",
        """
👥 دستورات گروه (قسمت 1):

⚡️ `Gpinfo`
💠 دریافت اطلاعات گروه.
-----------
⚡️ `inv` با ریپلی
💠 افزودن کاربری به گروه.
💎 شما میتوانید به جای ریپلی جلوی دستور یوزرنیم یا شناسه کاربر را قرار دهید.
-----------
⚡️ `Left`
💠 خروج از گروه
-----------
⚡️ `ChatLink`
💠 دریافت لینک گروه
-----------
⚡️ `STitel` نام
💠 تنظیم نام گروه
-----------
⚡️ `Rmsgs`
💠 پاکسازی همه پیام های گروه!
-----------
🔥 `DelGifs`
💠 پاکسازی همه گیف های ارسال شده در گروه
-----------
🔥 `DelPhotos`
💠 پاکسازی همه عکس های ارسال شده در گروه
-----------
🔥 `DelVideos`
💠 پاکسازی همه فیلم های ارسال شده در گروه
-----------
🔥 `DelMusics`
💠 پاکسازی همه موزیک های ارسال شده در گروه
-----------
🔥 `DelVoice`
💠 پاکسازی همه ویس های ارسال شده در گروه
-----------
⚡️ `Clean BlockList`
💠 پاکسازی لیست بلاک گروه
-----------
🔥 `Clean Deleted`
💠 پاکسازی کاربران دیلیت اکانت شده گروه
-----------
🔥 `Clean Bots`
💠 پاکسازی ربات های گروه
-----------
⚡️ `Del` عدد
💠 پاکسازی تعداد دلخواه پیام
-----------
⚡️ `DelAll` با ریپلی!
💠 پاکسازی همه پیام های یک کاربر
-----------
⚡️ `LeftAllGroups`
💠 خروج از تمام گروه های شما.
-----------
⚡️ `SFilter` متن
💠 فیلتر کردن کلمه در گروه
💎 شما میتوانید چند کلمه را با هم فیلتر کنید ، بعد متن اول بعدی را در خط بعد بنویسید.
-----------
🔥 `SDelFilter` متن
💠 حذف فیلتر کلمه در گروه
💎 شما میتوانید چند کلمه را با هم لغو فیلتر کنید ، بعد متن اول بعدی را در خط بعد بنویسید.
-----------
🔥 `SFilterList`
💠 نمایش لیست کلمات فیلتر در گروه.
-----------
🔥 `Clean SFilterList`
💠 پاکسازی لیست کلمات فیلتر شده.
-----------
⚡️ `sAllow` متن
💠 اجباری کردن کلمه در گروه
💎 شما میتوانید چند کلمه را با هم اجباری کنید ، بعد متن اول بعدی را در خط بعد بنویسید.
-----------
🔥 `SDelAllow` متن
💠 حذف اجباری کلمه در گروه
💎 شما میتوانید چند کلمه را با هم لغو اجباری کنید ، بعد متن اول بعدی را در خط بعد بنویسید.
-----------
🔥 `SAllowList`
💠 نمایش لیست کلمات اجباری در گروه.
-----------
🔥 `Clean SAllowList`
💠 پاکسازی لیست کلمات اجباری شده.
-----------
⚡️ `Tag`
💠 تگ-منشن کردن تمامی اعضای گروه
-----------
🔥 `TagAdmins`
💠 تگ - منشن کردن تمامی ادمین های گروه
-----------
🔥 `TagMembers`
💠 تگ - منشن کردن تمامی ممبر های گروه
-----------
🔥 `TagBots`
💠 تگ - منشن کردن تمامی ربات های گروه
-----------
⚡️ `Clean Members`
💠 اخراج تمام کاربران از گروه.
-----------
⚡️ `AddBots`
💠 افزودن چند ربات برای محدود کردن افزودن ربات در گروه
-----------
⚡️ `Pin`
💠 سنجاق کردن پیام در گروه
💎 شما میتوانید جلوی دستور ثانیه قرار دهید تا بعد از آن پیام از سنجاق در بیاید.
-----------
🔥 `UnPin`
💠 لغو سنجاق
-----------
🔥 `RePin`
💠 سنجاق کردن پیامی که قبلا با سلف آن را سنجاق کردید.
-----------
⚡️ `Kick` با ریپلی!
💠 اخراج کاربر از گروه
💎 شما میتوانید جلوی دستور یوزرنیم یا شناسه کاربر رو بگذارید.
-----------
⚡️ `Silent` با ریپلی!
💠 سکوت کردن کاربر در گروه
💎 شما میتوانید جلوی دستور یوزرنیم یا شناسه کاربر رو بگذارید.
-----------
🔥 `UnSilent` با ریپلی!
💠 لغو سکوت کردن کاربر در گروه
💎 شما میتوانید جلوی دستور یوزرنیم یا شناسه کاربر رو بگذارید.
-----------
🔥 `SilentList`
💠 نمایش لیست کاربران سکوت شده.
-----------
🔥 `Clean SilentList`
💠 پاکسازی لیست کاربران سکوت شده.
-----------
🔥 `SaveS`
💠 ذخیره تصاویر و ویس های زمان دار.
""",
        """
👥 دستورات گروه (قسمت 2):

⚡️ `sAllow` متن
💠 اجباری کردن کلمه در گروه
💎 شما میتوانید چند کلمه را با هم اجباری کنید ، بعد متن اول بعدی را در خط بعد بنویسید.
-----------
🔥 `SDelAllow` متن
💠 حذف اجباری کلمه در گروه
💎 شما میتوانید چند کلمه را با هم لغو اجباری کنید ، بعد متن اول بعدی را در خط بعد بنویسید.
-----------
🔥 `SAllowList`
💠 نمایش لیست کلمات اجباری در گروه.
-----------
🔥 `Clean SAllowList`
💠 پاکسازی لیست کلمات اجباری شده.
-----------
⚡️ `Tag`
💠 تگ-منشن کردن تمامی اعضای گروه
-----------
🔥 `TagAdmins`
💠 تگ - منشن کردن تمامی ادمین های گروه
-----------
🔥 `TagMembers`
💠 تگ - منشن کردن تمامی ممبر های گروه
-----------
🔥 `TagBots`
💠 تگ - منشن کردن تمامی ربات های گروه
-----------
⚡️ `Clean Members`
💠 اخراج تمام کاربران از گروه.
-----------
⚡️ `AddBots`
💠 افزودن چند ربات برای محدود کردن افزودن ربات در گروه
-----------
⚡️ `Pin`
💠 سنجاق کردن پیام در گروه
💎 شما میتوانید جلوی دستور ثانیه قرار دهید تا بعد از آن پیام از سنجاق در بیاید.
-----------
🔥 `UnPin`
💠 لغو سنجاق
-----------
🔥 `RePin`
💠 سنجاق کردن پیامی که قبلا با سلف آن را سنجاق کردید.
-----------
⚡️ `Kick` با ریپلی!
💠 اخراج کاربر از گروه
💎 شما میتوانید جلوی دستور یوزرنیم یا شناسه کاربر رو بگذارید.
-----------
⚡️ `Silent` با ریپلی!
💠 سکوت کردن کاربر در گروه
💎 شما میتوانید جلوی دستور یوزرنیم یا شناسه کاربر رو بگذارید.
-----------
🔥 `UnSilent` با ریپلی!
💠 لغو سکوت کردن کاربر در گروه
💎 شما میتوانید جلوی دستور یوزرنیم یا شناسه کاربر رو بگذارید.
-----------
🔥 `SilentList`
💠 نمایش لیست کاربران سکوت شده.
-----------
🔥 `Clean SilentList`
💠 پاکسازی لیست کاربران سکوت شده.
-----------
🔥 `SaveS`
💠 ذخیره تصاویر و ویس های زمان دار.
""",
        """
🔥 دستورات پیشرفته:

🔥 `Eyes` آی دی یا رپلای
💠 آنلاین و آفلاین شدن شخص رو نشون اطلاع بده توی سیو مسیج ها
-----------
🔥 `unEyes` آی دی یا رپلای
💠 آنلاین و آفلاین شدن شخص رو غیر فعال بکنه
-----------
🔥 `AntiLogin`
💠 جلوگیری از لاگین به اکانت
-----------
🔥 `UNAntiLogin`
💠 جلوگیری از لاگین به اکانت غیر فعال میکنه
-----------
🔥 `monshi` متن
💠 درصوت افلاین بودن متن مشخص شده رو به فرد پیام دهنده ارسال میکنه
-----------
🔥 `Unmonshi`
💠 ارسال پیام رو غیر فعال میکنه
-----------
🔥 `QR` با رپلای
💠 با رپلای روی پیام مورد نظر اطلاعات پیام رو به qr تبدیل میکنه
-----------
🔥 `AdsPM` 12H ID با رپلای
💠 روی متن مورد نظر رپلای بکنید و با زدن مثلا 12H متن مورد نظر هر 12 ساعت توی گروه مشخص شده ارسال میشه
💠 Example AdsPM 12H @IDGap
-----------
🔥 `SaveStory` ID
💠 ای دی کاربر رو وارد بکنید تا استوریش رو دانلود بکنه و توی سیو مسیج ها بزاره
-----------
🔥 `secretOn`
💠 فعال کردن ذخیره خودکار رسانه های زمان دار در سیو مسیج ها
-----------
🔥 `secretOff`
💠 غیرفعال کردن ذخیره خودکار رسانه های زمان دار
"""
    ]
    
    for i, text in enumerate(help_texts, 1):
        try:
            await event.reply(f"📚 راهنمای دستورات (قسمت {i}):\n{text}")
            await asyncio.sleep(1)  # Add a small delay between messages
        except Exception as e:
            print(f"Error sending help message part {i}: {e}")
            continue

@client.on(events.NewMessage(outgoing=True, pattern=r'(?i)^Clean TypingListAll$'))
async def clean_typing_all_list(event):
    typing_all_list.clear()
    save_media_data()
    await event.reply("✅ لیست تایپینگ همه‌گانی پاک شد.")

@client.on(events.NewMessage(outgoing=True, pattern=r'(?i)^SetPm (.+)$'))
async def set_pm(event):
    if event.is_reply:
        replied = await event.get_reply_message()
        text = event.pattern_match.group(1)
        if replied.sender_id not in pm_messages:
            pm_messages[replied.sender_id] = []
        pm_messages[replied.sender_id].append(text)
        save_media_data()
        await event.reply("✅ پیام جدید به لیست اضافه شد.")
    else:
        await event.reply("⚠️ لطفاً روی پیام کاربر ریپلای کنید.")

@client.on(events.NewMessage(outgoing=True, pattern=r'(?i)^DelPm (.+)$'))
async def del_pm(event):
    if event.is_reply:
        replied = await event.get_reply_message()
        text = event.pattern_match.group(1)
        if replied.sender_id in pm_messages and text in pm_messages[replied.sender_id]:
            pm_messages[replied.sender_id].remove(text)
            if not pm_messages[replied.sender_id]:
                del pm_messages[replied.sender_id]
            save_media_data()
            await event.reply("✅ پیام از لیست حذف شد.")
        else:
            await event.reply("⚠️ پیام مورد نظر یافت نشد.")
    else:
        await event.reply("⚠️ لطفاً روی پیام کاربر ریپلای کنید.")

@client.on(events.NewMessage(outgoing=True, pattern=r'(?i)^PmList$'))
async def show_pm_list(event):
    if event.is_reply:
        replied = await event.get_reply_message()
        if replied.sender_id in pm_messages and pm_messages[replied.sender_id]:
            text = "📝 لیست پیام‌ها:\n\n"
            for i, msg in enumerate(pm_messages[replied.sender_id], 1):
                text += f"{i}. {msg}\n"
            await event.reply(text)
        else:
            await event.reply("⚠️ هیچ پیامی تنظیم نشده است.")
    else:
        await event.reply("⚠️ لطفاً روی پیام کاربر ریپلای کنید.")

@client.on(events.NewMessage(outgoing=True, pattern=r'(?i)^Clean Pms$'))
async def clean_pms(event):
    if event.is_reply:
        replied = await event.get_reply_message()
        if replied.sender_id in pm_messages:
            del pm_messages[replied.sender_id]
            save_media_data()
            await event.reply("✅ پیام‌های کاربر پاک شد.")
        else:
            await event.reply("⚠️ هیچ پیامی تنظیم نشده است.")
    else:
        await event.reply("⚠️ لطفاً روی پیام کاربر ریپلای کنید.")

@client.on(events.NewMessage(outgoing=True, pattern=r'(?i)^SetPmAll (.+)$'))
async def set_pm_all(event):
    if event.is_reply:
        replied = await event.get_reply_message()
        text = event.pattern_match.group(1)
        if replied.sender_id not in pm_all_messages:
            pm_all_messages[replied.sender_id] = []
        pm_all_messages[replied.sender_id].append(text)
        save_media_data()
        await event.reply("✅ پیام جدید به لیست همه‌گانی اضافه شد.")
    else:
        await event.reply("⚠️ لطفاً روی پیام کاربر ریپلای کنید.")

@client.on(events.NewMessage(outgoing=True, pattern=r'(?i)^DelPmAll (.+)$'))
async def del_pm_all(event):
    if event.is_reply:
        replied = await event.get_reply_message()
        text = event.pattern_match.group(1)
        if replied.sender_id in pm_all_messages and text in pm_all_messages[replied.sender_id]:
            pm_all_messages[replied.sender_id].remove(text)
            if not pm_all_messages[replied.sender_id]:
                del pm_all_messages[replied.sender_id]
            save_media_data()
            await event.reply("✅ پیام از لیست همه‌گانی حذف شد.")
        else:
            await event.reply("⚠️ پیام مورد نظر یافت نشد.")
    else:
        await event.reply("⚠️ لطفاً روی پیام کاربر ریپلای کنید.")

@client.on(events.NewMessage(outgoing=True, pattern=r'(?i)^PmAllList$'))
async def show_pm_all_list(event):
    if event.is_reply:
        replied = await event.get_reply_message()
        if replied.sender_id in pm_all_messages and pm_all_messages[replied.sender_id]:
            text = "📝 لیست پیام‌های همه‌گانی:\n\n"
            for i, msg in enumerate(pm_all_messages[replied.sender_id], 1):
                text += f"{i}. {msg}\n"
            await event.reply(text)
        else:
            await event.reply("⚠️ هیچ پیامی تنظیم نشده است.")
    else:
        await event.reply("⚠️ لطفاً روی پیام کاربر ریپلای کنید.")

@client.on(events.NewMessage(outgoing=True, pattern=r'(?i)^Clean PmAllList$'))
async def clean_pm_all_list(event):
    if event.is_reply:
        replied = await event.get_reply_message()
        if replied.sender_id in pm_all_messages:
            del pm_all_messages[replied.sender_id]
            save_media_data()
            await event.reply("✅ پیام‌های همه‌گانی کاربر پاک شد.")
        else:
            await event.reply("⚠️ هیچ پیامی تنظیم نشده است.")
    else:
        await event.reply("⚠️ لطفاً روی پیام کاربر ریپلای کنید.")

@client.on(events.NewMessage(outgoing=True, pattern=r'(?i)^Gpinfo$'))
async def group_info(event):
    chat = await event.get_chat()
    if chat:
        text = f"📊 اطلاعات گروه:\n\n"
        text += f"• نام: {chat.title}\n"
        text += f"• شناسه: {chat.id}\n"
        text += f"• یوزرنیم: @{chat.username or 'ندارد'}\n"
        text += f"• تعداد اعضا: {chat.participants_count if hasattr(chat, 'participants_count') else 'نامشخص'}\n"
        await event.reply(text)
    else:
        await event.reply("⚠️ این دستور فقط در گروه قابل استفاده است.")

@client.on(events.NewMessage(outgoing=True, pattern=r'(?i)^inv$'))
async def invite_user(event):
    if event.is_reply:
        replied = await event.get_reply_message()
        try:
            await client(functions.channels.InviteToChannelRequest(
                channel=event.chat_id,
                users=[replied.sender_id]
            ))
            await event.reply("✅ کاربر به گروه اضافه شد.")
        except:
            await event.reply("❌ خطا در اضافه کردن کاربر.")
    else:
        await event.reply("⚠️ لطفاً روی پیام کاربر ریپلای کنید.")

@client.on(events.NewMessage(outgoing=True, pattern=r'(?i)^Left$'))
async def leave_group(event):
    try:
        await client(functions.channels.LeaveChannelRequest(
            channel=event.chat_id
        ))
        await event.reply("✅ از گروه خارج شدم.")
    except:
        await event.reply("❌ خطا در خروج از گروه.")

@client.on(events.NewMessage(outgoing=True, pattern=r'(?i)^ChatLink$'))
async def get_chat_link(event):
    try:
        chat = await event.get_chat()
        if chat.username:
            await event.reply(f"🔗 لینک گروه:\nhttps://t.me/{chat.username}")
        else:
            invite = await client(functions.messages.ExportChatInviteRequest(
                peer=event.chat_id
            ))
            await event.reply(f"🔗 لینک گروه:\n{invite.link}")
    except:
        await event.reply("❌ خطا در دریافت لینک گروه.")

@client.on(events.NewMessage(outgoing=True, pattern=r'(?i)^STitel (.+)$'))
async def set_group_title(event):
    try:
        title = event.pattern_match.group(1)
        await client(functions.channels.EditTitleRequest(
            channel=event.chat_id,
            title=title
        ))
        await event.reply("✅ نام گروه تغییر کرد.")
    except:
        await event.reply("❌ خطا در تغییر نام گروه.")

@client.on(events.NewMessage(outgoing=True, pattern=r'(?i)^Rmsgs$'))
async def delete_all_messages(event):
    try:
        messages = await client.get_messages(event.chat_id, limit=1000)
        await client.delete_messages(event.chat_id, messages)
        await event.reply("✅ پیام‌های گروه پاک شد.")
    except:
        await event.reply("❌ خطا در پاک کردن پیام‌ها.")

@client.on(events.NewMessage(outgoing=True, pattern=r'(?i)^DelGifs$'))
async def delete_gifs(event):
    try:
        messages = await client.get_messages(event.chat_id, limit=1000)
        gif_messages = [msg for msg in messages if msg.gif]
        await client.delete_messages(event.chat_id, gif_messages)
        await event.reply("✅ گیف‌های گروه پاک شد.")
    except:
        await event.reply("❌ خطا در پاک کردن گیف‌ها.")

@client.on(events.NewMessage(outgoing=True, pattern=r'(?i)^DelPhotos$'))
async def delete_photos(event):
    try:
        messages = await client.get_messages(event.chat_id, limit=1000)
        photo_messages = [msg for msg in messages if msg.photo]
        await client.delete_messages(event.chat_id, photo_messages)
        await event.reply("✅ عکس‌های گروه پاک شد.")
    except:
        await event.reply("❌ خطا در پاک کردن عکس‌ها.")

@client.on(events.NewMessage(outgoing=True, pattern=r'(?i)^DelVideos$'))
async def delete_videos(event):
    try:
        messages = await client.get_messages(event.chat_id, limit=1000)
        video_messages = [msg for msg in messages if msg.video]
        await client.delete_messages(event.chat_id, video_messages)
        await event.reply("✅ ویدئوهای گروه پاک شد.")
    except:
        await event.reply("❌ خطا در پاک کردن ویدئوها.")

@client.on(events.NewMessage(outgoing=True, pattern=r'(?i)^DelMusics$'))
async def delete_musics(event):
    try:
        messages = await client.get_messages(event.chat_id, limit=1000)
        music_messages = [msg for msg in messages if msg.audio]
        await client.delete_messages(event.chat_id, music_messages)
        await event.reply("✅ موزیک‌های گروه پاک شد.")
    except:
        await event.reply("❌ خطا در پاک کردن موزیک‌ها.")

@client.on(events.NewMessage(outgoing=True, pattern=r'(?i)^DelVoice$'))
async def delete_voices(event):
    try:
        messages = await client.get_messages(event.chat_id, limit=1000)
        voice_messages = [msg for msg in messages if msg.voice]
        await client.delete_messages(event.chat_id, voice_messages)
        await event.reply("✅ ویس‌های گروه پاک شد.")
    except:
        await event.reply("❌ خطا در پاک کردن ویس‌ها.")

@client.on(events.NewMessage(outgoing=True, pattern=r'(?i)^Clean BlockList$'))
async def clean_block_list(event):
    try:
        blocked = await client(functions.contacts.GetBlockedRequest(offset=0, limit=100))
        for user in blocked.users:
            await client(functions.contacts.UnblockRequest(id=user.id))
        await event.reply("✅ لیست بلاک پاک شد.")
    except:
        await event.reply("❌ خطا در پاک کردن لیست بلاک.")

@client.on(events.NewMessage(outgoing=True, pattern=r'(?i)^Clean Deleted$'))
async def clean_deleted(event):
    try:
        participants = await client.get_participants(event.chat_id)
        deleted_users = [user for user in participants if user.deleted]
        await client.edit_permissions(event.chat_id, deleted_users, view_messages=False)
        await event.reply(f"✅ {len(deleted_users)} کاربر دیلیت اکانت شده از گروه حذف شدند.")
    except:
        await event.reply("❌ خطا در پاک کردن کاربران دیلیت اکانت شده.")

@client.on(events.NewMessage(outgoing=True, pattern=r'(?i)^Clean Bots$'))
async def clean_bots(event):
    try:
        participants = await client.get_participants(event.chat_id)
        bots = [user for user in participants if user.bot]
        await client.edit_permissions(event.chat_id, bots, view_messages=False)
        await event.reply(f"✅ {len(bots)} ربات از گروه حذف شدند.")
    except:
        await event.reply("❌ خطا در پاک کردن ربات‌ها.")

@client.on(events.NewMessage(outgoing=True, pattern=r'(?i)^Del (\d+)$'))
async def delete_count(event):
    try:
        count = int(event.pattern_match.group(1))
        messages = await client.get_messages(event.chat_id, limit=count)
        await client.delete_messages(event.chat_id, messages)
        await event.reply(f"✅ {count} پیام پاک شد.")
    except:
        await event.reply("❌ خطا در پاک کردن پیام‌ها.")

@client.on(events.NewMessage(outgoing=True, pattern=r'(?i)^DelAll$'))
async def delete_all_user_messages(event):
    if event.is_reply:
        try:
            replied = await event.get_reply_message()
            messages = await client.get_messages(event.chat_id, from_user=replied.sender_id)
            await client.delete_messages(event.chat_id, messages)
            await event.reply("✅ پیام‌های کاربر پاک شد.")
        except:
            await event.reply("❌ خطا در پاک کردن پیام‌های کاربر.")
    else:
        await event.reply("⚠️ لطفاً روی پیام کاربر ریپلای کنید.")

@client.on(events.NewMessage(outgoing=True, pattern=r'(?i)^LeftAllGroups$'))
async def leave_all_groups(event):
    try:
        dialogs = await client.get_dialogs()
        groups = [dialog for dialog in dialogs if dialog.is_group]
        for group in groups:
            try:
                await client.leave_chat(group.id)
            except:
                continue
        await event.reply(f"✅ از {len(groups)} گروه خارج شدم.")
    except:
        await event.reply("❌ خطا در خروج از گروه‌ها.")

@client.on(events.NewMessage(outgoing=True, pattern=r'(?i)^SFilter (.+)$'))
async def filter_words(event):
    try:
        words = event.pattern_match.group(1).split('\n')
        for word in words:
            word = word.strip()
            if word:
                await client.edit_permissions(event.chat_id, None, send_messages=False, until_date=None)
                await event.reply(f"✅ کلمه '{word}' فیلتر شد.")
    except:
        await event.reply("❌ خطا در فیلتر کردن کلمات.")

@client.on(events.NewMessage(outgoing=True, pattern=r'(?i)^SDelFilter (.+)$'))
async def delete_filter_words(event):
    try:
        words = event.pattern_match.group(1).split('\n')
        for word in words:
            word = word.strip()
            if word in filtered_words:
                filtered_words.remove(word)
                await client.edit_permissions(event.chat_id, None, send_messages=True, until_date=None)
        await event.reply("✅ کلمات از لیست فیلتر حذف شدند.")
    except:
        await event.reply("❌ خطا در حذف کلمات از لیست فیلتر.")

@client.on(events.NewMessage(outgoing=True, pattern=r'(?i)^SFilterList$'))
async def show_filter_list(event):
    if filtered_words:
        text = "📝 لیست کلمات فیلتر شده:\n\n"
        for word in filtered_words:
            text += f"• {word}\n"
        await event.reply(text)
    else:
        await event.reply("⚠️ هیچ کلمه‌ای فیلتر نشده است.")

@client.on(events.NewMessage(outgoing=True, pattern=r'(?i)^Clean SFilterList$'))
async def clean_filter_list(event):
    filtered_words.clear()
    await event.reply("✅ لیست کلمات فیلتر شده پاک شد.")

@client.on(events.NewMessage(outgoing=True, pattern=r'(?i)^sAllow (.+)$'))
async def allow_words(event):
    try:
        words = event.pattern_match.group(1).split('\n')
        for word in words:
            word = word.strip()
            if word:
                allowed_words.add(word)
                await client.edit_permissions(event.chat_id, None, send_messages=True, until_date=None)
        await event.reply("✅ کلمات به لیست اجباری اضافه شدند.")
    except:
        await event.reply("❌ خطا در اضافه کردن کلمات به لیست اجباری.")

@client.on(events.NewMessage(outgoing=True, pattern=r'(?i)^SDelAllow (.+)$'))
async def delete_allowed_words(event):
    try:
        words = event.pattern_match.group(1).split('\n')
        for word in words:
            word = word.strip()
            if word in allowed_words:
                allowed_words.remove(word)
        await event.reply("✅ کلمات از لیست اجباری حذف شدند.")
    except:
        await event.reply("❌ خطا در حذف کلمات از لیست اجباری.")

@client.on(events.NewMessage(outgoing=True, pattern=r'(?i)^SAllowList$'))
async def show_allowed_list(event):
    if allowed_words:
        text = "📝 لیست کلمات اجباری:\n\n"
        for word in allowed_words:
            text += f"• {word}\n"
        await event.reply(text)
    else:
        await event.reply("⚠️ هیچ کلمه‌ای اجباری نشده است.")

@client.on(events.NewMessage(outgoing=True, pattern=r'(?i)^Clean SAllowList$'))
async def clean_allowed_list(event):
    allowed_words.clear()
    await event.reply("✅ لیست کلمات اجباری پاک شد.")

@client.on(events.NewMessage(outgoing=True, pattern=r'(?i)^Tag$'))
async def tag_all(event):
    try:
        participants = await client.get_participants(event.chat_id)
        text = ""
        for user in participants:
            text += f"@{user.username or 'ندارد'} "
        await event.reply(text)
    except:
        await event.reply("❌ خطا در تگ کردن اعضا.")

@client.on(events.NewMessage(outgoing=True, pattern=r'(?i)^TagAdmins$'))
async def tag_admins(event):
    try:
        participants = await client.get_participants(event.chat_id)
        admins = [user for user in participants if user.admin_rights]
        text = ""
        for admin in admins:
            text += f"@{admin.username or 'ندارد'} "
        await event.reply(text)
    except:
        await event.reply("❌ خطا در تگ کردن ادمین‌ها.")

@client.on(events.NewMessage(outgoing=True, pattern=r'(?i)^TagMembers$'))
async def tag_members(event):
    try:
        participants = await client.get_participants(event.chat_id)
        members = [user for user in participants if not user.bot and not user.admin_rights]
        text = ""
        for member in members:
            text += f"@{member.username or 'ندارد'} "
        await event.reply(text)
    except:
        await event.reply("❌ خطا در تگ کردن ممبرها.")

@client.on(events.NewMessage(outgoing=True, pattern=r'(?i)^TagBots$'))
async def tag_bots(event):
    try:
        participants = await client.get_participants(event.chat_id)
        bots = [user for user in participants if user.bot]
        text = ""
        for bot in bots:
            text += f"@{bot.username or 'ندارد'} "
        await event.reply(text)
    except:
        await event.reply("❌ خطا در تگ کردن ربات‌ها.")

@client.on(events.NewMessage(outgoing=True, pattern=r'(?i)^Clean Members$'))
async def clean_members(event):
    try:
        participants = await client.get_participants(event.chat_id)
        for user in participants:
            if not user.bot and not user.admin_rights:
                try:
                    await client.edit_permissions(event.chat_id, user, view_messages=False)
                except:
                    continue
        await event.reply("✅ تمام کاربران از گروه اخراج شدند.")
    except:
        await event.reply("❌ خطا در اخراج کاربران.")

@client.on(events.NewMessage(outgoing=True, pattern=r'(?i)^AddBots$'))
async def add_bots(event):
    try:
        # Add some common bot usernames that can help restrict bot adding
        bot_usernames = ['@BotFather', '@GroupHelpBot', '@SpamBot']
        for username in bot_usernames:
            try:
                await client(functions.channels.InviteToChannelRequest(
                    channel=event.chat_id,
                    users=[username]
                ))
            except:
                continue
        await event.reply("✅ ربات‌های محدود کننده اضافه شدند.")
    except:
        await event.reply("❌ خطا در اضافه کردن ربات‌ها.")

@client.on(events.NewMessage(outgoing=True, pattern=r'(?i)^Pin(?: (\d+))?$'))
async def pin_message(event):
    if event.is_reply:
        try:
            seconds = int(event.pattern_match.group(1)) if event.pattern_match.group(1) else None
            replied = await event.get_reply_message()
            await client.pin_message(event.chat_id, replied.id, notify=True)
            if seconds:
                await asyncio.sleep(seconds)
                await client.unpin_message(event.chat_id, replied.id)
            await event.reply("✅ پیام سنجاق شد.")
        except:
            await event.reply("❌ خطا در سنجاق کردن پیام.")
    else:
        await event.reply("⚠️ لطفاً روی پیام مورد نظر ریپلای کنید.")

@client.on(events.NewMessage(outgoing=True, pattern=r'(?i)^UnPin$'))
async def unpin_message(event):
    try:
        await client.unpin_message(event.chat_id)
        await event.reply("✅ سنجاق پیام لغو شد.")
    except:
        await event.reply("❌ خطا در لغو سنجاق پیام.")

@client.on(events.NewMessage(outgoing=True, pattern=r'(?i)^RePin$'))
async def repin_message(event):
    try:
        messages = await client.get_messages(event.chat_id, limit=100)
        for msg in messages:
            if msg.pinned:
                await client.pin_message(event.chat_id, msg.id, notify=True)
                await event.reply("✅ پیام مجدداً سنجاق شد.")
                return
        await event.reply("⚠️ هیچ پیام سنجاق شده‌ای یافت نشد.")
    except:
        await event.reply("❌ خطا در سنجاق مجدد پیام.")

@client.on(events.NewMessage(outgoing=True, pattern=r'(?i)^Kick(?: (.+))?$'))
async def kick_user(event):
    if event.is_reply or event.pattern_match.group(1):
        try:
            if event.is_reply:
                replied = await event.get_reply_message()
                user_id = replied.sender_id
            else:
                user_id = event.pattern_match.group(1)
                if user_id.startswith('@'):
                    user = await client.get_entity(user_id)
                    user_id = user.id
                else:
                    user_id = int(user_id)
            
            await client.edit_permissions(event.chat_id, user_id, view_messages=False)
            await event.reply("✅ کاربر از گروه اخراج شد.")
        except:
            await event.reply("❌ خطا در اخراج کاربر.")
    else:
        await event.reply("⚠️ لطفاً روی پیام کاربر ریپلای کنید یا یوزرنیم/شناسه کاربر را وارد کنید.")

@client.on(events.NewMessage(outgoing=True, pattern=r'(?i)^Silent(?: (.+))?$'))
async def silent_user(event):
    if event.is_reply or event.pattern_match.group(1):
        try:
            if event.is_reply:
                replied = await event.get_reply_message()
                user_id = replied.sender_id
            else:
                user_id = event.pattern_match.group(1)
                if user_id.startswith('@'):
                    user = await client.get_entity(user_id)
                    user_id = user.id
                else:
                    user_id = int(user_id)
            
            await client.edit_permissions(event.chat_id, user_id, send_messages=False)
            silent_users.add(user_id)
            await event.reply("✅ کاربر سکوت شد.")
        except:
            await event.reply("❌ خطا در سکوت کردن کاربر.")
    else:
        await event.reply("⚠️ لطفاً روی پیام کاربر ریپلای کنید یا یوزرنیم/شناسه کاربر را وارد کنید.")

@client.on(events.NewMessage(outgoing=True, pattern=r'(?i)^UnSilent(?: (.+))?$'))
async def unsilent_user(event):
    if event.is_reply or event.pattern_match.group(1):
        try:
            if event.is_reply:
                replied = await event.get_reply_message()
                user_id = replied.sender_id
            else:
                user_id = event.pattern_match.group(1)
                if user_id.startswith('@'):
                    user = await client.get_entity(user_id)
                    user_id = user.id
                else:
                    user_id = int(user_id)
            
            await client.edit_permissions(event.chat_id, user_id, send_messages=True)
            silent_users.discard(user_id)
            await event.reply("✅ سکوت کاربر لغو شد.")
        except:
            await event.reply("❌ خطا در لغو سکوت کاربر.")
    else:
        await event.reply("⚠️ لطفاً روی پیام کاربر ریپلای کنید یا یوزرنیم/شناسه کاربر را وارد کنید.")

@client.on(events.NewMessage(outgoing=True, pattern=r'(?i)^SilentList$'))
async def show_silent_list(event):
    if silent_users:
        text = "📝 لیست کاربران سکوت شده:\n\n"
        for user_id in silent_users:
            try:
                user = await client.get_entity(user_id)
                text += f"• @{user.username or 'ندارد'} ({user_id})\n"
            except:
                text += f"• {user_id}\n"
        await event.reply(text)
    else:
        await event.reply("⚠️ هیچ کاربری سکوت نشده است.")

@client.on(events.NewMessage(outgoing=True, pattern=r'(?i)^Clean SilentList$'))
async def clean_silent_list(event):
    silent_users.clear()
    save_media_data()
    await event.reply("✅ لیست کاربران سکوت شده پاک شد.")

@client.on(events.NewMessage(outgoing=True, pattern=r'(?i)^SaveS$'))
async def save_secret_media(event):
    # Delete the command message immediately
    await event.delete()
    
    if event.is_reply:
        try:
            replied = await event.get_reply_message()
            if replied.photo or replied.video or replied.voice or replied.audio:
                # Download the media first
                file = await replied.download_media()
                
                # Get sender info
                sender = await replied.get_sender()
                sender_id = sender.id
                sender_name = f"@{sender.username}" if sender.username else f"User {sender_id}"
                
                # Send the media to saved messages with sender info
                if replied.photo:
                    await client.send_file('me', file, caption=f"📸 تصویر زمان‌دار ذخیره شده\nاز: {sender_name} ({sender_id})")
                elif replied.video:
                    await client.send_file('me', file, caption=f"🎥 ویدئوی زمان‌دار ذخیره شده\nاز: {sender_name} ({sender_id})")
                elif replied.voice:
                    await client.send_file('me', file, caption=f"🎤 ویس زمان‌دار ذخیره شده\nاز: {sender_name} ({sender_id})")
                elif replied.audio:
                    await client.send_file('me', file, caption=f"🎵 موزیک زمان‌دار ذخیره شده\nاز: {sender_name} ({sender_id})")
                
                # Send success message to saved messages
                await client.send_message('me', f"✅ رسانه زمان‌دار از {sender_name} ({sender_id}) با موفقیت ذخیره شد.")
                
                # Clean up the downloaded file
                os.remove(file)
            else:
                # Send error message to saved messages
                await client.send_message('me', "⚠️ لطفاً روی یک رسانه زمان‌دار ریپلای کنید.")
        except Exception as e:
            # Send error message to saved messages
            await client.send_message('me', f"❌ خطا در ذخیره رسانه: {str(e)}")
    else:
        # Send error message to saved messages
        await client.send_message('me', "⚠️ لطفاً روی رسانه مورد نظر ریپلای کنید.")

@client.on(events.NewMessage(outgoing=True, pattern=r'(?i)^Eyes(?: (.+))?$'))
async def watch_user(event):
    if event.is_reply or event.pattern_match.group(1):
        try:
            if event.is_reply:
                replied = await event.get_reply_message()
                user_id = replied.sender_id
            else:
                user_id = event.pattern_match.group(1)
                if user_id.startswith('@'):
                    user = await client.get_entity(user_id)
                    user_id = user.id
                else:
                    user_id = int(user_id)
            
            watched_users.add(user_id)
            await event.reply("✅ کاربر به لیست مشاهده اضافه شد.")
        except:
            await event.reply("❌ خطا در اضافه کردن کاربر به لیست مشاهده.")
    else:
        await event.reply("⚠️ لطفاً روی پیام کاربر ریپلای کنید یا یوزرنیم/شناسه کاربر را وارد کنید.")

@client.on(events.NewMessage(outgoing=True, pattern=r'(?i)^unEyes(?: (.+))?$'))
async def unwatch_user(event):
    if event.is_reply or event.pattern_match.group(1):
        try:
            if event.is_reply:
                replied = await event.get_reply_message()
                user_id = replied.sender_id
            else:
                user_id = event.pattern_match.group(1)
                if user_id.startswith('@'):
                    user = await client.get_entity(user_id)
                    user_id = user.id
                else:
                    user_id = int(user_id)
            
            watched_users.discard(user_id)
            await event.reply("✅ کاربر از لیست مشاهده حذف شد.")
        except:
            await event.reply("❌ خطا در حذف کاربر از لیست مشاهده.")
    else:
        await event.reply("⚠️ لطفاً روی پیام کاربر ریپلای کنید یا یوزرنیم/شناسه کاربر را وارد کنید.")

@client.on(events.NewMessage(outgoing=True, pattern=r'(?i)^AntiLogin$'))
async def enable_anti_login(event):
    global anti_login
    anti_login = True
    await event.reply("✅ جلوگیری از لاگین فعال شد.")

@client.on(events.NewMessage(outgoing=True, pattern=r'(?i)^UNAntiLogin$'))
async def disable_anti_login(event):
    global anti_login
    anti_login = False
    await event.reply("✅ جلوگیری از لاگین غیرفعال شد.")

@client.on(events.NewMessage(outgoing=True, pattern=r'(?i)^monshi (.+)$'))
async def set_monshi(event):
    global monshi_text, monshi_enabled
    monshi_text = event.pattern_match.group(1)
    monshi_enabled = True
    await event.reply("✅ متن مونشی تنظیم شد.")

@client.on(events.NewMessage(outgoing=True, pattern=r'(?i)^Unmonshi$'))
async def disable_monshi(event):
    global monshi_enabled
    monshi_enabled = False
    await event.reply("✅ مونشی غیرفعال شد.")

@client.on(events.NewMessage(outgoing=True, pattern=r'(?i)^QR$'))
async def create_qr(event):
    if event.is_reply:
        try:
            replied = await event.get_reply_message()
            text = f"Message ID: {replied.id}\nFrom: {replied.sender_id}\nText: {replied.text}"
            
            # Create QR code
            qr = qrcode.QRCode(version=1, box_size=10, border=5)
            qr.add_data(text)
            qr.make(fit=True)
            img = qr.make_image(fill_color="black", back_color="white")
            
            # Save and send QR code
            img.save('qr.png')
            await event.reply(file='qr.png')
            os.remove('qr.png')
        except:
            await event.reply("❌ خطا در ایجاد QR کد.")
    else:
        await event.reply("⚠️ لطفاً روی پیام مورد نظر ریپلای کنید.")

@client.on(events.NewMessage(outgoing=True, pattern=r'(?i)^AdsPM (\d+)H (.+)$'))
async def schedule_ad(event):
    if event.is_reply:
        try:
            hours = int(event.pattern_match.group(1))
            target = event.pattern_match.group(2)
            replied = await event.get_reply_message()
            
            async def send_ad():
                while True:
                    await client.send_message(target, replied.text)
                    await asyncio.sleep(hours * 3600)
            
            task = asyncio.create_task(send_ad())
            ad_tasks[target] = task
            await event.reply(f"✅ تبلیغ هر {hours} ساعت ارسال خواهد شد.")
        except:
            await event.reply("❌ خطا در تنظیم تبلیغ.")
    else:
        await event.reply("⚠️ لطفاً روی پیام مورد نظر ریپلای کنید.")

@client.on(events.NewMessage(outgoing=True, pattern=r'(?i)^SaveStory (.+)$'))
async def save_story(event):
    try:
        user_id = event.pattern_match.group(1)
        if user_id.startswith('@'):
            user = await client.get_entity(user_id)
            user_id = user.id
        else:
            user_id = int(user_id)
        
        stories = await client.get_stories(user_id)
        for story in stories:
            if story.media:
                await client.forward_messages('me', story.id, user_id)
        await event.reply("✅ استوری‌ها ذخیره شدند.")
    except:
        await event.reply("❌ خطا در ذخیره استوری‌ها.")

# Add this handler for user status updates
@client.on(events.UserUpdate())
async def handle_user_update(event):
    if event.user_id in watched_users:
        user = await event.get_user()
        status = "آنلاین" if user.status else "آفلاین"
        await client.send_message('me', f"👤 وضعیت کاربر {user.first_name}:\n{status}")

# Add this handler for incoming messages
@client.on(events.NewMessage(incoming=True))
async def handle_incoming_message(event):
    if monshi_enabled and monshi_text and not await client.is_user_authorized():
        await event.reply(monshi_text)

# Add this handler for login attempts
@client.on(events.Raw(types.UpdateLoginToken))
async def handle_login_attempt(event):
    if anti_login:
        await client.log_out()

@client.on(events.NewMessage(outgoing=True, pattern=r'(?i)^secretOn$'))
async def enable_secret_mode(event):
    global secret_mode
    secret_mode = True
    save_media_data()
    await event.reply("✅ حالت مخفی فعال شد. تمام رسانه‌های زمان‌دار به صورت خودکار ذخیره خواهند شد.")

@client.on(events.NewMessage(outgoing=True, pattern=r'(?i)^secretOff$'))
async def disable_secret_mode(event):
    global secret_mode
    secret_mode = False
    save_media_data()
    await event.reply("✅ حالت مخفی غیرفعال شد.")

@client.on(events.NewMessage(incoming=True))
async def handle_incoming_message(event):
    # Handle typing
    if event.sender_id in typing_list:
        await client.action(event.chat_id, 'typing')
    if event.sender_id in typing_all_list:
        await client.action(event.chat_id, 'typing')
    
    # Handle PM auto-reply
    if event.sender_id in pm_messages and pm_messages[event.sender_id]:
        await asyncio.sleep(1)
        await event.reply(random.choice(pm_messages[event.sender_id]))
    
    if event.sender_id in pm_all_messages and pm_all_messages[event.sender_id]:
        await asyncio.sleep(1)
        await event.reply(random.choice(pm_all_messages[event.sender_id]))
    
    # Handle secret mode for time-sensitive media
    if secret_mode and (event.photo or event.video or event.voice or event.audio):
        try:
            # Download the media first
            file = await event.download_media()
            
            # Get sender info
            sender = await event.get_sender()
            sender_id = sender.id
            sender_name = f"@{sender.username}" if sender.username else f"User {sender_id}"
            
            # Send the media to saved messages with sender info
            if event.photo:
                await client.send_file('me', file, caption=f"📸 تصویر زمان‌دار ذخیره شده\nاز: {sender_name} ({sender_id})")
            elif event.video:
                await client.send_file('me', file, caption=f"🎥 ویدئوی زمان‌دار ذخیره شده\nاز: {sender_name} ({sender_id})")
            elif event.voice:
                await client.send_file('me', file, caption=f"🎤 ویس زمان‌دار ذخیره شده\nاز: {sender_name} ({sender_id})")
            elif event.audio:
                await client.send_file('me', file, caption=f"🎵 موزیک زمان‌دار ذخیره شده\nاز: {sender_name} ({sender_id})")
            
            # Clean up the downloaded file
            os.remove(file)
        except Exception as e:
            print(f"Error saving secret media: {str(e)}")

# بارگذاری داده‌های ذخیره شده
load_media_data()

print("✅ Selfbot is running...")

async def main():
    # بارگذاری داده‌های ذخیره شده
    load_media_data()

    print("✅ Selfbot is running...")
    
    # Connect and start
    try:
        print("Connecting to Telegram...")
        await client.connect()
        
        # If not authorized, try to authorize with the phone.txt file
        if not await client.is_user_authorized():
            phone_file = os.path.join(os.path.dirname(__file__), 'phone.txt')
            if os.path.exists(phone_file):
                with open(phone_file, 'r') as f:
                    phone = f.read().strip()
                print(f"Attempting to authenticate with phone number: {phone}")
                
                try:
                    # First, try to send code request
                    print(f"Sending code request to {phone}...")
                    await client.send_code_request(phone)
                    print("Code request sent. Please check your phone for the verification code.")
                    
                    # Wait for code input
                    print("Waiting for verification code input...")
                    verification_code = input("Please enter the verification code: ")
                    
                    # Sign in with code
                    await client.sign_in(phone, verification_code)
                    print("Authentication successful!")
                except Exception as e:
                    print(f"Authentication error: {e}")
                    return
            else:
                print("Error: phone.txt file not found. Unable to authenticate.")
                return
        
        # Check subscription expiry
        try:
            expiry_file = os.path.join(os.path.dirname(__file__), 'expiry_date.txt')
            if os.path.exists(expiry_file):
                with open(expiry_file, 'r') as f:
                    expiry_date_str = f.read().strip()
                    expiry_date = datetime.strptime(expiry_date_str, "%Y-%m-%d").date()
                
                current_date = datetime.now().date()
                if current_date > expiry_date:
                    print(f"❌ Self Bot subscription expired on {expiry_date_str}")
                    print("Exiting...")
                    return
                
                days_left = (expiry_date - current_date).days
                print(f"✅ Self Bot subscription active. {days_left} days remaining.")
            else:
                print("⚠️ Warning: No expiry date file found. Running without expiry check.")
        except Exception as e:
            print(f"Error checking subscription: {e}")
            
        me = await client.get_me()
        print(f"Logged in as {me.first_name} ({me.username})")
        
        # Register event handlers
        client.add_event_handler(on_message, events.NewMessage)
        
        print(f"Selfbot is now active and listening for messages...")
        
        # Keep the bot running until terminated
        await asyncio.sleep(float('inf'))
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        await client.disconnect()

# Run the bot with auto-restart on crash
if __name__ == "__main__":
    # Setup auto-restart mechanism
    max_retries = 5
    retry_count = 0
    retry_delay = 10  # seconds
    
    while retry_count < max_retries:
        try:
            # Run the main function
            asyncio.run(main())
            
            # If we get here normally (without exception), exit gracefully
            break
        except KeyboardInterrupt:
            print("\nBot terminated by user.")
            break
        except Exception as e:
            retry_count += 1
            print(f"Bot crashed with error: {e}")
            print(f"Retry {retry_count}/{max_retries} in {retry_delay} seconds...")
            time.sleep(retry_delay)
            # Increase delay for next retry
            retry_delay = min(retry_delay * 2, 300)  # max 5 minutes
    
    if retry_count >= max_retries:
        print("Maximum retry attempts reached. Please check the errors and restart manually.")
