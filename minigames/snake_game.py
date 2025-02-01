import pygame
import random

class SnakeGame:
    def __init__(self):
        # Resolução fixa
        self.largura = 1280
        self.altura = 720
        # Cria a janela (modo janela fixo, sem RESIZABLE para manter a resolução)
        self.tela = pygame.display.set_mode((self.largura, self.altura))
        pygame.display.set_caption("Snake Game")
        pygame.font.init()
        pygame.init()
        self.relogio = pygame.time.Clock()
        self.fps = 15

        # Variáveis do jogo
        self.score = 0
        self.rodando = True
        self.jogo_pausado = True  # Inicia pausado

        # Configuração da cobra (tamanho aumentado)
        self.tamanho_bloco = 20  # Tamanho do bloco aumentado
        self.snake_pos = [100, 100]  # Posição inicial
        self.snake_body = [
            [100, 100],
            [80, 100],
            [60, 100]
        ]
        self.direction = "RIGHT"
        self.change_to = self.direction

        # Configuração da maçã
        self.apple_pos = self._gerar_apple()
        self.apple_spawn = True

        # Obstáculos (cada um ocupa 2x2 blocos)
        self.obstaculos = self._gerar_obstaculos(qtd=5)

        # Cores
        self.cor_fundo = (0, 0, 0)
        self.cor_apple = (255, 0, 0)
        self.cor_texto = (255, 255, 255)
        self.cor_obstaculo = (139, 69, 19)  # Marrom

        # As cores da cobra serão calculadas para criar o efeito de rastro.
        self.cor_snake_head = (0, 255, 0)
        self.cor_snake_tail = (0, 100, 0)

        # Como a resolução é fixa, a escala é 1
        self.escala = 1

    def _gerar_apple(self):
        # Gera uma nova posição para a maçã alinhada com a grade (baseada na resolução fixa)
        return [
            random.randrange(1, (self.largura // self.tamanho_bloco)) * self.tamanho_bloco,
            random.randrange(1, (self.altura // self.tamanho_bloco)) * self.tamanho_bloco
        ]

    def _gerar_obstaculos(self, qtd=5):
        obstaculos = []
        obst_width = self.tamanho_bloco * 2
        obst_height = self.tamanho_bloco * 2
        for _ in range(qtd):
            # Gera posições alinhadas à grade
            x = random.randrange(0, (self.largura - obst_width) // self.tamanho_bloco) * self.tamanho_bloco
            y = random.randrange(0, (self.altura - obst_height) // self.tamanho_bloco) * self.tamanho_bloco
            # Evita que o obstáculo apareça sobre a posição inicial da cobra
            if [x, y] in self.snake_body or [x, y] == self.apple_pos:
                continue
            obstaculos.append(pygame.Rect(x, y, obst_width, obst_height))
        return obstaculos

    def _processar_eventos(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.rodando = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.rodando = False
                # Se o jogo estiver pausado, SPACE inicia o jogo
                if event.key == pygame.K_SPACE:
                    if self.jogo_pausado:
                        self.jogo_pausado = False
                # Se o jogo não estiver pausado, processa as teclas de direção
                if not self.jogo_pausado:
                    if event.key == pygame.K_UP and self.direction != "DOWN":
                        self.change_to = "UP"
                    elif event.key == pygame.K_DOWN and self.direction != "UP":
                        self.change_to = "DOWN"
                    elif event.key == pygame.K_LEFT and self.direction != "RIGHT":
                        self.change_to = "LEFT"
                    elif event.key == pygame.K_RIGHT and self.direction != "LEFT":
                        self.change_to = "RIGHT"

    def _atualizar_estado(self):
        # Atualiza a direção
        self.direction = self.change_to

        # Atualiza a posição da cabeça da cobra
        if self.direction == "UP":
            self.snake_pos[1] -= self.tamanho_bloco
        elif self.direction == "DOWN":
            self.snake_pos[1] += self.tamanho_bloco
        elif self.direction == "LEFT":
            self.snake_pos[0] -= self.tamanho_bloco
        elif self.direction == "RIGHT":
            self.snake_pos[0] += self.tamanho_bloco

        self.snake_body.insert(0, list(self.snake_pos))
        if self.snake_pos == self.apple_pos:
            self.score += 10
            self.apple_spawn = False
        else:
            self.snake_body.pop()

        if not self.apple_spawn:
            self.apple_pos = self._gerar_apple()
            self.apple_spawn = True

    def _checar_game_over(self):
        # Checa colisão com bordas (usando a resolução fixa)
        if (self.snake_pos[0] < 0 or self.snake_pos[0] >= self.largura or
            self.snake_pos[1] < 0 or self.snake_pos[1] >= self.altura):
            return True

        # Checa colisão com o próprio corpo
        for bloco in self.snake_body[1:]:
            if self.snake_pos == bloco:
                return True

        # Checa colisão com obstáculos
        snake_head_rect = pygame.Rect(self.snake_pos[0], self.snake_pos[1], self.tamanho_bloco, self.tamanho_bloco)
        for obst in self.obstaculos:
            if snake_head_rect.colliderect(obst):
                return True
        return False

    def _get_snake_color(self, i):
        # Calcula uma cor para o segmento i, interpolando entre a cor da cabeça e da cauda
        total = len(self.snake_body) - 1
        if total <= 0:
            return self.cor_snake_head
        ratio = i / total
        r = int(self.cor_snake_head[0] * (1 - ratio) + self.cor_snake_tail[0] * ratio)
        g = int(self.cor_snake_head[1] * (1 - ratio) + self.cor_snake_tail[1] * ratio)
        b = int(self.cor_snake_head[2] * (1 - ratio) + self.cor_snake_tail[2] * ratio)
        return (r, g, b)

    def _desenhar_elementos(self):
        self.tela.fill(self.cor_fundo)

        # Desenha os obstáculos
        for obst in self.obstaculos:
            pygame.draw.rect(self.tela, self.cor_obstaculo, obst)
            pygame.draw.rect(self.tela, (0, 0, 0), obst, 1)

        # Desenha a cobra com um efeito de gradiente (rastro)
        for i, pos in enumerate(self.snake_body):
            cor = self._get_snake_color(i)
            bloco = pygame.Rect(pos[0] * self.escala, pos[1] * self.escala,
                                  self.tamanho_bloco * self.escala, self.tamanho_bloco * self.escala)
            pygame.draw.rect(self.tela, cor, bloco)
            pygame.draw.rect(self.tela, (0, 0, 0), bloco, 1)

        # Desenha a maçã
        apple_rect = pygame.Rect(self.apple_pos[0] * self.escala, self.apple_pos[1] * self.escala,
                                 self.tamanho_bloco * self.escala, self.tamanho_bloco * self.escala)
        pygame.draw.rect(self.tela, self.cor_apple, apple_rect)

        # Exibe o score
        fonte = pygame.font.SysFont(None, int(36 * self.escala))
        texto_score = fonte.render(f"Score: {self.score}", True, self.cor_texto)
        self.tela.blit(texto_score, (10, 10))

    def run(self):
        while self.rodando:
            self._processar_eventos()
            if not self.jogo_pausado:
                self._atualizar_estado()

            if self._checar_game_over():
                self.rodando = False

            self._desenhar_elementos()

            # Se o jogo estiver pausado, exibe mensagem central
            if self.jogo_pausado:
                fonte_pause = pygame.font.SysFont(None, int(48 * self.escala))
                msg = fonte_pause.render("Pressione SPACE para começar", True, self.cor_texto)
                pos_x = self.largura // 2 - msg.get_width() // 2
                pos_y = self.altura // 2 - msg.get_height() // 2
                self.tela.blit(msg, (pos_x, pos_y))

            pygame.display.flip()
            self.relogio.tick(self.fps)
        pygame.quit()
        return self.score

if __name__ == "__main__":
    jogo = SnakeGame()
    final_score = jogo.run()
    print(f"Score final: {final_score}")
