import pygame
import sys
import random
import math
import json
import os
from pathlib import Path

# --- CONSTANTS ---
WIDTH, HEIGHT = 900, 500
FPS = 60
PLAYER_SPEED = 5
JUMP_POWER = 14
GRAVITY = 0.8
INVINCIBILITY_MS = 1000

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

# Try to load images; fall back to colored rectangles if missing
player_img = load_image('Kip.png', (48, 48))
bg_img = load_image('achtergrond 3.jpg', (WIDTH, HEIGHT))
machine_img = load_image('Mayonnaise_Machine.png', (48, 48))
# cache flipped machine image (vertical flip)
if machine_img:
    machine_img_up = pygame.transform.flip(machine_img, True, False)
else:
    machine_img_up = None

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
        # Arrow keys and WASD support
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            self.rect.x -= PLAYER_SPEED
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            self.rect.x += PLAYER_SPEED
        if keys[pygame.K_SPACE] or keys[pygame.K_UP] or keys[pygame.K_w]:
            if self.on_ground:
                self.vel_y = -JUMP_POWER
                self.on_ground = False
                self.float_timer = 0
                self.is_floating = False

        # Zweven (alleen in de lucht)
        self.max_float_time = 500
        if not self.on_ground and (keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT]):
            if self.float_timer < self.max_float_time:
                self.vel_y = 0
                self.is_floating = True
                self.float_timer += clock.get_time()
            else:
                self.is_floating = False
        else:
            self.is_floating = False

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
        # keep inside level horizontally (clamp to world)
        if self.rect.left < 0:
            self.rect.left = 0
        try:
            max_x = WORLD_WIDTH
        except NameError:
            max_x = WIDTH
        if self.rect.right > max_x:
            self.rect.right = max_x
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

    def respawn(self):
        """Respawn the player at the start without resetting eggs or score."""
        # respawn at the level start
        self.rect.topleft = (50, HEIGHT - 50 - self.rect.height)
        self.vel_y = 0
        self.on_ground = False
        # give a short invincibility after respawn
        self.invincible_until = pygame.time.get_ticks() + INVINCIBILITY_MS

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


# simple particle effects for egg loss
effects = []

def spawn_egg_lost_effect(x, y, count=12):
    """Spawn small particles at (x,y). Each particle is a dict.
    Particles have vx, vy, life, r, color."""
    for i in range(count):
        ang = random.random() * math.pi * 2
        speed = random.uniform(1.5, 4.0)
        vx = math.cos(ang) * speed
        vy = math.sin(ang) * speed * -0.5
        effects.append({
            'x': x,
            'y': y,
            'vx': vx,
            'vy': vy,
            'life': random.uniform(0.6, 1.2),
            'r': random.randint(2, 5),
            'color': (255, 0, 0)
        })

def play_egg_sound():
    pass

class MayonnaiseMachine:
    def __init__(self, x, y, direction=1, shoot_interval=2000, projectile_speed=3.0):
        self.x = x
        self.y = y
        self.rect = pygame.Rect(x, y, 48, 48)
        self.direction = direction  # 1 = down, -1 = up
        # if placed high on screen, flip to shoot upward automatically
        self.shoot_interval = shoot_interval
        self.last_shot = pygame.time.get_ticks() - random.randint(0, shoot_interval)
        self.projectiles = []
        self.projectile_speed = projectile_speed

    def update(self, dt):
        now = pygame.time.get_ticks()
        if now - self.last_shot >= self.shoot_interval:
            self.shoot()
            self.last_shot = now
        # update projectiles
        for p in self.projectiles:
            p.update(dt)
        # remove projectiles that are off the world horizontally or off-screen vertically
        self.projectiles = [p for p in self.projectiles if (-50 < p.rect.x < WORLD_WIDTH + 50) and (-200 < p.rect.y < HEIGHT + 200)]

    def shoot(self):
        # shoot vertically (down or up). direction: 1 = down, -1 = up
        # make projectiles noticeably slower and a bit variable
        # use the machine's configured projectile speed (pixels per frame)
        base = self.projectile_speed
        variance = 0.6
        speed = (6.0 + random.random() * variance)
        # direction: 1 = down, -1 = up
        vy = base * speed * self.direction
        px = self.rect.centerx
        py = self.rect.centery + (self.direction * 20)
        self.projectiles.append(Projectile(px, py, 0, vy))

    def draw(self, surf):
        pygame.draw.rect(surf, (200, 200, 220), self.rect)
        # draw nozzle
        nozzle = (self.rect.centerx + self.direction * 30, self.rect.centery)
        pygame.draw.circle(surf, (180, 180, 200), nozzle, 8)
        for p in self.projectiles:
            p.draw(surf)

# --- LEVEL SETUP ---
ground_y = HEIGHT - 50

# level variable
level = 1

# placeholder globals that will be built by build_level()
WORLD_WIDTH = None
platforms = []
obstacles = []
machines = []
world_bg = None
finish_rect = None
# checkpoint per level (respawn point)
checkpoint_x = 50
checkpoints = []
checkpoints_activated = set()
checkpoint_rect = None

def build_level(lv):
    """Create WORLD_WIDTH, platforms, obstacles, machines and world_bg for level `lv`."""
    global WORLD_WIDTH, platforms, obstacles, machines, world_bg, finish_rect
    # Try to load a JSON level file first
    levels_dir = Path(__file__).parent / 'levels'
    json_path = levels_dir / f'level{lv}.json'
    if json_path.exists():
        try:
            with open(json_path, 'r', encoding='utf8') as f:
                data = json.load(f)
            WORLD_WIDTH = int(data.get('world_width', 1600))
            # platforms
            platforms = [pygame.Rect(*p) for p in data.get('platforms', [[0, ground_y, WORLD_WIDTH, 50]])]
            # obstacles
            obstacles = [pygame.Rect(*p) for p in data.get('obstacles', [])]
            # holes (floor openings)
            holes = [pygame.Rect(*h) for h in data.get('holes', [])]
            # spikes
            spikes = [pygame.Rect(*s) for s in data.get('spikes', [])]
            # jump pads
            jump_pads = [pygame.Rect(*j) for j in data.get('jump_pads', [])]
            # machines
            machines = []
            for m in data.get('machines', []):
                mx = int(m.get('x'))
                my = int(m.get('y'))
                md = int(m.get('direction', 1))
                mi = int(m.get('shoot_interval', 1800))
                msp = float(m.get('projectile_speed', 3.0))
                machines.append(MayonnaiseMachine(mx, my, direction=md, shoot_interval=mi, projectile_speed=msp))
            # finish
            fx = int(data.get('finish_x', WORLD_WIDTH - 80))
            finish_rect = pygame.Rect(fx, ground_y - 120, 40, 120)
            # checkpoints (optional in JSON)
            checkpoints = [pygame.Rect(*c) for c in data.get('checkpoints', [])]
            if not checkpoints:
                # default checkpoint at 20% of the level
                cx = max(50, int(WORLD_WIDTH * 0.2))
                checkpoints = [pygame.Rect(cx, ground_y - 40, 24, 40)]
            # use the first checkpoint as the respawn point initially
            globals()['checkpoints'] = checkpoints
            globals()['checkpoints_activated'] = set()
            globals()['checkpoint_rect'] = checkpoints[0] if checkpoints else None
            globals()['checkpoint_x'] = checkpoints[0].x if checkpoints else 50
            # build tiled background
            try:
                world_bg = pygame.Surface((WORLD_WIDTH, HEIGHT)).convert()
                if bg_img:
                    bw = bg_img.get_width()
                    for x in range(0, WORLD_WIDTH, bw):
                        world_bg.blit(bg_img, (x, 0))
                else:
                    world_bg.fill((153, 211, 232))
            except Exception:
                world_bg = None
            # attach hole/spike/jump lists to globals for gameplay
            globals()['holes'] = holes
            globals()['spikes'] = spikes
            globals()['jump_pads'] = jump_pads
            return
        except Exception:
            # fall back to procedural generation on any load error
            pass

    # Procedural fallback if no JSON level
    base = 1600
    WORLD_WIDTH = base + (lv - 1) * 600
    # ground platform across the whole world
    platforms = [pygame.Rect(0, ground_y, WORLD_WIDTH, 50)]
    # create some obstacles; spacing and heights vary with level
    obstacles = []
    holes = []
    spikes = []
    jump_pads = []
    seed_x = 280
    for i in range(5 + lv // 2):
        w = random.randint(80, 180)
        h_off = random.choice([80, 100, 140, 160])
        obstacles.append(pygame.Rect(seed_x + i * 260, ground_y - h_off, w, 16))
        # ensure reachability: if very high, add a jump pad shortly before
        if h_off >= 140:
            jp_x = max(50, seed_x + i * 260 - 80)
            jump_pads.append(pygame.Rect(jp_x, ground_y - 16, 40, 8))
    # add some holes in the ground
    for i in range(max(1, lv//2)):
        hx = 400 + i * 450
        holes.append(pygame.Rect(hx, ground_y, random.randint(60, 120), 50))
    # add some spikes on the ground and on some obstacles
    for i in range(max(1, lv//2)):
        sx = 600 + i * 340
        spikes.append(pygame.Rect(sx, ground_y - 16, 32, 16))
    # machines placed at fractions across the world, mounted above ground to shoot down
    machines = []
    positions = [int(WORLD_WIDTH * 0.25), int(WORLD_WIDTH * 0.5), int(WORLD_WIDTH * 0.78)]
    for idx, px in enumerate(positions):
        interval = max(600, 1800 - lv * 100 + idx * 200)
        machines.append(MayonnaiseMachine(px, ground_y - 220, direction=1, shoot_interval=interval))
    # build tiled background for the whole world
    try:
        world_bg = pygame.Surface((WORLD_WIDTH, HEIGHT)).convert()
        if bg_img:
            bw = bg_img.get_width()
            for x in range(0, WORLD_WIDTH, bw):
                world_bg.blit(bg_img, (x, 0))
        else:
            world_bg.fill((153, 211, 232))
    except Exception:
        world_bg = None
    # finish flag near the right end
    finish_rect = pygame.Rect(WORLD_WIDTH - 80, ground_y - 120, 40, 120)
    # default checkpoint placement for procedural levels
    cx = max(50, int(WORLD_WIDTH * 0.2))
    checkpoints = [pygame.Rect(cx, ground_y - 40, 24, 40)]
    globals()['checkpoints'] = checkpoints
    globals()['checkpoints_activated'] = set()
    globals()['checkpoint_rect'] = checkpoints[0]
    globals()['checkpoint_x'] = checkpoints[0].x
    globals()['holes'] = holes
    globals()['spikes'] = spikes
    globals()['jump_pads'] = jump_pads

# build initial level
build_level(level)

# Camera offset (simple)
camera_x = 0

# Create player
player = Player(50, HEIGHT - 50 - 48)

# Game state
game_over = False
win = False
final_victory = False

def reset_level():
    global player, machines, camera_x, game_over, win
    player.reset()
    camera_x = 0
    game_over = False
    win = False
    # rebuild the current level (machines, platforms, obstacles, world_bg)
    build_level(level)

def advance_level():
    """Move to the next level: increment level, expand WORLD_WIDTH and rebuild world."""
    global level, camera_x, win, final_victory
    levels_dir = Path(__file__).parent / 'levels'
    total_levels = len([p for p in levels_dir.glob('level*.json') if p.is_file()])
    level += 1
    # if JSON levels exist and we've finished them all, show victory
    if total_levels > 0 and level > total_levels:
        win = True
        final_victory = True
        level = 1
        return
    camera_x = 0
    build_level(level)
    player.reset()

# --- MAIN LOOP ---
running = True
while running:
    dt = clock.tick(FPS) / 16.0  # normalize movement scale
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_r and (game_over or win):
                # restart from level 1 after finishing or game over
                level
                final_victory = False
                build_level(level)
                player.reset()
                game_over = False
                win = False
            if event.key == pygame.K_ESCAPE:
                running = False
    

    if not game_over and not win:
        # save previous bottom and sides to help with platform collision detection
        prev_bottom = player.rect.bottom
        prev_left = player.rect.left
        prev_right = player.rect.right
        player.update(dt)
        # compute whether player is currently centered over a hole (used to avoid snapping to ground)
        px = player.rect.centerx
        over_hole = None
        for h in globals().get('holes', []):
            if h.left <= px <= h.right:
                over_hole = h
                break
        # ---- X-axis collision (zijkanten) ----
        for obj in (platforms + obstacles):
            if player.rect.colliderect(obj):
                # kwam van links
                if prev_right <= obj.left:
                    player.rect.right = obj.left
                    player.vel_x = 0
                # kwam van rechts
                elif prev_left >= obj.right:
                    player.rect.left = obj.right
                    player.vel_x = 0
        # basic platform / ground collision handling
        landed = False
        # check platforms and obstacles first (use a tolerant foot check so landing is reliable)
        for plat in (platforms + obstacles):
            # if this is the ground platform and the player is over a hole, skip snapping
            if (plat in platforms) and over_hole and plat.y >= ground_y - 4:
                continue
            # create a small landing rect representing player's feet during the frame
            feet = pygame.Rect(player.rect.left + 6, prev_bottom - 4, player.rect.width - 12, 6)
            if feet.colliderect(plat) and player.vel_y >= 0:
                # snap to platform top
                player.rect.bottom = plat.top
                player.vel_y = 0
                player.on_ground = True
                landed = True
                break

        # ground (don't land if over a hole)
        if not landed:
            if not over_hole:
                player.check_ground(ground_y)
            else:
                # over a hole: ensure player is not considered on_ground so they fall
                player.on_ground = False
                # death occurs after falling off-screen so the fall is visible
                if player.rect.top > HEIGHT:
                    spawn_egg_lost_effect(player.rect.centerx, player.rect.centery, count=28)
                    play_egg_sound()
                    player.eggs = 0
                    game_over = True

        # update machines and their projectiles
        # use a slightly smaller hitbox to avoid early triggers
        hitbox = player.rect.inflate(-6, -6)
        for m in machines:
            m.update(dt)
            # check collisions
            for p in list(m.projectiles):
                if hitbox.colliderect(p.rect.inflate(-6, -6)):
                    if player.hit():
                        # visual + sound feedback for egg loss
                        spawn_egg_lost_effect(player.rect.centerx, player.rect.centery)
                        play_egg_sound()
                        # remove that projectile
                        try:
                            m.projectiles.remove(p)
                        except ValueError:
                            pass
        # check finish flag
        if finish_rect and player.rect.colliderect(finish_rect):
            # advance to next level
            advance_level()

        # (checkpoints removed from game logic)

        # check spikes (lose an egg) using smaller hitbox
        for s in globals().get('spikes', []):
            if hitbox.colliderect(s):
                if player.hit():
                    spawn_egg_lost_effect(player.rect.centerx, player.rect.centery)
                    play_egg_sound()
                    if player.eggs <= 0:
                        game_over = True
        # check jump pads (bounce)
        for jp in globals().get('jump_pads', []):
            if player.rect.colliderect(jp):
                # only trigger when landing onto pad
                if prev_bottom <= jp.top and player.vel_y >= 0:
                    player.vel_y = -JUMP_POWER * 1.8
                    player.on_ground = True

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
    if 'world_bg' in globals() and world_bg:
        screen.blit(world_bg, (-camera_x, 0))
    else:
        screen.fill((153, 211, 232))

    # draw obstacles (platforms are drawn below with hole splitting)
    for plat in obstacles:
        r = plat.copy()
        r.x -= camera_x
        pygame.draw.rect(screen, (140, 100, 60), r)
    # draw platforms but exclude holes so the floor has gaps rather than black bars
    holes_list = globals().get('holes', [])
    for plat in platforms:
        # split platform horizontally by holes that intersect it
        seg_x = plat.x
        seg_w = plat.width
        segments = []
        # find holes that intersect this platform horizontally
        inter_holes = [h for h in holes_list if h.y <= plat.y + plat.height and (h.left < plat.right and h.right > plat.left)]
        if not inter_holes:
            r = plat.copy(); r.x -= camera_x
            pygame.draw.rect(screen, (100, 60, 40), r)
        else:
            # sort holes by x
            inter_holes.sort(key=lambda hh: hh.x)
            cur = plat.left
            for h in inter_holes:
                hx = max(h.left, plat.left)
                if hx > cur:
                    seg = pygame.Rect(cur, plat.y, hx - cur, plat.height)
                    seg.x -= camera_x
                    pygame.draw.rect(screen, (100, 60, 40), seg)
                cur = min(plat.right, h.right)
            # final segment
            if cur < plat.right:
                seg = pygame.Rect(cur, plat.y, plat.right - cur, plat.height)
                seg.x -= camera_x
                pygame.draw.rect(screen, (100, 60, 40), seg)
    # draw spikes
    for s in globals().get('spikes', []):
        r = s.copy()
        r.x -= camera_x
        # draw simple triangle spikes
        step = r.width // 4 if r.width >= 4 else 4
        for x in range(r.x, r.x + r.width, step):
            pygame.draw.polygon(screen, (160, 20, 20), [(x, r.y + r.height), (x + step//2, r.y), (x + step, r.y + r.height)])
    # draw jump pads
    for jp in globals().get('jump_pads', []):
        r = jp.copy()
        r.x -= camera_x
        # darker blue so the pad stands out
        pygame.draw.rect(screen, (255, 255, 0), r)

    # draw machines
    for m in machines:
        r = m.rect.copy()
        r.x -= camera_x
        # draw machine sprite if available (flip vertically when direction is up)
        if machine_img:
            img = machine_img_up if (m.direction == -1 and machine_img_up) else machine_img
            screen.blit(img, r.topleft)
        else:
            pygame.draw.rect(screen, (190, 190, 210), r)
            nozzle = (r.centerx + m.direction * 18, r.centery)
            pygame.draw.circle(screen, (160, 160, 180), nozzle, 6)
    
        # projectiles
        for p in m.projectiles:
            pr = p.rect.copy()
            pr.x -= camera_x
            pygame.draw.ellipse(screen, (240,240,200), pr)

    # draw finish flag
    if finish_rect:
        fr = finish_rect.copy()
        fr.x -= camera_x
        # enhanced flag pole (taller) and a waving banner for visibility
        pole_x = fr.x + fr.width//2 - 3
        pygame.draw.rect(screen, (80, 50, 30), (pole_x, fr.y - 10, 6, fr.height + 10))
        # waving flag
        t = pygame.time.get_ticks() / 180.0
        off = int(6 * math.sin(t))
        flag_top = fr.y + 12
        points = [
            (fr.x + 6, flag_top),
            (fr.x + fr.width + off, flag_top - 6),
            (fr.x + fr.width - 4 + off, flag_top + 12),
            (fr.x + 6, flag_top + 20)
        ]
        pygame.draw.polygon(screen, (200, 20, 20), points)
        pygame.draw.polygon(screen, (60, 30, 30), points, 2)
    # checkpoints removed from visuals/game logic

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

    # update & draw particle effects (egg loss)
    for e in list(effects):
        # update physics
        e['x'] += e['vx'] * dt * 6
        e['y'] += e['vy'] * dt * 6
        e['vy'] += GRAVITY * 0.15
        e['life'] -= 0.04 * dt
        # draw (fade by shrinking)
        if e['life'] > 0:
            r = max(1, int(e['r'] * max(0.2, e['life'])))
            col = e['color']
            pygame.draw.circle(screen, col, (int(e['x'] - camera_x), int(e['y'])), r)
        else:
            try:
                effects.remove(e)
            except ValueError:
                pass

    # HUD (lighter color for readability)
    hud_col = (245, 245, 245)
    eggs_text = font.render(f"Eggs: {player.eggs}", True, hud_col)
    score_text = font.render(f"Score: {player.score}", True, hud_col)
    level_text = font.render(f"Level: {level}", True, hud_col)
    controls_text = font.render("Arrow keys / A-D-Space = Move", True, hud_col)
    controls2_text = font.render("Shift in air = Float", True, hud_col)
    screen.blit(controls_text, (520, HEIGHT - 500))
    screen.blit(controls2_text, (670, HEIGHT - 470))
    screen.blit(eggs_text, (16, 16))
    screen.blit(score_text, (16, 48))
    screen.blit(level_text, (16, 80))

    if game_over:
        # translucent background for readability
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 150))
        screen.blit(overlay, (0, 0))
        go_text = large_font.render("Game Over", True, (255, 230, 230))
        info = font.render("Press R to restart or ESC to quit", True, (245,245,245))
        screen.blit(go_text, (WIDTH//2 - go_text.get_width()//2, HEIGHT//2 - 60))
        screen.blit(info, (WIDTH//2 - info.get_width()//2, HEIGHT//2 + 10))
    if win:
        # translucent background for readability
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 150))
        screen.blit(overlay, (0, 0))
        if globals().get('final_victory'):
            # Dutch victory message
            w_text = large_font.render("Gefeliciteerd! Je hebt alle levels voltooid!", True, (245,245,245))
            info = font.render("Druk op R om opnieuw te beginnen of ESC om af te sluiten", True, (245,245,245))
        else:
            w_text = large_font.render("Level Voltooid!", True, (245,245,245))
            info = font.render("Druk op R om door te gaan of ESC om te stoppen", True, (245,245,245))
        screen.blit(w_text, (WIDTH//2 - w_text.get_width()//2, HEIGHT//2 - 60))
        screen.blit(info, (WIDTH//2 - info.get_width()//2, HEIGHT//2 + 10))

    pygame.display.flip()

pygame.quit()
sys.exit()
