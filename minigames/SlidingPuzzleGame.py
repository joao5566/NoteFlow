import pygame
import random
import sys

class SlidingPuzzleGame:
    def __init__(self):
        pygame.init()
        pygame.font.init()
        self.largura = 1280
        self.altura = 720
        self.tela = pygame.display.set_mode((self.largura, self.altura))  # Janela com resolução fixa
        pygame.display.set_caption("Puzzle Deslizante")
        self.relogio = pygame.time.Clock()
        self.fps = 30

        # Estados: "menu", "game", "game_over"
        self.estado = "menu"

        # Variáveis para dificuldade; o score final é fixo conforme dificuldade.
        self.board_size = None  # Será definido pelo jogador (3, 4 ou 5)
        self.score = 0  

        # Tabuleiro (lista de listas) e posição do espaço vazio (0)
        self.board = None
        self.blank_pos = None  # (row, col)

        # Fontes
        self.fonte_menu = pygame.font.SysFont(None, 60)
        self.fonte_game = pygame.font.SysFont(None, 48)
        self.fonte_moves = pygame.font.SysFont(None, 36)

        # Paleta de cores (tons de azul e cinza suaves)
        self.cor_fundo = (200, 230, 255)    # Azul claro para o fundo
        self.cor_celula = (235, 200, 255)    # Azul bem claro para as células
        self.cor_texto = (50, 50, 50)        # Cinza escuro para o texto
        self.cor_grid = (150, 150, 200)       # Azul acinzentado para a grade

        # Tamanho das células (definido após a escolha de dificuldade)
        self.cell_size = None

    def gerar_tabuleiro_solved(self, n):
        board = [[col + row * n + 1 for col in range(n)] for row in range(n)]
        board[n-1][n-1] = 0
        return board

    def encontrar_blank(self):
        for r, row in enumerate(self.board):
            for c, value in enumerate(row):
                if value == 0:
                    return (r, c)
        return None

    def scramble_board(self, moves=1000):
        n = self.board_size
        for _ in range(moves):
            r, c = self.blank_pos
            possiveis = []
            if r > 0:
                possiveis.append((r - 1, c))
            if r < n - 1:
                possiveis.append((r + 1, c))
            if c > 0:
                possiveis.append((r, c - 1))
            if c < n - 1:
                possiveis.append((r, c + 1))
            r_swap, c_swap = random.choice(possiveis)
            self.board[r][c], self.board[r_swap][c_swap] = self.board[r_swap][c_swap], self.board[r][c]
            self.blank_pos = (r_swap, c_swap)

    def desenhar_menu(self):
        self.tela.fill(self.cor_fundo)
        titulo = self.fonte_menu.render("Puzzle Deslizante", True, self.cor_texto)
        instrucao = self.fonte_menu.render("Pressione 1: Fácil (3x3), 2: Médio (4x4), 3: Difícil (5x5)", True, self.cor_texto)
        self.tela.blit(titulo, (self.largura // 2 - titulo.get_width() // 2, self.altura // 3))
        self.tela.blit(instrucao, (self.largura // 2 - instrucao.get_width() // 2, self.altura // 2))
        pygame.display.flip()

    def processar_eventos_menu(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.estado = "sair"
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_1:
                    self.board_size = 3
                elif event.key == pygame.K_2:
                    self.board_size = 4
                elif event.key == pygame.K_3:
                    self.board_size = 5
                if self.board_size is not None:
                    self.iniciar_jogo()
                    self.estado = "game"

    def iniciar_jogo(self):
        self.cell_size = min(self.largura, self.altura) // self.board_size
        self.board = self.gerar_tabuleiro_solved(self.board_size)
        self.blank_pos = (self.board_size - 1, self.board_size - 1)
        self.score = 0
        self.scramble_board(moves=1000)

    def desenhar_tabuleiro(self):
        self.tela.fill(self.cor_fundo)
        n = self.board_size
        for r in range(n):
            for c in range(n):
                val = self.board[r][c]
                rect = pygame.Rect(c * self.cell_size, r * self.cell_size, self.cell_size, self.cell_size)
                pygame.draw.rect(self.tela, self.cor_celula, rect)
                pygame.draw.rect(self.tela, self.cor_grid, rect, 2)
                if val != 0:
                    texto = self.fonte_game.render(str(val), True, self.cor_texto)
                    self.tela.blit(texto, (c * self.cell_size + (self.cell_size - texto.get_width()) // 2,
                                             r * self.cell_size + (self.cell_size - texto.get_height()) // 2))

    def processar_eventos_game(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.estado = "sair"
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.estado = "sair"
            elif event.type == pygame.MOUSEBUTTONDOWN:
                mouse_x, mouse_y = pygame.mouse.get_pos()
                col = mouse_x // self.cell_size
                row = mouse_y // self.cell_size
                if self.adjacente_ao_blank(row, col):
                    self.mover_bloco(row, col)
                    self.score += 1

    def adjacent_positions(self, row, col):
        positions = []
        if row > 0:
            positions.append((row - 1, col))
        if row < self.board_size - 1:
            positions.append((row + 1, col))
        if col > 0:
            positions.append((row, col - 1))
        if col < self.board_size - 1:
            positions.append((row, col + 1))
        return positions

    def adjacente_ao_blank(self, row, col):
        blank_r, blank_c = self.blank_pos
        return (row, col) in self.adjacent_positions(blank_r, blank_c)

    def mover_bloco(self, row, col):
        blank_r, blank_c = self.blank_pos
        self.board[blank_r][blank_c], self.board[row][col] = self.board[row][col], self.board[blank_r][blank_c]
        self.blank_pos = (row, col)

    def is_solved(self):
        n = self.board_size
        expected = 1
        for r in range(n):
            for c in range(n):
                if r == n - 1 and c == n - 1:
                    if self.board[r][c] != 0:
                        return False
                else:
                    if self.board[r][c] != expected:
                        return False
                    expected += 1
        return True

    def desenhar_game_over(self):
        self.tela.fill(self.cor_fundo)
        msg = self.fonte_menu.render("Puzzle Resolvido!", True, self.cor_texto)
        self.tela.blit(msg, (self.largura // 2 - msg.get_width() // 2, self.altura // 2 - msg.get_height() // 2))
        pygame.display.flip()
        pygame.time.delay(3000)

    def run(self):
        while self.estado != "sair":
            if self.estado == "menu":
                self.desenhar_menu()
                self.processar_eventos_menu()
            elif self.estado == "game":
                self.processar_eventos_game()
                self.desenhar_tabuleiro()
                if self.is_solved():
                    self.estado = "game_over"
                pygame.display.flip()
                self.relogio.tick(self.fps)
            elif self.estado == "game_over":
                self.desenhar_game_over()
                if self.board_size == 3:
                    self.score = 10
                elif self.board_size == 4:
                    self.score = 20
                elif self.board_size == 5:
                    self.score = 30
                self.estado = "sair"
        pygame.quit()
        return self.score

if __name__ == "__main__":
    game = SlidingPuzzleGame()
    final_score = game.run()
    print(f"Score final: {final_score}")
