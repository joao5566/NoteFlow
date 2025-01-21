
import random
import pygame
class BlockStack:
    def __init__(self):
        pygame.init()
        self.largura = 300
        self.altura = 600
        self.tela = pygame.display.set_mode((self.largura, self.altura))
        pygame.display.set_caption("Block Stack")
        self.relogio = pygame.time.Clock()
        self.score = 0
        self.rodando = True
        self.grid = [[0 for _ in range(10)] for _ in range(20)]  # Grade de 20x10 (padrão para Tetris)
        self.velocidade_inicial = 5  # Velocidade inicial (FPS)
        self.velocidade_maxima = 15  # Velocidade máxima (FPS)
        
        # Definição de cores
        self.COR_FUNDO = (0, 0, 0)
        self.COR_TETRIS = (0, 255, 0)
        self.COR_LINHA = (255, 255, 255)

        # Definindo as formas do Tetris
        self.formas = [
            [[1, 1, 1, 1]],  # Linha
            [[1, 1], [1, 1]],  # Quadrado
            [[0, 1, 0], [1, 1, 1]],  # T
            [[1, 1, 0], [0, 1, 1]],  # S
            [[0, 1, 1], [1, 1, 0]],  # Z
            [[1, 0, 0], [1, 1, 1]],  # L
            [[0, 0, 1], [1, 1, 1]],  # J
        ]
        self.current_piece = self._gerar_peca()

    def _gerar_peca(self):
        forma = random.choice(self.formas)
        return {'formato': forma, 'x': 5, 'y': 0}

    def _desenhar_peca(self, peca):
        for y, linha in enumerate(peca['formato']):
            for x, valor in enumerate(linha):
                if valor:
                    pygame.draw.rect(self.tela, self.COR_TETRIS, (peca['x'] * 30 + x * 30, peca['y'] * 30 + y * 30, 30, 30))

    def _checar_colisao(self, peca):
        for y, linha in enumerate(peca['formato']):
            for x, valor in enumerate(linha):
                if valor:
                    if peca['y'] + y >= 20 or peca['x'] + x < 0 or peca['x'] + x >= 10:
                        return True
                    if peca['y'] + y >= 0 and self.grid[peca['y'] + y][peca['x'] + x] != 0:
                        return True
        return False

    def _mover_peca(self, peca, dx, dy):
        peca['x'] += dx
        peca['y'] += dy

        if self._checar_colisao(peca):
            peca['x'] -= dx
            peca['y'] -= dy
            return False
        return True

    def _rodar_peca(self, peca):
        # Rodar a peça 90 graus no sentido horário
        peca['formato'] = [list(x) for x in zip(*peca['formato'])]  # Converte em lista
        peca['formato'] = peca['formato'][::-1]  # Depois inverte a lista
        
        if self._checar_colisao(peca):
            # Desfaz a rotação se houver colisão
            peca['formato'] = peca['formato'][::-1]  # Restaura para o estado anterior
            return False

        # Ajustar posição se a peça estiver "presa" na parede
        if peca['x'] < 0:
            peca['x'] = 0
        elif peca['x'] + len(peca['formato'][0]) > 10:
            peca['x'] = 10 - len(peca['formato'][0])

        return True

    def _limpar_linhas(self):
        for i in range(19, -1, -1):
            if all(self.grid[i]):
                self.score += 100
                self.grid.pop(i)
                self.grid.insert(0, [0] * 10)

    def _adicionar_peca_na_grade(self, peca):
        for y, linha in enumerate(peca['formato']):
            for x, valor in enumerate(linha):
                if valor:
                    grid_x = peca['x'] + x
                    grid_y = peca['y'] + y
                    if grid_x < 0 or grid_x >= 10 or grid_y >= 20:
                        return False  # Se a peça ultrapassar os limites da grade, não adiciona
                    self.grid[grid_y][grid_x] = 1  # Adiciona a peça na grade
        return True

    def _desenhar_grade(self):
        for i in range(20):
            for j in range(10):
                if self.grid[i][j]:
                    pygame.draw.rect(self.tela, self.COR_TETRIS, (j * 30, i * 30, 30, 30))
                pygame.draw.rect(self.tela, self.COR_LINHA, (j * 30, i * 30, 30, 30), 1)

    def _mostrar_game_over(self):
        font = pygame.font.Font(None, 48)
        text = font.render("Game Over", True, (255, 0, 0))
        self.tela.blit(text, (self.largura // 2 - 100, self.altura // 2))

    def _atualizar_velocidade(self):
        # Aumenta a velocidade conforme a pontuação
        nova_velocidade = self.velocidade_inicial + self.score // 200  # Aumenta 1 FPS a cada 1000 pontos
        self.velocidade = min(self.velocidade_maxima, nova_velocidade)  # Limita a velocidade máxima

    def run(self):
        while self.rodando:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.rodando = False
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_LEFT:
                        self._mover_peca(self.current_piece, -1, 0)
                    if event.key == pygame.K_RIGHT:
                        self._mover_peca(self.current_piece, 1, 0)
                    if event.key == pygame.K_DOWN:
                        self._mover_peca(self.current_piece, 0, 1)
                    if event.key == pygame.K_UP:
                        self._rodar_peca(self.current_piece)

            if not self._mover_peca(self.current_piece, 0, 1):
                self._adicionar_peca_na_grade(self.current_piece)
                self._limpar_linhas()
                self.current_piece = self._gerar_peca()

            if self._checar_colisao(self.current_piece):
                self._mostrar_game_over()  # Mostrar Game Over
                pygame.display.flip()
                pygame.time.delay(2000)  # Esperar 2 segundos antes de fechar
                self.rodando = False

            self.tela.fill(self.COR_FUNDO)
            self._desenhar_grade()
            self._desenhar_peca(self.current_piece)

            font = pygame.font.Font(None, 36)
            text = font.render(f"Score: {self.score}", True, (255, 255, 255))
            self.tela.blit(text, (10, 10))

            self._atualizar_velocidade()  # Atualiza a velocidade
            pygame.display.flip()
            self.relogio.tick(self.velocidade)  # Controla a velocidade do jogo

        pygame.quit()
        return self.score


if __name__ == "__main__":
    jogo = BlockStack()
    final_score = jogo.run()
    print(f"Score final: {final_score}")

