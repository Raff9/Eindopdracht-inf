import pygame
import sys
import random

# --- CONSTANTS ---
WIDTH, HEIGHT = 900, 500
FPS = 60
PLAYER_SPEED = 5
JUMP_POWER = 14
GRAVITY = 0.8
INVINCIBILITY_MS = 1500

# --- INITIALIZATION ---
pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Chicken World")
clock = pygame.time.Clock()
font = pygame.font.SysFont(None, 36)
large_font = pygame.font.SysFont(None, 64)

# Try to load images; fall back to colored rectangles if missing
def load_image(path, size=None):
    try:
        im = pygame.image.load(path).convert_alpha()
        if size:
            im = pygame.transform.scale(im, size)
        return im
    except Exception:
        return None

player_img = load_image('Kip.png', (48, 48))
bg_img = load_image('achtergrond 3.jpg', (WIDTH, HEIGHT))

# --- GAME CLASSES ---
class Player:
    def __init__(self, x, y):
        self.rect = pygame.Rect(x, y, 48, 48)
        self.vel_y = 0
        self.on_ground = False
        self.eggs = 3
        self.invincible_until = 0
        self.score = 0

    def handle_input(self):
        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT]:
            self.rect.x -= PLAYER_SPEED
        if keys[pygame.K_RIGHT]:
            self.rect.x += PLAYER_SPEED
        if keys[pygame.K_SPACE] or keys[pygame.K_UP]:
            if self.on_ground:
                self.vel_y = -JUMP_POWER
                self.on_ground = False

    def apply_gravity(self):
        self.vel_y += GRAVITY
        self.rect.y += int(self.vel_y)

    def check_ground(self, ground_y):
        if self.rect.bottom >= ground_y:
            self.rect.bottom = ground_y
            self.vel_y = 0
            self.on_ground = True

    def update(self, dt):
        self.handle_input()
        self.apply_gravity()
        # keep inside level horizontally
        if self.rect.left < 0:
            self.rect.left = 0
        if self.rect.right > WIDTH:
            self.rect.right = WIDTH
        # score: farthest x reached
        self.score = max(self.score, self.rect.x)

    def draw(self, surf):
        if player_img:
            surf.blit(player_img, self.rect.topleft)
        else:
            color = (255, 220, 180)
            pygame.draw.rect(surf, color, self.rect)

    def hit(self):
        now = pygame.time.get_ticks()
        if now >= self.invincible_until:
            self.eggs -= 1
            self.invincible_until = now + INVINCIBILITY_MS
            return True
        return False

    def reset(self):
        self.rect.topleft = (50, HEIGHT - 50 - self.rect.height)
        self.vel_y = 0
        self.on_ground = False
        self.eggs = 3
        self.invincible_until = 0
        self.score = 0

class Projectile:
    def __init__(self, x, y, vx, vy=0):
        self.rect = pygame.Rect(x, y, 16, 16)
        self.vx = vx
        self.vy = vy

    def update(self, dt):
        self.rect.x += int(self.vx * dt)
        self.rect.y += int(self.vy * dt)

    def draw(self, surf):
        pygame.draw.ellipse(surf, (240, 240, 200), self.rect)

class MayonnaiseMachine:
    def __init__(self, x, y, direction=-1, shoot_interval=2000):
        self.x = x
        self.y = y
        self.rect = pygame.Rect(x, y, 48, 48)
        self.direction = direction  # -1 left, 1 right
        self.shoot_interval = shoot_interval
        self.last_shot = pygame.time.get_ticks() - random.randint(0, shoot_interval)
        self.projectiles = []

    def update(self, dt):
        now = pygame.time.get_ticks()
        if now - self.last_shot >= self.shoot_interval:
            self.shoot()
            self.last_shot = now
        # update projectiles
        for p in self.projectiles:
            p.update(dt)
        # remove off-screen
        self.projectiles = [p for p in self.projectiles if -50 < p.rect.x < WIDTH + 50]

    def shoot(self):
        speed = 0.3 * (1 + random.random() * 0.6)
        vx = speed * ( -200 if self.direction == -1 else 200)
        # spawn slightly in front
        px = self.rect.centerx + (self.direction * 20)
        py = self.rect.centery
        self.projectiles.append(Projectile(px, py, vx))

    def draw(self, surf):
        pygame.draw.rect(surf, (200, 200, 220), self.rect)
        # draw nozzle
        nozzle = (self.rect.centerx + self.direction * 30, self.rect.centery)
        pygame.draw.circle(surf, (180, 180, 200), nozzle, 8)
        for p in self.projectiles:
            p.draw(surf)

# --- LEVEL SETUP ---
ground_y = HEIGHT - 50
platforms = [pygame.Rect(0, ground_y, WIDTH, 50)]
# mayonnaise machines placed at various x positions
machines = [MayonnaiseMachine(400, ground_y - 48, direction=-1, shoot_interval=1800),
            MayonnaiseMachine(700, ground_y - 48, direction=-1, shoot_interval=2500),
            MayonnaiseMachine(1200, ground_y - 48, direction=1, shoot_interval=2200)]
# Make world width larger for simple side-scrolling feel
WORLD_WIDTH = 1600

# Camera offset (simple)
camera_x = 0

# Create player
player = Player(50, HEIGHT - 50 - 48)

# Game state
game_over = False
win = False

def reset_level():
    global player, machines, camera_x, game_over, win
    player.reset()
    camera_x = 0
    game_over = False
    win = False
    # reset machines
    machines.clear()
    machines.extend([
        MayonnaiseMachine(400, ground_y - 48, direction=-1, shoot_interval=1800),
        MayonnaiseMachine(700, ground_y - 48, direction=-1, shoot_interval=2500),
        MayonnaiseMachine(1200, ground_y - 48, direction=1, shoot_interval=2200)
    ])

# --- MAIN LOOP ---
running = True
while running:
    dt = clock.tick(FPS) / 16.0  # normalize movement scale
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_r and (game_over or win):
                reset_level()
            if event.key == pygame.K_ESCAPE:
                running = False

    if not game_over and not win:
        player.update(dt)
        player.check_ground(ground_y)

        # update machines and their projectiles
        for m in machines:
            m.update(dt)
            # check collisions
            for p in m.projectiles:
                if player.rect.colliderect(p.rect):
                    if player.hit():
                        # remove that projectile by marking off-screen
                        p.rect.x = -9999
        # simple win condition: reach near end of world
        if player.rect.x >= WORLD_WIDTH - 80:
            win = True

        # camera follows player but clamped
        camera_x = max(0, min(player.rect.x - 200, WORLD_WIDTH - WIDTH))

        # clamp player within world
        if player.rect.left < 0:
            player.rect.left = 0
        if player.rect.right > WORLD_WIDTH:
            player.rect.right = WORLD_WIDTH

        if player.eggs <= 0:
            game_over = True

    # --- DRAW ---
    if bg_img:
        screen.blit(bg_img, (-camera_x, 0))
    else:
        screen.fill((153, 211, 232))

    # draw platforms (only ground for now)
    for plat in platforms:
        r = plat.copy()
        r.x -= camera_x
        pygame.draw.rect(screen, (100, 60, 40), r)

    # draw machines
    for m in machines:
        r = m.rect.copy()
        r.x -= camera_x
        # draw machine body
        pygame.draw.rect(screen, (190, 190, 210), r)
        # draw nozzle
        nozzle = (r.centerx + m.direction * 18, r.centery)
        pygame.draw.circle(screen, (160, 160, 180), nozzle, 6)
        # projectiles
        for p in m.projectiles:
            pr = p.rect.copy()
            pr.x -= camera_x
            pygame.draw.ellipse(screen, (240,240,200), pr)

    # draw player (adjusted by camera)
    player_draw_pos = player.rect.copy()
    player_draw_pos.x -= camera_x
    if player_img:
        screen.blit(player_img, player_draw_pos.topleft)
    else:
        # flashing when invincible
        now = pygame.time.get_ticks()
        if now < player.invincible_until and (now // 120) % 2 == 0:
            # skip drawing to create blink
            pass
        else:
            pygame.draw.rect(screen, (255,220,180), player_draw_pos)

    # HUD
    eggs_text = font.render(f"Eggs: {player.eggs}", True, (30, 30, 30))
    score_text = font.render(f"Score: {player.score}", True, (30, 30, 30))
    screen.blit(eggs_text, (16, 16))
    screen.blit(score_text, (16, 48))

    if game_over:
        go_text = large_font.render("Game Over", True, (200, 30, 30))
        info = font.render("Press R to restart or ESC to quit", True, (30,30,30))
        screen.blit(go_text, (WIDTH//2 - go_text.get_width()//2, HEIGHT//2 - 60))
        screen.blit(info, (WIDTH//2 - info.get_width()//2, HEIGHT//2 + 10))
    if win:
        w_text = large_font.render("You Win!", True, (30, 150, 30))
        info = font.render("Press R to play again or ESC to quit", True, (30,30,30))
        screen.blit(w_text, (WIDTH//2 - w_text.get_width()//2, HEIGHT//2 - 60))
        screen.blit(info, (WIDTH//2 - info.get_width()//2, HEIGHT//2 + 10))

    pygame.display.flip()

pygame.quit()
sys.exit()
