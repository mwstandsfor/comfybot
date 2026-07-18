# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

ComfyBot is a Telegram bot that generates images via ComfyUI (a node-based AI image generation interface). Users send text prompts to the bot on Telegram; the bot queues them to ComfyUI, monitors generation via WebSocket, and sends back the resulting image.

## Running the Bot

```bash
# Local development
pip install -r requirements.txt
python comfy-botfater.py

# Docker (production)
docker compose up -d
docker compose logs -f
docker compose up -d --build  # after code changes
```

Requires a `.env` file with:
```
TELEGRAM_TOKEN=your_token
COMFYUI_HOST=host.docker.internal:8188
```

## Architecture

All bot logic lives in a single file: **`comfy-botfater.py`**.

### Key Components

**User state** — stored in-memory in `user_settings` dict (keyed by Telegram user ID). Includes `width`, `height`, `steps`, `last_prompt`, `last_seed`, `current_prompt_id`. Resets on restart.

**ComfyUI workflow** — `zimage.json` is a ComfyUI node graph loaded at runtime. Node IDs are hardcoded constants at the top of the file:
- `PROMPT_NODE_ID = "45"` — text prompt
- `SIZE_NODE_ID = "41"` — image dimensions
- `KSAMPLER_NODE_ID = "44"` — generation steps
- `SEED_NODE_ID = "63"` — seed value
- `OUTPUT_NODE_ID = "9"` — output/save node

**Image generation pipeline:**
1. Clone workflow JSON, inject user settings (prompt, size, steps, seed)
2. HTTP POST to `/prompt` → receive `prompt_id`
3. WebSocket on `/ws` monitors execution events
4. HTTP GET `/history/{prompt_id}` to find output filename
5. HTTP GET `/view?filename=...` to fetch image bytes
6. Send image back via Telegram

**Aspect ratio system** — `ASPECT_RATIOS` dict maps friendly names (e.g. `"16:9"`) to `(width, height)` tuples. User selection via inline keyboard updates `user_settings`.

### Commands

| Command | Handler | Purpose |
|---------|---------|---------|
| Text message | `handle_message()` | Generate image from prompt |
| `/r` | `retry()` | Regenerate last prompt with new seed |
| `/scale` | `scale()` | Two-step menu: scale factor → quality; upscales last image |
| `/settings` | `settings()` | Inline keyboard for aspect ratio and steps |
| `/cancel` | `cancel()` | Cancel active generation by prompt_id |

### Scaling flow (`/scale`)
Two-step inline keyboard: user picks scale factor (1.5x or 2x), then quality (steps: 8 or 12). Stores selection in `user_settings["pending_scale"]` between the two button presses, then regenerates at the scaled dimensions.
