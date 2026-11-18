'''
Space Dodger - asteroid shooter bertema neon dengan Pygame.

Kontrol:
    Panah kiri/kanan atau A/D : gerakkan pesawat
    Spasi                     : tembak
    P                         : pause / lanjut
    M                         : matikan / hidupkan suara
    R                         : restart (saat game over)
    Esc                       : kembali ke menu / keluar

Jalankan dengan: python main.py
'''

import array
import math
import os
import random

import pygame

# ============================================================
# KONSTANTA PENGATURAN
# ============================================================
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
FPS = 60
TITLE = 'Space Dodger'

# Audio (sintesis, tanpa file eksternal)
SAMPLE_RATE = 22050
SOUND_VOLUME = 0.35
MUSIC_VOLUME = 0.16

# Palet warna bertema neon / gelap
BLACK = (10, 10, 25)
DARK_BLUE = (18, 18, 45)
NEON_CYAN = (0, 255, 255)
NEON_MAGENTA = (255, 60, 200)
NEON_GREEN = (60, 255, 140)
NEON_YELLOW = (255, 230, 90)
NEON_ORANGE = (255, 140, 40)
NEON_RED = (255, 70, 90)
WHITE = (235, 240, 255)
GREY = (90, 90, 130)

# Pemain
PLAYER_SPEED = 6
PLAYER_LIVES = 3
PLAYER_SIZE = 28
SHOOT_COOLDOWN = 220
INVULNERABLE_TIME = 1500

# Peluru
BULLET_SPEED = 9
BULLET_RADIUS = 3
BULLET_SCORE = 10

# Asteroid
ASTEROID_MIN_SPEED = 1.5
ASTEROID_MAX_SPEED = 3.2
ASTEROID_SPEED_PER_LEVEL = 0.18
ASTEROID_MIN_RADIUS = 14
ASTEROID_MAX_RADIUS = 30

# Power-up
POWERUP_DROP_CHANCE = 0.15
POWERUP_DURATION = 6000
POWERUP_FALL_SPEED = 2.2
POWERUP_RADIUS = 14

# Partikel ledakan
PARTICLE_LIFETIME = 550

# Kesulitan
DIFFICULTY_STEP = 500
SPAWN_INTERVAL_START = 950
SPAWN_INTERVAL_MIN = 260
SPAWN_INTERVAL_STEP = 65

# Boss
BOSS_LEVEL_STEP = 5
BOSS_BASE_HP = 12
BOSS_HP_PER_TIER = 6
BOSS_RADIUS = 55
BOSS_ENTER_SPEED = 1.2
BOSS_DRIFT_SPEED = 1.8
BOSS_SCORE_MULTIPLIER = 30
BOSS_WARNING_TIME = 1500
BOSS_DROP_POWERUPS = 3

HISCORE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'highscore.txt')

# ============================================================
# SINTESIS SUARA (tanpa file audio eksternal)
# ============================================================
def _build_samples(duration, generator):
    '''Bangun buffer mono 16-bit dari fungsi generator(t) -> amplitudo (-1..1).'''
    total = int(SAMPLE_RATE * duration)
    data = array.array('h')
    for i in range(total):
        t = i / SAMPLE_RATE
        value = generator(t, duration)
        value = max(-1.0, min(1.0, value))
        data.append(int(value * 32767))
    return data


def _make_sound(data):
    '''Ubah array sampel menjadi pygame Sound mono 16-bit.'''
    return pygame.mixer.Sound(buffer=data.tobytes())


def _shoot_gen(t, dur):
    # nada kotak menurun cepat, seperti laser
    freq = 900 - 600 * (t / dur)
    phase = 2 * math.pi * freq * t
    env = 1.0 - (t / dur)
    square = 1.0 if math.sin(phase) >= 0 else -1.0
    return square * env * 0.5


def _explosion_gen(t, dur):
    # noise meluruh, seperti ledakan
    env = (1.0 - (t / dur)) ** 2
    return (random.uniform(-1.0, 1.0)) * env * 0.8


def _powerup_gen(t, dur):
    # nada naik bersih, seperti mengambil bonus
    freq = 500 + 700 * (t / dur)
    env = (1.0 - (t / dur)) ** 0.6
    return math.sin(2 * math.pi * freq * t) * env * 0.6


def _hit_gen(t, dur):
    # dentuman rendah
    freq = 180 - 120 * (t / dur)
    env = (1.0 - (t / dur)) ** 2
    return math.sin(2 * math.pi * freq * t) * env * 0.9


def _boss_warn_gen(t, dur):
    # pulsa rendah menandakan boss datang
    pulse = math.sin(2 * math.pi * 140 * t)
    gate = 0.5 + 0.5 * math.sin(2 * math.pi * 6 * t)
    return pulse * gate * 0.7


def _boss_hit_gen(t, dur):
    # ledakan logam singkat
    env = (1.0 - (t / dur)) ** 1.5
    tone = math.sin(2 * math.pi * 240 * t)
    noise = random.uniform(-1.0, 1.0)
    return (tone * 0.5 + noise * 0.5) * env * 0.7


def _build_music():
    '''Loop musik latar sederhana: arpeggio pad + bass lembut.'''
    duration = 8.0
    total = int(SAMPLE_RATE * duration)
    data = array.array('h')

    # tangga nada minor A agar terasa gelap tapi megah
    notes = [220.0, 261.63, 293.66, 329.63, 392.0, 329.63, 293.66, 261.63]
    note_len = duration / len(notes)

    for i in range(total):
        t = i / SAMPLE_RATE
        idx = int(t / note_len) % len(notes)
        freq = notes[idx]
        local = (t % note_len) / note_len
        pad_env = math.sin(math.pi * local) ** 1.5
        pad = (math.sin(2 * math.pi * freq * t)
               + 0.4 * math.sin(2 * math.pi * freq * 2 * t)) * 0.5
        bass_freq = notes[0] / 2
        bass = math.sin(2 * math.pi * bass_freq * t) * 0.35
        sample = (pad * pad_env + bass) * 0.35
        sample = max(-1.0, min(1.0, sample))
        data.append(int(sample * 32767))

    return _make_sound(data)


class SoundBank:
    '''Kumpulan efek suara + musik latar, dibuat saat pertama dipakai.'''

    def __init__(self):
        self.enabled = True
        self.sounds = {}
        self.music = None
        try:
            self.sounds['shoot'] = _make_sound(_build_samples(0.09, _shoot_gen))
            self.sounds['explosion'] = _make_sound(_build_samples(0.30, _explosion_gen))
            self.sounds['powerup'] = _make_sound(_build_samples(0.22, _powerup_gen))
            self.sounds['hit'] = _make_sound(_build_samples(0.28, _hit_gen))
            self.sounds['boss_warn'] = _make_sound(_build_samples(0.55, _boss_warn_gen))
            self.sounds['boss_hit'] = _make_sound(_build_samples(0.16, _boss_hit_gen))
            self.music = _build_music()
            for snd in self.sounds.values():
                snd.set_volume(SOUND_VOLUME)
            self.music.set_volume(MUSIC_VOLUME)
        except pygame.error:
            # audio device tidak tersedia: game tetap jalan tanpa suara
            self.sounds = {}
            self.music = None
            self.enabled = False

    def play(self, name):
        if self.enabled and name in self.sounds:
            self.sounds[name].play()

    def start_music(self):
        if self.enabled and self.music:
            self.music.play(loops=-1, fade_ms=800)

    def stop_music(self):
        if self.music:
            self.music.fadeout(600)

    def toggle(self):
        '''Hidup/matikan suara; kembalikan status baru.'''
        self.enabled = not self.enabled
        if not self.enabled:
            self.stop_music()
        else:
            self.start_music()
        return self.enabled


class Star:
    '''Bintang latar dengan dua lapisan (parallax).'''

    def __init__(self, layer):
        self.layer = layer
        self.reset(initial=True)

    def reset(self, initial=False):
        self.x = random.uniform(0, SCREEN_WIDTH)
        if initial:
            self.y = random.uniform(0, SCREEN_HEIGHT)
        else:
            self.y = random.uniform(-40, 0)

        if self.layer == 0:
            self.speed = random.uniform(0.3, 0.8)
            self.size = 1
            self.color = GREY
        else:
            self.speed = random.uniform(1.1, 2.4)
            self.size = 2
            self.color = WHITE

    def update(self):
        self.y += self.speed
        if self.y > SCREEN_HEIGHT + 2:
            self.reset()

    def draw(self, surface):
        pygame.draw.circle(surface, self.color, (int(self.x), int(self.y)), self.size)


class Player:
    '''Pesawat yang dikendalikan pemain.'''

    def __init__(self, x, y):
        self.x = float(x)
        self.y = float(y)
        self.size = PLAYER_SIZE
        self.speed = PLAYER_SPEED
        self.lives = PLAYER_LIVES
        self.shield_until = 0
        self.double_until = 0
        self.invulnerable_until = 0
        self.last_shot = 0

    def has_shield(self):
        return pygame.time.get_ticks() < self.shield_until

    def has_double(self):
        return pygame.time.get_ticks() < self.double_until

    def is_invulnerable(self):
        return pygame.time.get_ticks() < self.invulnerable_until

    def move(self, keys):
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            self.x -= self.speed
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            self.x += self.speed
        half = self.size // 2
        self.x = max(half, min(SCREEN_WIDTH - half, self.x))

    def shoot(self):
        '''Kembalikan daftar peluru baru (kosong bila masih cooldown).'''
        now = pygame.time.get_ticks()
        if now - self.last_shot < SHOOT_COOLDOWN:
            return []
        self.last_shot = now
        nose_y = self.y - self.size // 2
        if self.has_double():
            return [Bullet(self.x - 8, nose_y), Bullet(self.x + 8, nose_y)]
        return [Bullet(self.x, nose_y)]

    def hit(self):
        self.lives -= 1
        self.invulnerable_until = pygame.time.get_ticks() + INVULNERABLE_TIME

    def draw(self, surface):
        if self.is_invulnerable() and (pygame.time.get_ticks() // 100) % 2 == 0:
            return

        cx, cy = int(self.x), int(self.y)
        s = self.size // 2

        flame = random.randint(5, 11)
        pygame.draw.polygon(surface, NEON_ORANGE, [
            (cx - s // 2, cy + s // 2),
            (cx + s // 2, cy + s // 2),
            (cx, cy + s // 2 + flame),
        ])

        body = [
            (cx, cy - s),
            (cx - s, cy + s),
            (cx, cy + s // 3),
            (cx + s, cy + s),
        ]
        pygame.draw.polygon(surface, NEON_CYAN, body)
        pygame.draw.polygon(surface, WHITE, body, 1)
        pygame.draw.circle(surface, WHITE, (cx, cy - s // 3), 3)

        if self.has_shield():
            pygame.draw.circle(surface, NEON_GREEN, (cx, cy), s + 9, 2)


class Bullet:
    '''Peluru pemain yang bergerak lurus ke atas.'''

    def __init__(self, x, y):
        self.x = float(x)
        self.y = float(y)
        self.radius = BULLET_RADIUS
        self.speed = BULLET_SPEED

    def update(self):
        self.y -= self.speed

    def offscreen(self):
        return self.y < -12

    def draw(self, surface):
        pos = (int(self.x), int(self.y))
        pygame.draw.circle(surface, NEON_YELLOW, pos, self.radius)
        pygame.draw.circle(surface, WHITE, pos, self.radius, 1)
        pygame.draw.line(surface, NEON_YELLOW,
                         (int(self.x), int(self.y) + 8),
                         (int(self.x), int(self.y) + 16), 1)



class Asteroid:
    '''Asteroid yang jatuh dari atas layar.'''

    COLORS = (NEON_MAGENTA, NEON_ORANGE, NEON_RED)

    def __init__(self, level=1):
        self.radius = random.randint(ASTEROID_MIN_RADIUS, ASTEROID_MAX_RADIUS)
        self.x = float(random.randint(self.radius, SCREEN_WIDTH - self.radius))
        self.y = float(-self.radius)

        base_speed = random.uniform(ASTEROID_MIN_SPEED, ASTEROID_MAX_SPEED)
        self.speed = base_speed + (level - 1) * ASTEROID_SPEED_PER_LEVEL

        self.rotation = random.uniform(0, 360)
        self.rotation_speed = random.uniform(-80, 80)
        self.color = random.choice(Asteroid.COLORS)

        self.shape = []
        sides = random.randint(8, 11)
        for i in range(sides):
            angle = math.tau * i / sides
            r = self.radius * random.uniform(0.72, 1.08)
            self.shape.append((math.cos(angle) * r, math.sin(angle) * r))

    def update(self, dt):
        self.y += self.speed
        self.rotation += self.rotation_speed * (dt / 1000.0)

    def offscreen(self):
        return self.y - self.radius > SCREEN_HEIGHT

    def _rotated(self, scale=1.0):
        rad = math.radians(self.rotation)
        cos_r, sin_r = math.cos(rad), math.sin(rad)
        pts = []
        for px, py in self.shape:
            rx = px * cos_r - py * sin_r
            ry = px * sin_r + py * cos_r
            pts.append((int(self.x + rx * scale), int(self.y + ry * scale)))
        return pts

    def draw(self, surface):
        pts = self._rotated()
        pygame.draw.polygon(surface, DARK_BLUE, pts)
        pygame.draw.polygon(surface, self.color, pts, 2)


class Boss:
    '''Asteroid raksasa dengan health bar; muncul tiap kelipatan BOSS_LEVEL_STEP level.'''

    def __init__(self, tier):
        self.tier = tier
        self.max_hp = BOSS_BASE_HP + (tier - 1) * BOSS_HP_PER_TIER
        self.hp = self.max_hp
        self.radius = BOSS_RADIUS + min(20, (tier - 1) * 3)

        self.x = float(SCREEN_WIDTH // 2)
        self.y = float(-self.radius - 10)
        self.direction = random.choice((-1, 1))

        self.rotation = 0.0
        self.rotation_speed = 22  # derajat per detik
        self.color = NEON_RED
        self.entering = True
        self.hit_flash = 0

        # bentuk poligon kasar ala asteroid
        self.shape = []
        sides = 12
        for i in range(sides):
            angle = math.tau * i / sides
            r = self.radius * random.uniform(0.82, 1.05)
            self.shape.append((math.cos(angle) * r, math.sin(angle) * r))

    def update(self, dt):
        self.rotation += self.rotation_speed * (dt / 1000.0)
        if self.hit_flash > 0:
            self.hit_flash = max(0, self.hit_flash - dt)

        if self.entering:
            # turun perlahan sampai posisi tempur
            self.y += BOSS_ENTER_SPEED
            if self.y >= self.radius + 70:
                self.entering = False
        else:
            # geser kiri-kanan sambil turun pelan
            self.x += self.direction * BOSS_DRIFT_SPEED
            self.y += 0.15
            if self.x < self.radius:
                self.x = float(self.radius)
                self.direction = 1
            elif self.x > SCREEN_WIDTH - self.radius:
                self.x = float(SCREEN_WIDTH - self.radius)
                self.direction = -1

    def take_hit(self):
        self.hp -= 1
        self.hit_flash = 120
        return self.hp <= 0

    def points(self):
        rad = math.radians(self.rotation)
        cos_r, sin_r = math.cos(rad), math.sin(rad)
        pts = []
        for px, py in self.shape:
            rx = px * cos_r - py * sin_r
            ry = px * sin_r + py * cos_r
            pts.append((int(self.x + rx), int(self.y + ry)))
        return pts

    def draw(self, surface):
        pts = self.points()
        fill = NEON_ORANGE if self.hit_flash > 0 else DARK_BLUE
        pygame.draw.polygon(surface, fill, pts)
        pygame.draw.polygon(surface, self.color, pts, 3)

        # inti bercahaya di tengah
        core = NEON_YELLOW if self.hit_flash > 0 else NEON_MAGENTA
        pygame.draw.circle(surface, core, (int(self.x), int(self.y)),
                           max(6, self.radius // 4), 2)

        self.draw_health_bar(surface)

    def draw_health_bar(self, surface):
        if self.entering:
            return
        width = 260
        height = 12
        x = SCREEN_WIDTH // 2 - width // 2
        y = 24
        ratio = max(0.0, self.hp / self.max_hp)

        pygame.draw.rect(surface, DARK_BLUE, pygame.Rect(x, y, width, height),
                         border_radius=4)
        pygame.draw.rect(surface, NEON_RED,
                         pygame.Rect(x, y, int(width * ratio), height),
                         border_radius=4)
        pygame.draw.rect(surface, WHITE, pygame.Rect(x, y, width, height), 1,
                         border_radius=4)


class PowerUp:
    '''Item bonus: perisai sementara atau tembakan ganda.'''

    SHIELD = 'shield'
    DOUBLE = 'double'

    def __init__(self, x, y, kind):
        self.x = float(x)
        self.y = float(y)
        self.kind = kind
        self.radius = POWERUP_RADIUS
        self.speed = POWERUP_FALL_SPEED
        self.pulse = 0.0

    def update(self, dt):
        self.y += self.speed
        self.pulse = (self.pulse + dt / 1000.0 * 6) % math.tau

    def offscreen(self):
        return self.y - self.radius > SCREEN_HEIGHT

    def draw(self, surface):
        cx, cy = int(self.x), int(self.y)
        color = NEON_GREEN if self.kind == PowerUp.SHIELD else NEON_YELLOW

        pulse_radius = self.radius + int(2 * math.sin(self.pulse))
        pygame.draw.circle(surface, color, (cx, cy), pulse_radius, 1)
        pygame.draw.rect(surface, color,
                         pygame.Rect(cx - self.radius, cy - self.radius,
                                     self.radius * 2, self.radius * 2), 2,
                         border_radius=4)

        if self.kind == PowerUp.SHIELD:
            shield = [
                (cx, cy - 7), (cx - 6, cy - 3), (cx - 6, cy + 3),
                (cx, cy + 7), (cx + 6, cy + 3), (cx + 6, cy - 3),
            ]
            pygame.draw.polygon(surface, color, shield, 2)
        else:
            pygame.draw.line(surface, color, (cx - 4, cy + 6), (cx - 4, cy - 6), 3)
            pygame.draw.line(surface, color, (cx + 4, cy + 6), (cx + 4, cy - 6), 3)


class Particle:
    '''Pecahan kecil untuk efek ledakan.'''

    def __init__(self, x, y, color, spread=1.0):
        self.x = float(x)
        self.y = float(y)
        speed = random.uniform(1.0, 4.5) * spread
        angle = random.uniform(0, math.tau)
        self.vx = math.cos(angle) * speed
        self.vy = math.sin(angle) * speed
        self.color = color
        self.life = PARTICLE_LIFETIME
        self.max_life = PARTICLE_LIFETIME
        self.radius = random.randint(1, 3)

    def update(self, dt):
        self.x += self.vx
        self.y += self.vy
        self.vx *= 0.97
        self.vy *= 0.97
        self.life -= dt

    def dead(self):
        return self.life <= 0

    def draw(self, surface):
        ratio = max(0.0, self.life / self.max_life)
        r = max(1, int(self.radius * ratio + 0.5))
        pygame.draw.circle(surface, self.color, (int(self.x), int(self.y)), r)



class Game:
    '''Pengelola state, input, update, dan render.'''

    MENU = 'menu'
    PLAYING = 'playing'
    PAUSED = 'paused'
    GAME_OVER = 'gameover'

    def __init__(self):
        pygame.init()
        try:
            # mono 16-bit agar cocok dengan buffer hasil sintesis
            pygame.mixer.init(frequency=SAMPLE_RATE, size=-16, channels=1, buffer=512)
        except pygame.error:
            pass

        pygame.display.set_caption(TITLE)
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        self.clock = pygame.time.Clock()

        self.font_big = pygame.font.SysFont('consolas', 56, bold=True)
        self.font_mid = pygame.font.SysFont('consolas', 28, bold=True)
        self.font_small = pygame.font.SysFont('consolas', 20)

        self.stars = [Star(0) for _ in range(70)] + [Star(1) for _ in range(35)]

        self.running = True
        self.state = Game.MENU
        self.highscore = self.load_highscore()
        self.sound = SoundBank()

        self.player = None
        self.asteroids = []
        self.bullets = []
        self.powerups = []
        self.particles = []
        self.boss = None
        self.boss_pending_tier = 0
        self.boss_warning_timer = 0.0
        self.last_boss_level = 0
        self.score = 0
        self.level = 1
        self.spawn_timer = 0
        self.flash_timer = 0

        self.reset_game()

    # --------------------------------------------------------
    # Highscore
    # --------------------------------------------------------
    def load_highscore(self):
        try:
            with open(HISCORE_FILE, 'r', encoding='utf-8') as f:
                return int(f.read().strip() or 0)
        except (OSError, ValueError):
            return 0

    def save_highscore(self):
        try:
            with open(HISCORE_FILE, 'w', encoding='utf-8') as f:
                f.write(str(self.highscore))
        except OSError:
            pass

    # --------------------------------------------------------
    # Siklus permainan
    # --------------------------------------------------------
    def reset_game(self):
        self.player = Player(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 60)
        self.asteroids = []
        self.bullets = []
        self.powerups = []
        self.particles = []
        self.boss = None
        self.boss_pending_tier = 0
        self.boss_warning_timer = 0.0
        self.last_boss_level = 0
        self.score = 0
        self.level = 1
        self.spawn_timer = 0
        self.flash_timer = 0

    def start_game(self):
        self.reset_game()
        self.state = Game.PLAYING
        self.sound.start_music()

    def game_over(self):
        self.state = Game.GAME_OVER
        self.sound.stop_music()
        if self.score > self.highscore:
            self.highscore = self.score
            self.save_highscore()

    def run(self):
        while self.running:
            dt = self.clock.tick(FPS)
            self.handle_events()
            self.update(dt)
            self.draw()

        self.sound.stop_music()
        pygame.quit()

    # --------------------------------------------------------
    # Input
    # --------------------------------------------------------
    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                self.handle_keydown(event.key)
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if self.state == Game.MENU:
                    start_rect, quit_rect = self.menu_buttons()
                    if start_rect.collidepoint(event.pos):
                        self.start_game()
                    elif quit_rect.collidepoint(event.pos):
                        self.running = False

    def handle_keydown(self, key):
        # tombol suara berlaku di semua layar
        if key == pygame.K_m:
            self.sound.toggle()
            return

        if self.state == Game.MENU:
            if key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE):
                self.start_game()
            elif key == pygame.K_ESCAPE:
                self.running = False

        elif self.state == Game.PLAYING:
            if key == pygame.K_p:
                self.state = Game.PAUSED
            elif key == pygame.K_ESCAPE:
                self.state = Game.MENU
                self.sound.stop_music()

        elif self.state == Game.PAUSED:
            if key == pygame.K_p:
                self.state = Game.PLAYING

        elif self.state == Game.GAME_OVER:
            if key == pygame.K_r:
                self.start_game()
            elif key == pygame.K_ESCAPE:
                self.state = Game.MENU

    def menu_buttons(self):
        width, height = 240, 56
        cx = SCREEN_WIDTH // 2
        start = pygame.Rect(cx - width // 2, 330, width, height)
        quit_btn = pygame.Rect(cx - width // 2, 410, width, height)
        return start, quit_btn

    # --------------------------------------------------------
    # Update
    # --------------------------------------------------------
    def update(self, dt):
        for star in self.stars:
            star.update()

        if self.state != Game.PLAYING:
            return

        keys = pygame.key.get_pressed()
        self.player.move(keys)

        if keys[pygame.K_SPACE]:
            new_bullets = self.player.shoot()
            if new_bullets:
                self.bullets.extend(new_bullets)
                self.sound.play('shoot')

        self.update_boss_spawn(dt)

        # asteroid biasa berhenti muncul selama boss aktif
        if self.boss is None:
            self.spawn_timer += dt
            interval = max(SPAWN_INTERVAL_MIN,
                           SPAWN_INTERVAL_START - (self.level - 1) * SPAWN_INTERVAL_STEP)
            if self.spawn_timer >= interval:
                self.spawn_timer = 0
                self.asteroids.append(Asteroid(self.level))

        for bullet in self.bullets:
            bullet.update()
        self.bullets = [b for b in self.bullets if not b.offscreen()]

        for asteroid in self.asteroids:
            asteroid.update(dt)
        self.asteroids = [a for a in self.asteroids if not a.offscreen()]

        if self.boss is not None:
            self.boss.update(dt)

        for powerup in self.powerups:
            powerup.update(dt)
        self.powerups = [p for p in self.powerups if not p.offscreen()]

        for particle in self.particles:
            particle.update(dt)
        self.particles = [p for p in self.particles if not p.dead()]

        if self.flash_timer > 0:
            self.flash_timer = max(0, self.flash_timer - dt)

        self.check_collisions()

    def update_boss_spawn(self, dt):
        '''Atur peringatan dan kemunculan boss.'''
        if self.boss is not None:
            return

        if self.boss_warning_timer > 0:
            self.boss_warning_timer -= dt
            if self.boss_warning_timer <= 0:
                self.boss = Boss(max(1, self.boss_pending_tier))
                self.boss_pending_tier = 0
        elif self.boss_pending_tier > 0:
            self.boss_warning_timer = BOSS_WARNING_TIME
            self.sound.play('boss_warn')

    def check_collisions(self):
        # 1) peluru mengenai asteroid
        for bullet in self.bullets[:]:
            for asteroid in self.asteroids[:]:
                if self._hit(bullet.x, bullet.y, bullet.radius,
                             asteroid.x, asteroid.y, asteroid.radius):
                    self.bullets.remove(bullet)
                    self.asteroids.remove(asteroid)
                    self.explode(asteroid.x, asteroid.y, asteroid.color)
                    self.sound.play('explosion')
                    self.score += BULLET_SCORE
                    self.maybe_drop_powerup(asteroid.x, asteroid.y)
                    self.update_level()
                    break

        # 2) peluru mengenai boss
        if self.boss is not None:
            for bullet in self.bullets[:]:
                if self._hit(bullet.x, bullet.y, bullet.radius,
                             self.boss.x, self.boss.y, self.boss.radius * 0.92):
                    self.bullets.remove(bullet)
                    self.sound.play('boss_hit')
                    self.explode(bullet.x, bullet.y - 8, NEON_YELLOW, count=5, spread=0.6)
                    if self.boss.take_hit():
                        self.defeat_boss()
                        break

        # 3) pemain menabrak asteroid
        if not self.player.is_invulnerable():
            for asteroid in self.asteroids[:]:
                if self._hit(self.player.x, self.player.y, self.player.size * 0.45,
                             asteroid.x, asteroid.y, asteroid.radius):
                    self.asteroids.remove(asteroid)
                    self.explode(asteroid.x, asteroid.y, asteroid.color)
                    if self.player.has_shield():
                        self.score += 5
                        self.sound.play('boss_hit')
                    else:
                        self.damage_player()
                        if self.state != Game.PLAYING:
                            return

        # 4) pemain menabrak boss
        if (self.boss is not None and not self.player.is_invulnerable()
                and self._hit(self.player.x, self.player.y, self.player.size * 0.45,
                              self.boss.x, self.boss.y, self.boss.radius * 0.85)):
            if self.player.has_shield():
                self.player.shield_until = 0  # perisai pecah menahan boss
                self.sound.play('boss_hit')
                self.explode(self.player.x, self.player.y, NEON_GREEN)
            else:
                self.damage_player()
                if self.state != Game.PLAYING:
                    return

        # 5) pemain mengambil power-up
        for powerup in self.powerups[:]:
            if self._hit(self.player.x, self.player.y, self.player.size * 0.5,
                         powerup.x, powerup.y, powerup.radius):
                self.powerups.remove(powerup)
                self.apply_powerup(powerup.kind)
                self.sound.play('powerup')

    @staticmethod
    def _hit(x1, y1, r1, x2, y2, r2):
        dx = x1 - x2
        dy = y1 - y2
        return dx * dx + dy * dy <= (r1 + r2) ** 2

    def damage_player(self):
        self.player.hit()
        self.flash_timer = 180
        self.sound.play('hit')
        self.explode(self.player.x, self.player.y, NEON_CYAN, count=14, spread=1.2)
        if self.player.lives <= 0:
            self.game_over()

    def update_level(self):
        new_level = self.score // DIFFICULTY_STEP + 1
        if new_level > self.level:
            self.level = new_level
            # jadwalkan boss pada level kelipatan BOSS_LEVEL_STEP
            if self.level % BOSS_LEVEL_STEP == 0 and self.level > self.last_boss_level:
                self.last_boss_level = self.level
                self.boss_pending_tier = self.level // BOSS_LEVEL_STEP

    def defeat_boss(self):
        '''Bonus skor, ledakan besar, dan hadiah power-up.'''
        tier = self.boss.tier
        self.explode(self.boss.x, self.boss.y, NEON_RED, count=70, spread=2.2)
        self.explode(self.boss.x, self.boss.y, NEON_YELLOW, count=30, spread=1.6)
        self.sound.play('explosion')

        for _ in range(BOSS_DROP_POWERUPS):
            offset_x = random.uniform(-self.boss.radius, self.boss.radius)
            kind = random.choice((PowerUp.SHIELD, PowerUp.DOUBLE))
            self.powerups.append(PowerUp(self.boss.x + offset_x, self.boss.y, kind))

        self.score += self.boss.max_hp * BOSS_SCORE_MULTIPLIER
        self.boss = None
        self.update_level()

    def maybe_drop_powerup(self, x, y):
        if random.random() < POWERUP_DROP_CHANCE:
            kind = random.choice((PowerUp.SHIELD, PowerUp.DOUBLE))
            self.powerups.append(PowerUp(x, y, kind))

    def apply_powerup(self, kind):
        now = pygame.time.get_ticks()
        if kind == PowerUp.SHIELD:
            self.player.shield_until = now + POWERUP_DURATION
        elif kind == PowerUp.DOUBLE:
            self.player.double_until = now + POWERUP_DURATION

    def explode(self, x, y, color, count=18, spread=1.0):
        for _ in range(count):
            self.particles.append(Particle(x, y, color, spread))
        for _ in range(max(2, count // 3)):
            self.particles.append(Particle(x, y, WHITE, spread))

    # --------------------------------------------------------
    # Render
    # --------------------------------------------------------
    def draw(self):
        self.screen.fill(BLACK)

        for star in self.stars:
            star.draw(self.screen)

        if self.state == Game.MENU:
            self.draw_menu()
        elif self.state in (Game.PLAYING, Game.PAUSED):
            self.draw_play()
            if self.boss_warning_timer > 0:
                self.draw_boss_warning()
            if self.state == Game.PAUSED:
                self.draw_pause_overlay()
        elif self.state == Game.GAME_OVER:
            self.draw_play(show_player=False)
            self.draw_game_over()

        if self.flash_timer > 0:
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            alpha = int(90 * (self.flash_timer / 180))
            overlay.fill((255, 60, 90, alpha))
            self.screen.blit(overlay, (0, 0))

        pygame.display.flip()

    def draw_play(self, show_player=True):
        for powerup in self.powerups:
            powerup.draw(self.screen)
        for asteroid in self.asteroids:
            asteroid.draw(self.screen)
        if self.boss is not None:
            self.boss.draw(self.screen)
        for bullet in self.bullets:
            bullet.draw(self.screen)
        if show_player and self.player:
            self.player.draw(self.screen)
        for particle in self.particles:
            particle.draw(self.screen)

        self.draw_hud()

    def draw_hud(self):
        score_surf = self.font_mid.render(f'SCORE {self.score}', True, NEON_CYAN)
        self.screen.blit(score_surf, (16, 12))

        hi_surf = self.font_small.render(f'HI {self.highscore}', True, NEON_YELLOW)
        self.screen.blit(hi_surf, (16, 46))

        lvl_surf = self.font_small.render(f'LEVEL {self.level}', True, NEON_MAGENTA)
        self.screen.blit(lvl_surf, (SCREEN_WIDTH - lvl_surf.get_width() - 16, 16))

        for i in range(self.player.lives):
            x = SCREEN_WIDTH - 24 - i * 24
            y = 52
            pygame.draw.polygon(self.screen, NEON_GREEN, [
                (x, y - 8), (x - 8, y + 6), (x + 8, y + 6),
            ])

        # indikator power-up aktif
        now = pygame.time.get_ticks()
        y_off = 82
        if self.player.has_shield():
            left = (self.player.shield_until - now) / 1000.0
            txt = self.font_small.render(f'SHIELD {left:.1f}s', True, NEON_GREEN)
            self.screen.blit(txt, (16, y_off))
            y_off += 24
        if self.player.has_double():
            left = (self.player.double_until - now) / 1000.0
            txt = self.font_small.render(f'DOUBLE {left:.1f}s', True, NEON_YELLOW)
            self.screen.blit(txt, (16, y_off))

    def draw_boss_warning(self):
        # kedip merah di tepi layar
        pulse = (pygame.time.get_ticks() // 150) % 2
        if pulse:
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            overlay.fill((255, 40, 70, 40))
            self.screen.blit(overlay, (0, 0))

        text = self.font_big.render('WARNING', True, NEON_RED)
        self.screen.blit(text, (SCREEN_WIDTH // 2 - text.get_width() // 2, 210))
        sub = self.font_mid.render('BOSS INCOMING', True, NEON_ORANGE)
        self.screen.blit(sub, (SCREEN_WIDTH // 2 - sub.get_width() // 2, 280))

    def draw_menu(self):
        cx = SCREEN_WIDTH // 2

        title = self.font_big.render(TITLE.upper(), True, NEON_CYAN)
        self.screen.blit(title, (cx - title.get_width() // 2, 120))

        subtitle = self.font_small.render('Asteroid Shooter', True, NEON_MAGENTA)
        self.screen.blit(subtitle, (cx - subtitle.get_width() // 2, 190))

        start_rect, quit_rect = self.menu_buttons()
        self.draw_button(start_rect, 'START', NEON_GREEN)
        self.draw_button(quit_rect, 'QUIT', NEON_RED)

        hi = self.font_small.render(f'High Score: {self.highscore}', True, NEON_YELLOW)
        self.screen.blit(hi, (cx - hi.get_width() // 2, 250))

        hint = self.font_small.render('Panah / A-D gerak  -  SPASI tembak  -  P pause  -  M suara',
                                      True, GREY)
        self.screen.blit(hint, (cx - hint.get_width() // 2, SCREEN_HEIGHT - 50))

        if not self.sound.enabled:
            muted = self.font_small.render('(suara mati)', True, NEON_RED)
            self.screen.blit(muted, (cx - muted.get_width() // 2, SCREEN_HEIGHT - 26))

    def draw_button(self, rect, label, color):
        pygame.draw.rect(self.screen, DARK_BLUE, rect, border_radius=8)
        pygame.draw.rect(self.screen, color, rect, 2, border_radius=8)
        text = self.font_mid.render(label, True, color)
        self.screen.blit(text, (rect.centerx - text.get_width() // 2,
                                rect.centery - text.get_height() // 2))

    def draw_pause_overlay(self):
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 150))
        self.screen.blit(overlay, (0, 0))

        text = self.font_big.render('PAUSED', True, NEON_CYAN)
        self.screen.blit(text, (SCREEN_WIDTH // 2 - text.get_width() // 2,
                                SCREEN_HEIGHT // 2 - 60))

        hint = self.font_small.render('Tekan P untuk lanjut', True, WHITE)
        self.screen.blit(hint, (SCREEN_WIDTH // 2 - hint.get_width() // 2,
                                SCREEN_HEIGHT // 2 + 10))

    def draw_game_over(self):
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 170))
        self.screen.blit(overlay, (0, 0))

        cx = SCREEN_WIDTH // 2

        title = self.font_big.render('GAME OVER', True, NEON_RED)
        self.screen.blit(title, (cx - title.get_width() // 2, 180))

        score = self.font_mid.render(f'Skor: {self.score}', True, WHITE)
        self.screen.blit(score, (cx - score.get_width() // 2, 270))

        hi = self.font_mid.render(f'High Score: {self.highscore}', True, NEON_YELLOW)
        self.screen.blit(hi, (cx - hi.get_width() // 2, 315))

        if self.score >= self.highscore and self.score > 0:
            new_hi = self.font_small.render('NEW HIGH SCORE!', True, NEON_GREEN)
            self.screen.blit(new_hi, (cx - new_hi.get_width() // 2, 360))

        hint = self.font_small.render('Tekan R untuk restart  -  Esc untuk menu',
                                      True, GREY)
        self.screen.blit(hint, (cx - hint.get_width() // 2, 420))


if __name__ == '__main__':
    Game().run()
