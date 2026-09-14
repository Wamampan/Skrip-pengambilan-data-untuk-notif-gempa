# BMKG Gempa Monitor

Program Python sederhana untuk memantau data gempa terkini dari BMKG melalui file XML. Program mengambil data secara berkala, membandingkannya dengan data yang sudah disimpan pada pemeriksaan sebelumnya, kemudian menampilkan informasi apabila terjadi perubahan. Notifikasi perubahan dapat dikirim ke Discord menggunakan webhook.

## Fitur

- Mengambil data XML gempa dari URL BMKG.
- Memantau URL secara terus-menerus dengan interval tertentu.
- Menjalankan pemeriksaan satu kali tanpa melakukan pengulangan.
- Mendeteksi perubahan menggunakan hash SHA-256.
- Menampilkan informasi gempa, seperti:
  - tanggal dan waktu;
  - magnitude;
  - kedalaman;
  - wilayah;
  - potensi tsunami;
  - lintang dan bujur;
  - informasi gempa yang dirasakan.
- Menyimpan data XML terakhir sebagai acuan pemeriksaan berikutnya.
- Mencatat kejadian gempa baru ke file log.
- Mengirim embed notifikasi ke Discord, termasuk file XML terbaru.
- Tidak membutuhkan library Python eksternal karena menggunakan modul bawaan Python.

## Kebutuhan Sistem

- Python 3.10 atau lebih baru. Kode menggunakan sintaks union type seperti `bytes | None`.
- Koneksi internet untuk mengakses server BMKG.
- Opsional: Discord webhook jika ingin menerima notifikasi otomatis.

## Struktur Berkas

```text
.
├── bmkg_gempa_monitor.py
├── README.md
└── .bmkg_monitor_state/       # dibuat otomatis saat program berjalan
    ├── last_autogempa.xml      # data XML terakhir yang berhasil diambil
    └── gempa_log.txt           # catatan perubahan atau gempa baru
```

Direktori `.bmkg_monitor_state` dibuat di direktori kerja tempat perintah dijalankan. File `last_autogempa.xml` digunakan sebagai baseline. Pada eksekusi pertama, data hanya disimpan sebagai baseline dan tidak dianggap sebagai gempa baru.

## Sumber Data Default

Secara bawaan, program memantau URL berikut:

```text
https://data.bmkg.go.id/DataMKG/TEWS/autogempa.xml
```

URL tersebut dapat diganti menggunakan argumen `--url`.

## Cara Menjalankan

Buka PowerShell atau Command Prompt pada folder proyek, kemudian jalankan perintah berikut.

### Pemeriksaan satu kali

```powershell
python bmkg_gempa_monitor.py --once
```

Program mengambil XML satu kali, membandingkannya dengan data sebelumnya, menampilkan hasil, lalu keluar.

### Pemantauan terus-menerus

```powershell
python bmkg_gempa_monitor.py
```

Secara default, pemeriksaan dilakukan setiap 30 detik. Tekan `Ctrl+C` untuk menghentikan program.

### Mengatur interval pemeriksaan

Nilai interval menggunakan satuan detik.

```powershell
python bmkg_gempa_monitor.py --interval 60
```

Contoh tersebut memeriksa data setiap 60 detik. Interval harus berupa bilangan bulat positif.

### Menggunakan URL XML lain

```powershell
python bmkg_gempa_monitor.py --url "https://contoh.test/data.xml"
```

Format XML harus memiliki elemen utama `gempa` dengan field yang diharapkan program, misalnya `Tanggal`, `Jam`, `Magnitude`, `Kedalaman`, dan `Wilayah`.

## Konfigurasi Discord

### Menggunakan argumen `--webhook`

```powershell
python bmkg_gempa_monitor.py --webhook "https://discord.com/api/webhooks/ID/TOKEN"
```

Ketika perubahan terdeteksi, program mengirim embed ke Discord. Embed berisi rincian gempa dan melampirkan `autogempa.xml` terbaru.

### Menggunakan environment variable

Cara ini lebih baik daripada menuliskan webhook langsung di command line karena URL tidak perlu muncul di riwayat perintah.

PowerShell:

```powershell
$env:DISCORD_WEBHOOK_URL = "https://discord.com/api/webhooks/ID/TOKEN"
python bmkg_gempa_monitor.py
```

Command Prompt:

```bat
set DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/ID/TOKEN
python bmkg_gempa_monitor.py
```

Jangan membagikan URL webhook. Siapa pun yang memiliki URL tersebut dapat mengirim pesan ke channel Discord yang terkait.

## Argumen Command Line

| Argumen | Default | Keterangan |
|---|---:|---|
| `--url URL` | URL BMKG | URL XML yang dipantau. |
| `--interval DETIK` | `30` | Jeda antar pemeriksaan saat mode kontinu. |
| `--once` | tidak aktif | Melakukan satu pemeriksaan lalu keluar. |
| `--webhook URL` | nilai `DISCORD_WEBHOOK_URL` | URL Discord webhook untuk notifikasi. |
| `--notify-on-start` | tidak aktif | Opsi tersedia pada antarmuka CLI, tetapi belum mengubah perilaku program saat ini. |
| `--send-xml` | tidak aktif | Opsi tersedia pada antarmuka CLI, tetapi belum mengubah perilaku program saat ini. |

Untuk melihat bantuan langsung dari program:

```powershell
python bmkg_gempa_monitor.py --help
```

## Cara Kerja Program

1. Program membaca argumen command line dan URL sumber data.
2. Program mengambil XML menggunakan `urllib` dengan timeout 15 detik.
3. Jika belum ada file state, XML yang diambil disimpan sebagai baseline.
4. Jika sudah ada baseline, program menghitung hash SHA-256 dari data lama dan data baru.
5. Jika hash sama, program menyatakan tidak ada perubahan.
6. Jika hash berbeda, program:
   - mengekstrak informasi gempa lama dan terbaru;
   - menampilkan perbandingan di terminal;
   - menulis ringkasan ke `gempa_log.txt`;
   - mengirim notifikasi Discord jika webhook dikonfigurasi;
   - menyimpan XML terbaru sebagai baseline berikutnya.

Perubahan isi XML dianggap sebagai indikasi adanya data gempa baru. Karena program membandingkan seluruh isi XML, perubahan metadata atau format XML juga dapat memicu notifikasi.

## Penanganan Kesalahan

- Kesalahan HTTP saat mengambil data ditampilkan di terminal dan tidak menghentikan pemantauan.
- Gangguan koneksi ditampilkan sebagai kesalahan koneksi.
- XML yang tidak valid dilaporkan dan dicatat sebagai konten yang berubah tetapi gagal diparsing.
- Kesalahan pengiriman Discord ditampilkan di terminal; program tetap dapat melanjutkan pemantauan.
- `Ctrl+C` menghentikan loop secara normal.

## Contoh Penggunaan Lengkap

Pemeriksaan sekali dengan interval tidak diperlukan:

```powershell
python bmkg_gempa_monitor.py --once --webhook "https://discord.com/api/webhooks/ID/TOKEN"
```

Pemantauan setiap 2 menit dengan webhook dari environment variable:

```powershell
$env:DISCORD_WEBHOOK_URL = "https://discord.com/api/webhooks/ID/TOKEN"
python bmkg_gempa_monitor.py --interval 120
```

## Catatan Operasional

- Jangan menghapus `.bmkg_monitor_state` jika ingin mempertahankan baseline dan riwayat log.
- Jika direktori state dihapus, pemeriksaan berikutnya dianggap sebagai pengambilan data pertama.
- Pastikan interval tidak terlalu kecil agar tidak membebani server sumber data.
- Data yang ditampilkan berasal dari BMKG. Untuk informasi resmi dan tindakan keselamatan, tetap rujuk kanal resmi BMKG.

## Lisensi

Belum ada berkas lisensi yang disertakan dalam proyek ini.