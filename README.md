# 🌋 BMKG Gempa Monitor

Script Python ringan untuk memantau data gempa bumi terkini dari **BMKG (Badan Meteorologi, Klimatologi, dan Geofisika)** secara real-time, dengan dukungan notifikasi otomatis ke **Discord** melalui webhook.

---

## ✨ Fitur

- 🔄 **Polling otomatis** ke endpoint XML resmi BMKG (`autogempa.xml`) dengan interval yang bisa dikustomisasi
- 🧠 **Deteksi perubahan berbasis hash (SHA-256)** — hanya memproses saat benar-benar ada data gempa baru
- 📋 **Ekstraksi otomatis** informasi penting: tanggal, jam, magnitudo, kedalaman, wilayah, potensi tsunami, area yang merasakan, serta koordinat
- 🔔 **Notifikasi Discord** via webhook, lengkap dengan rich embed berwarna (merah untuk potensi tsunami, oranye untuk lainnya)
- 📎 **Lampiran file XML mentah** otomatis dikirim bersama notifikasi Discord
- 🗂️ **Logging historis** setiap kejadian gempa baru ke file teks lokal
- ⚙️ Mode sekali-jalan (`--once`) untuk dijalankan lewat cron/scheduler, atau mode terus-menerus (daemon-like loop)
- 🔒 Mendukung penyimpanan webhook URL sebagai environment variable agar tidak tercatat di command history

---

## 📦 Requirements

- Python **3.8+**
- Tidak ada dependency pihak ketiga — hanya modul bawaan Python (`urllib`, `xml.etree.ElementTree`, `hashlib`, `argparse`, dll.)

---

## 🚀 Instalasi

```bash
git clone https://github.com/username/bmkg-gempa-monitor.git
cd bmkg-gempa-monitor
```

Tidak perlu `pip install` apa pun. Cukup pastikan Python 3 sudah terpasang.

---

## 🔧 Cara Penggunaan

### Cek sekali saja
```bash
python bmkg_gempa_monitor.py --once
```

### Pantau terus-menerus (default interval 30 detik)
```bash
python bmkg_gempa_monitor.py
```

### Interval custom & URL custom
```bash
python bmkg_gempa_monitor.py --interval 60 --url "https://data.bmkg.go.id/DataMKG/TEWS/autogempa.xml"
```

### Aktifkan notifikasi Discord
```bash
python bmkg_gempa_monitor.py --webhook "https://discord.com/api/webhooks/xxxx/yyyy"
```

Atau simpan webhook sebagai environment variable (lebih aman):
```bash
export DISCORD_WEBHOOK_URL="https://discord.com/api/webhooks/xxxx/yyyy"
python bmkg_gempa_monitor.py
```

---

## ⚙️ Argumen CLI

| Argumen | Default | Deskripsi |
|---|---|---|
| `--url` | URL BMKG resmi | URL XML gempa yang dipantau |
| `--interval` | `30` | Interval cek dalam detik |
| `--once` | `False` | Cek sekali lalu keluar (cocok untuk cron job) |
| `--webhook` | env `DISCORD_WEBHOOK_URL` | URL webhook Discord untuk notifikasi |
| `--notify-on-start` | `False` | Kirim notifikasi juga saat pengambilan data pertama kali |
| `--send-xml` | `False` | Kirim file XML mentah ke Discord setiap fetch sukses |

---

## 🗂️ Struktur Data & State

Program menyimpan state lokal di folder `.bmkg_monitor_state/`:

```
.bmkg_monitor_state/
├── last_autogempa.xml   # Snapshot XML terakhir (baseline perbandingan)
└── gempa_log.txt        # Riwayat setiap gempa baru yang terdeteksi
```

Contoh entri log:
```
[2026-09-11 15:36:44] Gempa baru: 11 Sep 2026 07:53:46 WIB M4.7 Pusat gempa berada di darat 40 km utara Donggala (Lintang 0.32 LS, Bujur 119.82 BT)
```

---

## 🛰️ Sumber Data

Data diambil dari endpoint XML publik BMKG:
```
https://data.bmkg.go.id/DataMKG/TEWS/autogempa.xml
```
Endpoint ini selalu berisi data **satu gempa terakhir** yang terjadi di Indonesia, sehingga script ini melakukan polling berkala dan membandingkan hash konten untuk mendeteksi pembaruan.

---

## 🖼️ Contoh Notifikasi Discord

Setiap notifikasi berisi:
- Judul dengan magnitudo gempa
- Deskripsi lokasi & koordinat
- Field terstruktur: Tanggal, Jam, Magnitude, Kedalaman, Potensi, Lintang, Bujur, Dirasakan
- Warna embed otomatis (🔴 merah = potensi tsunami, 🟠 oranye = tidak)
- Lampiran file XML mentah (opsional)

---

## ⚠️ Disclaimer

Proyek ini bersifat independen dan **tidak berafiliasi resmi** dengan BMKG. Selalu rujuk [situs resmi BMKG](https://www.bmkg.go.id) atau aplikasi resmi InfoBMKG untuk informasi kebencanaan yang akurat dan mendesak.

---

## 📄 Lisensi

Silakan sesuaikan dengan lisensi pilihanmu, misalnya [MIT License](https://opensource.org/licenses/MIT).

---

## 🤝 Kontribusi

Pull request dan issue sangat diterima. Untuk perubahan besar, silakan buka issue terlebih dahulu untuk mendiskusikan apa yang ingin diubah.
