import os
import json
import datetime
from utils import message_exporter, structure_exporter  # 將來會補上
import zipfile

# 載入 config
with open("config.json", "r", encoding="utf-8") as f:
    config = json.load(f)

BACKUP_ROOT = config.get("backup_folder", "./backups")

def zip_folder(folder_path, zip_path):
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, _, files in os.walk(folder_path):
            for file in files:
                abs_path = os.path.join(root, file)
                rel_path = os.path.relpath(abs_path, folder_path)
                zipf.write(abs_path, rel_path)

async def run_backup(bot, guild, formats=["json", "html", "txt"]):
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    guild_name = guild.name.replace(" ", "_").lower()
    backup_path = os.path.join(BACKUP_ROOT, f"{guild_name}_{timestamp}")

    os.makedirs(backup_path, exist_ok=True)

    # 匯出頻道訊息
    await message_exporter.export_all_messages(bot, guild, backup_path, formats)

    # 匯出頻道/分類/權限/角色結構
    await structure_exporter.export_structure(guild, backup_path)

    # TODO: 匯出附件（下一步實作）

    # 壓縮備份檔案
    zip_path = os.path.join(BACKUP_ROOT, f"{guild_name}_{timestamp}.zip")
    zip_folder(backup_path, zip_path)

    print(f"備份完成：{zip_path}")
