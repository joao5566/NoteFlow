import random
import pygame

# Configurações iniciais
tela_largura_inicial = 400
tela_altura_inicial = 600
fps = 60
bloco_tamanho = 30  # Tamanho base dos blocos

# Cores
AZUL_CLARO = (135, 206, 250)
VERDE = (34, 139, 34)
BRANCO = (255, 255, 255)
CINZA = (100, 100, 100)

# Classe do Pet
class Pet:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.velocidade = 0
        self.gravidade = 0.5
        self.salto_forca = -10

    def atualizar(self):
        self.velocidade += self.gravidade
        self.y += self.velocidade
        # Impede que o pet ultrapasse o fundo da tela
        if self.y > tela_altura_inicial - 40:
            self.y = tela_altura_inicial - 40
            self.velocidade = 0

    def pular(self):
        self.velocidade = self.salto_forca

    def desenhar(self, tela, escala):
        tamanho = int(40 * escala)
        surface = pygame.Surface((tamanho, tamanho))
        surface.fill(VERDE)
        tela.blit(surface, (int(self.x * escala), int(self.y * escala)))

# Classe dos Obstáculos
class Obstaculo:
    def __init__(self, x, bloco_tam, espaco):
        self.x = x
        self.largura = bloco_tam * 2  # Obstáculo com 2 blocos de largura
        self.altura = random.randint(bloco_tam * 5, bloco_tam * 15)
        self.espaco = espaco  # Espaço entre os obstáculos superior e inferior
        self.velocidade = 5

    def atualizar(self):
        self.x -= self.velocidade

    def desenhar(self, tela, escala):
        # Obstáculo superior
        rect_superior = pygame.Rect(int(self.x * escala), 0, int(self.largura * escala), int(self.altura * escala))
        pygame.draw.rect(tela, VERDE, rect_superior)
        pygame.draw.rect(tela, CINZA, rect_superior, 1)
        # Obstáculo inferior
        rect_inferior = pygame.Rect(
            int(self.x * escala), 
            int((self.altura + self.espaco) * escala), 
            int(self.largura * escala), 
            tela_altura_atual - int((self.altura + self.espaco) * escala)
        )
        pygame.draw.rect(tela, VERDE, rect_inferior)
        pygame.draw.rect(tela, CINZA, rect_inferior, 1)

    def colidir(self, pet, escala):
        tamanho = int(40 * escala)
        pet_rect = pygame.Rect(int(pet.x * escala), int(pet.y * escala), tamanho, tamanho)
        obst_rect_superior = pygame.Rect(int(self.x * escala), 0, int(self.largura * escala), int(self.altura * escala))
        obst_rect_inferior = pygame.Rect(int(self.x * escala), int((self.altura + self.espaco) * escala), int(self.largura * escala), tela_altura_atual - int((self.altura + self.espaco) * escala))
        return pet_rect.colliderect(obst_rect_superior) or pet_rect.colliderect(obst_rect_inferior)

# Variáveis globais para dimensões atuais (dinâmicas)
tela_largura_atual = tela_largura_inicial
tela_altura_atual = tela_altura_inicial

# Classe principal do jogo
class FlappyPetGame:
    def __init__(self, fullscreen=False):
        pygame.init()
        if fullscreen:
            info = pygame.display.Info()
            tela_largura_max = info.current_w
            tela_altura_max = info.current_h
            self.tela = pygame.display.set_mode((tela_largura_max, tela_altura_max), pygame.RESIZABLE)
        else:
            self.tela = pygame.display.set_mode((tela_largura_inicial, tela_altura_inicial), pygame.RESIZABLE)
        pygame.display.set_caption("Flappy Pet")
        self.relogio = pygame.time.Clock()
        self.pet = Pet(50, tela_altura_inicial // 2)
        self.obstaculos = [Obstaculo(tela_largura_inicial, bloco_tamanho, 150)]
        self.score = 0
        self.rodando = True
        self.jogo_pausado = True
        self.velocidade = 5
        self.escala = 1  # Escala inicial

    def atualizar_tamanho(self, nova_largura, nova_altura):
        global tela_largura_atual, tela_altura_atual
        tela_largura_atual = nova_largura
        tela_altura_atual = nova_altura
        # Atualiza a escala com base na largura inicial
        self.escala = nova_largura / tela_largura_inicial

    def run(self):
        while self.rodando:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.rodando = False
                elif event.type == pygame.VIDEORESIZE:
                    self.atualizar_tamanho(event.w, event.h)
                    self.tela = pygame.display.set_mode((event.w, event.h), pygame.RESIZABLE)
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_SPACE:
                        if self.jogo_pausado:
                            self.jogo_pausado = False
                        else:
                            self.pet.pular()

            self.tela.fill(AZUL_CLARO)

            if not self.jogo_pausado:
                self.pet.atualizar()
                self.pet.desenhar(self.tela, self.escala)

                # Remover obstáculo se sair da tela e incrementar score
                if self.obstaculos and self.obstaculos[0].x < -bloco_tamanho * 2:
                    self.obstaculos.pop(0)
                    self.obstaculos.append(Obstaculo(tela_largura_inicial, bloco_tamanho, 150))
                    self.score += 1

                for obstaculo in self.obstaculos:
                    obstaculo.atualizar()
                    obstaculo.desenhar(self.tela, self.escala)
                    if obstaculo.colidir(self.pet, self.escala):
                        self.rodando = False

                fonte = pygame.font.SysFont(None, int(36 * self.escala))
                score_texto = fonte.render(f"Score: {self.score}", True, BRANCO)
                self.tela.blit(score_texto, (10, 10))
            else:
                fonte = pygame.font.SysFont(None, int(48 * self.escala))
                start_texto = fonte.render("Pressione ESPAÇO para começar", True, (0, 0, 0))
                self.tela.blit(start_texto, ((tela_largura_atual - start_texto.get_width()) // 2, (tela_altura_atual - start_texto.get_height()) // 2))

            pygame.display.flip()
            self.relogio.tick(fps)

        pygame.quit()
        return self.score

if __name__ == "__main__":
    # Para iniciar em tela cheia, defina fullscreen=True
    jogo = FlappyPetGame(fullscreen=False)
    final_score = jogo.run()
    print(f"Score final: {final_score}")
