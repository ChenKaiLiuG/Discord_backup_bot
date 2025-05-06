import os
import json
import datetime
import discord
import requests

from utils.attachment_downloader import download_attachments

async def run_backup(bot: discord.ext.commands.bot.Bot, guild: discord.guild.Guild):
    """主備份流程，包含訊息與結構備份"""

    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    with open("config.json", "r", encoding="utf-8") as f:
        backup_folder = json.load(f)["backup_folder"]
    backup_path = os.path.join(backup_folder, f"{guild.name}_{timestamp}")
    os.makedirs(backup_path, exist_ok=True)

    # 匯出伺服器結構與使用者清單
    await export_structure(guild, backup_path)

    # 備份每個頻道的訊息
    for channel in guild.text_channels:
        await export_channel_messages(channel, backup_path)
    for thread in guild.threads:
        await export_thread_messages(thread, backup_path)

    # 匯出伺服器的 Emoji
    await export_emojis(guild, backup_path, download_emojis=True)
    print(f"伺服器 {guild.name} 備份完成，儲存於 {backup_path}")

# ---------------------------------------------------------------------
# 結構匯出

async def export_structure(guild: discord.guild.Guild, backup_path: str):
    """匯出伺服器結構與成員清單"""
    structure_file = os.path.join(backup_path, "structure.json")
    members_file = os.path.join(backup_path, "members.json")

    structure = {
        "guild_id": guild.id,
        "guild_name": guild.name,
        "categories": [],
        "channels": [],
        "roles": [],
    }

    structure["categories"] = [
        {"id": category.id, "name": category.name} 
        for category in guild.categories
    ]

    structure["channels"] = [
        {"id": channel.id, "name": channel.name, "type": "text"}
        for channel in guild.text_channels
    ]

    structure["channels"] += [
        {"id": channel.id, "name": channel.name, "type": "voice"}
        for channel in guild.voice_channels
    ]

    structure["roles"] = [
        {"id": role.id, "name": role.name, "permissions": [str(perm) for perm in role.permissions]}
        for role in guild.roles 
    ]

    with open(structure_file, "w", encoding="utf-8") as f:
        json.dump(structure, f, ensure_ascii=False, indent=2)

    members = [{
        "id": member.id,
        "name": member.name,
        "discriminator": member.discriminator,
        "nickname": member.nick if member.nick else None,
        "status": str(member.status)
    } for member in guild.members]

    with open(members_file, "w", encoding="utf-8") as f:
        json.dump(members, f, ensure_ascii=False, indent=2)

# ---------------------------------------------------------------------
# 訊息匯出

async def export_channel_messages(channel: discord.channel.TextChannel, backup_path: str):
    """將頻道訊息匯出為 json/html/txt 檔案"""
    with open("config.json", "r", encoding="utf-8") as f:
        config = json.load(f)

    output_format = set(config.get("output_format", []))
    download_attachments_enabled = config.get("download_attachments", False)

    print(f"正在備份頻道：{channel.name}")
    messages = []

    try:
        async for message in channel.history(limit=None, oldest_first=True):
            messages.append({
                "id": message.id,
                "author": f"{message.author.name}#{message.author.discriminator}",
                "content": message.content,
                "timestamp": str(message.created_at),
                "attachments": [a.url for a in message.attachments],
                "embeds": [e.to_dict() for e in message.embeds],
                "pinned": message.pinned
            })

    except Exception as e:
        print(f"無法備份頻道 {channel.name}：{e}")
        return

    channel_dir = os.path.join(backup_path, "channels")
    os.makedirs(channel_dir, exist_ok=True)

    # 儲存為 JSON
    if "json" in output_format:
        json_path = os.path.join(channel_dir, f"{channel.name}.json")
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(messages, f, ensure_ascii=False, indent=2)

    # 儲存為 TXT
    if "txt" in output_format:
        txt_path = os.path.join(channel_dir, f"{channel.name}.txt")
        with open(txt_path, "w", encoding="utf-8") as f:
            for msg in messages:
                f.write(f"[{msg['timestamp']}] {msg['author']}: {msg['content']}\n")

    # 儲存為 HTML（含附件圖片顯示）
    if "html" in output_format:
    html_path = os.path.join(channel_dir, f"{channel.name}.html")
    attachments_subdir = f"{channel.name}_attachments"
    with open(html_path, "w", encoding="utf-8") as f:
        f.write("""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Channel: {0}</title>
    <style>
        body {{ font-family: sans-serif; background: #2c2f33; color: #dcddde; padding: 20px; }}
        .message {{ margin-bottom: 20px; padding: 10px; background: #36393f; border-radius: 5px; }}
        .author {{ font-weight: bold; color: #7289da; }}
        .timestamp {{ color: #72767d; font-size: 0.9em; margin-left: 5px; }}
        img {{ max-width: 400px; border-radius: 4px; display: block; margin-top: 5px; }}
        a.attachment {{ display: block; color: #00b0f4; margin-top: 5px; }}
    </style>
</head>
<body>
<h1>Channel: {0}</h1>
""".format(channel.name))

        for msg in messages:
            f.write('<div class="message">')
            f.write(f'<span class="author">{msg["author"]}</span>')
            f.write(f'<span class="timestamp">[{msg["timestamp"]}]</span><br>')
            f.write(f'<div class="content">{msg["content"]}</div>')

            # 顯示附件（圖片或連結）
            for url in msg["attachments"]:
                filename = os.path.basename(url)
                file_path = f"{attachments_subdir}/{filename}"
                if any(filename.lower().endswith(ext) for ext in [".png", ".jpg", ".jpeg", ".gif", ".webp"]):
                    f.write(f'<img src="{file_path}" alt="{filename}">')
                else:
                    f.write(f'<a class="attachment" href="{file_path}">{filename}</a>')

            f.write('</div>\n')

        f.write("</body></html>")


    # 下載附件
    if download_attachments_enabled:
        attachments_path = os.path.join(channel_dir, f"{channel.name}_attachments")
        os.makedirs(attachments_path, exist_ok=True)
        await download_attachments(messages, attachments_path)

# ---------------------------------------------------------------------
# Emoji匯出
async def export_emojis(guild: discord.guild.Guild, backup_path: str, download_emojis: bool = False):
    """匯出伺服器的 Emoji"""
    emojis = []
    for emoji in guild.emojis:
        emojis.append({
            "id": emoji.id,
            "name": emoji.name,
            "url": str(emoji.url)
        })

    emojis_file = os.path.join(backup_path, "emojis.json")
    with open(emojis_file, "w", encoding="utf-8") as f:
        json.dump(emojis, f, ensure_ascii=False, indent=2)
    
    # 下載 Emoji 圖片
    if download_emojis:
        emojis_dir = os.path.join(backup_path, "emojis")
        os.makedirs(emojis_dir, exist_ok=True)
        for emoji in emojis:
            emoji_url = emoji["url"]
            # 判斷Emoji是否為靜態或動態
            if emoji_url.endswith(".gif"):
                emoji_name = f"{emoji['name']}.gif"
            else:
                emoji_name = f"{emoji['name']}.png"
            emoji_path = os.path.join(emojis_dir, emoji_name)
            response = requests.get(emoji_url)
            if response.status_code == 200:
                with open(emoji_path, "wb") as f:
                    f.write(response.content)
                print(f"下載 Emoji {emoji['name']} 成功")
            else:
                print(f"下載 Emoji {emoji['name']} 失敗，狀態碼：{response.status_code}")

# ---------------------------------------------------------------------
# 統一備份所有流程（供排程與指令使用）
async def run_backup_all(bot: discord.ext.commands.bot.Bot, guild: discord.guild.Guild):
    try:
        await run_backup(bot, guild)
    except Exception as e:
        print(f"備份伺服器 {guild.name} 時發生錯誤：{e}")

async def export_thread_messages(thread: discord.Thread , backup_path: str):
    """將討論串訊息匯出為 json 檔案"""
    print(f"正在備份討論串：{thread.name}")
    messages = []

    try:
        async for message in thread.history(limit=None, oldest_first=True):
            messages.append({
                "id": message.id,
                "author": f"{message.author.name}#{message.author.discriminator}",
                "content": message.content,
                "timestamp": str(message.created_at),
                "attachments": [a.url for a in message.attachments],
                "embeds": [e.to_dict() for e in message.embeds],
                "pinned": message.pinned
            })

    except Exception as e:
        print(f"無法備份討論串 {thread.name}：{e}")
        return

    thread_dir = os.path.join(backup_path, "threads")
    os.makedirs(thread_dir, exist_ok=True)

    # 儲存為 JSON
    json_path = os.path.join(thread_dir, f"{thread.name}.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(messages, f, ensure_ascii=False, indent=2)
