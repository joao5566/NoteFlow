import pygame

class SimpleClickerGame:
    def __init__(self):
        pygame.init()
        self.tela = pygame.display.set_mode((400, 300))
        pygame.display.set_caption("Simple Clicker Game")
        self.relogio = pygame.time.Clock()
        self.score = 0
        self.rodando = True

    def run(self):
        while self.rodando:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.rodando = False
                if event.type == pygame.MOUSEBUTTONDOWN:
                    self.score += 1

            self.tela.fill((255, 255, 255))
            fonte = pygame.font.SysFont(None, 36)
            texto = fonte.render(f"Score: {self.score}", True, (0, 0, 0))
            self.tela.blit(texto, (10, 10))

            pygame.display.flip()
            self.relogio.tick(60)

        pygame.quit()
        return self.score

if __name__ == "__main__":
    jogo = SimpleClickerGame()
    final_score = jogo.run()
    print(f"Score final: {final_score}")

