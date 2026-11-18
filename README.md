# Space Dodger

Game **asteroid shooter** sederhana berbasis **Python 3 + Pygame**. Kamu mengendalikan sebuah pesawat di bagian bawah layar, menghindari asteroid yang jatuh, dan menembaknya untuk mengumpulkan skor. Semua grafik digambar langsung dengan `pygame.draw` dan **semua suara disintesis saat runtime** - **tanpa file gambar atau audio eksternal**, jadi game langsung bisa dijalankan.

## Fitur

- Pesawat pemain dengan kontrol panah / A-D dan tembakan (spasi)
- Asteroid jatuh dengan kecepatan & bentuk acak, berotasi
- 3 nyawa + waktu kebal sementara setelah terkena hit
- Skor bertambah saat asteroid hancur; **level naik setiap 500 poin**
- Power-up acak: **Perisai** (shield) dan **Tembakan Ganda** (double shot)
- **Boss asteroid** setiap level kelipatan 5:
  - Peringatan "BOSS INCOMING" sebelum muncul
  - Health bar di atas layar, HP naik tiap tier
  - Bergerak geser kiri-kanan, ledakan besar saat kalah
  - Bonus skor besar + menjatuhkan 3 power-up
- Efek ledakan partikel saat asteroid / boss hancur
- Background bintang bergerak dengan **parallax 2 lapis**
- Palet warna neon bertema gelap
- **Efek suara sintesis**: tembak, ledakan, ambil power-up, kena hit, peringatan boss, boss kena tembak
- **Musik latar** loop yang dibuat secara prosedural
- Menu utama, layar game, pause (P), dan layar Game Over (R untuk restart)
- **High score** disimpan ke `highscore.txt`
- Resolusi 800x600 @ 60 FPS

## Kontrol

| Tombol | Aksi |
| --- | --- |
| Panah kiri / kanan atau A / D | Gerakkan pesawat |
| Spasi | Tembak |
| P | Pause / lanjut |
| M | Matikan / hidupkan suara |
| R | Restart (saat Game Over) |
| Esc | Kembali ke menu / keluar |
| Enter / Klik START | Mulai game dari menu |

## Cara Menjalankan

1. Pastikan **Python 3.9+** terpasang.
2. Install dependency:

   ```bash
   pip install -r requirements.txt
   ```

   atau langsung:

   ```bash
   pip install pygame
   ```

   Catatan: pada **Python 3.13+ / 3.15**, paket `pygame` resmi mungkin belum punya wheel. Gunakan **pygame-ce** (menyediakan modul `pygame` yang sama):

   ```bash
   pip install pygame-ce
   ```

3. Jalankan game:

   ```bash
   python main.py
   ```

## Struktur Kode

Semua ada di satu file `main.py`, dipisah per kelas:

- `SoundBank` + fungsi `_build_*` - sintesis efek suara & musik (tanpa file)
- `Star` - bintang latar (parallax)
- `Player` - pesawat pemain, nyawa, power-up
- `Bullet` - peluru
- `Asteroid` - asteroid dengan bentuk & rotasi acak
- `Boss` - boss asteroid dengan health bar dan pola gerak
- `PowerUp` - item bonus (shield / double shot)
- `Particle` - partikel ledakan
- `Game` - state game, input, update, render, highscore, penjadwalan boss

Pengaturan utama (kecepatan, warna, nyawa, pengaturan boss, audio, dsb.) ada sebagai **konstanta di bagian atas file** agar mudah diubah.

## Ide Pengembangan

- Pola serangan boss: menembakkan asteroid kecil atau laser ke arah pemain
- Sistem combo/multiplier skor saat menghancurkan beberapa asteroid beruntun
- Menu pengaturan (volume, tingkat kesulitan) dan leaderboard lokal
