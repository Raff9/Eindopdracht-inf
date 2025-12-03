import pygame

pygame.init()
color = (97, 215, 110)

# Player properties
player_width = 120
player_height = 100
player_x = 150
player_y = 150
player_x_direction = 0
player_y_direction = 0
player_speed = 5

# player properties
keys = pygame.key.get_pressed()

if keys[pygame.K_a]:
    player_x -= player_speed
if keys[pygame.K_d]:
    player_x += player_speed
if keys[pygame.K_w]:
    player_y -= player_speed
if keys[pygame.K_s]:
    player_y += player_speed

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
playerHitbox = player.get_rect()
playerHitbox.topleft = (player_x, player_y)
text = font.render('Chicken world', True, (83, 64, 175))
text_rect = text.get_rect(center=(width // 2, height // 2))
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    screen.blit(achtergrond, (0, 0))
    screen.blit(player, (player_x, player_y))
    screen.blit(text, text_rect)
    #pygame.draw.rect(screen, (255, 255, 255), (player_x, player_y,))
    pygame.display.flip()


# Toetsen die ingedrukt worden
keys = pygame.key.get_pressed()


clock.tick(60)

# Draw player
pygame.display.update()