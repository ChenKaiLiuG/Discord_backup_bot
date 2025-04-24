# Discord_backup_bot
## Bot structure
discord_backup_bot/  
├── bot.py                  # 主程式，啟動 Bot 並處理指令  
├── config.json             # 儲存 Token、伺服器 ID、輸出格式等  
├── backup_manager.py       # 控管備份流程的模組  
├── utils/  
│   ├── message_exporter.py     # 匯出訊息（JSON/HTML/TXT）  
│   ├── attachment_downloader.py  # 下載附件  
│   ├── structure_exporter.py    # 匯出頻道、角色、分類等設定  
│   └── formatter.py          # 控管輸出格式  
├── backups/                # 備份資料儲存資料夾  
│   └── ...  
└── scheduler.py            # 可獨立執行的排程備份腳本  
