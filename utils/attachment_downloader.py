import os
import aiohttp
import asyncio
from urllib.parse import urlparse

async def download_attachments(messages, download_folder):
    os.makedirs(download_folder, exist_ok=True)
    async with aiohttp.ClientSession() as session:
        tasks = []
        for msg in messages:
            for i, url in enumerate(msg.get("attachments", [])):
                tasks.append(download_and_save(session, url, msg["id"], i, download_folder))
        await asyncio.gather(*tasks)

async def download_and_save(session, url, msg_id, index, folder):
    parsed_url = urlparse(url)
    filename = f"{msg_id}_{index}_{os.path.basename(parsed_url.path)}"
    path = os.path.join(folder, filename)

    try:
        async with session.get(url) as resp:
            if resp.status == 200:
                with open(path, 'wb') as f:
                    f.write(await resp.read())
                print(f"成功下載：{filename}")
            else:
                print(f"下載失敗（{resp.status}）：{url}")
    except Exception as e:
        print(f"附件下載錯誤：{e}")
