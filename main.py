import discord
from discord.ext import tasks
import requests
import json
import os
from datetime import datetime

intents = discord.Intents.default()
intents.message_content = True

bot = discord.Client(intents=intents)

APP_ID = 3678970
CHECK_INTERVAL = 400  # 15 dakikada bir
DATA_FILE = "config.json"   # Hem buildid hem kanal bilgisini tutacak

# Config dosyasından verileri yükle
def load_config():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r") as f:
                return json.load(f)
        except:
            pass
    return {"buildid": None, "channel_id": None}

# Config dosyasını kaydet
def save_config(buildid=None, channel_id=None):
    config = load_config()
    if buildid is not None:
        config["buildid"] = buildid
    if channel_id is not None:
        config["channel_id"] = channel_id
    with open(DATA_FILE, "w") as f:
        json.dump(config, f)

config = load_config()
CHANNEL_ID = config.get("channel_id")

def get_current_buildid():
    try:
        r = requests.get(f"https://api.steamcmd.net/v1/info/{APP_ID}", timeout=15)
        if r.status_code == 200:
            data = r.json()
            buildid = data.get("data", {}).get("branches", {}).get("public", {}).get("buildid")
            return int(buildid) if buildid else None
    except Exception as e:
        print(f"Build ID hatası: {e}")
        return None
    return None

@bot.event
async def on_ready():
    print(f"✅ {bot.user} olarak giriş yapıldı!")
    print(f"Kayıtlı kanal ID: {CHANNEL_ID}")
    check_for_update.start()
    print("Güncelleme kontrolü başlatıldı.")

@tasks.loop(seconds=CHECK_INTERVAL)
async def check_for_update():
    global CHANNEL_ID
    if not CHANNEL_ID:
        return

    current = get_current_buildid()
    last_build = config.get("buildid")

    if current and current != last_build:
        channel = bot.get_channel(CHANNEL_ID)
        if channel:
            embed = discord.Embed(
                title="🎮 TBH: Task Bar Hero Güncellemesi Geldi!",
                description=f"**Yeni Build ID:** `{current}`",
                color=0x00ff00,
                timestamp=datetime.utcnow()
            )
            embed.add_field(name="Steam Mağaza", value=f"[Aç](https://store.steampowered.com/app/{APP_ID}/)", inline=True)
            embed.add_field(name="SteamDB", value=f"[Değişiklikler](https://steamdb.info/app/{APP_ID}/)", inline=True)
            await channel.send(embed=embed)

            save_config(buildid=current)
            print(f"Yeni güncelleme bildirildi: {current}")
        else:
            print("Kanal bulunamadı.")

@bot.event
async def on_message(message):
    global CHANNEL_ID
    if message.author.bot:
        return

    if message.content.lower() == "!setchannel":
        CHANNEL_ID = message.channel.id
        save_config(channel_id=CHANNEL_ID)
        await message.channel.send("✅ Ersin artık TBH güncelleme bildirimleri için **kalıcı** olarak ayarlandı!")
        
        current = get_current_buildid()
        if current:
            save_config(buildid=current)
            await message.channel.send(f"📊 Mevcut build: `{current}`")

    if message.content.lower() == "!testupdate":
        if CHANNEL_ID:
            channel = bot.get_channel(CHANNEL_ID)
            if channel:
                embed = discord.Embed(title="🧪 TEST BİLDİRİMİ", description="Ersin çalışıyor!", color=0xffaa00)
                await channel.send(embed=embed)

bot.run(os.getenv("DISCORD_TOKEN"))
