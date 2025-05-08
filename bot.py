import discord
from discord.ext import commands
import asyncio
import json
import threading

from backup_manager import run_backup
from utils.scheduler import schedule_backups

# -----------------------------------------------------
# 載入 Token 與設定
with open("config.json", "r", encoding="utf-8") as f:
    config = json.load(f)

BOT_TOKEN = config["bot_token"]

# -----------------------------------------------------
# 啟用 Intents
intents = discord.Intents.default()
intents.messages = True
intents.guilds = True
intents.members = True  # 匯出成員資訊需要這個
intents.message_content = True  

# -----------------------------------------------------
# 建立 bot 實例
bot = commands.Bot(command_prefix="!", intents=intents)

# -----------------------------------------------------
# 當 bot 準備好後執行的事件
@bot.event
async def on_ready():
    print(f"機器人已登入：{bot.user.name} (ID: {bot.user.id})")
    print(f"目前已加入 {len(bot.guilds)} 個伺服器")
    asyncio.create_task(run_schedule())

# -----------------------------------------------------
# 指令：!backup（手動備份當前伺服器）
@bot.command()
async def backup(ctx):
    await ctx.send("開始備份伺服器資料...")
    await run_backup(bot, ctx.guild)
    await ctx.send("備份完成！")

# -----------------------------------------------------
# 啟動排程
async def run_schedule():
    thread = threading.Thread(target=schedule_backups, args=(bot,), daemon=True)
    thread.start()

# -----------------------------------------------------
# 啟動 bot
bot.run(BOT_TOKEN)
