import os
import json
import logging
from pyrogram import Client, filters
from pyrogram.types import Message

# Logging setup
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Load environment variables
API_ID = int(os.getenv("API_ID", "0"))
API_HASH = os.getenv("API_HASH", "")
BOT_TOKEN = os.getenv("BOT_TOKEN", "")
MAIN_ADMIN_ID = int(os.getenv("MAIN_ADMIN_ID", "0"))
SOURCE_CHAT_ID = -1001927755960############  # Replace with actual source chat ID
TARGET_CHAT_ID = -1002369229203############  # Replace with actual target chat ID

if not all([API_ID, API_HASH, BOT_TOKEN, MAIN_ADMIN_ID, SOURCE_CHAT_ID, TARGET_CHAT_ID]):
    logger.error("❌ Missing environment variables. Exiting...")
    exit(1)

# File paths
REPLACEMENT_FILE = "replacements.json"
BLOCKED_FILE = "blocked.json"

# Ensure essential files exist
def ensure_files():
    if not os.path.exists(REPLACEMENT_FILE):
        with open(REPLACEMENT_FILE, "w") as f:
            json.dump({"texts": {}, "links": {}}, f)

    if not os.path.exists(BLOCKED_FILE):
        with open(BLOCKED_FILE, "w") as f:
            json.dump({"blocked_messages": []}, f)

ensure_files()

# Load JSON data
def load_json(file, default):
    try:
        with open(file, "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return default

def save_json(file, data):
    with open(file, "w") as f:
        json.dump(data, f)

def load_replacements():
    return load_json(REPLACEMENT_FILE, {"texts": {}, "links": {}})

def save_replacements(data):
    save_json(REPLACEMENT_FILE, data)

def load_blocked():
    return load_json(BLOCKED_FILE, {"blocked_messages": []})

def save_blocked(data):
    save_json(BLOCKED_FILE, data)

# Initialize Pyrogram bot
app = Client("bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# Check if user is admin
async def is_admin(user_id):
    return user_id == MAIN_ADMIN_ID

# **Forward & Replace Messages**
@app.on_message(filters.chat(SOURCE_CHAT_ID))
async def forward_and_replace(client, message: Message):
    blocked = load_blocked()["blocked_messages"]
    if message.message_id in blocked:
        logger.info(f"🚫 Blocked message {message.message_id} ignored.")
        return
    
    replacements = load_replacements()
    message_text = message.text or message.caption or ""

    for old, new in {**replacements["texts"], **replacements["links"]}.items():
        message_text = message_text.replace(old, new)

    await client.send_message(TARGET_CHAT_ID, message_text) if message.text else \
        await client.copy_message(TARGET_CHAT_ID, SOURCE_CHAT_ID, message.message_id, caption=message_text)

# **Admin Commands**
@app.on_message(filters.command("addreplace") & filters.user(MAIN_ADMIN_ID))
async def add_replace(client, message: Message):
    try:
        _, old, new = message.text.split(" ", 2)
        replacements = load_replacements()
        replacements["texts"][old] = new
        save_replacements(replacements)
        await message.reply_text(f"✅ Added replacement: `{old}` → `{new}`")
    except:
        await message.reply_text("⚠️ Usage: `/addreplace old_text new_text`")

@app.on_message(filters.command("block") & filters.user(MAIN_ADMIN_ID))
async def block_message(client, message: Message):
    try:
        message_id = int(message.text.split(" ", 1)[1])
        blocked = load_blocked()
        if message_id not in blocked["blocked_messages"]:
            blocked["blocked_messages"].append(message_id)
            save_blocked(blocked)
            await message.reply_text(f"✅ Blocked message ID `{message_id}`.")
        else:
            await message.reply_text(f"⚠️ Message ID `{message_id}` is already blocked.")
    except:
        await message.reply_text("⚠️ Usage: `/block message_id`")

if __name__ == "__main__":
    logger.info("✅ Bot is running...")
    app.run()
