from datetime import datetime
import html

def format_timestamp(iso_string):
    dt = datetime.fromisoformat(iso_string)
    return dt.strftime("%Y-%m-%d %H:%M:%S")

def format_message_as_txt(messages):
    lines = []
    for msg in messages:
        timestamp = format_timestamp(msg["timestamp"])
        line = f"[{timestamp}] {msg['author']}: {msg['content']}"
        if msg["attachments"]:
            line += f" (附件: {', '.join(msg['attachments'])})"
        lines.append(line)
    return "\n".join(lines)

def format_message_as_html(channel_name, messages):
    html_lines = [
        f"<html><head><meta charset='UTF-8'><title>{channel_name}</title></head><body>",
        f"<h1>頻道：#{html.escape(channel_name)}</h1><ul>"
    ]
    for msg in messages:
        timestamp = format_timestamp(msg["timestamp"])
        content = html.escape(msg["content"])
        author = html.escape(msg["author"])
        attachments = ""
        if msg["attachments"]:
            attachments = "<br>".join([f"<a href='{html.escape(a)}'>{html.escape(a)}</a>" for a in msg["attachments"]])
        html_lines.append(f"<li><strong>{author}</strong> [{timestamp}]:<br>{content}<br>{attachments}</li>")
    html_lines.append("</ul></body></html>")
    return "\n".join(html_lines)
