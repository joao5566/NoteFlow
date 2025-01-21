import pygame
import random

# Configurações principais
tela_largura = 400
tela_altura = 600
fps = 60

# Cores
AZUL_CLARO = (135, 206, 250)
VERDE = (34, 139, 34)

# Classe do Pet
class Pet:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.velocidade = 0
        self.gravidade = 0.5
        self.salto_forca = -10

    def atualizar(self):
        self.velocidade += self.gravidade
        self.y += self.velocidade

        # Limita a queda
        if self.y > tela_altura - 40:
            self.y = tela_altura - 40
            self.velocidade = 0

    def pular(self):
        self.velocidade = self.salto_forca

    def desenhar(self, tela):
        surface = pygame.Surface((40, 40))
        surface.fill(VERDE)
        tela.blit(surface, (self.x, self.y))

# Classe dos Obstáculos
class Obstaculo:
    def __init__(self, x):
        self.x = x
        self.altura = random.randint(150, 450)
        self.largura = 60
        self.espaco = 150
        self.velocidade = 5

    def atualizar(self):
        self.x -= self.velocidade

    def desenhar(self, tela):
        pygame.draw.rect(tela, VERDE, (self.x, 0, self.largura, self.altura))
        pygame.draw.rect(tela, VERDE, (self.x, self.altura + self.espaco, self.largura, tela_altura))

    def colidir(self, pet):
        if pet.x + 40 > self.x and pet.x < self.x + self.largura:
            if pet.y < self.altura or pet.y + 40 > self.altura + self.espaco:
                return True
        return False

# Classe principal do jogo
class FlappyPetGame:
    def __init__(self):
        pygame.init()
        self.tela = pygame.display.set_mode((tela_largura, tela_altura))
        pygame.display.set_caption("Flappy Pet")
        self.relogio = pygame.time.Clock()
        self.pet = Pet(50, tela_altura // 2)
        self.obstaculos = [Obstaculo(tela_largura)]
        self.score = 0
        self.rodando = True
        self.jogo_pausado = True

    def run(self):
        while self.rodando:
            self.tela.fill(AZUL_CLARO)

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.rodando = False
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_SPACE:
                        if self.jogo_pausado:
                            self.jogo_pausado = False  # Começa o jogo ao pressionar espaço
                        else:
                            self.pet.pular()

            if not self.jogo_pausado:
                # Atualização do pet
                self.pet.atualizar()
                self.pet.desenhar(self.tela)

                # Atualização dos obstáculos
                if len(self.obstaculos) > 0 and self.obstaculos[0].x < -60:
                    self.obstaculos.pop(0)
                    self.obstaculos.append(Obstaculo(tela_largura))
                    self.score += 1

                for obstaculo in self.obstaculos:
                    obstaculo.atualizar()
                    obstaculo.desenhar(self.tela)
                    if obstaculo.colidir(self.pet):
                        self.rodando = False

                # Exibir score
                fonte = pygame.font.SysFont(None, 36)
                score_texto = fonte.render(f"Score: {self.score}", True, (0, 0, 0))
                self.tela.blit(score_texto, (10, 10))
            else:
                # Exibir mensagem de início quando o jogo estiver pausado
                fonte = pygame.font.SysFont(None, 48)
                start_texto = fonte.render("Pressione ESPAÇO para começar", True, (0, 0, 0))
                self.tela.blit(start_texto, (tela_largura // 2 - start_texto.get_width() // 2, tela_altura // 2 - start_texto.get_height() // 2))

            pygame.display.flip()
            self.relogio.tick(fps)

        pygame.quit()
        return self.score

if __name__ == "__main__":
    jogo = FlappyPetGame()
    final_score = jogo.run()
    print(f"Score final: {final_score}")

