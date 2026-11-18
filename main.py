'''
Space Dodger - game asteroid shooter sederhana dengan Pygame.

Kontrol:
    Panah kiri/kanan atau A/D : gerakkan pesawat
    Spasi                     : tembak
    P                         : pause
    R                         : restart (saat game over)
    Esc                       : kembali ke menu / keluar

Jalankan dengan: python main.py
'''

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
SHOOT_COOLDOWN = 220      # milidetik antar tembakan
INVULNERABLE_TIME = 1500  # milidetik kebal setelah kena hit

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
POWERUP_DROP_CHANCE = 0.15  # peluang muncul saat asteroid hancur
POWERUP_DURATION = 6000     # milidetik durasi efek
POWERUP_FALL_SPEED = 2.2
POWERUP_RADIUS = 14

# Partikel ledakan
PARTICLE_LIFETIME = 550  # milidetik

# Kesulitan
DIFFICULTY_STEP = 500       # skor per level
SPAWN_INTERVAL_START = 950  # milidetik
SPAWN_INTERVAL_MIN = 260
SPAWN_INTERVAL_STEP = 65

# Lokasi file highscore (di samping file main.py)
HISCORE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'highscore.txt')


class Star:
    '''Bintang latar dengan dua lapisan (parallax).'''

    def __init__(self, layer):
        self.layer = layer  # 0 = jauh dan lambat, 1 = dekat dan cepat
        self.reset(initial=True)

    def reset(self, initial=False):
        self.x = random.uniform(0, SCREEN_WIDTH)
        # saat inisialisasi sebar di seluruh layar, setelah itu muncul dari atas
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
        self.shield_until = 0        # timestamp berakhirnya perisai
        self.double_until = 0        # timestamp berakhirnya tembakan ganda
        self.invulnerable_until = 0  # timestamp berakhirnya kebal
        self.last_shot = 0

    # -- status ----------------------------------------------
    def has_shield(self):
        return pygame.time.get_ticks() < self.shield_until

    def has_double(self):
        return pygame.time.get_ticks() < self.double_until

    def is_invulnerable(self):
        return pygame.time.get_ticks() < self.invulnerable_until

    # -- aksi ------------------------------------------------
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
        '''Kurangi nyawa dan beri waktu kebal sementara.'''
        self.lives -= 1
        self.invulnerable_until = pygame.time.get_ticks() + INVULNERABLE_TIME

    # -- gambar ----------------------------------------------
    def draw(self, surface):
        # berkedip saat sedang kebal
        if self.is_invulnerable() and (pygame.time.get_ticks() // 100) % 2 == 0:
            return

        cx, cy = int(self.x), int(self.y)
        s = self.size // 2

        # semburan mesin (berkedip acak)
        flame = random.randint(5, 11)
        pygame.draw.polygon(surface, NEON_ORANGE, [
            (cx - s // 2, cy + s // 2),
            (cx + s // 2, cy + s // 2),
            (cx, cy + s // 2 + flame),
        ])

        # badan pesawat
        body = [
            (cx, cy - s),
            (cx - s, cy + s),
            (cx, cy + s // 3),
            (cx + s, cy + s),
        ]
        pygame.draw.polygon(surface, NEON_CYAN, body)
        pygame.draw.polygon(surface, WHITE, body, 1)

        # kokpit
        pygame.draw.circle(surface, WHITE, (cx, cy - s // 3), 3)

        # cincin perisai
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
        # jejak peluru
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
        self.rotation_speed = random.uniform(-80, 80)  # derajat per detik
        self.color = random.choice(Asteroid.COLORS)

        # bentuk poligon acak agar tiap asteroid terlihat berbeda
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

    def points(self):
        '''Hitung titik poligon setelah rotasi (koordinat layar).'''
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
        pygame.draw.polygon(surface, DARK_BLUE, pts)      # isi gelap
        pygame.draw.polygon(surface, self.color, pts, 2)  # outline neon


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

        # bingkai berdenyut
        pulse_radius = self.radius + int(2 * math.sin(self.pulse))
        pygame.draw.circle(surface, color, (cx, cy), pulse_radius, 1)
        pygame.draw.rect(surface, color,
                         pygame.Rect(cx - self.radius, cy - self.radius,
                                     self.radius * 2, self.radius * 2), 2,
                         border_radius=4)

        if self.kind == PowerUp.SHIELD:
            # ikon perisai sederhana
            shield = [
                (cx, cy - 7), (cx - 6, cy - 3), (cx - 6, cy + 3),
                (cx, cy + 7), (cx + 6, cy + 3), (cx + 6, cy - 3),
            ]
            pygame.draw.polygon(surface, color, shield, 2)
        else:
            # ikon dua peluru
            pygame.draw.line(surface, color, (cx - 4, cy + 6), (cx - 4, cy - 6), 3)
            pygame.draw.line(surface, color, (cx + 4, cy + 6), (cx + 4, cy - 6), 3)


class Particle:
    '''Pecahan kecil untuk efek ledakan.'''

    def __init__(self, x, y, color):
        self.x = float(x)
        self.y = float(y)

        speed = random.uniform(1.0, 4.5)
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
        pygame.display.set_caption(TITLE)
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        self.clock = pygame.time.Clock()

        self.font_big = pygame.font.SysFont('consolas', 56, bold=True)
        self.font_mid = pygame.font.SysFont('consolas', 28, bold=True)
        self.font_small = pygame.font.SysFont('consolas', 20)

        # latar bintang dua lapisan (parallax)
        self.stars = [Star(0) for _ in range(70)] + [Star(1) for _ in range(35)]

        self.running = True
        self.state = Game.MENU
        self.highscore = self.load_highscore()

        # data permainan
        self.player = None
        self.asteroids = []
        self.bullets = []
        self.powerups = []
        self.particles = []
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
            pass  # gagal menyimpan tidak boleh membuat game crash

    # --------------------------------------------------------
    # Siklus permainan
    # --------------------------------------------------------
    def reset_game(self):
        self.player = Player(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 60)
        self.asteroids = []
        self.bullets = []
        self.powerups = []
        self.particles = []
        self.score = 0
        self.level = 1
        self.spawn_timer = 0
        self.flash_timer = 0

    def start_game(self):
        self.reset_game()
        self.state = Game.PLAYING

    def game_over(self):
        self.state = Game.GAME_OVER
        if self.score > self.highscore:
            self.highscore = self.score
            self.save_highscore()

    def run(self):
        while self.running:
            dt = self.clock.tick(FPS)
            self.handle_events()
            self.update(dt)
            self.draw()

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
        if self.state == Game.MENU:
            if key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE):
                self.start_game()
            elif key == pygame.K_ESCAPE:
                self.running = False

        elif self.state == Game.PLAYING:
            if key == pygame.K_p:
                self.state = Game.PAUSED

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
        # bintang selalu bergerak agar layar tetap hidup
        for star in self.stars:
            star.update()

        if self.state != Game.PLAYING:
            return

        keys = pygame.key.get_pressed()
        self.player.move(keys)

        # tembak selama spasi ditahan
        if keys[pygame.K_SPACE]:
            self.bullets.extend(self.player.shoot())

        # spawn asteroid; interval mengecil seiring level
        self.spawn_timer += dt
        interval = max(SPAWN_INTERVAL_MIN,
                       SPAWN_INTERVAL_START - (self.level - 1) * SPAWN_INTERVAL_STEP)
        if self.spawn_timer >= interval:
            self.spawn_timer = 0
            self.asteroids.append(Asteroid(self.level))

        # perbarui semua objek
        for bullet in self.bullets:
            bullet.update()
        self.bullets = [b for b in self.bullets if not b.offscreen()]

        for asteroid in self.asteroids:
            asteroid.update(dt)
        self.asteroids = [a for a in self.asteroids if not a.offscreen()]

        for powerup in self.powerups:
            powerup.update(dt)
        self.powerups = [p for p in self.powerups if not p.offscreen()]

        for particle in self.particles:
            particle.update(dt)
        self.particles = [p for p in self.particles if not p.dead()]

        if self.flash_timer > 0:
            self.flash_timer = max(0, self.flash_timer - dt)

        self.check_collisions()

    def check_collisions(self):
        # 1) peluru mengenai asteroid
        for bullet in self.bullets[:]:
            for asteroid in self.asteroids[:]:
                if self._hit(bullet.x, bullet.y, bullet.radius,
                             asteroid.x, asteroid.y, asteroid.radius):
                    self.bullets.remove(bullet)
                    self.asteroids.remove(asteroid)
                    self.explode(asteroid.x, asteroid.y, asteroid.color)
                    self.score += BULLET_SCORE
                    self.maybe_drop_powerup(asteroid.x, asteroid.y)
                    self.update_level()
                    break

        # 2) pemain menabrak asteroid
        if not self.player.is_invulnerable():
            for asteroid in self.asteroids[:]:
                if self._hit(self.player.x, self.player.y, self.player.size * 0.45,
                             asteroid.x, asteroid.y, asteroid.radius):
                    self.asteroids.remove(asteroid)
                    self.explode(asteroid.x, asteroid.y, asteroid.color)

                    if self.player.has_shield():
                        self.score += 5  # perisai menyerap tabrakan
                    else:
                        self.damage_player()
                        if self.state != Game.PLAYING:
                            return

        # 3) pemain mengambil power-up
        for powerup in self.powerups[:]:
            if self._hit(self.player.x, self.player.y, self.player.size * 0.5,
                         powerup.x, powerup.y, powerup.radius):
                self.powerups.remove(powerup)
                self.apply_powerup(powerup.kind)

    @staticmethod
    def _hit(x1, y1, r1, x2, y2, r2):
        '''Deteksi tabrakan dua lingkaran.'''
        dx = x1 - x2
        dy = y1 - y2
        return dx * dx + dy * dy <= (r1 + r2) ** 2

    def damage_player(self):
        '''Kurangi nyawa pemain dan akhiri game bila habis.'''
        self.player.hit()
        self.flash_timer = 180  # efek layar berkedip

        if self.player.lives <= 0:
            self.game_over()

    def update_level(self):
        '''Naikkan level tiap kelipatan DIFFICULTY_STEP poin.'''
        new_level = self.score // DIFFICULTY_STEP + 1
        if new_level > self.level:
            self.level = new_level

    def maybe_drop_powerup(self, x, y):
        '''Kadang-kadang munculkan power-up di lokasi asteroid hancur.'''
        if random.random() < POWERUP_DROP_CHANCE:
            kind = random.choice((PowerUp.SHIELD, PowerUp.DOUBLE))
            self.powerups.append(PowerUp(x, y, kind))

    def apply_powerup(self, kind):
        now = pygame.time.get_ticks()
        if kind == PowerUp.SHIELD:
            self.player.shield_until = now + POWERUP_DURATION
        elif kind == PowerUp.DOUBLE:
            self.player.double_until = now + POWERUP_DURATION

    def explode(self, x, y, color):
        '''Buat sekumpulan partikel ledakan.'''
        for _ in range(18):
            self.particles.append(Particle(x, y, color))
        # sedikit percikan putih untuk kesan terang
        for _ in range(6):
            self.particles.append(Particle(x, y, WHITE))

    # --------------------------------------------------------
    # Render
    # --------------------------------------------------------
    def draw(self):
        self.screen.fill(BLACK)

        # bintang latar (parallax)
        for star in self.stars:
            star.draw(self.screen)

        if self.state == Game.MENU:
            self.draw_menu()
        elif self.state in (Game.PLAYING, Game.PAUSED):
            self.draw_play()
            if self.state == Game.PAUSED:
                self.draw_pause_overlay()
        elif self.state == Game.GAME_OVER:
            self.draw_play(show_player=False)
            self.draw_game_over()

        # efek kedip merah saat kena hit
        if self.flash_timer > 0:
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            alpha = int(90 * (self.flash_timer / 180))
            overlay.fill((255, 60, 90, alpha))
            self.screen.blit(overlay, (0, 0))

        pygame.display.flip()

    def draw_play(self, show_player=True):
        # gambar objek permainan
        for powerup in self.powerups:
            powerup.draw(self.screen)
        for asteroid in self.asteroids:
            asteroid.draw(self.screen)
        for bullet in self.bullets:
            bullet.draw(self.screen)
        if show_player and self.player:
            self.player.draw(self.screen)
        for particle in self.particles:
            particle.draw(self.screen)

        self.draw_hud()

    def draw_hud(self):
        # skor kiri atas
        score_surf = self.font_mid.render(f'SCORE {self.score}', True, NEON_CYAN)
        self.screen.blit(score_surf, (16, 12))

        # highscore di bawah skor
        hi_surf = self.font_small.render(f'HI {self.highscore}', True, NEON_YELLOW)
        self.screen.blit(hi_surf, (16, 46))

        # level kanan atas
        lvl_surf = self.font_small.render(f'LEVEL {self.level}', True, NEON_MAGENTA)
        self.screen.blit(lvl_surf, (SCREEN_WIDTH - lvl_surf.get_width() - 16, 16))

        # nyawa sebagai segitiga kecil
        for i in range(self.player.lives):
            x = SCREEN_WIDTH - 24 - i * 24
            y = 52
            pygame.draw.polygon(self.screen, NEON_GREEN, [
                (x, y - 8), (x - 8, y + 6), (x + 8, y + 6),
            ])

    def draw_menu(self):
        cx = SCREEN_WIDTH // 2

        title = self.font_big.render(TITLE.upper(), True, NEON_CYAN)
        self.screen.blit(title, (cx - title.get_width() // 2, 120))

        subtitle = self.font_small.render('Asteroid Shooter', True, NEON_MAGENTA)
        self.screen.blit(subtitle, (cx - subtitle.get_width() // 2, 190))

        start_rect, quit_rect = self.menu_buttons()
        self.draw_button(start_rect, 'START', NEON_GREEN)
        self.draw_button(quit_rect, 'QUIT', NEON_RED)

        hint = self.font_small.render('Panah / A-D gerak  -  SPASI tembak  -  P pause',
                                      True, GREY)
        self.screen.blit(hint, (cx - hint.get_width() // 2, SCREEN_HEIGHT - 50))

        hi = self.font_small.render(f'High Score: {self.highscore}', True, NEON_YELLOW)
        self.screen.blit(hi, (cx - hi.get_width() // 2, 250))

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


# Entry point permainan
if __name__ == '__main__':
    Game().run()
