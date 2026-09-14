#!/usr/bin/env python3
"""
Monitor XML Gempa BMKG
=======================
Memantau URL XML gempa terkini dari BMKG dan mendeteksi perubahan
(artinya: ada data gempa baru).

URL default:
    https://data.bmkg.go.id/DataMKG/TEWS/autogempa.xml

Cara pakai:
    # Cek sekali saja
    python bmkg_gempa_monitor.py --once

    # Pantau terus-menerus, cek tiap 60 detik (default)
    python bmkg_gempa_monitor.py

    # Pantau dengan interval custom (detik) & url custom
    python bmkg_gempa_monitor.py --interval 30 --url "https://data.bmkg.go.id/DataMKG/TEWS/autogempa.xml"

    # Kirim notifikasi ke Discord saat ada gempa baru
    python bmkg_gempa_monitor.py --webhook "https://discord.com/api/webhooks/xxxx/yyyy"

    # Bisa juga simpan webhook URL sebagai environment variable, supaya
    # tidak perlu diketik tiap kali / tidak tersimpan di history terminal:
    #   export DISCORD_WEBHOOK_URL="https://discord.com/api/webhooks/xxxx/yyyy"
    #   python bmkg_gempa_monitor.py

Tidak butuh dependency eksternal (pakai urllib bawaan Python).
"""

import argparse
import hashlib
import json
import os
import sys
import time
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from urllib.request import urlopen, Request
from urllib.error import URLError, HTTPError

DEFAULT_URL = "https://data.bmkg.go.id/DataMKG/TEWS/autogempa.xml"
STATE_DIR = ".bmkg_monitor_state"
STATE_FILE = os.path.join(STATE_DIR, "last_autogempa.xml")
LOG_FILE = os.path.join(STATE_DIR, "gempa_log.txt")


# ---------------------------------------------------------------------
# Ambil data dari URL
# ---------------------------------------------------------------------
def fetch_xml(url: str, timeout: int = 15) -> bytes:
    """Mengambil konten XML dari URL. Melempar exception jika gagal."""
    req = Request(url, headers={"User-Agent": "xml-change-monitor/1.0"})
    with urlopen(req, timeout=timeout) as resp:
        return resp.read()


# ---------------------------------------------------------------------
# Ekstraksi info gempa yang ramah-manusia
# ---------------------------------------------------------------------
def extract_gempa_info(xml_content: bytes) -> dict:
    """
    Struktur autogempa.xml BMKG kurang lebih:
    <Infogempa>
        <gempa>
            <Tanggal>...</Tanggal>
            <Jam>...</Jam>
            <Magnitude>...</Magnitude>
            <Kedalaman>...</Kedalaman>
            <Wilayah>...</Wilayah>
            <Potensi>...</Potensi>
            ...
        </gempa>
    </Infogempa>
    """
    root = ET.fromstring(xml_content)
    gempa = root.find("gempa")
    if gempa is None:
        return {}

    fields = ["Tanggal", "Jam", "DateTime", "Magnitude", "Kedalaman",
              "Wilayah", "Potensi", "Dirasakan", "Lintang", "Bujur"]
    info = {}
    for field in fields:
        el = gempa.find(field)
        if el is not None and el.text:
            info[field] = el.text.strip()
    return info


def print_gempa_info(info: dict):
    if not info:
        print("Tidak bisa mengekstrak info gempa (format XML tidak sesuai dugaan).")
        return
    print("  Data gempa terkini:")
    for key in ["Tanggal", "Jam", "Magnitude", "Kedalaman", "Wilayah", "Potensi",
                "Lintang", "Bujur", "Dirasakan"]:
        if key in info:
            print(f"    {key:12s}: {info[key]}")


# ---------------------------------------------------------------------
# Notifikasi Discord
# ---------------------------------------------------------------------
def send_discord_notification(webhook_url: str, info: dict, source_url: str,
                              xml_content: bytes | None = None,
                              status_text: str | None = None):
    """
    Mengirim notifikasi embed ke Discord lewat webhook.
    Jika xml_content disediakan, kirim juga file XML sebagai attachment.
    Tidak butuh library requests, cukup urllib bawaan Python.
    """
    magnitude = info.get("Magnitude", "?")
    wilayah = info.get("Wilayah", "?")
    tanggal = info.get("Tanggal", "?")
    jam = info.get("Jam", "?")
    kedalaman = info.get("Kedalaman", "?")
    potensi = info.get("Potensi", "?")
    dirasakan = info.get("Dirasakan", "-")
    lintang = info.get("Lintang", "-")
    bujur = info.get("Bujur", "-")

    # warna embed merah kalau berpotensi tsunami, kalau tidak kuning/oranye
    is_tsunami = "tidak" not in potensi.lower()
    color = 0xE74C3C if is_tsunami else 0xF39C12

    title = f"\U0001F6A8 Info Gempa Terkini - M{magnitude}"
    description = f"**{wilayah}**"
    if lintang != "-" and bujur != "-":
        description = f"{description}\n📍 Lintang: {lintang} | Bujur: {bujur}"
    if status_text:
        title = f"\U0001F6A8 {status_text}"
        description = f"{description}\n{status_text}"

    payload = {
        "username": "BMKG Gempa Monitor",
        "embeds": [
            {
                "title": title,
                "description": description,
                "color": color,
                "fields": [
                    {"name": "Tanggal", "value": tanggal, "inline": True},
                    {"name": "Jam", "value": jam, "inline": True},
                    {"name": "Magnitude", "value": magnitude, "inline": True},
                    {"name": "Kedalaman", "value": kedalaman, "inline": True},
                    {"name": "Potensi", "value": potensi, "inline": True},
                    {"name": "Lintang", "value": lintang, "inline": True},
                    {"name": "Bujur", "value": bujur, "inline": True},
                    {"name": "Dirasakan", "value": dirasakan, "inline": True},
                ],
                "footer": {"text": "Sumber: BMKG - data.bmkg.go.id"},
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        ],
    }

    if xml_content is not None:
        boundary = "----WebKitFormBoundary" + hashlib.md5(str(time.time()).encode()).hexdigest()[:16]
        payload_json = json.dumps(payload).encode("utf-8")
        parts = []
        parts.append(f"--{boundary}".encode("utf-8"))
        parts.append(b'Content-Disposition: form-data; name="payload_json"')
        parts.append(b"")
        parts.append(payload_json)
        parts.append(f"--{boundary}".encode("utf-8"))
        parts.append(b'Content-Disposition: form-data; name="file"; filename="autogempa.xml"')
        parts.append(b"Content-Type: application/xml")
        parts.append(b"")
        parts.append(xml_content)
        parts.append(f"--{boundary}--".encode("utf-8"))
        parts.append(b"")
        data = b"\r\n".join(parts)
        content_type = f"multipart/form-data; boundary={boundary}"
    else:
        data = json.dumps(payload).encode("utf-8")
        content_type = "application/json"

    req = Request(
        webhook_url,
        data=data,
        headers={
            "Content-Type": content_type,
            "User-Agent": "xml-change-monitor/1.0",
        },
        method="POST",
    )

    try:
        with urlopen(req, timeout=15) as resp:
            # Discord webhook sukses biasanya balas 204 No Content
            if resp.status not in (200, 204):
                print(f"  [Discord] Respons tidak terduga: HTTP {resp.status}")
            else:
                print("  [Discord] Notifikasi terkirim.")
    except HTTPError as e:
        body = e.read().decode("utf-8", errors="ignore")
        print(f"  [Discord] Gagal kirim notifikasi (HTTP {e.code}): {body}")
    except URLError as e:
        print(f"  [Discord] Gagal kirim notifikasi (koneksi bermasalah: {e.reason}).")
    except Exception as e:
        print(f"  [Discord] Gagal kirim notifikasi: {e}")


# ---------------------------------------------------------------------
# Penanganan state (menyimpan versi terakhir yang berhasil diambil)
# ---------------------------------------------------------------------
def load_previous_content() -> bytes | None:
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "rb") as f:
            return f.read()
    return None


def save_current_content(content: bytes):
    os.makedirs(STATE_DIR, exist_ok=True)
    with open(STATE_FILE, "wb") as f:
        f.write(content)


def log_event(message: str):
    os.makedirs(STATE_DIR, exist_ok=True)
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"[{timestamp}] {message}\n")


def content_hash(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


# ---------------------------------------------------------------------
# Satu siklus cek
# ---------------------------------------------------------------------
def check_once(url: str, verbose: bool = True, webhook_url: str | None = None,
                notify_on_start: bool = False, send_xml: bool = False) -> bool:
    """
    Mengambil XML dari url, membandingkan dengan versi sebelumnya.
    Return True jika terjadi perubahan (data gempa baru).
    """
    timestamp = datetime.now().strftime("%H:%M:%S")

    try:
        current = fetch_xml(url)
    except HTTPError as e:
        print(f"[{timestamp}] Gagal mengambil data (HTTP {e.code}).")
        return False
    except URLError as e:
        print(f"[{timestamp}] Gagal mengambil data (koneksi bermasalah: {e.reason}).")
        return False
    except Exception as e:
        print(f"[{timestamp}] Gagal mengambil data: {e}")
        return False

    previous = load_previous_content()

    if previous is None:
        # pertama kali berjalan -> ini bukan "perubahan", cuma baseline awal
        print(f"[{timestamp}] Pengambilan data pertama kali. Menyimpan sebagai acuan awal.")
        save_current_content(current)
        return False

    if content_hash(previous) == content_hash(current):
        if verbose:
            print(f"[{timestamp}] Tidak ada perubahan.")
        return False

    # ada perubahan -> data gempa baru terdeteksi
    print(f"[{timestamp}] PERUBAHAN TERDETEKSI - kemungkinan ada gempa baru!")
    try:
        old_info = extract_gempa_info(previous)
        new_info = extract_gempa_info(current)

        print("  Sebelumnya:")
        if old_info.get("Tanggal"):
            print(f"    {old_info.get('Tanggal')} {old_info.get('Jam','')} - "
                  f"M{old_info.get('Magnitude','?')} - {old_info.get('Wilayah','?')}")
        print("  Sekarang:")
        print_gempa_info(new_info)

        log_line = (f"Gempa baru: {new_info.get('Tanggal','?')} {new_info.get('Jam','?')} "
                    f"M{new_info.get('Magnitude','?')} {new_info.get('Wilayah','?')} "
                    f"(Lintang {new_info.get('Lintang','?')}, Bujur {new_info.get('Bujur','?')})")
        log_event(log_line)

        if webhook_url and new_info:
            send_discord_notification(webhook_url, new_info, url, xml_content=current)
    except ET.ParseError:
        print("  XML tidak valid / gagal diparsing, tapi konten berubah dari sebelumnya.")
        log_event("Konten berubah, tapi gagal parsing XML.")

    save_current_content(current)
    return True


# ---------------------------------------------------------------------
# UTAMA (mengatur bagaimana program dijalankan dari command line)
# ---------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(description="Monitor perubahan XML gempa BMKG")
    parser.add_argument("--url", default=DEFAULT_URL, help="URL XML yang dipantau")
    parser.add_argument("--interval", type=int, default=30,
                         help="Interval cek dalam detik (default: 30)")
    parser.add_argument("--once", action="store_true",
                         help="Cek sekali saja lalu keluar (tidak looping)")
    parser.add_argument("--webhook", default=os.environ.get("DISCORD_WEBHOOK_URL"),
                         help="URL Discord webhook untuk notifikasi. "
                              "Bisa juga diisi lewat env var DISCORD_WEBHOOK_URL")
    parser.add_argument("--notify-on-start", action="store_true",
                         help="Kirim notifikasi Discord juga untuk pengambilan data pertama kali "
                              "(default: hanya kirim saat ada PERUBAHAN)")
    parser.add_argument("--send-xml", action="store_true",
                         help="Kirim file XML ke Discord setiap kali fetch sukses, meski data tidak berubah")
    args = parser.parse_args()

    if args.webhook:
        print("Notifikasi Discord: AKTIF")
    else:
        print("Notifikasi Discord: tidak diaktifkan (gunakan --webhook atau env DISCORD_WEBHOOK_URL)")

    if args.once:
        check_once(args.url, webhook_url=args.webhook,
                   notify_on_start=args.notify_on_start,
                   send_xml=args.send_xml)
        return

    print(f"Memantau: {args.url}")
    print(f"Interval: {args.interval} detik")
    print("Tekan Ctrl+C untuk berhenti.\n")

    try:
        while True:
            check_once(args.url, webhook_url=args.webhook,
                       notify_on_start=args.notify_on_start,
                       send_xml=args.send_xml)
            time.sleep(args.interval)
    except KeyboardInterrupt:
        print("\nDihentikan oleh user.")
        sys.exit(0)


if __name__ == "__main__":
    main()
    