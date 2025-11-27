import pygame

pygame.init()

# Set up display
width, height = 800, 500
screen = pygame.display.set_mode((width, height))
pygame.display.set_caption("Simple Pygame Window")
clock = pygame.time.Clock()
running = True
bg_color = (153, 211, 232)
font = pygame.font.SysFont(None, 48)
text = font.render('Chicken world', True, (83, 64, 175))
text_rect = text.get_rect(center=(width // 2, height // 2))
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    screen.fill(bg_color)
    screen.blit(text, text_rect)
    pygame.display.flip()
    clock.tick(60)

width, height = 800, 200
color = (97, 215, 110)

# Player properties
player_width = 50
player_height = 50
player_x = 150
player_y = 150
player_x_direction = 0
player_y_direction = 0