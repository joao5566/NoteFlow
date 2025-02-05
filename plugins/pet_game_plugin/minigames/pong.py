import pygame
import random  # Adiciona a importação do módulo random
# Classe do jogo Pong
class PongGame:
    def __init__(self):
        pygame.init()
        self.largura = 600
        self.altura = 400
        self.tela = pygame.display.set_mode((self.largura, self.altura))
        pygame.display.set_caption("Pong: Player vs. Machine")

        # Cores
        self.BRANCO = (255, 255, 255)
        self.AZUL = (0, 0, 255)

        # Variáveis do jogo
        self.largura_pala = 10
        self.altura_pala = 60
        self.largura_bola = 15
        self.velocidade_pala = 10
        self.velocidade_bola_x = 3.7  # Reduzindo a velocidade da bola
        self.velocidade_bola_y = 3.5  # Reduzindo a velocidade da bola
        self.pontos_jogador = 0
        self.pontos_maquina = 0

        # Paddles e bola
        self.pala_jogador = pygame.Rect(30, self.altura // 2 - self.altura_pala // 2, self.largura_pala, self.altura_pala)
        self.pala_maquina = pygame.Rect(self.largura - 30 - self.largura_pala, self.altura // 2 - self.altura_pala // 2, self.largura_pala, self.altura_pala)
        self.bola = pygame.Rect(self.largura // 2 - self.largura_bola // 2, self.altura // 2 - self.largura_bola // 2, self.largura_bola, self.largura_bola)

        # Lista para armazenar as sombras da bola
        self.rastro_bola = []

        self.relogio = pygame.time.Clock()

    def desenhar_placar(self):
        fonte = pygame.font.SysFont("Arial", 30)
        texto_pontos = fonte.render(f"{self.pontos_jogador} | {self.pontos_maquina}", True, self.BRANCO)
        self.tela.blit(texto_pontos, (self.largura // 2 - texto_pontos.get_width() // 2, 20))

    def mover_bola(self):
        # Adiciona o rastro da bola (sombras)
        if len(self.rastro_bola) > 10:  # Mantém um limite no tamanho do rastro
            self.rastro_bola.pop(0)
        self.rastro_bola.append(self.bola.center)

        self.bola.x += self.velocidade_bola_x
        self.bola.y += self.velocidade_bola_y

        # Verifica colisão com o topo e fundo
        if self.bola.top <= 0 or self.bola.bottom >= self.altura:
            self.velocidade_bola_y = -self.velocidade_bola_y

        # Verifica colisão com a pala do jogador
        if self.bola.colliderect(self.pala_jogador):
            self.velocidade_bola_x = -self.velocidade_bola_x

        # Verifica colisão com a pala da máquina
        if self.bola.colliderect(self.pala_maquina):
            self.velocidade_bola_x = -self.velocidade_bola_x

        # Verifica se a bola saiu da tela (pontos)
        if self.bola.left <= 0:  # Se a bola passar pela pala do jogador
            self.pontos_maquina += 1
            self.bola.center = (self.largura // 2, self.altura // 2)
            self.velocidade_bola_x = -self.velocidade_bola_x  # Bola vai para a máquina
        elif self.bola.right >= self.largura:  # Se a bola passar pela pala da máquina
            self.pontos_jogador += 1
            self.bola.center = (self.largura // 2, self.altura // 2)
            self.velocidade_bola_x = -self.velocidade_bola_x  # Bola vai para o jogador

    def mover_pala_maquina(self):
        # A máquina vai tentar se mover para a bola, mas com um fator aleatório
        erro = random.randint(-1, 1)  # Adiciona um pequeno erro no movimento da máquina
        if self.bola.centery < self.pala_maquina.centery:
            self.pala_maquina.y -= 3 + erro  # Movendo com um erro
        elif self.bola.centery > self.pala_maquina.centery:
            self.pala_maquina.y += 3 + erro  # Movendo com um erro

        # Evita que a pala da máquina ultrapasse a tela
        if self.pala_maquina.top < 0:
            self.pala_maquina.top = 0
        elif self.pala_maquina.bottom > self.altura:
            self.pala_maquina.bottom = self.altura

    def mover_pala_jogador(self):
        keys = pygame.key.get_pressed()

        if keys[pygame.K_UP] and self.pala_jogador.top > 0:
            self.pala_jogador.y -= self.velocidade_pala
        if keys[pygame.K_DOWN] and self.pala_jogador.bottom < self.altura:
            self.pala_jogador.y += self.velocidade_pala

    def desenhar_rastro(self):
        for i in range(len(self.rastro_bola) - 1):
            pygame.draw.circle(self.tela, (255, 255, 255, int(255 * (i / len(self.rastro_bola)))), self.rastro_bola[i], 5)

    def run(self):
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    return self.pontos_jogador  # Retorna o score

            # Mover as palas
            self.mover_pala_jogador()
            self.mover_pala_maquina()

            # Mover a bola
            self.mover_bola()

            # Desenhar a tela
            self.tela.fill(self.AZUL)
            pygame.draw.rect(self.tela, self.BRANCO, self.pala_jogador)
            pygame.draw.rect(self.tela, self.BRANCO, self.pala_maquina)
            pygame.draw.ellipse(self.tela, self.BRANCO, self.bola)
            self.desenhar_rastro()  # Desenha o rastro da bola
            self.desenhar_placar()

            pygame.display.flip()
            self.relogio.tick(60)

if __name__ == "__main__":
    jogo = PongGame()
    score = jogo.run()
    print(f"Pontuação final: {score}")

