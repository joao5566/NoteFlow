import pygame
import random

class FormaTower:
    def __init__(self):
        pygame.init()
        self.tela = pygame.display.set_mode((800, 600))
        pygame.display.set_caption("Forma Tower")
        self.relogio = pygame.time.Clock()
        self.score = 0
        self.rodando = True

        # Variáveis do jogador
        self.player = pygame.Rect(400, 550, 40, 40)  # Exemplo para um quadrado
        self.velocidade = 5
        self.salto = -15  # Valor do pulo
        self.velocidade_gravidade = 0.5
        self.movimento = 0
        self.velocidade_horizontal = 5

        # Controle de movimento
        self.movendo_esquerda = False
        self.movendo_direita = False

        # Plataformas
        self.plataformas = []
        self.criar_plataformas()

        # Fim de jogo
        self.game_over = False

        # Variáveis para movimentação da câmera
        self.camera_y = 0

    def criar_plataformas(self):
        # Gera plataformas no início em posições aleatórias, sempre acima do jogador
        for i in range(5):  # Criar algumas plataformas iniciais
            x = random.randint(100, 700)
            y = random.randint(100, 500)  # Certifica-se que elas não fiquem muito baixas
            plataforma = pygame.Rect(x, y, 100, 20)
            self.plataformas.append(plataforma)
        
        # Garante que o jogador comece em cima de uma plataforma
        self.player.bottom = self.plataformas[-1].top

    def run(self):
        while self.rodando:
            self.tela.fill((0, 0, 0))  # Fundo preto

            for evento in pygame.event.get():
                if evento.type == pygame.QUIT:
                    self.rodando = False
                if evento.type == pygame.KEYDOWN:
                    if evento.key == pygame.K_UP and (self.player.bottom == 600 or self.player.bottom in [plataforma.top for plataforma in self.plataformas]):
                        self.movimento = self.salto
                    if evento.key == pygame.K_LEFT:
                        self.movendo_esquerda = True
                    if evento.key == pygame.K_RIGHT:
                        self.movendo_direita = True

                if evento.type == pygame.KEYUP:
                    if evento.key == pygame.K_LEFT:
                        self.movendo_esquerda = False
                    if evento.key == pygame.K_RIGHT:
                        self.movendo_direita = False

            # Lógica de movimento do jogador
            if self.movendo_esquerda:
                self.player.x -= self.velocidade_horizontal
            if self.movendo_direita:
                self.player.x += self.velocidade_horizontal

            # Lógica de gravidade e movimento vertical
            self.movimento += self.velocidade_gravidade
            self.player.y += self.movimento

            # Atualiza a pontuação conforme o jogador sobe
            self.score = max(self.score, self.player.top)

            # Remover plataformas que ficaram abaixo do jogador
            self.plataformas = [plataforma for plataforma in self.plataformas if plataforma.top > self.player.top - 100]

            # Gerar novas plataformas acima do jogador
            self.gerar_plataformas_acima()

            # Desenhando o jogador
            pygame.draw.rect(self.tela, (255, 0, 0), self.player)  # Cor do jogador

            # Atualizar as plataformas
            self.atualizar_plataformas()

            # Verificar colisões
            self.verificar_colisoes()

            # Exibir pontuação
            self.exibir_pontuacao()

            pygame.display.flip()
            self.relogio.tick(60)

        pygame.quit()
        return self.score

    def gerar_plataformas_acima(self):
        # Gerar plataformas acima do jogador, em posições aleatórias
        while self.player.top - self.camera_y > 100:  # Se o jogador subiu mais de 100 pixels
            x = random.randint(100, 700)
            y = self.camera_y - random.randint(50, 100)  # Coloca a plataforma mais acima
            plataforma = pygame.Rect(x, y, 100, 20)
            self.plataformas.append(plataforma)

            # Aumentar a "altura da câmera" para acompanhar a movimentação do jogador
            self.camera_y -= 100  # Ajusta a câmera para garantir que plataformas mais acima sejam geradas

    def atualizar_plataformas(self):
        for plataforma in self.plataformas:
            pygame.draw.rect(self.tela, (0, 255, 0), plataforma)  # Cor das plataformas

    def verificar_colisoes(self):
        em_cima_de_plataforma = False  # Variável para verificar se o jogador está tocando uma plataforma
        for plataforma in self.plataformas:
            # Verifica se o jogador está na posição certa para "cair" em cima da plataforma
            if self.player.colliderect(plataforma) and self.movimento > 0:
                self.movimento = 0
                self.player.bottom = plataforma.top
                em_cima_de_plataforma = True  # O jogador está tocando a plataforma
                self.score = max(self.score, self.player.top)  # Atualiza a pontuação com a altura alcançada

        # Se o jogador cair fora da tela (perde o jogo)
        if self.player.top > 600:
            self.game_over = True
            self.rodando = False

        # Permite pular apenas quando estiver tocando o solo ou uma plataforma
        if em_cima_de_plataforma or self.player.bottom == 600:
            if self.movimento >= 0:  # Garantir que o jogador não fique pulando constantemente
                self.movimento = 0

    def exibir_pontuacao(self):
        fonte = pygame.font.SysFont(None, 30)
        texto = fonte.render(f"Altura: {self.score}", True, (255, 255, 255))
        self.tela.blit(texto, (10, 10))

if __name__ == "__main__":
    jogo = FormaTower()
    final_score = jogo.run()
    print(f"Pontuação final: {final_score}")

