# Space Dodger

Game **asteroid shooter** sederhana berbasis **Python 3 + Pygame**. Kamu mengendalikan sebuah pesawat di bagian bawah layar, menghindari asteroid yang jatuh, dan menembaknya untuk mengumpulkan skor. Semua grafik digambar langsung dengan `pygame.draw` dan **semua suara disintesis saat runtime** - **tanpa file gambar atau audio eksternal**, jadi game langsung bisa dijalankan.

---

## Cara Memainkan (Langkah demi Langkah)

Ikuti langkah ini agar game bisa langsung dimainkan oleh siapa pun:

### 1. Siapkan Python
- Pasang **Python 3.9 atau lebih baru** dari https://www.python.org/downloads/ .
- Saat instalasi di Windows, **centang "Add Python to PATH"**.
- Cek instalasi dengan membuka terminal/CMD lalu jalankan:

  ```bash
  python --version
  ```

### 2. Unduh project
- Clone repo ini, atau klik **Code -> Download ZIP** lalu ekstrak:

  ```bash
  git clone https://github.com/Iqbalarbani/Space-Dodger-game-py.git
  cd Space-Dodger-game-py
  ```

### 3. Pasang dependency (pygame)
Jalankan salah satu perintah berikut di terminal, di dalam folder project:

```bash
pip install -r requirements.txt
```

atau langsung:

```bash
pip install pygame
```

> **Catatan penting:** pada **Python 3.13 / 3.15** paket `pygame` resmi mungkin belum punya wheel siap pakai dan gagal saat instalasi. Bila itu terjadi, gunakan **pygame-ce** (menyediakan modul `pygame` yang sama persis):
>
> ```bash
> pip install pygame-ce
> ```

### 4. Jalankan game
Dari folder project, jalankan:

```bash
python main.py
```

Jika berhasil, akan terbuka jendela game berukuran **800x600** dengan latar bintang dan menu utama.

> Game harus dijalankan di **komputer/laptop lokal** (butuh jendela & speaker). Tidak akan tampil jika dijalankan di server tanpa layar.

### 5. Mulai bermain
Pada menu utama:
- Tekan **Enter** atau klik tombol **START** untuk mulai.
- Tekan **Esc** atau klik **QUIT** untuk keluar.

---

## Cara Bermain (Gameplay)

### Tujuan
Kendalikan pesawat di bagian bawah layar. Tembak asteroid yang berjatuhan untuk mendapatkan skor, dan **jangan sampai menabrak**. Kamu punya **3 nyawa**.

### Kontrol

| Aksi | Tombol |
| --- | --- |
| Mulai game (dari menu) | Enter / klik START |
| Gerak kiri / kanan | Panah kiri / kanan, atau A / D |
| Tembak | Spasi (tahan untuk tembak terus) |
| Pause / lanjut | P |
| Matikan / hidupkan suara | M |
| Restart saat Game Over | R |
| Kembali ke menu / keluar | Esc |

### Aturan & Skor
- **Menembak asteroid** memberi **+10 poin** per asteroid.
- **Menabrak asteroid** mengurangi **1 nyawa**. Setelah kena, pesawat **kebal sebentar** (berkedip).
- **Level naik setiap 500 poin** - asteroid muncul lebih cepat dan lebih cepat jatuh.
- **Power-up** muncul acak saat asteroid hancur. Ambil dengan menabraknya memakai pesawat:
  - **Kotak hijau (SHIELD)** = perisai sementara, menyerap satu tabrakan.
  - **Kotak kuning (DOUBLE)** = tembakan ganda sementara.
  - Sisa waktu efek ditampilkan di kiri layar.
- **BOSS** muncul setiap **level kelipatan 5**:
  - Didahului tulisan **WARNING / BOSS INCOMING**.
  - Punya **health bar** di atas layar; tembak terus sampai habis.
  - Saat kalah: bonus skor besar + menjatuhkan **3 power-up**.
- **Game Over** saat nyawa habis. Skor tertinggi otomatis disimpan ke `highscore.txt` dan tampil di menu.

### Tips
- Terus bergerak kiri-kanan agar tidak mudah tertabrak.
- Dahulukan asteroid yang paling dekat.
- Simpan perisai untuk saat boss muncul.
- Aktifkan tembakan ganda untuk menghabisi boss lebih cepat.

---

## Fitur

- Pesawat pemain dengan kontrol panah / A-D dan tembakan (spasi)
- Asteroid jatuh dengan kecepatan & bentuk acak, berotasi
- 3 nyawa + waktu kebal sementara setelah terkena hit
- Skor bertambah saat asteroid hancur; level naik setiap 500 poin
- Power-up acak: Perisai (shield) dan Tembakan Ganda (double shot)
- Boss asteroid setiap level kelipatan 5 (health bar, peringatan, bonus skor, drop power-up)
- Efek ledakan partikel saat asteroid / boss hancur
- Background bintang bergerak dengan parallax 2 lapis
- Palet warna neon bertema gelap
- Efek suara sintesis (tembak, ledakan, power-up, kena hit, boss)
- Musik latar loop prosedural
- Menu utama, layar game, pause (P), dan layar Game Over (R untuk restart)
- High score disimpan ke `highscore.txt`
- Resolusi 800x600 @ 60 FPS

---

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

Pengaturan utama (kecepatan, warna, nyawa, pengaturan boss, audio, dsb.) ada sebagai konstanta di bagian atas file agar mudah diubah.

---

## Troubleshooting

| Masalah | Solusi |
| --- | --- |
| `No module named 'pygame'` | Jalankan `pip install pygame` atau `pip install pygame-ce` |
| Instalasi pygame gagal saat build | Gunakan `pip install pygame-ce` (Python 3.13+) |
| Jendela tidak muncul | Jalankan di desktop lokal, bukan server tanpa layar |
| Tidak ada suara | Cek volume OS, atau tekan **M** (mungkin sedang mute) |
| `python` tidak dikenali | Pakai `py` atau `python3`; pastikan Python masuk PATH |

---

## Ide Pengembangan

- Pola serangan boss: menembakkan asteroid kecil atau laser ke arah pemain
- Sistem combo/multiplier skor saat menghancurkan beberapa asteroid beruntun
- Menu pengaturan (volume, tingkat kesulitan) dan leaderboard lokal
