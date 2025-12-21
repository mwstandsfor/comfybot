# comfybot
A guide to setting up ComfyUI with a Telegram bot so you can generate images from your phone.


-----

## Part 1: Install ComfyUI


> [!note]
> First run will be slow as it downloads some files.


### 1. Get ComfyUI

#### **I use the desktop app, download it here**
- https://www.comfy.org/download
- Once downloaded and installed and open.


### 2. Setup Z-Image workflow

- Click on Templates, the last item in the menu bar on the left hand side.
- Go to `Image`.
- Get `Z-Image-Turbo Text to Image`
This should open it prompt the models to download.

#### **Test it** 
- Use the base prompt or use your own with a basic image prompt in the Step 3: green node
- Click `run` on the bottom floating bar.

#### **Save your workflow**
- Save your workflow by clicking on the `image_z_image_turbo` tab in the workflow viewer. 
- Save it or Save as. You first need to save the workflow before you can export it. I saved it as `zimage`.


### 3. Activate Dev Mode

You need to export the json workflow in order to get it to work. For this you need to activate Dev mode.

#### **Go to Settings**
- Click on the comfyui icon on the app > Settings
- It should be the first menu item that pop ups. Make sure `Enable dev mode options (API save, etc.)` is active.

#### **Get port number**
- While we are here, note down the port number in the popup menu, go to the last item, `Server-config`
- **Note down your port number.**


### 4. Export workflow 

You need to export the workflow for the bot.
- Click on the comfyui icon on the app icon > File > Export (API)
- Save it on like your desktop for now. We will move it later to your code folder.

 
> [!note]
> There is a zimage.json file in the repo. Can ignore it or use it.



-----

## Part 3: Set Up the Telegram Bot

### 1. Create a bot on Telegram

1. Open Telegram and search for `@BotFather`
2. Send `/newbot`
3. Follow the prompts to name your bot
4. Copy the **API token** it gives you (looks like `123456789:ABCdefGHIjklMNOpqrsTUVwxyz`)

### 2. Install Docker

1. Download Docker Desktop: https://www.docker.com/products/docker-desktop/
2. Install and open it
3. Make sure it’s running (whale icon in menu bar)

### 3. Set up the bot code

```bash
mkdir -p ~/comfybot
cd ~/comfybot
```

Copy these files 

- `comfy-botfater.py`
- `zimage.json`
- `Dockerfile`
- `docker-compose.yml`
- `requirements.txt`

### 4. Edit docker-compose.yml with your token

```bash
nano docker-compose.yml
```

Replace the `TELEGRAM_TOKEN` with your bot token from BotFather:

```yaml
services:
  comfybot:
    build: .
    container_name: comfybot
    restart: unless-stopped
    environment:
      - TELEGRAM_TOKEN=YOUR_TOKEN_HERE
      - COMFYUI_HOST=host.docker.internal:8188
    volumes:
      - ./zimage.json:/app/zimage.json:ro
```

> [!important]
> If your ComfyUI runs on a different port, change `8188` to match.

Save and exit (Ctrl+X, then Y, then Enter).

### 5. Build and run

```bash
docker compose up -d
```

Check it’s running:

```bash
docker compose logs -f
```

You should see:

```
🚀 Starting bot...
   ComfyUI: host.docker.internal:8188
```

-----

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
1. **Send `/settings`** to change aspect ratio

-----

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

-----

## Troubleshooting

> [!warning] “Connection refused” error
> 
> - Make sure ComfyUI is running
> - Check the port matches in `docker-compose.yml`

> [!warning] Bot not responding
> 
> - Check logs: `docker compose logs -f`
> - Make sure your Telegram token is correct

> [!warning] Images not generating
> 
> - Open ComfyUI in browser (http://127.0.0.1:8188)
> - Check if models are loaded correctly
> - Look for errors in the ComfyUI terminal

> [!warning] Wrong model files
> If you get errors about missing models, double-check:
> 
> 1. File names match exactly what’s in `zimage.json`
> 2. Files are in the correct folders under `~/ComfyUI/models/`

-----

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

-----

## Optional: Access from Anywhere (Tailscale)

If you want to use the bot when away from home:

1. Install Tailscale: https://tailscale.com/download
2. Set up on your Mac
3. Update `docker-compose.yml`:
   
   ```yaml
   COMFYUI_HOST=your-mac-name.tailnet-name:8188
   ```
4. Rebuild: `docker compose up -d --build`

Now your bot works from anywhere!

