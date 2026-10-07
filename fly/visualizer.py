
import pygame  # type: ignore[reportMissingImports]

class Visualizer:
    def __init__(self):
        pygame.init()

        self.screen = pygame.display.set_mode((2400, 1800))
        pygame.display.set_caption("Fly In")
        self.running = True

        self.progress = 0.0 
        self.speed = 0.01

        self.clock = pygame.time.Clock()

    def draw(self):
        self.screen.fill((30, 30, 30))

        speed = 0.01
        progress = 0.0 
        speed = 0.1

        pygame.draw.line(
            self.screen,
            "white",
            (200, 900),
            (1200, 900),
            10
        )

        pygame.draw.circle(
            self.screen,
            ("red"),
            (200, 900),
            100
        )

        pygame.draw.circle(
            self.screen,
            ("red"),
            (1200, 900),
            100
        )

        x = 200 + (1200 - 200 ) * self.progress
        pygame.draw.circle(
            self.screen,
            ("green"),
            (x, 900),
            50
        )

        if self.progress <= 1.0:
            self.progress += self.speed

        pygame.display.flip()


    def run(self):
        while self.running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
            self.draw()
            self.clock.tick(80)

        pygame.quit()


visualizer = Visualizer()
visualizer.run()