#!/usr/bin/env python3
"""
Telegram bot for ComfyUI.
Loads workflow from zimage.json in the same directory.
"""

import json
import urllib.request
import urllib.parse
import websockets
import uuid
import os
import random
import logging
from pathlib import Path

# Enable debug logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
log = logging.getLogger(__name__)

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes

# === CONFIG ===
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
COMFYUI_HOST = os.environ.get("COMFYUI_HOST", "127.0.0.1:7860")

# Load workflow from zimage.json in the same directory as this script
SCRIPT_DIR = Path(__file__).parent
WORKFLOW_PATH = SCRIPT_DIR / "zimage.json"

# Node IDs (change if your workflow differs)
PROMPT_NODE_ID = "45"
SEED_NODE_ID = "63"  # Seed Generator node
OUTPUT_NODE_ID = "9"
SIZE_NODE_ID = "41"  # EmptySD3LatentImage node

# Aspect ratio presets (name: (width, height))
ASPECT_RATIOS = {
    "1:1": (1024, 1024),
    "16:9": (1344, 768),
    "9:16": (768, 1344),
    "4:3": (1152, 896),
    "3:4": (896, 1152),
    "3:2": (1216, 832),
    "2:3": (832, 1216),
    "2:1": (1408, 704),
}

# Per-user settings (in-memory, resets on restart)
user_settings: dict[int, dict] = {}


def get_user_settings(user_id: int) -> dict:
    """Get settings for a user, with defaults."""
    if user_id not in user_settings:
        user_settings[user_id] = {
            "aspect_ratio": "1:1",
            "width": 1024,
            "height": 1024,
            "last_prompt": None,
            "current_prompt_id": None,
        }
    return user_settings[user_id]


def load_workflow() -> dict:
    """Load workflow from JSON file."""
    if not WORKFLOW_PATH.exists():
        raise FileNotFoundError(f"zimage.json not found at {WORKFLOW_PATH}")
    
    with open(WORKFLOW_PATH, "r") as f:
        return json.load(f)


def queue_prompt(prompt: dict) -> str:
    """Queue a prompt and return the prompt_id."""
    # Randomize seed
    if SEED_NODE_ID in prompt:
        prompt[SEED_NODE_ID]["inputs"]["seed"] = random.randint(0, 2**53)

    data = json.dumps({"prompt": prompt}).encode("utf-8")
    req = urllib.request.Request(
        f"http://{COMFYUI_HOST}/prompt",
        data=data,
        headers={"Content-Type": "application/json"},
    )
    log.info(f"Queueing prompt to {COMFYUI_HOST}...")
    with urllib.request.urlopen(req) as resp:
        result = json.loads(resp.read())
        log.info(f"Queued! prompt_id: {result['prompt_id']}")
        return result["prompt_id"]


def cancel_prompt(prompt_id: str) -> bool:
    """Cancel a queued prompt by prompt_id. Returns True if successful."""
    try:
        data = json.dumps({"delete": [prompt_id]}).encode("utf-8")
        req = urllib.request.Request(
            f"http://{COMFYUI_HOST}/queue",
            data=data,
            headers={"Content-Type": "application/json"},
        )
        log.info(f"Canceling prompt_id: {prompt_id}")
        with urllib.request.urlopen(req) as resp:
            log.info(f"Canceled prompt_id: {prompt_id}")
            return True
    except Exception as e:
        log.error(f"Failed to cancel prompt: {e}")
        return False


async def wait_for_image(prompt_id: str) -> bytes | None:
    """Wait for completion via websocket, then fetch the image."""
    client_id = str(uuid.uuid4())
    
    log.info(f"Connecting to websocket...")
    async with websockets.connect(f"ws://{COMFYUI_HOST}/ws?clientId={client_id}") as ws:
        log.info(f"Connected! Waiting for completion...")
        while True:
            msg = await ws.recv()
            if isinstance(msg, str):
                data = json.loads(msg)
                msg_type = data.get("type")
                log.info(f"WS message: {msg_type}")
                
                # Check for completion via executing message
                if msg_type == "executing":
                    exec_data = data.get("data", {})
                    node = exec_data.get("node")
                    log.info(f"  Executing node: {node}")
                    if exec_data.get("prompt_id") == prompt_id and node is None:
                        log.info("Generation complete!")
                        break
                
                # Also check status message for queue becoming empty
                if msg_type == "status":
                    status_data = data.get("data", {}).get("status", {})
                    queue_remaining = status_data.get("exec_info", {}).get("queue_remaining", -1)
                    log.info(f"  Queue remaining: {queue_remaining}")
                    if queue_remaining == 0:
                        log.info("Queue empty - generation complete!")
                        break
    
    # Fetch history to get the output filename
    with urllib.request.urlopen(f"http://{COMFYUI_HOST}/history/{prompt_id}") as resp:
        history = json.loads(resp.read())
    
    outputs = history.get(prompt_id, {}).get("outputs", {})
    
    # Look for SaveImage output
    if OUTPUT_NODE_ID in outputs and outputs[OUTPUT_NODE_ID].get("images"):
        img_info = outputs[OUTPUT_NODE_ID]["images"][0]
        filename = img_info["filename"]
        subfolder = img_info.get("subfolder", "")
        img_type = img_info.get("type", "output")
        
        params = urllib.parse.urlencode({"filename": filename, "subfolder": subfolder, "type": img_type})
        with urllib.request.urlopen(f"http://{COMFYUI_HOST}/view?{params}") as resp:
            return resp.read()
    
    return None


async def generate_image(prompt_text: str, user_id: int) -> bytes | None:
    """Generate an image from a text prompt."""
    settings = get_user_settings(user_id)

    workflow = load_workflow()
    workflow[PROMPT_NODE_ID]["inputs"]["text"] = prompt_text
    workflow[SIZE_NODE_ID]["inputs"]["width"] = settings["width"]
    workflow[SIZE_NODE_ID]["inputs"]["height"] = settings["height"]

    prompt_id = queue_prompt(workflow)

    # Store the current prompt_id so user can cancel it
    settings["current_prompt_id"] = prompt_id

    try:
        return await wait_for_image(prompt_id)
    finally:
        # Clear the prompt_id when done (whether successful or not)
        settings["current_prompt_id"] = None


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /start command."""
    await update.message.reply_text(
        "🎨 Z-Image Bot\n\n"
        "Send me a text prompt and I'll generate an image!\n\n"
        "Commands:\n"
        "/settings - Change aspect ratio\n"
        "/r - Retry last prompt with new seed\n"
        "/cancel - Cancel current generation\n\n"
        "Example: A cat wearing a top hat, digital art"
    )


async def settings(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /settings command - show aspect ratio buttons."""
    user_id = update.effective_user.id
    current = get_user_settings(user_id)

    # Build keyboard with aspect ratio options
    buttons = []
    row = []
    for name, (w, h) in ASPECT_RATIOS.items():
        # Mark current selection with ✓
        label = f"✓ {name}" if name == current["aspect_ratio"] else name
        row.append(InlineKeyboardButton(label, callback_data=f"ar:{name}"))
        if len(row) == 3:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)

    keyboard = InlineKeyboardMarkup(buttons)

    await update.message.reply_text(
        f"📐 Current: {current['aspect_ratio']} ({current['width']}×{current['height']})\n\n"
        "Select aspect ratio:",
        reply_markup=keyboard
    )


async def retry(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /r command - retry the last prompt with a new seed."""
    user_id = update.effective_user.id
    settings = get_user_settings(user_id)

    last_prompt = settings.get("last_prompt")
    if not last_prompt:
        await update.message.reply_text("❌ No previous prompt to retry. Send a prompt first!")
        return

    status_msg = await update.message.reply_text(
        f"🔄 Retrying with new seed ({settings['aspect_ratio']})...\n"
        f"Prompt: {last_prompt[:100]}{'...' if len(last_prompt) > 100 else ''}"
    )

    try:
        image_data = await generate_image(last_prompt, user_id)

        if image_data:
            await update.message.reply_photo(
                photo=image_data,
                caption=f"✨ {last_prompt[:200]}"
            )
            await status_msg.delete()
        else:
            await status_msg.edit_text("❌ Failed to get image from ComfyUI")

    except Exception as e:
        await status_msg.edit_text(f"❌ Error: {str(e)}")


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /cancel command - cancel the current generation."""
    user_id = update.effective_user.id
    settings = get_user_settings(user_id)

    prompt_id = settings.get("current_prompt_id")
    if not prompt_id:
        await update.message.reply_text("❌ No active generation to cancel.")
        return

    if cancel_prompt(prompt_id):
        await update.message.reply_text("✅ Generation canceled!")
        settings["current_prompt_id"] = None
    else:
        await update.message.reply_text("❌ Failed to cancel generation. It may have already completed.")


async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle button presses."""
    query = update.callback_query
    await query.answer()
    
    data = query.data
    user_id = update.effective_user.id
    
    if data.startswith("ar:"):
        # Aspect ratio selection
        ratio_name = data[3:]
        if ratio_name in ASPECT_RATIOS:
            width, height = ASPECT_RATIOS[ratio_name]
            user_settings[user_id] = {
                "aspect_ratio": ratio_name,
                "width": width,
                "height": height,
            }
            await query.edit_message_text(
                f"✅ Aspect ratio set to {ratio_name} ({width}×{height})"
            )


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle text messages - generate images."""
    prompt_text = update.message.text.strip()
    user_id = update.effective_user.id

    if not prompt_text:
        await update.message.reply_text("Please send a text prompt.")
        return

    settings = get_user_settings(user_id)
    status_msg = await update.message.reply_text(
        f"🎨 Generating ({settings['aspect_ratio']})..."
    )

    try:
        image_data = await generate_image(prompt_text, user_id)

        if image_data:
            # Store the prompt for /r command
            settings["last_prompt"] = prompt_text

            await update.message.reply_photo(
                photo=image_data,
                caption=f"✨ {prompt_text[:200]}"
            )
            await status_msg.delete()
        else:
            await status_msg.edit_text("❌ Failed to get image from ComfyUI")

    except Exception as e:
        await status_msg.edit_text(f"❌ Error: {str(e)}")


def main():
    if TELEGRAM_TOKEN == "YOUR_BOT_TOKEN_HERE":
        print("❌ Set your TELEGRAM_TOKEN!")
        print("   export TELEGRAM_TOKEN='your_token_here'")
        return
    
    # Check workflow exists
    if not WORKFLOW_PATH.exists():
        print(f"❌ zimage.json not found at {WORKFLOW_PATH}")
        print("   Place your ComfyUI workflow (API format) there.")
        return
    
    print(f"🚀 Starting bot...")
    print(f"   ComfyUI: {COMFYUI_HOST}")
    print(f"   Workflow: {WORKFLOW_PATH}")
    print(f"   Prompt node: {PROMPT_NODE_ID}")
    
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("settings", settings))
    app.add_handler(CommandHandler("r", retry))
    app.add_handler(CommandHandler("cancel", cancel))
    app.add_handler(CallbackQueryHandler(button_callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    app.run_polling()


if __name__ == "__main__":
    main()
