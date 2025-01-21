import pygame
import sys

class PygameClickGame:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((600, 400))
        pygame.display.set_caption("Jogo de Clique - Pygame")
        self.clock = pygame.time.Clock()
        self.score = 0
        self.running = True

    def run(self):
        while self.running:
            self.screen.fill((0, 0, 0))  # Fundo preto
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    self.score += 1  # Incrementa a pontuação ao clicar

            # Exibe a pontuação na tela
            font = pygame.font.SysFont(None, 55)
            score_text = font.render(f"Pontuação: {self.score}", True, (255, 255, 255))
            self.screen.blit(score_text, (200, 180))

            pygame.display.flip()
            self.clock.tick(60)

        pygame.quit()
        return self.score

