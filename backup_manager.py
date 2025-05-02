import os
import json
import datetime
import discord
import requests

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
    with open("config.json", "r", encoding="utf-8") as f:
        output_format = set(json.load(f)["output_format"])
    """將頻道訊息匯出為 json/html/txt 檔案"""
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

    # 儲存為簡易 HTML
    if "html" in output_format:
        html_path = os.path.join(channel_dir, f"{channel.name}.html")
        with open(html_path, "w", encoding="utf-8") as f:
            f.write("<html><body>\n")
            f.write(f"<h1>Channel: {channel.name}</h1>\n")
            for msg in messages:
                f.write(f"<p><b>{msg['author']}</b> [{msg['timestamp']}]: {msg['content']}</p>\n")
            f.write("</body></html>")

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


