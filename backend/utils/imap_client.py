# imap_client.py
import imaplib
import email
from email.header import decode_header
from typing import List, Dict, Optional
from datetime import datetime
import re
from email.utils import parseaddr


class ImapClient:
    def __init__(self, server: str, username: str, password: str, port: int = 993, folder: str = "INBOX"):
        self.server = server
        self.username = username
        self.password = password
        self.port = port
        self.folder = folder
        self.conn = None

    def connect(self):
        self.conn = imaplib.IMAP4_SSL(self.server, self.port)
        self.conn.login(self.username, self.password)
        self.conn.select(self.folder)

    def close(self):
        if self.conn:
            self.conn.close()
            self.conn.logout()

    def _decode_header(self, value: str) -> str:
        if value is None:
            return ""
        parts = decode_header(value)
        decoded = ""
        for part, enc in parts:
            if isinstance(part, bytes):
                decoded += part.decode(enc or "utf-8", errors="ignore")
            else:
                decoded += part
        return decoded

    def _extract_text(self, message) -> str:
        if message.is_multipart():
            for part in message.walk():
                content_type = part.get_content_type()
                if content_type == "text/plain" and not part.get("Content-Disposition"):
                    return part.get_payload(decode=True).decode(part.get_content_charset() or "utf-8", errors="ignore")
        else:
            return message.get_payload(decode=True).decode(message.get_content_charset() or "utf-8", errors="ignore")
        return ""

    def fetch_latest_emails(self, limit: int = 10) -> List[Dict]:
        self.connect()

        # 搜索全部邮件，可改为 'UNSEEN' 或按时间范围
        status, messages = self.conn.search(None, 'ALL')
        if status != "OK":
            return []

        email_ids = messages[0].split()
        latest_ids = email_ids[-limit:]

        results = []
        for uid in latest_ids:
            res, msg_data = self.conn.fetch(uid, "(RFC822)")
            if res != "OK":
                continue
            msg = email.message_from_bytes(msg_data[0][1])

            message_id = msg.get("Message-ID", "").strip()
            # sender = self._decode_header(msg.get("From"))
            raw_from = msg.get("From")
            name, addr = parseaddr(raw_from)
            sender_name = self._decode_header(name)
            sender_email = addr

            subject = self._decode_header(msg.get("Subject"))
            date_str = msg.get("Date")
            received_at = self._parse_date(date_str)
            body = self._extract_text(msg)

            # 提取邮箱地址（只保留邮箱）
            # match = re.search(r"<(.+?)>", sender)
            # sender_email = match.group(1) if match else sender

            results.append({
                "message_id": message_id,
                "sender_email": sender_email,
                "sender_name": sender_name,
                "subject": subject,
                "body": body,
                "received_at": received_at,
            })

        self.close()
        return results

    def _parse_date(self, date_str: Optional[str]) -> Optional[datetime]:
        if not date_str:
            return None
        try:
            parsed_date = email.utils.parsedate_to_datetime(date_str)
            return parsed_date
        except Exception:
            return None

