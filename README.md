# Kuroyami AI Agent
Kuro adalah AI yang membantu kamu memonitor PC yang menggunakan Windows, membuka aplikasi, menulis kode, serta terintegrasi dengan ekosistem Google. Proyek ini dibangun di atas Python dengan antarmuka web berbasis Flask dan integrasi API Groq, OpenRouter, dan Google Workspace.

>[!NOTE]
> Pengembangan proyek ini sudah dihentikan.
> Proyek ini open-source, kamu bisa mengubahnya sebebas mungkin.

## 🤖 Fitur
- **Monitoring Sistem** – CPU, GPU, RAM, disk, baterai, dan uptime.
- **Kontrol Aplikasi** – Buka aplikasi, buat file, baca file, dan scan struktur proyek.
- **Integrasi Google Ecosystem** – Kelola Gmail, Google Tasks, Google Docs, Google Slides, dan YouTube langsung via Kuro.
- **Kontrol & Informasi Musik** – Tampilkan informasi dan kontrol lagu yang sedang diputar lewat Windows Media Control.
- **API Groq & OpenRouter** – Memanfaatkan AI cepat untuk respons cerdas.
- **Instalasi Simpel** - Hanya install dependensi Python dan jalankan.

## ⚙️ Konfigurasi Google Ecosystem API
Untuk mengaktifkan fitur Gmail, Google Tasks, Docs, Slides, dan YouTube, kamu perlu menyiapkan kredensial Google API terlebih dahulu:
1. Buat Google Cloud ProjectBuka Google Cloud Console.
2. Buat proyek baru (misal: Kuroyami-AI).
3. Masuk ke menu APIs & Services > Library, lalu aktifkan API berikut:Gmail APIGoogle Tasks APIGoogle Docs APIGoogle Slides APIYouTube Data API v32.
4. Atur OAuth Consent Screen & CredentialsMasuk ke APIs & Services > OAuth consent screen, pilih External, lalu isi data aplikasi dasar.
5. Tambahkan email kamu ke daftar Test Users.Masuk ke APIs & Services > Credentials > Create Credentials > OAuth client ID.
6. Pilih Application Type: Desktop App.Download file JSON kredensial yang dihasilkan, ubah namamu menjadi credentials.json, lalu letakkan di root direktori proyek ini.
7. Autentikasi Pertama KaliSaat pertama kali fungsi Google dipanggil di Kuro, browser akan otomatis terbuka untuk meminta izin akun Google kamu.
8. Setelah diizinkan, file token.json akan dibuat otomatis untuk sesi berikutnya.

## ✨ Cara Memulai
- **Sebelum dgunakan atur nama atau konfigurasi persona kamu, silakan ubah di file main.py dan isi api di .env**
- Install dependensi Python:
Bash
```
pip install -r requirements.txt
```

- Jalankan aplikasi:
Bash
```
py main.py
```

## Cara Pakai
- **Chat:** Ketik pesan di kolom chat. Kuro akan merespons.
- **Voice:** Berbicara dengan Kuro secara realtime.

## Kontribusi & Lisensi
- Dikembangkan secara mandiri oleh saya sendiri.
- Proyek ini dilisensikan di bawah MIT License, lihat file LICENSE untuk detail.
