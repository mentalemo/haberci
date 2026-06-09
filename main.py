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
CHECK_INTERVAL = 60  # Test için 60 saniye (sonra 900 yapacağız)
DATA_FILE = "last_build.json"
CHANNEL_ID = None

def get_current_buildid():
    try:
        r = requests.get(f"https://api.steamcmd.net/v1/info/{APP_ID}", timeout=15)
        if r.status_code == 200:
            data = r.json()
            buildid = data.get("data", {}).get("branches", {}).get("public", {}).get("buildid")
            return int(buildid) if buildid else None
    except Exception as e:
        print(f"Build ID alınırken hata: {e}")
        return None
    return None

@bot.event
async def on_ready():
    print(f"✅ {bot.user} olarak giriş yapıldı!")
    check_for_update.start()
    print("Güncelleme kontrol döngüsü başlatıldı.")

@tasks.loop(seconds=CHECK_INTERVAL)
async def check_for_update():
    global CHANNEL_ID
    if not CHANNEL_ID:
        return

    current = get_current_buildid()
    last_build = None

    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r") as f:
                data = json.load(f)
                last_build = data.get("buildid")
        except:
            pass

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

            with open(DATA_FILE, "w") as f:
                json.dump({"buildid": current}, f)
            print(f"Yeni build tespit edildi: {current}")
        else:
            print("Kanal bulunamadı.")

@bot.event
async def on_message(message):
    global CHANNEL_ID
    if message.author.bot:
        return

    if message.content.lower() == "!setchannel":
        CHANNEL_ID = message.channel.id
        await message.channel.send("✅ Bu kanal artık TBH güncelleme bildirimleri için ayarlandı!")
        current = get_current_buildid()
        if current:
            with open(DATA_FILE, "w") as f:
                json.dump({"buildid": current}, f)
            await message.channel.send(f"📊 Şu anki build: `{current}`")

    if message.content.lower() == "!testupdate":
        if CHANNEL_ID:
            channel = bot.get_channel(CHANNEL_ID)
            if channel:
                embed = discord.Embed(title="🧪 TEST BİLDİRİMİ", description="Bot çalışıyor! Her şey yolunda.", color=0xffaa00)
                await channel.send(embed=embed)

bot.run(os.getenv("DISCORD_TOKEN"))
