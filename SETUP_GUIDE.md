# ComfyUI Telegram Bot Setup Guide

A guide to setting up ComfyUI with a Telegram bot so you can generate images from your phone.

---

## Part 1: Install ComfyUI

### 1. Install Homebrew (if you don't have it)
```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

### 2. Install Python
```bash
brew install python@3.12
```

### 3. Download ComfyUI
```bash
cd ~
git clone https://github.com/comfyanonymous/ComfyUI.git
cd ComfyUI
```

### 4. Create a virtual environment and install dependencies
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 5. Run ComfyUI to test
```bash
python main.py
```

Open http://127.0.0.1:8188 in your browser. You should see the ComfyUI interface.

> [!note]
> First run will be slow as it downloads some files.

---

## Part 2: Download the Z-Image Model

The bot uses the Z-Image Turbo model. You need to download these files:

### 1. Download the model files

**Diffusion Model (UNET):**
- Go to: https://huggingface.co/zer0int/z-image-turbo-bf16
- Download `z_image_turbo_bf16.safetensors`
- Put it in: `~/ComfyUI/models/diffusion_models/`

**CLIP Text Encoder:**
- Go to: https://huggingface.co/Comfy-Org/Qwen2.5_VL_3B_Instruct_GGUF
- Download `qwen_3_4b.safetensors` (or similar Qwen clip)
- Put it in: `~/ComfyUI/models/clip/`

**VAE:**
- Go to: https://huggingface.co/black-forest-labs/FLUX.1-schnell
- Download `ae.safetensors`
- Put it in: `~/ComfyUI/models/vae/`

### 2. Verify the files are in place
```bash
ls ~/ComfyUI/models/diffusion_models/  # should show z_image_turbo_bf16.safetensors
ls ~/ComfyUI/models/clip/               # should show qwen_3_4b.safetensors
ls ~/ComfyUI/models/vae/                # should show ae.safetensors
```

---

## Part 3: Set Up the Telegram Bot

### 1. Create a bot on Telegram
1. Open Telegram and search for `@BotFather`
2. Send `/newbot`
3. Follow the prompts to name your bot
4. Copy the **API token** it gives you (looks like `123456789:ABCdefGHIjklMNOpqrsTUVwxyz`)

### 2. Install Docker
1. Download Docker Desktop: https://www.docker.com/products/docker-desktop/
2. Install and open it
3. Make sure it's running (whale icon in menu bar)

### 3. Clone the bot repo
```bash
cd ~
git clone https://github.com/mwstandsfor/comfybot.git
cd comfybot
```

### 4. Create your `.env` file with your token
```bash
echo "TELEGRAM_TOKEN=your_token_here" > .env
```

Replace `your_token_here` with the actual token from BotFather.

> [!important]
> The `.env` file keeps your token secret and is ignored by git.
> If your ComfyUI runs on a different port than 8188, also add:
> `echo "COMFYUI_HOST=host.docker.internal:YOUR_PORT" >> .env`

### 5. Build and run
```bash
docker compose up -d
```

Check it's running:
```bash
docker compose logs -f
```

You should see:
```
🚀 Starting bot...
   ComfyUI: host.docker.internal:8188
```

---

## Part 4: Using the Bot

1. **Start ComfyUI first** (it must be running!)
   ```bash
   cd ~/ComfyUI
   source venv/bin/activate
   python main.py
   ```

2. **Open Telegram** and find your bot (search for the name you gave it)

3. **Send `/start`** to see instructions

4. **Send any text prompt** to generate an image
   - Example: `A cat wearing a top hat, digital art`

5. **Send `/settings`** to change aspect ratio

---

## Useful Commands

### ComfyUI
```bash
# Start ComfyUI
cd ~/ComfyUI && source venv/bin/activate && python main.py

# Start on a different port
python main.py --port 7860
```

### Docker Bot
```bash
# View logs
docker compose logs -f

# Restart bot
docker compose restart

# Stop bot
docker compose down

# Rebuild after changes
docker compose up -d --build
```

---

## Troubleshooting

> [!warning] "Connection refused" error
> - Make sure ComfyUI is running
> - Check the port in your `.env` matches your ComfyUI port (default is 8188)

> [!warning] Bot not responding
> - Check logs: `docker compose logs -f`
> - Make sure your `.env` file exists and has the correct token

> [!warning] Images not generating
> - Open ComfyUI in browser (http://127.0.0.1:8188)
> - Check if models are loaded correctly
> - Look for errors in the ComfyUI terminal

> [!warning] Wrong model files
> If you get errors about missing models, double-check:
> 1. File names match exactly what's in `zimage.json`
> 2. Files are in the correct folders under `~/ComfyUI/models/`

---

## Optional: Run ComfyUI on Startup

Create a launch script:
```bash
cat > ~/start-comfyui.sh << 'EOF'
#!/bin/bash
cd ~/ComfyUI
source venv/bin/activate
python main.py
EOF
chmod +x ~/start-comfyui.sh
```

Then just run `~/start-comfyui.sh` to start ComfyUI.

---

## Optional: Access from Anywhere (Tailscale)

If you want to use the bot when away from home:

1. Install Tailscale: https://tailscale.com/download
2. Set up on your Mac
3. Add to your `.env`:
   ```
   COMFYUI_HOST=your-mac-name.tailnet-name:8188
   ```
4. Rebuild: `docker compose up -d --build`

Now your bot works from anywhere!
