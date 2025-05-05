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

    print(f"伺服器結構與成員已儲存：{structure_file}, {members_file}")
