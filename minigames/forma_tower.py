import pygame
import random
import sys

class StackGame:
    def __init__(self):
        pygame.init()
        pygame.font.init()
        
        # Define a resolução dinâmica usando as informações do display
        info = pygame.display.Info()
        self.largura = info.current_w
        self.altura = info.current_h
        
        # Cria a tela em modo FULLSCREEN (para maximizar a janela)
        self.tela = pygame.display.set_mode((self.largura, self.altura), pygame.FULLSCREEN)
        pygame.display.set_caption("Stack!")
        self.relogio = pygame.time.Clock()
        self.fps = 30

        # Define os parâmetros dos blocos proporcionalmente à resolução
        # Usando a resolução base 1280x720 para referência
        self.altura_bloco = int(self.altura * 30 / 720)
        self.largura_bloco_inicial = int(self.largura * 300 / 1280)

        # Função para gerar uma cor aleatória
        self.random_color = lambda: (random.randint(50, 255), random.randint(50, 255), random.randint(50, 255))

        # Cria a pilha de blocos
        self.stack = []
        base_bloco = {
            "x": (self.largura - self.largura_bloco_inicial) // 2,
            "y": self.altura - self.altura_bloco,
            "largura": self.largura_bloco_inicial,
            "altura": self.altura_bloco,
            "color": self.random_color()
        }
        self.stack.append(base_bloco)

        # Bloco atual que se move horizontalmente (começa acima do bloco base)
        self.current_block = {
            "x": 0,
            "y": base_bloco["y"] - self.altura_bloco,
            "largura": self.largura_bloco_inicial,
            "altura": self.altura_bloco,
            "color": self.random_color()
        }
        self.block_direction = 1  # 1 = direita, -1 = esquerda
        self.block_speed = 8 * (self.largura / 1280)  # ajusta a velocidade proporcionalmente

        # Partículas: lista de dicionários com x, y, dx, dy e lifetime
        self.particles = []

        # Estado do jogo
        self.score = 0
        self.rodando = True
        self.jogo_pausado = True  # Inicia pausado

    def criar_particulas(self, x, y, color, quantidade=20):
        """Cria partículas no local (x, y) com uma cor base."""
        for _ in range(quantidade):
            particle = {
                "x": x + random.randint(-10, 10),
                "y": y + random.randint(-10, 10),
                "dx": random.uniform(-2, 2),
                "dy": random.uniform(-2, 2),
                "lifetime": random.randint(20, 40),
                "color": color
            }
            self.particles.append(particle)

    def atualizar_particulas(self):
        """Atualiza a posição e a vida útil das partículas."""
        for particle in self.particles[:]:
            particle["x"] += particle["dx"]
            particle["y"] += particle["dy"]
            particle["lifetime"] -= 1
            if particle["lifetime"] <= 0:
                self.particles.remove(particle)

    def desenhar_particulas(self):
        """Desenha as partículas na tela."""
        for particle in self.particles:
            pygame.draw.circle(self.tela, particle["color"], (int(particle["x"]), int(particle["y"])), 3)

    def processar_eventos(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.rodando = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.rodando = False
                if event.key == pygame.K_SPACE:
                    if self.jogo_pausado:
                        self.jogo_pausado = False
                    else:
                        self.drop_block()

    def drop_block(self):
        """Quando o bloco é 'droppado', calcula a sobreposição com o bloco anterior.
           Se não houver sobreposição, o jogo termina; caso contrário, corta o excedente,
           gera partículas e prepara o próximo bloco."""
        last_block = self.stack[-1]
        overlap_start = max(last_block["x"], self.current_block["x"])
        overlap_end = min(last_block["x"] + last_block["largura"],
                          self.current_block["x"] + self.current_block["largura"])
        overlap = overlap_end - overlap_start

        if overlap <= 0:
            # Sem sobreposição: fim do jogo
            self.rodando = False
            return

        # Cria partículas no local do drop
        self.criar_particulas(self.current_block["x"] + self.current_block["largura"] // 2,
                               self.current_block["y"] + self.current_block["altura"] // 2,
                               self.current_block["color"])

        # Atualiza o bloco atual com a área de sobreposição
        self.current_block["x"] = overlap_start
        self.current_block["largura"] = overlap

        # Adiciona o bloco atual à pilha
        self.stack.append(self.current_block.copy())
        self.score += 1

        # Prepara o próximo bloco, que se inicia na extremidade esquerda e acima do bloco atual
        new_y = self.current_block["y"] - self.altura_bloco
        self.current_block = {
            "x": 0,
            "y": new_y,
            "largura": overlap,
            "altura": self.altura_bloco,
            "color": self.random_color()
        }
        # Aumenta a velocidade para dificultar (ajustada proporcionalmente)
        self.block_speed = min(self.block_speed + 0.5 * (self.largura / 1280), 20 * (self.largura / 1280))
        # Reinicia a direção para a direita
        self.block_direction = 1

        # Atualiza a "câmera" se necessário
        self.atualizar_camera()

    def atualizar_camera(self):
        """Se o bloco atual estiver muito próximo do topo, desloca toda a pilha para baixo."""
        threshold = 100 * (self.altura / 720)
        if self.current_block["y"] < threshold:
            desloc = threshold - self.current_block["y"]
            for bloco in self.stack:
                bloco["y"] += desloc
            self.current_block["y"] += desloc

    def atualizar_bloco(self):
        # Move o bloco atual horizontalmente
        self.current_block["x"] += self.block_direction * self.block_speed
        # Inverte a direção se atingir as bordas da janela
        if self.current_block["x"] < 0:
            self.current_block["x"] = 0
            self.block_direction = 1
        elif self.current_block["x"] + self.current_block["largura"] > self.largura:
            self.current_block["x"] = self.largura - self.current_block["largura"]
            self.block_direction = -1

    def desenhar_elementos(self):
        self.tela.fill((30, 30, 30))
        # Desenha a pilha de blocos
        for bloco in self.stack:
            pygame.draw.rect(self.tela, bloco["color"],
                             (bloco["x"], bloco["y"], bloco["largura"], bloco["altura"]))
            pygame.draw.rect(self.tela, (0, 0, 0),
                             (bloco["x"], bloco["y"], bloco["largura"], bloco["altura"]), 2)

        # Desenha o bloco atual
        pygame.draw.rect(self.tela, self.current_block["color"],
                         (self.current_block["x"], self.current_block["y"],
                          self.current_block["largura"], self.current_block["altura"]))
        pygame.draw.rect(self.tela, (0, 0, 0),
                         (self.current_block["x"], self.current_block["y"],
                          self.current_block["largura"], self.current_block["altura"]), 2)

        # Desenha partículas
        self.desenhar_particulas()

        # Exibe o score
        fonte = pygame.font.SysFont(None, int(48 * (self.largura / 1280)))
        texto_score = fonte.render(f"Score: {self.score}", True, self.cor_texto)
        self.tela.blit(texto_score, (10, 10))

    def run(self):
        while self.rodando:
            self.processar_eventos()
            if not self.jogo_pausado:
                self.atualizar_bloco()
            # Atualiza a câmera se necessário
            self.atualizar_camera()

            # Atualiza partículas
            self.atualizar_particulas()

            self.desenhar_elementos()

            # Se o jogo estiver pausado, exibe mensagem central
            if self.jogo_pausado:
                fonte_pause = pygame.font.SysFont(None, int(48 * (self.largura / 1280)))
                msg = fonte_pause.render("Pressione SPACE para começar", True, self.cor_texto)
                pos_x = self.largura // 2 - msg.get_width() // 2
                pos_y = self.altura // 2 - msg.get_height() // 2
                self.tela.blit(msg, (pos_x, pos_y))

            pygame.display.flip()
            self.relogio.tick(self.fps)
        pygame.quit()
        return self.score

    @property
    def cor_texto(self):
        return (255, 255, 255)

if __name__ == "__main__":
    game = StackGame()
    final_score = game.run()
    print(f"Score final: {final_score}")
