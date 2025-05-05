import schedule
import time
import json
from backup_manager import run_backup_all
import threading
import re

def load_schedule_config():
    with open("config.json", "r", encoding="utf-8") as f:
        config = json.load(f)
    return config.get("SCHEDULE", "daily@03:00")

def parse_schedule(schedule_str):
    # 若為 False 或 null，不排程
    if isinstance(schedule_str, bool) and not schedule_str:
        return "disabled", None, None

    if schedule_str == "hourly":
        return "hourly", None, None

    match_daily = re.match(r"^daily@(\d{2}):(\d{2})$", schedule_str)
    if match_daily:
        hour, minute = match_daily.groups()
        return "daily", None, f"{hour}:{minute}"

    match_weekly = re.match(r"^weekly@([a-zA-Z]+)@(\d{2}):(\d{2})$", schedule_str)
    if match_weekly:
        day, hour, minute = match_weekly.groups()
        return "weekly", day.lower(), f"{hour}:{minute}"

    return "daily", None, "03:00"  # fallback 預設

def schedule_backups(bot):
    schedule_str = load_schedule_config()
    schedule_type, day, time_str = parse_schedule(schedule_str)

    if schedule_type == "disabled":
        print("[排程備份] 排程功能已停用（config 設定為 false）")
        return

    def job():
        print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] [排程備份] 執行中...")
        for guild in bot.guilds:
            bot.loop.create_task(run_backup_all(bot, guild))

    if schedule_type == "hourly":
        schedule.every().hour.at(":00").do(job)
    elif schedule_type == "daily" and time_str:
        schedule.every().day.at(time_str).do(job)
    elif schedule_type == "weekly" and day and time_str:
        try:
            getattr(schedule.every(), day).at(time_str).do(job)
        except AttributeError:
            print(f"[排程備份] 錯誤：無效的星期名稱 {day}，預設為每週一。")
            schedule.every().monday.at(time_str).do(job)
    else:
        schedule.every().day.at("03:00").do(job)

    print(f"[排程備份] 啟用排程模式：{schedule_str}")

    while True:
        schedule.run_pending()
        time.sleep(60)
