import pygame
import random
import math
import time

class DefesaDasFormas:
    def __init__(self):
        pygame.init()
        self.largura = 800
        self.altura = 600
        self.tela = pygame.display.set_mode((self.largura, self.altura), pygame.RESIZABLE)
        pygame.display.set_caption("Defesa das Formas")
        self.relogio = pygame.time.Clock()

        # Cores
        self.COR_FUNDO = (0, 0, 0)
        self.COR_ESTRELA = (255, 255, 0)
        self.COR_INIMIGO = (255, 0, 0)
        self.COR_CIRCULO_TORRE = (0, 255, 0)
        self.COR_TRIANGULO_TORRE = (0, 0, 255)
        self.COR_TEXTO = (255, 255, 255)
        self.COR_BOTAO = (100, 100, 100)
        self.COR_PROJETEIS = (255, 255, 255)
        self.COR_BARRA_VIDA = (255, 0, 0)
        

        # Variáveis do jogo
        self.score = 0
        self.moedas = 50  # Moedas iniciais
        self.formas = []  # Inimigos
        self.torres = []  # Torres posicionadas pelo usuário
        self.projeteis = []  # Projeteis disparados pelas torres
        self.rodando = True
        self.posicionando_torre = None
        self.vida_circulo = 100  # Vida inicial do círculo central

        # Limitação de disparos
        self.cooldown_torre = 500  # 500ms entre disparos
        self.tempo_ultimo_disparo = pygame.time.get_ticks()

        # Centro da tela e raio da estrela
        self.centro_x, self.centro_y = self.largura // 2, self.altura // 2
        self.raio_centro = 50

        # Fontes
        self.fonte_score = pygame.font.SysFont(None, 36)
        self.fonte_ajuda = pygame.font.SysFont(None, 28)

        # Preço das torres e área da loja
        self.preco_torre_circulo = 30
        self.preco_torre_triangulo = 50
        self.tamanho_loja = 100

        # Dificuldade e controle de ondas
        self.dificuldade = 1
        # Não usaremos mais a contagem automática de tempo para aumentar inimigos.
        # Agora, as ondas são iniciadas pelo jogador.
        self.wave_active = False  # Estado da onda: False = aguardando (pausa), True = onda ativa

        # Tempo para controle (opcional, pode ser usado para efeitos)
        self.tempo_inicio = pygame.time.get_ticks()

    def desenhar_estrela(self):
        pygame.draw.circle(self.tela, self.COR_ESTRELA, (self.centro_x, self.centro_y), self.raio_centro)

    def desenhar_formas(self):
        for forma in self.formas:
            pygame.draw.rect(self.tela, self.COR_INIMIGO, pygame.Rect(forma['x'], forma['y'], 30, 30))
            pygame.draw.rect(self.tela, (0, 0, 0), pygame.Rect(forma['x'], forma['y'], 30, 30), 1)

    def desenhar_torres(self):
        for torre in self.torres:
            if torre['tipo'] == 'circulo':
                pygame.draw.circle(self.tela, self.COR_CIRCULO_TORRE, (torre['x'], torre['y']), 30)
                pygame.draw.circle(self.tela, (0,0,0), (torre['x'], torre['y']), 30, 1)
            elif torre['tipo'] == 'triangulo':
                pontos = [
                    (torre['x'], torre['y'] - 30),
                    (torre['x'] - 30, torre['y'] + 30),
                    (torre['x'] + 30, torre['y'] + 30)
                ]
                pygame.draw.polygon(self.tela, self.COR_TRIANGULO_TORRE, pontos)
                pygame.draw.polygon(self.tela, (0,0,0), pontos, 1)

    def desenhar_projeteis(self):
        for proj in self.projeteis:
            pygame.draw.circle(self.tela, self.COR_PROJETEIS, (int(proj['x']), int(proj['y'])), 5)

    def desenhar_loja(self):
        # Desenha o painel da loja na parte inferior da tela
        pygame.draw.rect(self.tela, (50, 50, 50), pygame.Rect(0, self.altura - self.tamanho_loja, self.largura, self.tamanho_loja))
        # Botão para torre circular
        pygame.draw.circle(self.tela, self.COR_CIRCULO_TORRE, (50, self.altura - self.tamanho_loja + 50), 30)
        # Botão para torre triangular
        pygame.draw.polygon(self.tela, self.COR_TRIANGULO_TORRE, [(self.largura - 150, self.altura - self.tamanho_loja + 50), 
                                                                  (self.largura - 180, self.altura - self.tamanho_loja + 80),
                                                                  (self.largura - 120, self.altura - self.tamanho_loja + 80)])
        # Exibe preços e informações
        texto_circulo = self.fonte_ajuda.render(f"{self.preco_torre_circulo} moedas", True, self.COR_TEXTO)
        texto_triangulo = self.fonte_ajuda.render(f"{self.preco_torre_triangulo} moedas", True, self.COR_TEXTO)
        self.tela.blit(texto_circulo, (90, self.altura - self.tamanho_loja + 40))
        self.tela.blit(texto_triangulo, (self.largura - 170, self.altura - self.tamanho_loja + 40))
        texto_loja = self.fonte_ajuda.render(f"Loja: Círculo ({self.preco_torre_circulo}) | Triângulo ({self.preco_torre_triangulo})", True, self.COR_TEXTO)
        self.tela.blit(texto_loja, (10, self.altura - self.tamanho_loja + 120))

    def criar_forma(self):
        # Cria inimigos de forma aleatória
        tipo_inimigo = random.choice(['básico', 'rápido', 'forte', 'gigante'])
        vida_inimigo = 1 + (self.score // 30)
        if tipo_inimigo == 'básico':
            vida_inimigo = 1
        elif tipo_inimigo == 'rápido':
            vida_inimigo = 2
        elif tipo_inimigo == 'forte':
            vida_inimigo = 4
        elif tipo_inimigo == 'gigante':
            vida_inimigo = 6

        forma = {
            'x': random.choice([-30, self.largura + 30]),
            'y': random.randint(0, self.altura),
            'tipo': tipo_inimigo,
            'velocidade': random.randint(1, 3) if tipo_inimigo != 'forte' else 1,
            'vida': vida_inimigo
        }
        self.formas.append(forma)

    def verificar_colisao(self, mouse_x, mouse_y):
        # Permite "atirar" nos inimigos com o mouse
        for forma in self.formas:
            dist = math.sqrt((forma['x'] - mouse_x) ** 2 + (forma['y'] - mouse_y) ** 2)
            if dist < 20:
                forma['vida'] -= 1
                if forma['vida'] <= 0:
                    self.formas.remove(forma)
                    self.score += 3
                    self.moedas += 5
                break

    def comprar_torre(self, tipo):
        if tipo == 'circulo' and self.moedas >= self.preco_torre_circulo:
            self.moedas -= self.preco_torre_circulo
            self.posicionando_torre = 'circulo'
        elif tipo == 'triangulo' and self.moedas >= self.preco_torre_triangulo:
            self.moedas -= self.preco_torre_triangulo
            self.posicionando_torre = 'triangulo'

    def posicionar_torre(self, x, y):
        if self.posicionando_torre == 'circulo':
            torre = {'x': x, 'y': y, 'tipo': 'circulo'}
            self.torres.append(torre)
            self.posicionando_torre = None
        elif self.posicionando_torre == 'triangulo':
            torre = {'x': x, 'y': y, 'tipo': 'triangulo'}
            self.torres.append(torre)
            self.posicionando_torre = None

    def atacar(self):
        tempo_atual = pygame.time.get_ticks()
        if tempo_atual - self.tempo_ultimo_disparo >= self.cooldown_torre:
            for torre in self.torres:
                for forma in self.formas:
                    distancia = math.sqrt((torre['x'] - forma['x'])**2 + (torre['y'] - forma['y'])**2)
                    if distancia < 100:
                        direcao_x = forma['x'] - torre['x']
                        direcao_y = forma['y'] - torre['y']
                        distancia_total = math.sqrt(direcao_x ** 2 + direcao_y ** 2)
                        direcao_x /= distancia_total
                        direcao_y /= distancia_total

                        projeteis = {'x': torre['x'], 'y': torre['y'], 'dx': direcao_x * 5, 'dy': direcao_y * 5, 'alvo': forma}
                        self.projeteis.append(projeteis)
            self.tempo_ultimo_disparo = tempo_atual

    def mover_projeteis(self):
        for proj in self.projeteis[:]:
            proj['x'] += proj['dx']
            proj['y'] += proj['dy']
            dist = math.sqrt((proj['x'] - proj['alvo']['x'])**2 + (proj['y'] - proj['alvo']['y'])**2)
            if dist < 20:
                if proj['alvo'] in self.formas:
                    self.formas.remove(proj['alvo'])
                    self.projeteis.remove(proj)
                    self.score += 3
                    self.moedas += 5
                break

    def mover_inimigos(self):
        for forma in self.formas:
            direcao_x = self.centro_x - forma['x']
            direcao_y = self.centro_y - forma['y']
            distancia_total = math.sqrt(direcao_x ** 2 + direcao_y ** 2)
            direcao_x /= distancia_total
            direcao_y /= distancia_total
            forma['x'] += direcao_x * 1
            forma['y'] += direcao_y * 1
            if abs(forma['x'] - self.centro_x) < self.raio_centro and abs(forma['y'] - self.centro_y) < self.raio_centro:
                self.vida_circulo -= 5
                self.formas.remove(forma)

    def desenhar_gameover(self):
        font = pygame.font.SysFont(None, 72)
        texto_gameover = font.render("GAME OVER", True, self.COR_TEXTO)
        self.tela.blit(texto_gameover, (self.largura // 2 - texto_gameover.get_width() // 2, self.altura // 3))
        texto_score = self.fonte_score.render(f"Pontuação Final: {self.score}", True, self.COR_TEXTO)
        self.tela.blit(texto_score, (self.largura // 2 - texto_score.get_width() // 2, self.altura // 2))

    def run(self):
        BRANCO = (255, 255, 255)
        # Estado de onda: False = aguardando (pause para posicionar torres e iniciar a próxima onda)
        self.wave_active = False

        while self.rodando:
            if self.vida_circulo <= 0:
                self.desenhar_gameover()
                pygame.display.flip()
                pygame.time.delay(3000)
                break

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.rodando = False
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        self.rodando = False
                    # Compras de torres via teclado
                    if event.key == pygame.K_1:
                        self.comprar_torre('circulo')
                    if event.key == pygame.K_2:
                        self.comprar_torre('triangulo')
                    # Pressionar ENTER inicia a próxima onda se estiver pausado
                    if event.key == pygame.K_RETURN:
                        if not self.wave_active:
                            self.wave_active = True
                            # Inicia a onda com um número de inimigos baseado na dificuldade
                            for _ in range(5 + self.dificuldade):
                                self.criar_forma()
                    # Outros controles de torre podem ser adicionados aqui

                if event.type == pygame.MOUSEBUTTONDOWN:
                    mouse_x, mouse_y = pygame.mouse.get_pos()
                    # Verifica se o clique foi na área da loja
                    if 20 < mouse_x < 80 and self.altura - self.tamanho_loja + 20 < mouse_y < self.altura - self.tamanho_loja + 80:
                        self.comprar_torre('circulo')
                    elif self.largura - 150 < mouse_x < self.largura - 90 and self.altura - self.tamanho_loja + 20 < mouse_y < self.altura - self.tamanho_loja + 80:
                        self.comprar_torre('triangulo')
                    elif self.posicionando_torre:
                        self.posicionar_torre(mouse_x, mouse_y)
                    else:
                        self.verificar_colisao(mouse_x, mouse_y)

            # Se a onda estiver ativa, atualiza inimigos, projéteis e ataques
            if self.wave_active:
                for forma in self.formas:
                    # Movimenta a forma horizontalmente (para dar variação)
                    forma['x'] += forma['velocidade'] if forma['x'] < self.largura // 2 else -forma['velocidade']
                self.mover_inimigos()
                self.atacar()
                self.mover_projeteis()

                # Se todas as formas foram eliminadas, encerra a onda e aguarda o jogador iniciar a próxima
                if not self.formas:
                    self.wave_active = False
                    self.dificuldade += 1  # Aumenta a dificuldade para a próxima onda

            # --- Desenhar os elementos do jogo ---
            self.tela.fill(self.COR_FUNDO)
            self.desenhar_estrela()
            self.desenhar_formas()
            self.desenhar_torres()
            self.desenhar_projeteis()
            self.desenhar_loja()
            pygame.draw.rect(self.tela, self.COR_BARRA_VIDA, pygame.Rect(self.centro_x - 50, self.centro_y + self.raio_centro + 10, 100, 10))
            pygame.draw.rect(self.tela, (0, 255, 0), pygame.Rect(self.centro_x - 50, self.centro_y + self.raio_centro + 10, self.vida_circulo, 10))

            texto_score = self.fonte_score.render("Score: " + str(self.score), True, self.COR_TEXTO)
            texto_moedas = self.fonte_score.render("Moedas: " + str(self.moedas), True, self.COR_TEXTO)
            self.tela.blit(texto_score, (10, 10))
            self.tela.blit(texto_moedas, (10, 40))

            # Se não houver uma onda ativa, exibe a mensagem para iniciar a próxima
            if not self.wave_active:
                fonte_pause = pygame.font.SysFont(None, 36)
                msg = fonte_pause.render("Posicione suas torres e pressione ENTER para a próxima onda", True, BRANCO)
                #self.tela.blit(msg, (20, 20))
                self.tela.blit(msg, (self.largura // 2 - msg.get_width() // 2, self.altura // 2))

            pygame.display.flip()
            self.relogio.tick(60)

        pygame.quit()
        return self.score


def iniciar_jogo():
    jogo = DefesaDasFormas()
    final_score = jogo.run()
    print(f"Pontuação final: {final_score}")

if __name__ == "__main__":
    iniciar_jogo()
