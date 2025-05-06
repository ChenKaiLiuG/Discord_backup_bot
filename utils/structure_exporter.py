import os
import json

def export_structure(guild, backup_path):
    """匯出伺服器的結構，包括頻道、分類、角色與權限"""
    print(f"正在匯出伺服器結構：{guild.name}")

    structure_file = os.path.join(backup_path, "structure.json")
    members_file = os.path.join(backup_path, "members.json")

    # 匯出伺服器的結構
    structure = {
        "guild_id": guild.id,
        "guild_name": guild.name,
        "categories": [],
        "channels": [],
        "roles": [],
    }

    # 建立 id → 名稱 的類別對照表
    category_name_map = {category.id: category.name for category in guild.categories}

    # 類別清單
    for category in guild.categories:
        structure["categories"].append({
            "id": category.id,
            "name": category.name
        })

    # 頻道（文字 + 語音）
    all_channels = guild.text_channels + guild.voice_channels
    for channel in all_channels:
        # 權限覆寫
        overwrites = []
        for target, perms in channel.overwrites.items():
            target_type = "role" if hasattr(target, "permissions") else "member"
            overwrites.append({
                "target_id": target.id,
                "target_name": target.name,
                "target_type": target_type,
                "allow": perms.pair()[0].value,
                "deny": perms.pair()[1].value
            })

        structure["channels"].append({
            "id": channel.id,
            "name": channel.name,
            "type": "text" if channel in guild.text_channels else "voice",
            "parent_id": channel.category_id,
            "parent_name": category_name_map.get(channel.category_id),  # 新增的欄位
            "sync_with_category": channel.permissions_synced,
            "overwrites": overwrites
        })

    # 角色清單
    for role in guild.roles:
        structure["roles"].append({
            "id": role.id,
            "name": role.name,
            "permissions": [str(perm) for perm in role.permissions]
        })

    # 儲存
    with open(structure_file, "w", encoding="utf-8") as f:
        json.dump(structure, f, ensure_ascii=False, indent=2)

    # 成員清單
    members = [{
        "id": member.id,
        "name": member.name,
        "discriminator": member.discriminator,
        "nickname": member.nick if member.nick else None,
        "status": str(member.status)
    } for member in guild.members]

    with open(members_file, "w", encoding="utf-8") as f:
        json.dump(members, f, ensure_ascii=False, indent=2)

    # 輸出 HTML 頻道結構圖
    html_file = os.path.join(backup_path, "structure.html")
    with open(html_file, "w", encoding="utf-8") as f:
        f.write("<html><head><meta charset='utf-8'><style>\n")
        f.write("body { font-family: Arial, sans-serif; }\n")
        f.write(".category { font-weight: bold; margin-top: 1em; }\n")
        f.write(".channel { margin-left: 20px; }\n")
        f.write(".voice { color: gray; font-style: italic; }\n")
        f.write("</style></head><body>\n")
        f.write(f"<h1>伺服器結構：{guild.name}</h1>\n")

        # 類別 → 頻道對照
        categories = {c.id: [] for c in guild.categories}
        uncategorized = []

        for ch in structure["channels"]:
            if ch["parent_id"] in categories:
                categories[ch["parent_id"]].append(ch)
            else:
                uncategorized.append(ch)

        # 有類別的
        for cat in structure["categories"]:
            f.write(f"<div class='category'>{cat['name']}</div>\n")
            for ch in categories.get(cat["id"], []):
                channel_type = "voice" if ch["type"] == "voice" else "text"
                voice_class = " voice" if channel_type == "voice" else ""
                f.write(f"<div class='channel{voice_class}'>#{ch['name']}</div>\n")

        # 無分類的頻道
        if uncategorized:
            f.write(f"<div class='category'>未分類</div>\n")
            for ch in uncategorized:
                voice_class = " voice" if ch["type"] == "voice" else ""
                f.write(f"<div class='channel{voice_class}'>#{ch['name']}</div>\n")

        f.write("</body></html>")

    print(f"伺服器結構與成員已儲存：{structure_file}, {members_file}")
