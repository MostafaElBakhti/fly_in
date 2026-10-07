
import pygame

class visualizer:
    
    pygame.init()

    # Set up the game window
    screen = pygame.display.set_mode((2400, 1800))
    pygame.display.set_caption("Hello Pygame")
    screen.fill("black")
    

    # Game loop
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

    # Quit Pygame
    pygame.quit()