import os
import json

def export_structure(guild, backup_path):
    """匯出伺服器的結構，包括頻道、分類、角色與權限"""
    print(f"正在匯出伺服器結構：{guild.name}")

    structure_file = os.path.join(backup_path, "structure.json")
    members_file = os.path.join(backup_path, "members.json")
    
    # 匯出伺服器的頻道結構
    structure = {
        "guild_id": guild.id,
        "guild_name": guild.name,
        "categories": [],
        "channels": [],
        "roles": [],
    }

    # 頻道結構
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

    # 角色與權限
    for role in guild.roles:
        structure["roles"].append({
            "id": role.id,
            "name": role.name,
            "permissions": [str(perm) for perm in role.permissions]
        })

    # 儲存伺服器結構
    with open(structure_file, "w", encoding="utf-8") as f:
        json.dump(structure, f, ensure_ascii=False, indent=2)

    # 儲存所有成員的 ID、名稱、暱稱與狀態
    members = [{
        "id": member.id,
        "name": member.name,
        "discriminator": member.discriminator,
        "nickname": member.nick if member.nick else None,  # 儲存暱稱
        "status": str(member.status)  # 儲存狀態（如：online, offline, dnd）
    } for member in guild.members]

    with open(members_file, "w", encoding="utf-8") as f:
        json.dump(members, f, ensure_ascii=False, indent=2)

    print(f"伺服器結構與成員已儲存：{structure_file}, {members_file}")
