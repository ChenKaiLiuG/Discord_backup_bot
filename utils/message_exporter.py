import os
import json
import html
import discord
from utils.attachment_downloader import download_attachments

async def export_channel_messages(channel: discord.TextChannel, backup_path: str, output_format: set[str] , download_attachments_enabled: bool = False):
    """將頻道訊息匯出為 json/html/txt 檔案"""
    print(f"正在備份頻道：{channel.name}")
    messages = await collect_messages(channel)

    channel_dir = os.path.join(backup_path, "channels")
    os.makedirs(channel_dir, exist_ok=True)
    await save_messages(channel.name, messages, channel_dir, output_format, download_attachments_enabled)
    
    try:
        # 備份封存的公開討論串
        async for thread in channel.archived_threads(limit=None):
            await export_thread_messages(thread, backup_path, output_format, download_attachments_enabled)

        # 備份封存的私密討論串
        async for thread in channel.archived_threads(private=True, limit=None):
            await export_thread_messages(thread, backup_path, output_format, download_attachments_enabled)

        # 活躍討論串
        for thread in channel.threads:
            await export_thread_messages(thread, backup_path, output_format, download_attachments_enabled)
    except Exception as e:
        print(f"備份討論串時發生錯誤：{e}")

async def export_thread_messages(thread: discord.Thread, backup_path: str, output_format: set[str] , download_attachments_enabled: bool = False):
    """將討論串訊息匯出為 json/html/txt 檔案"""
    print(f"正在備份討論串：{thread.name}")
    messages = await collect_messages(thread)

    thread_dir = os.path.join(backup_path, "threads")
    os.makedirs(thread_dir, exist_ok=True)

    await save_messages(thread.name, messages, thread_dir , output_format, download_attachments_enabled)

# ------------------------------------------------------

async def collect_messages(channel_or_thread):
    """收集訊息"""
    messages = []
    try:
        async def get_reactions(reactions):
            result = []
            for reaction in reactions:
                users = []
                async for user in reaction.users():
                    users.append({ "id": user.id, "name": user.name })
                result.append({
                    "emoji": getattr(reaction.emoji, "name", reaction.emoji),
                    "sender": users
                })
            return result

        async for message in channel_or_thread.history(limit=None, oldest_first=True):
            messages.append({
                "id": message.id,
                "author": f"{message.author.name}#{message.author.discriminator}" if message.author else "Unknown",
                "content": message.content,
                "system_content": message.system_content,  # ➕系統通知
                "timestamp": str(message.created_at),
                "attachments": [a.url for a in message.attachments],
                "embeds": [e.to_dict() for e in message.embeds],
                "components": [c.to_dict() for c in message.components] if hasattr(message, "components") else [],
                "pinned": message.pinned,
                "type": str(message.type),  # ➕訊息類型
                "is_webhook": bool(message.webhook_id),  # ➕是否為 Webhook
                "reply_to": message.reference.message_id if message.reference else None,
                "stickers": [s.name for s in message.stickers] if message.stickers else [],
                "reactions": await get_reactions(message.reactions),
            })
    except Exception as e:
        print(f"無法備份 {channel_or_thread.name}：{e}")
    return messages

async def save_messages(name, messages, directory, output_format, download_attachments_enabled):
    """儲存訊息為 json/txt/html，並下載附件"""
    if "json" in output_format:
        json_path = os.path.join(directory, f"{name}.json")
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(messages, f, ensure_ascii=False, indent=2)

    if "txt" in output_format:
        txt_path = os.path.join(directory, f"{name}.txt")
        with open(txt_path, "w", encoding="utf-8") as f:
            for msg in messages:
                f.write(f"[{msg['timestamp']}] {msg['author']}: {msg['content']}\n")

    if "html" in output_format:
        html_path = os.path.join(directory, f"{name}.html")
        attachments_subdir = f"{name}_attachments"
        with open(html_path, "w", encoding="utf-8") as f:
            f.write(generate_html_header(name))
            for msg in messages:
                f.write('<div class="message">')
                f.write(f'<span class="author">{html.escape(msg["author"])}</span>')
                f.write(f'<span class="timestamp">[{msg["timestamp"]}]</span><br>')
                f.write(f'<div class="content">{html.escape(msg["content"])}</div>')
                for url in msg["attachments"]:
                    filename = os.path.basename(url)
                    file_path = f"{attachments_subdir}/{filename}"
                    if any(filename.lower().endswith(ext) for ext in [".png", ".jpg", ".jpeg", ".gif", ".webp"]):
                        f.write(f'<img src="{file_path}" alt="{filename}">')
                    else:
                        f.write(f'<a class="attachment" href="{file_path}">{filename}</a>')
                f.write('</div>\n')
            f.write("</body></html>")

    if download_attachments_enabled:
        attachments_path = os.path.join(directory, f"{name}_attachments")
        os.makedirs(attachments_path, exist_ok=True)
        await download_attachments(messages, attachments_path)

def generate_html_header(channel_name):
    return f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Channel: {channel_name}</title>
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
<h1>Channel: {channel_name}</h1>
"""
