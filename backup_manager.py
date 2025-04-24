import os
import json
import datetime

async def run_backup(bot, guild):
    """主備份流程，包含訊息與結構備份"""

    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = os.path.join("backups", f"{guild.name}_{timestamp}")
    os.makedirs(backup_path, exist_ok=True)

    # 匯出伺服器結構與使用者清單
    await export_structure(guild, backup_path)

    # 備份每個頻道的訊息
    for channel in guild.text_channels:
        await export_channel_messages(channel, backup_path)

    print(f"伺服器 {guild.name} 備份完成，儲存於 {backup_path}")

# ---------------------------------------------------------------------
# 結構匯出

async def export_structure(guild, backup_path):
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

    for category in guild.categories:
        structure["categories"].append({
            "id": category.id,
            "name": category.name
        })

    for channel in guild.text_channels:
        structure["channels"].append({
            "id": channel.id,
            "name": channel.name,
            "type": "text"
        })

    for channel in guild.voice_channels:
        structure["channels"].append({
            "id": channel.id,
            "name": channel.name,
            "type": "voice"
        })

    for role in guild.roles:
        structure["roles"].append({
            "id": role.id,
            "name": role.name,
            "permissions": [str(perm) for perm in role.permissions]
        })

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

async def export_channel_messages(channel, backup_path):
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
    json_path = os.path.join(channel_dir, f"{channel.name}.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(messages, f, ensure_ascii=False, indent=2)

    # 儲存為 TXT
    txt_path = os.path.join(channel_dir, f"{channel.name}.txt")
    with open(txt_path, "w", encoding="utf-8") as f:
        for msg in messages:
            f.write(f"[{msg['timestamp']}] {msg['author']}: {msg['content']}\n")

    # 儲存為簡易 HTML
    html_path = os.path.join(channel_dir, f"{channel.name}.html")
    with open(html_path, "w", encoding="utf-8") as f:
        f.write("<html><body>\n")
        f.write(f"<h1>Channel: {channel.name}</h1>\n")
        for msg in messages:
            f.write(f"<p><b>{msg['author']}</b> [{msg['timestamp']}]: {msg['content']}</p>\n")
        f.write("</body></html>")
