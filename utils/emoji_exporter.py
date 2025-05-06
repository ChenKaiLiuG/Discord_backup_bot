import os
import json
import requests
from discord import Guild

async def export_emojis(guild: Guild, backup_path: str, download_emojis: bool = False):
    """匯出伺服器的 Emoji 清單與圖片（選擇性）"""
    emojis = []
    for emoji in guild.emojis:
        emojis.append({
            "id": emoji.id,
            "name": emoji.name,
            "url": str(emoji.url)
        })

    # 儲存 JSON 清單
    emojis_file = os.path.join(backup_path, "emojis.json")
    with open(emojis_file, "w", encoding="utf-8") as f:
        json.dump(emojis, f, ensure_ascii=False, indent=2)

    # 選擇性下載圖片
    if download_emojis:
        emojis_dir = os.path.join(backup_path, "emojis")
        os.makedirs(emojis_dir, exist_ok=True)
        for emoji in emojis:
            emoji_url = emoji["url"]
            ext = ".gif" if emoji_url.endswith(".gif") else ".png"
            emoji_name = f"{emoji['name']}{ext}"
            emoji_path = os.path.join(emojis_dir, emoji_name)

            try:
                response = requests.get(emoji_url)
                response.raise_for_status()
                with open(emoji_path, "wb") as f:
                    f.write(response.content)
                print(f"下載 Emoji {emoji['name']} 成功")
            except Exception as e:
                print(f"下載 Emoji {emoji['name']} 失敗：{e}")
