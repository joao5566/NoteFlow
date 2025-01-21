import pygame
import random

# Inicialização do Pygame
pygame.init()

# Configurações da tela
largura = 600
altura = 400
tela = pygame.display.set_mode((largura, altura))
pygame.display.set_caption("Catch the Falling Objects")

# Cores
AZUL = (0, 0, 255)
VERDE = (0, 255, 0)
VERMELHO = (255, 0, 0)
BRANCO = (255, 255, 255)

# Classe para o jogo
class CatchTheFallingObjects:
    def __init__(self):
        pygame.init()
        self.largura = 600
        self.altura = 400
        self.tela = pygame.display.set_mode((self.largura, self.altura))  # Inicializa a tela
        pygame.display.set_caption("Catch the Falling Objects")

        self.relogio = pygame.time.Clock()
        self.score = 0
        self.vidas = 3  # Número de vidas do jogador

        # Outras variáveis do jogo
        self.cesta = pygame.Rect(self.largura // 2 - 50, self.altura - 50, 100, 20)
        self.velocidade_cesta = 10
        self.objetos = []
        self.velocidade_objetos = 5
        self.rodando = True

    def criar_objeto(self):
        # Criar um objeto aleatório (um círculo) com menor frequência
        if random.random() < 0.005:  # Diminui a taxa de criação de objetos
            x = random.randint(0, largura - 20)
            y = -20  # Começa fora da tela, no topo
            objeto = pygame.Rect(x, y, 20, 20)  # O objeto é um círculo
            self.objetos.append(objeto)

    def mover_objetos(self):
        for objeto in self.objetos:
            objeto.y += self.velocidade_objetos
        # Remover objetos que saem da tela
        self.objetos = [objeto for objeto in self.objetos if objeto.y < altura]

    def verificar_colisao(self):
        # Verifica se a cesta pega algum objeto
        for objeto in self.objetos[:]:
            if self.cesta.colliderect(objeto):  # Colisão com a cesta
                self.objetos.remove(objeto)  # Remove o objeto se a cesta pegar
                self.score += 1  # Incrementa a pontuação

    def verificar_falhas(self):
        # Verifica se algum objeto chegou ao fundo sem ser pego
        for objeto in self.objetos[:]:
            if objeto.y >= altura - 20:  # Se o objeto chegou ao fundo sem ser pego
                self.objetos.remove(objeto)  # Remove o objeto
                self.vidas -= 1  # O jogador perde uma vida

    def desenhar_gameover(self):
        font = pygame.font.SysFont(None, 72)
        texto_gameover = font.render("GAME OVER", True, BRANCO)
        self.tela.blit(texto_gameover, (self.largura // 2 - texto_gameover.get_width() // 2, self.altura // 3))

        texto_score = pygame.font.SysFont(None, 36).render(f"Pontuação Final: {self.score}", True, BRANCO)
        self.tela.blit(texto_score, (self.largura // 2 - texto_score.get_width() // 2, self.altura // 2))

    def run(self):
        while self.rodando:
            # Verifica se o jogador fechou a janela
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.rodando = False
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        self.rodando = False

                if event.type == pygame.MOUSEBUTTONDOWN:
                    mouse_x, mouse_y = pygame.mouse.get_pos()
                    self.verificar_colisao(mouse_x, mouse_y)

            # Movimento da cesta
            keys = pygame.key.get_pressed()
            if keys[pygame.K_LEFT] and self.cesta.left > 0:
                self.cesta.x -= self.velocidade_cesta
            if keys[pygame.K_RIGHT] and self.cesta.right < largura:
                self.cesta.x += self.velocidade_cesta

            self.criar_objeto()
            self.mover_objetos()
            self.verificar_falhas()
            self.verificar_colisao()

            # Se as vidas acabaram, exibe Game Over
            if self.vidas <= 0:
                self.desenhar_gameover()
                pygame.display.flip()
                pygame.time.wait(3000)  # Espera 3 segundos antes de retornar
                break  # Sai do loop sem fechar o Pygame ou o aplicativo principal

            # Atualiza a tela do jogo
            self.tela.fill(AZUL)

            # Desenha a cesta
            pygame.draw.rect(self.tela, VERDE, self.cesta)

            # Desenha os objetos caindo
            for objeto in self.objetos:
                pygame.draw.circle(self.tela, VERMELHO, objeto.center, 10)

            # Exibe a pontuação e as vidas
            fonte_score = pygame.font.SysFont(None, 36)
            texto_score = fonte_score.render(f"Score: {self.score}", True, BRANCO)
            texto_vidas = fonte_score.render(f"Vidas: {self.vidas}", True, BRANCO)
            self.tela.blit(texto_score, (10, 10))
            self.tela.blit(texto_vidas, (10, 40))

            pygame.display.flip()
            self.relogio.tick(60)

        # Aqui apenas sai do loop principal, não chama pygame.quit()
        pygame.quit()  # Agora chamamos o pygame.quit() para garantir que o Pygame finalize corretamente
        return self.score

# Executar o jogo
if __name__ == "__main__":
    jogo = CatchTheFallingObjects()
    final_score = jogo.run()
    print(f"Pontuação final: {final_score}")

