import pygame
import random
import time

class MemoryGame:
    def __init__(self):
        pygame.init()
        # Tela cheia
        self.largura = pygame.display.Info().current_w
        self.altura = pygame.display.Info().current_h
        self.tela = pygame.display.set_mode((self.largura, self.altura), pygame.FULLSCREEN)
        pygame.display.set_caption("Memory Game")

        # Cores (aumentadas para 10 cores para suportar 20 cartas)
        self.BRANCO = (255, 255, 255)
        self.AZUL = (0, 0, 255)
        self.VERMELHO = (255, 0, 0)
        self.AMARELO = (255, 255, 0)
        self.VERDE = (0, 255, 0)
        self.CORES = [
            self.VERMELHO, self.AMARELO, self.VERDE, (0, 0, 255), (255, 165, 0), (128, 0, 128),
            (255, 20, 147), (0, 255, 255), (255, 99, 71), (240, 230, 140)  # Cores adicionais
        ]

        # Configurações do jogo
        self.num_pares = 10  # 20 cartas no total
        self.pares = []
        self.cartas_viradas = []      # Armazena os índices das cartas viradas
        self.cartas_removidas = []    # Armazena os pares removidos
        self.score = 0
        self.next_target = 100        # Próximo alvo de pontuação

        # Cartas
        self.largura_carta = 100
        self.altura_carta = 100
        self.cartas = []
        self.relogio = pygame.time.Clock()

        # Botão de fechar
        self.botao_fechar = pygame.Rect(self.largura - 120, 10, 100, 50)

        # Variáveis para gerenciar o delay sem bloquear o loop
        self.espera = False
        self.tempo_inicio = 0
        self.duracao_espera = 1000  # 1 segundo

        # Variável para o cheat
        self.cheat_enabled = False

    def inicializar_cartas(self):
        """Inicializa as cartas para o jogo"""
        self.pares = random.sample(self.CORES, self.num_pares) * 2  # Cria pares de cores
        random.shuffle(self.pares)  # Embaralha as cores
        self.cartas = [
            {"retangulo": pygame.Rect(
                100 + (i % 5) * (self.largura_carta + 20),
                100 + (i // 5) * (self.altura_carta + 20),
                self.largura_carta,
                self.altura_carta
            ),
             "cor": self.pares[i]} for i in range(len(self.pares))
        ]  # Cada carta tem seu retângulo e cor associados

    def desenhar_placar(self):
        """Desenha o placar com o score e o próximo alvo"""
        fonte = pygame.font.SysFont("Arial", 30)
        texto_score = fonte.render(f"Score: {self.score}", True, self.BRANCO)
        texto_alvo = fonte.render(f"Próximo Alvo: {self.next_target}", True, self.BRANCO)
        self.tela.blit(texto_score, (10, 10))
        self.tela.blit(texto_alvo, (10, 50))

    def desenhar_cartas(self):
        """Desenha as cartas na tela com uma borda preta. Revela todas as cartas se o cheat estiver ativo."""
        for i, carta in enumerate(self.cartas):
            retangulo = carta["retangulo"]
            cor = carta["cor"]

            if self.cheat_enabled:
                # Desenha todas as cartas como viradas
                pygame.draw.rect(self.tela, cor, retangulo)
            else:
                if i in self.cartas_removidas:  # Cartas removidas
                    continue

                if i in self.cartas_viradas:
                    # Desenha a carta virada com sua cor
                    pygame.draw.rect(self.tela, cor, retangulo)
                else:
                    # Desenha a carta virada para baixo (branca) com linhas pretas
                    pygame.draw.rect(self.tela, self.BRANCO, retangulo)
                    pygame.draw.line(self.tela, (0, 0, 0), (retangulo.x, retangulo.y),
                                     (retangulo.x + self.largura_carta, retangulo.y + self.altura_carta), 5)
                    pygame.draw.line(self.tela, (0, 0, 0), (retangulo.x, retangulo.y + self.altura_carta),
                                     (retangulo.x + self.largura_carta, retangulo.y), 5)

            # Desenha a borda preta ao redor da carta
            pygame.draw.rect(self.tela, (0, 0, 0), retangulo, 3)  # Espessura da borda = 3

    def desenhar_botao_fechar(self):
        """Desenha o botão de fechar"""
        pygame.draw.rect(self.tela, (255, 0, 0), self.botao_fechar)  # Botão vermelho
        fonte = pygame.font.SysFont("Arial", 24)
        texto = fonte.render("Fechar", True, self.BRANCO)
        self.tela.blit(texto, (self.botao_fechar.x + 10, self.botao_fechar.y + 10))

    def exibir_mensagem(self, texto, duracao):
        """Exibe uma mensagem centralizada na tela por uma duração específica"""
        fonte = pygame.font.SysFont("Arial", 40)
        mensagem = fonte.render(texto, True, self.BRANCO)

        # Centraliza a mensagem na tela
        rect = mensagem.get_rect(center=(self.largura // 2, self.altura // 2))

        # Preenche a tela com a cor de fundo
        self.tela.fill(self.AZUL)

        # Desenha a mensagem
        self.tela.blit(mensagem, rect)

        pygame.display.flip()

        # Aguarda a duração especificada sem bloquear o loop
        inicio = pygame.time.get_ticks()
        while pygame.time.get_ticks() - inicio < duracao:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    exit()
            self.relogio.tick(60)

    def checar_acertos(self):
        """Checa se duas cartas viradas são iguais"""
        if len(self.cartas_viradas) == 2:
            i1, i2 = self.cartas_viradas
            if self.cartas[i1]["cor"] == self.cartas[i2]["cor"]:
                # Se as cartas forem iguais, elas são removidas
                self.cartas_removidas.extend([i1, i2])
                self.score += 10  # Incrementa a pontuação por acerto
                self.cartas_viradas.clear()  # Limpa as cartas viradas para a próxima jogada

                # Verifica se a pontuação atingiu o próximo alvo
                if self.score >= self.next_target:
                    self.reiniciar_jogo()
            else:
                # Inicia o período de espera para virar as cartas de volta
                self.espera = True
                self.tempo_inicio = pygame.time.get_ticks()

    def reiniciar_jogo(self):
        """Reinicia o jogo mantendo a pontuação e incrementando o próximo alvo"""
        # Exibe uma mensagem de reinício (opcional)
        self.exibir_mensagem("Reiniciando o jogo!", 2000)  # Mostra a mensagem por 2 segundos

        # Reinicializa as cartas
        self.inicializar_cartas()

        # Limpa as listas de cartas removidas e viradas
        self.cartas_removidas.clear()
        self.cartas_viradas.clear()

        # Incrementa o próximo alvo
        self.next_target += 100

    def run(self):
        self.inicializar_cartas()
        rodando = True
        while rodando:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    return self.score  # Retorna o score final

                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_c:
                        self.cheat_enabled = not self.cheat_enabled  # Alterna o estado do cheat
                        if self.cheat_enabled:
                            self.exibir_mensagem("Cheat Ativado!", 1000)  # Mostra mensagem por 1 segundo
                        else:
                            self.exibir_mensagem("Cheat Desativado!", 1000)  # Mostra mensagem por 1 segundo

                if event.type == pygame.MOUSEBUTTONDOWN and not self.espera and not self.cheat_enabled:
                    x, y = pygame.mouse.get_pos()
                    if self.botao_fechar.collidepoint(x, y):
                        pygame.quit()  # Fechar o jogo se o botão for clicado
                        return self.score

                    # Verifica se clicou em uma carta
                    for i, carta in enumerate(self.cartas):
                        if (carta["retangulo"].collidepoint(x, y) and
                            i not in self.cartas_viradas and
                            i not in self.cartas_removidas):
                            self.cartas_viradas.append(i)  # Adiciona a carta à lista das viradas
                            if len(self.cartas_viradas) == 2:
                                self.checar_acertos()
                            break  # Evita virar múltiplas cartas com um único clique

            # Gerenciar o período de espera para virar cartas de volta
            if self.espera:
                tempo_atual = pygame.time.get_ticks()
                if tempo_atual - self.tempo_inicio >= self.duracao_espera:
                    # Virar as cartas de volta
                    self.cartas_viradas.clear()
                    self.espera = False

            # Desenho da tela
            self.tela.fill(self.AZUL)
            self.desenhar_cartas()
            self.desenhar_placar()
            self.desenhar_botao_fechar()

            pygame.display.flip()  # Atualiza a tela com o estado atual

            self.relogio.tick(60)

if __name__ == "__main__":
    jogo = MemoryGame()
    final_score = jogo.run()
    print(f"Pontuação final: {final_score}")

