import pygame
import random
import sys

class StackGame:
    def __init__(self):
        pygame.init()
        pygame.font.init()
        
        # Resolução base (para referência e escala)
        self.base_largura = 1280
        self.base_altura = 720
        
        # Inicialmente, usa a resolução base
        self.largura = self.base_largura
        self.altura = self.base_altura
        
        # Cria a tela em modo janela, redimensionável (não full screen)
        self.tela = pygame.display.set_mode((self.largura, self.altura), pygame.RESIZABLE)
        pygame.display.set_caption("Stack!")
        self.relogio = pygame.time.Clock()
        self.fps = 30

        # Define os parâmetros dos blocos com base na resolução
        self.altura_bloco = int(self.altura * 30 / self.base_altura)
        self.largura_bloco_inicial = int(self.largura * 300 / self.base_largura)

        # Função para gerar uma cor aleatória
        self.random_color = lambda: (random.randint(50, 255),
                                     random.randint(50, 255),
                                     random.randint(50, 255))

        # Cria a pilha de blocos: o bloco base
        self.stack = []
        base_bloco = {
            "x": (self.largura - self.largura_bloco_inicial) // 2,
            "y": self.altura - self.altura_bloco,
            "largura": self.largura_bloco_inicial,
            "altura": self.altura_bloco,
            "color": self.random_color()
        }
        self.stack.append(base_bloco)

        # Bloco atual que se move horizontalmente (inicia acima do bloco base)
        self.current_block = {
            "x": 0,
            "y": base_bloco["y"] - self.altura_bloco,
            "largura": self.largura_bloco_inicial,
            "altura": self.altura_bloco,
            "color": self.random_color()
        }
        self.block_direction = 1  # 1 = direita, -1 = esquerda
        self.block_speed = 8 * (self.largura / self.base_largura)  # velocidade proporcional

        # Partículas
        self.particles = []

        # Estado do jogo
        self.score = 0
        self.rodando = True
        self.jogo_pausado = True  # inicia pausado

    def criar_particulas(self, x, y, color, quantidade=20):
        """Cria partículas no local (x, y) com a cor informada."""
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
            pygame.draw.circle(self.tela, particle["color"],
                               (int(particle["x"]), int(particle["y"])), 3)

    def processar_eventos(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.rodando = False
            elif event.type == pygame.VIDEORESIZE:
                # Salva a resolução antiga para calcular o fator de escala
                old_largura = self.largura
                old_altura = self.altura
                # Atualiza para a nova resolução
                self.largura, self.altura = event.w, event.h
                self.tela = pygame.display.set_mode((self.largura, self.altura), pygame.RESIZABLE)
                # Fatores de escala
                scale_x = self.largura / old_largura
                scale_y = self.altura / old_altura
                # Atualiza os blocos já existentes na pilha
                for bloco in self.stack:
                    bloco["x"] = int(bloco["x"] * scale_x)
                    bloco["y"] = int(bloco["y"] * scale_y)
                    bloco["largura"] = int(bloco["largura"] * scale_x)
                    bloco["altura"] = int(bloco["altura"] * scale_y)
                # Atualiza o bloco atual
                self.current_block["x"] = int(self.current_block["x"] * scale_x)
                self.current_block["y"] = int(self.current_block["y"] * scale_y)
                self.current_block["largura"] = int(self.current_block["largura"] * scale_x)
                self.current_block["altura"] = int(self.current_block["altura"] * scale_y)
                # Recalcula os parâmetros de escala dos blocos
                self.altura_bloco = int(self.altura * 30 / self.base_altura)
                self.largura_bloco_inicial = int(self.largura * 300 / self.base_largura)
                # Atualiza a velocidade do bloco atual proporcionalmente
                self.block_speed = 8 * (self.largura / self.base_largura)
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.rodando = False
                if event.key == pygame.K_SPACE:
                    if self.jogo_pausado:
                        self.jogo_pausado = False
                    else:
                        self.drop_block()

    def drop_block(self):
        """Calcula a sobreposição entre o bloco atual e o bloco anterior.
           Se não houver sobreposição, termina o jogo; senão, gera partículas e prepara o próximo bloco."""
        last_block = self.stack[-1]
        overlap_start = max(last_block["x"], self.current_block["x"])
        overlap_end = min(last_block["x"] + last_block["largura"],
                          self.current_block["x"] + self.current_block["largura"])
        overlap = overlap_end - overlap_start

        if overlap <= 0:
            self.rodando = False
            return

        # Cria partículas na posição do bloco atual
        self.criar_particulas(self.current_block["x"] + self.current_block["largura"] // 2,
                               self.current_block["y"] + self.current_block["altura"] // 2,
                               self.current_block["color"])

        # Atualiza o bloco atual com a área de sobreposição
        self.current_block["x"] = overlap_start
        self.current_block["largura"] = overlap

        # Adiciona o bloco atual à pilha
        self.stack.append(self.current_block.copy())
        self.score += 1

        # Prepara o próximo bloco, iniciando à esquerda e acima do bloco atual
        new_y = self.current_block["y"] - self.altura_bloco
        self.current_block = {
            "x": 0,
            "y": new_y,
            "largura": overlap,
            "altura": self.altura_bloco,
            "color": self.random_color()
        }
        # Aumenta a velocidade para dificultar
        self.block_speed = min(self.block_speed + 0.5 * (self.largura / self.base_largura),
                               20 * (self.largura / self.base_largura))
        self.block_direction = 1
        self.atualizar_camera()

    def atualizar_camera(self):
        """Desloca a pilha de blocos para baixo se o bloco atual estiver muito próximo do topo."""
        threshold = 100 * (self.altura / self.base_altura)
        if self.current_block["y"] < threshold:
            desloc = threshold - self.current_block["y"]
            for bloco in self.stack:
                bloco["y"] += desloc
            self.current_block["y"] += desloc

    def atualizar_bloco(self):
        # Move o bloco atual horizontalmente
        self.current_block["x"] += self.block_direction * self.block_speed
        # Inverte a direção ao atingir as bordas
        if self.current_block["x"] < 0:
            self.current_block["x"] = 0
            self.block_direction = 1
        elif self.current_block["x"] + self.current_block["largura"] > self.largura:
            self.current_block["x"] = self.largura - self.current_block["largura"]
            self.block_direction = -1

    def desenhar_elementos(self):
        self.tela.fill((30, 30, 30))
        for bloco in self.stack:
            pygame.draw.rect(self.tela, bloco["color"],
                             (bloco["x"], bloco["y"], bloco["largura"], bloco["altura"]))
            pygame.draw.rect(self.tela, (0, 0, 0),
                             (bloco["x"], bloco["y"], bloco["largura"], bloco["altura"]), 2)

        pygame.draw.rect(self.tela, self.current_block["color"],
                         (self.current_block["x"], self.current_block["y"],
                          self.current_block["largura"], self.current_block["altura"]))
        pygame.draw.rect(self.tela, (0, 0, 0),
                         (self.current_block["x"], self.current_block["y"],
                          self.current_block["largura"], self.current_block["altura"]), 2)

        self.desenhar_particulas()
        fonte = pygame.font.SysFont(None, int(48 * (self.largura / self.base_largura)))
        texto_score = fonte.render(f"Score: {self.score}", True, self.cor_texto)
        self.tela.blit(texto_score, (10, 10))

    def run(self):
        while self.rodando:
            self.processar_eventos()
            if not self.jogo_pausado:
                self.atualizar_bloco()
            self.atualizar_camera()
            self.atualizar_particulas()
            self.desenhar_elementos()
            if self.jogo_pausado:
                fonte_pause = pygame.font.SysFont(None, int(48 * (self.largura / self.base_largura)))
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
