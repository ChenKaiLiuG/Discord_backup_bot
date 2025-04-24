import discord
from discord.ext import commands
import json
import os
from backup_manager import run_backup

# 讀取設定檔
CONFIG_PATH = "config.json"

def load_config():
    if not os.path.exists(CONFIG_PATH):
        raise FileNotFoundError("找不到 config.json 設定檔，請先建立。")
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

config = load_config()
TOKEN = config["token"]
GUILD_ID = int(config["guild_id"])
DEFAULT_FORMATS = config.get("output_format", ["json"])

# 建立 bot
intents = discord.Intents.default()
intents.messages = True
intents.guilds = True
intents.message_content = True  # 必須在 Dev Portal 勾選 Message Content Intent

bot = commands.Bot(command_prefix="!", intents=intents)

# 動態記憶格式設定
current_formats = set(DEFAULT_FORMATS)

@bot.event
async def on_ready():
    print(f"備份機器人已啟動：{bot.user.name}")
    print(f"已連接到伺服器：{GUILD_ID}")

@bot.command()
async def backup(ctx, *args):
    """主備份指令"""
    global current_formats

    if ctx.guild is None or ctx.guild.id != GUILD_ID:
        await ctx.send("你不在授權的伺服器中，無法備份。")
        return

    if not args or args[0] == "now":
        await ctx.send("開始備份中，請稍候...")
        await run_backup(bot, ctx.guild, formats=current_formats)
        await ctx.send("備份完成！")
    elif args[0] == "format":
        if len(args) == 1:
            await ctx.send(f"目前格式：{'、'.join(current_formats)}")
        else:
            current_formats = set(args[1:])
            await ctx.send(f"備份格式已更新為：{'、'.join(current_formats)}")
    else:
        await ctx.send("不明的參數，可用參數為：`now`, `format [json|html|txt]`")

bot.run(TOKEN)
