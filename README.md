# Space Dodger

Game **asteroid shooter** sederhana berbasis **Python 3 + Pygame**. Kamu mengendalikan sebuah pesawat di bagian bawah layar, menghindari asteroid yang jatuh, dan menembaknya untuk mengumpulkan skor. Semua grafik digambar langsung dengan `pygame.draw` - **tanpa file gambar eksternal**, jadi game langsung bisa dijalankan.

## Fitur

- Pesawat pemain dengan kontrol panah / A-D dan tembakan (spasi)
- Asteroid jatuh dengan kecepatan & bentuk acak, berotasi
- 3 nyawa + waktu kebal sementara setelah terkena hit
- Skor bertambah saat asteroid hancur; **level naik setiap 500 poin**
- Power-up acak: **Perisai** (shield) dan **Tembakan Ganda** (double shot)
- Efek ledakan partikel saat asteroid hancur
- Background bintang bergerak dengan **parallax 2 lapis**
- Palet warna neon bertema gelap
- Menu utama, layar game, pause (P), dan layar Game Over (R untuk restart)
- **High score** disimpan ke `highscore.txt`
- Resolusi 800x600 @ 60 FPS

## Kontrol

| Tombol | Aksi |
| --- | --- |
| Panah kiri / kanan atau A / D | Gerakkan pesawat |
| Spasi | Tembak |
| P | Pause / lanjut |
| R | Restart (saat Game Over) |
| Esc | Kembali ke menu / keluar |
| Enter / Klik START | Mulai game dari menu |

## Cara Menjalankan

1. Pastikan **Python 3.8+** terpasang.
2. Install dependency:

   ```bash
   pip install -r requirements.txt
   ```

   atau langsung:

   ```bash
   pip install pygame
   ```

3. Jalankan game:

   ```bash
   python main.py
   ```

## Struktur Kode

Semua ada di satu file `main.py`, dipisah per kelas:

- `Star` - bintang latar (parallax)
- `Player` - pesawat pemain, nyawa, power-up
- `Bullet` - peluru
- `Asteroid` - asteroid dengan bentuk & rotasi acak
- `PowerUp` - item bonus (shield / double shot)
- `Particle` - partikel ledakan
- `Game` - state game, input, update, render, highscore

Pengaturan utama (kecepatan, warna, nyawa, dsb.) ada sebagai **konstanta di bagian atas file** agar mudah diubah.

## Ide Pengembangan

- Boss asteroid besar dengan health bar di tiap level kelipatan 5
- Efek suara (tembakan, ledakan, power-up) memakai `pygame.mixer`
- Sistem combo/multiplier skor saat menghancurkan beberapa asteroid beruntun
