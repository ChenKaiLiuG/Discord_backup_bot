import os
import json
import datetime
import discord
from utils.structure_exporter import export_structure
from utils.message_exporter import export_channel_messages, export_thread_messages
from utils.emoji_exporter import export_emojis
from utils.attachment_downloader import download_attachments

async def run_backup(bot: discord.ext.commands.bot.Bot, guild: discord.guild.Guild):
    """主備份流程，包含訊息與結構備份"""
    with open("config.json", "r", encoding="utf-8") as f:
        config = json.load(f)
        
    output_format = set(config.get("output_format",[]))
    download_attachments_enabled = config.get("download_attachments",False)
    backup_folder = config.get("backup_folder", "backup")
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = os.path.join(backup_folder, f"{guild.name}_{timestamp}")
    os.makedirs(backup_path, exist_ok=True)

    export_structure(guild, backup_path)

    for channel in guild.text_channels:
        await export_channel_messages(channel, backup_path, output_format, download_attachments_enabled)

    await export_emojis(guild, backup_path, download_emojis=True)

    print(f"伺服器 {guild.name} 備份完成，儲存於 {backup_path}")

async def run_backup_all(bot: discord.ext.commands.bot.Bot, guild: discord.guild.Guild):
    try:
        await run_backup(bot, guild)
    except Exception as e:
        print(f"備份伺服器 {guild.name} 時發生錯誤：{e}")
