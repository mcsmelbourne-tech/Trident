"""Turns a TradingView alert (delivered by repository_dispatch) into a Telegram message.

Env: TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, ALERT_PAYLOAD (json), MANUAL_MESSAGE (optional test text)
     DRY_RUN=1 prints the message instead of sending it.
"""
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request


def build_message(payload, manual):
    if not isinstance(payload, dict) or not payload:
        return (manual or "").strip() or "TradingView alert (empty payload)"
    ticker = str(payload.get("ticker", "")).strip()
    interval = str(payload.get("interval", "")).strip()
    price = str(payload.get("price", "")).strip()
    action = str(payload.get("action", "")).strip().upper()
    note = str(payload.get("message", "")).strip()
    when = str(payload.get("time", "")).strip()

    icon = {"BUY": "🟢", "SELL": "🔴"}.get(action, "🔔")
    head = " ".join(x for x in (icon, action, ticker, f"({interval})" if interval else "") if x)
    lines = [head or f"{icon} TradingView alert"]
    if price:
        lines.append(f"Price: {price}")
    if note and note != head:
        lines.append(note)
    if when:
        lines.append(f"Time: {when}")
    return "\n".join(lines)


def send(token, chat_id, text):
    # Telegram limit is 4096 characters per message
    for i in range(0, len(text), 4000):
        data = urllib.parse.urlencode(
            {"chat_id": chat_id, "text": text[i:i + 4000], "disable_web_page_preview": "true"}
        ).encode()
        req = urllib.request.Request(f"https://api.telegram.org/bot{token}/sendMessage", data=data)
        try:
            with urllib.request.urlopen(req, timeout=20) as resp:
                resp.read()
        except urllib.error.HTTPError as e:
            sys.exit(f"Telegram error {e.code}: {e.read().decode(errors='replace')}")


def main():
    try:
        payload = json.loads(os.environ.get("ALERT_PAYLOAD") or "null")
    except json.JSONDecodeError:
        payload = None
    text = build_message(payload, os.environ.get("MANUAL_MESSAGE"))

    if os.environ.get("DRY_RUN"):
        print(text)
        return
    token, chat = os.environ.get("TELEGRAM_BOT_TOKEN"), os.environ.get("TELEGRAM_CHAT_ID")
    if not token or not chat:
        sys.exit("Missing TELEGRAM_BOT_TOKEN / TELEGRAM_CHAT_ID repository secrets.")
    send(token, chat, text)
    print("Sent.")


if __name__ == "__main__":
    main()

