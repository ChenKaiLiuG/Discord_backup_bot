import os
import discord
import aiohttp
from utils.formatter import format_message_as_html, format_message_as_txt

async def download_attachment(attachment, download_folder):
    """下載附件到指定資料夾"""
    file_path = os.path.join(download_folder, attachment.filename)
    async with aiohttp.ClientSession() as session:
        async with session.get(attachment.url) as response:
            if response.status == 200:
                with open(file_path, "wb") as f:
                    f.write(await response.read())
                print(f"已下載附件：{attachment.filename}")
            else:
                print(f"下載附件失敗：{attachment.filename}")
    return file_path

async def export_all_messages(bot, guild, backup_path, formats=["json"]):
    print(f"正在備份伺服器訊息：{guild.name}")

    message_dir = os.path.join(backup_path, "messages")
    os.makedirs(message_dir, exist_ok=True)

    for channel in guild.text_channels:
        if not channel.permissions_for(guild.me).read_message_history:
            print(f"跳過無權限頻道：{channel.name}")
            continue

        try:
            print(f"備份頻道：#{channel.name}")
            messages = []
            channel_folder = os.path.join(message_dir, channel.name)
            os.makedirs(channel_folder, exist_ok=True)

            async for msg in channel.history(limit=None, oldest_first=True):
                attachments = []
                for attachment in msg.attachments:
                    file_path = await download_attachment(attachment, channel_folder)
                    attachments.append(file_path)

                messages.append({
                    "id": msg.id,
                    "author": f"{msg.author.name}#{msg.author.discriminator}",
                    "content": msg.content,
                    "timestamp": msg.created_at.isoformat(),
                    "attachments": attachments
                })

            base_filename = os.path.join(channel_folder, f"{channel.name}")
            if "json" in formats:
                with open(base_filename + ".json", "w", encoding="utf-8") as f:
                    json.dump(messages, f, ensure_ascii=False, indent=2)

            if "html" in formats:
                html = format_message_as_html(channel.name, messages)
                with open(base_filename + ".html", "w", encoding="utf-8") as f:
                    f.write(html)

            if "txt" in formats:
                txt = format_message_as_txt(messages)
                with open(base_filename + ".txt", "w", encoding="utf-8") as f:
                    f.write(txt)

        except Exception as e:
            print(f"備份頻道失敗：{channel.name}，錯誤：{e}")
