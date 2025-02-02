import pygame
import random
import sys

class SnakeGame:
    def __init__(self):
        # Inicialização do Pygame e fontes
        pygame.init()
        pygame.font.init()

        # Resolução interna fixa
        self.resolucao_base = (1280, 720)
        self.base_largura, self.base_altura = self.resolucao_base

        # Cria a janela redimensionável
        self.largura = 1280
        self.altura = 720
        self.tela = pygame.display.set_mode((self.largura, self.altura), pygame.RESIZABLE)
        pygame.display.set_caption("Snake Game")

        # Superfície base (resolução fixa)
        self.base_surface = pygame.Surface(self.resolucao_base)

        self.relogio = pygame.time.Clock()
        self.fps = 15

        # Variáveis do jogo
        self.score = 0
        self.rodando = True
        self.jogo_pausado = True  # Inicia pausado

        # Configuração da cobra (tamanho aumentado)
        self.tamanho_bloco = 25
        self.snake_pos = [100, 100]
        self.snake_body = [
            [100, 100],
            [75, 100],
            [50, 100]
        ]
        self.direction = "RIGHT"
        self.change_to = self.direction

        # Obstáculos (cada um ocupa 2x2 blocos)
        self.obstaculos = self._gerar_obstaculos(qtd=5)

        # Configuração da maçã (agora a maçã é gerada após os obstáculos)
        self.apple_pos = self._gerar_apple()
        self.apple_spawn = True

        # Cores
        self.cor_fundo = (0, 0, 0)
        self.cor_apple = (255, 0, 0)
        self.cor_texto = (255, 255, 255)
        self.cor_obstaculo = (139, 69, 19)

        # Cores da cobra (gradiente para rastro)
        self.cor_snake_head = (0, 255, 0)
        self.cor_snake_tail = (0, 100, 0)

        # Como a resolução é fixa, a escala é 1
        self.escala = 1

    def _gerar_apple(self):
        """Gera a posição da maçã garantindo que ela não colida com os obstáculos."""
        max_cols = self.base_largura // self.tamanho_bloco
        max_rows = self.base_altura // self.tamanho_bloco

        while True:
            x = random.randrange(0, max_cols) * self.tamanho_bloco
            y = random.randrange(0, max_rows) * self.tamanho_bloco
            apple_rect = pygame.Rect(x, y, self.tamanho_bloco, self.tamanho_bloco)
            collision = False
            # Verifica se a nova posição colide com algum obstáculo
            for obst in self.obstaculos:
                if apple_rect.colliderect(obst):
                    collision = True
                    break
            if not collision:
                return [x, y]

    def _gerar_obstaculos(self, qtd=5):
        obstaculos = []
        obst_width = self.tamanho_bloco * 2
        obst_height = self.tamanho_bloco * 2
        max_cols = self.base_largura // self.tamanho_bloco
        max_rows = self.base_altura // self.tamanho_bloco
        attempts = 0
        while len(obstaculos) < qtd and attempts < 100:
            x = random.randrange(0, max_cols - 1) * self.tamanho_bloco
            y = random.randrange(0, max_rows - 1) * self.tamanho_bloco
            # Evita que o obstáculo apareça na área da cobra ou onde a maçã (ainda não gerada) possa estar
            if [x, y] in self.snake_body:
                attempts += 1
                continue
            obst = pygame.Rect(x, y, obst_width, obst_height)
            obstaculos.append(obst)
            attempts += 1
        return obstaculos

    def _processar_eventos(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.rodando = False
            elif event.type == pygame.VIDEORESIZE:
                self.largura, self.altura = event.w, event.h
                self.tela = pygame.display.set_mode((self.largura, self.altura), pygame.RESIZABLE)
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.rodando = False
                if event.key == pygame.K_SPACE:
                    if self.jogo_pausado:
                        self.jogo_pausado = False
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
        self.direction = self.change_to

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
        if (self.snake_pos[0] < 0 or self.snake_pos[0] >= self.resolucao_base[0] or
            self.snake_pos[1] < 0 or self.snake_pos[1] >= self.resolucao_base[1]):
            return True

        for bloco in self.snake_body[1:]:
            if self.snake_pos == bloco:
                return True

        snake_head_rect = pygame.Rect(self.snake_pos[0], self.snake_pos[1],
                                      self.tamanho_bloco, self.tamanho_bloco)
        for obst in self.obstaculos:
            if snake_head_rect.colliderect(obst):
                return True
        return False

    def _get_snake_color(self, i):
        total = len(self.snake_body) - 1
        if total <= 0:
            return self.cor_snake_head
        ratio = i / total
        r = int(self.cor_snake_head[0] * (1 - ratio) + self.cor_snake_tail[0] * ratio)
        g = int(self.cor_snake_head[1] * (1 - ratio) + self.cor_snake_tail[1] * ratio)
        b = int(self.cor_snake_head[2] * (1 - ratio) + self.cor_snake_tail[2] * ratio)
        return (r, g, b)

    def _desenhar_elementos(self):
        self.base_surface.fill(self.cor_fundo)

        for obst in self.obstaculos:
            pygame.draw.rect(self.base_surface, self.cor_obstaculo, obst)
            pygame.draw.rect(self.base_surface, (0, 0, 0), obst, 1)

        for i, pos in enumerate(self.snake_body):
            cor = self._get_snake_color(i)
            bloco = pygame.Rect(pos[0], pos[1], self.tamanho_bloco, self.tamanho_bloco)
            pygame.draw.rect(self.base_surface, cor, bloco)
            pygame.draw.rect(self.base_surface, (0, 0, 0), bloco, 1)

        apple_rect = pygame.Rect(self.apple_pos[0], self.apple_pos[1],
                                 self.tamanho_bloco, self.tamanho_bloco)
        pygame.draw.rect(self.base_surface, self.cor_apple, apple_rect)

        fonte = pygame.font.SysFont(None, 36)
        texto_score = fonte.render(f"Score: {self.score}", True, self.cor_texto)
        self.base_surface.blit(texto_score, (10, 10))

        if self.jogo_pausado:
            fonte_pause = pygame.font.SysFont(None, 48)
            msg = fonte_pause.render("Pressione SPACE para começar", True, self.cor_texto)
            pos_x = self.resolucao_base[0] // 2 - msg.get_width() // 2
            pos_y = self.resolucao_base[1] // 2 - msg.get_height() // 2
            self.base_surface.blit(msg, (pos_x, pos_y))

    def run(self):
        while self.rodando:
            self._processar_eventos()
            if not self.jogo_pausado:
                self._atualizar_estado()

            if self._checar_game_over():
                self.rodando = False

            self._desenhar_elementos()

            # Calcula o fator de escala para manter a proporção da resolução base
            fator = min(self.largura / self.resolucao_base[0], self.altura / self.resolucao_base[1])
            nova_largura = int(self.resolucao_base[0] * fator)
            nova_altura = int(self.resolucao_base[1] * fator)
            tela_escalada = pygame.transform.smoothscale(self.base_surface, (nova_largura, nova_altura))

            # Calcula o offset para centralizar a superfície escalada na janela
            offset_x = (self.largura - nova_largura) // 2
            offset_y = (self.altura - nova_altura) // 2
            self.tela.fill(self.cor_fundo)
            self.tela.blit(tela_escalada, (offset_x, offset_y))

            pygame.display.flip()
            self.relogio.tick(self.fps)
        pygame.quit()
        return self.score

if __name__ == "__main__":
    jogo = SnakeGame()
    final_score = jogo.run()
    print(f"Score final: {final_score}")
