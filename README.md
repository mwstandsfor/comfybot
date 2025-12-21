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

## Part 2: Set Up the Telegram Bot

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

### 4. Add your exported workflow

Copy the `zimage.json` you exported earlier into the `comfybot` folder, replacing the existing one.

### 5. Create your `.env` file

```bash
echo "TELEGRAM_TOKEN=your_token_here" > .env
```

Replace `your_token_here` with the actual token from BotFather.

> [!important]
> If your ComfyUI port is different from 8188, also add:
> ```bash
> echo "COMFYUI_HOST=host.docker.internal:YOUR_PORT" >> .env
> ```

### 6. Build and run

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

-----

## Part 3: Using the Bot

1. **Start ComfyUI first** - open the ComfyUI desktop app (it must be running!)

2. **Open Telegram** and find your bot (search for the name you gave it)

3. **Send `/start`** to see instructions

4. **Send any text prompt** to generate an image
   - Example: `A cat wearing a top hat, digital art`

5. **Send `/settings`** to change aspect ratio

-----

## Useful Commands

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

> [!warning] "Connection refused" error
> 
> - Make sure ComfyUI desktop app is running
> - Check the port in your `.env` matches your ComfyUI port (find it in ComfyUI Settings > Server-config)

> [!warning] Bot not responding
> 
> - Check logs: `docker compose logs -f`
> - Make sure your `.env` file exists and has the correct token

> [!warning] Images not generating
> 
> - Open ComfyUI and try running the workflow manually
> - Check if models are loaded correctly
> - Look for errors in the ComfyUI interface

> [!warning] Wrong model files
> If you get errors about missing models, double-check:
> 
> 1. The models downloaded correctly via the template
> 2. File names in your exported `zimage.json` match what's installed

