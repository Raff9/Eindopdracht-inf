import pygame

pygame.init()
color = (97, 215, 110)

# Player properties
player_width = 120
player_height = 100
player_x = 150
player_y = 350
player_speed = 3

# zwaartekracht en springen
gravity = 0.5
vertical_velocity = 0
jump_strength = -12

# Set up display
width, height = 900, 500
screen = pygame.display.set_mode((width, height))
pygame.display.set_caption("Simple Pygame Window")
clock = pygame.time.Clock()
running = True
bg_color = (153, 211, 232)
font = pygame.font.SysFont(None, 48)
achtergrond = pygame.image.load('achtergrond 3.jpg')
achtergrond = pygame.transform.scale(achtergrond, (width, height))
player = pygame.image.load('Kip.png')
player = pygame.transform.scale(player, (player_width, player_height))
text = font.render('Chicken world', True, (83, 64, 175))
text_rect = text.get_rect(center=(width // 2, height // 2))

# Hitbox van speler
playerHitbox = player.get_rect()
playerHitbox.width = 80
playerHitbox.height = 80

# Vloer
ground = pygame.Rect(0, 450, 1000, 50)

# Game loop
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    keys = pygame.key.get_pressed()

    # BEWEGEN LINKS/RECHTS
    if keys[pygame.K_a]:
        player_x -= player_speed
    if keys[pygame.K_d]:
        player_x += player_speed

    # SPRINGEN
    if keys[pygame.K_SPACE]:
        if playerHitbox.bottom >= ground.top:
            vertical_velocity = jump_strength

    # ZWAARTEKRACHT
    vertical_velocity += gravity
    player_y += vertical_velocity

    # HITBOX UPDATEN
    playerHitbox.center = (
        player_x + player_width // 2,
        player_y + player_height // 2,
    )

    # COLLISION MET DE GROND
    if playerHitbox.bottom >= ground.top:
        playerHitbox.bottom = ground.top
        # speler moet op de grond staan
        player_y = playerHitbox.top - (player_height - playerHitbox.height) / 2
        vertical_velocity = 0  # stoppen met vallen

    # TEKENEN
    screen.blit(achtergrond, (0, 0))
    screen.blit(player, (player_x, player_y))
    pygame.draw.rect(screen, (139, 69, 19), ground)
    pygame.draw.rect(screen, (255, 0, 0), playerHitbox, 2)
    screen.blit(text, text_rect)

    pygame.display.flip()
    clock.tick(60)