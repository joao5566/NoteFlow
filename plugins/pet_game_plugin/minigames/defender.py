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
        self.COR_RESISTENTE = (128, 0, 128)   # Inimigos resistentes (roxo)
        self.COR_ROSA = (255, 105, 180)        # Inimigo rosa
        self.COR_CIRCULO_TORRE = (0, 255, 0)     # Torre verde
        self.COR_TRIANGULO_TORRE = (0, 0, 255)    # Torre azul
        self.COR_SUPER_TORRE = (255, 215, 0)      # Torre super
        self.COR_UPGRADE = (255, 165, 0)          # Upgrade para torre azul (laranja)
        self.COR_CURA = (0, 255, 255)             # Item de cura (ciano)
        self.COR_TEXTO = (220, 20, 60)
        self.COR_BOTAO = (100, 100, 100)
        self.COR_PROJETEIS = (255, 255, 255)
        self.COR_BARRA_VIDA = (255, 0, 0)
        
        # Variáveis do jogo
        self.score = 0
        self.moedas = 500
        self.formas = []         # Lista de inimigos
        self.torres = []         # Cada torre tem 15 de vida
        self.projeteis = []
        self.rodando = True
        self.posicionando_torre = None
        self.vida_circulo = 100

        # Efeitos extras
        self.explosions = []
        self.powerups = []

        self.cooldown_torre = 500
        self.tempo_ultimo_disparo = pygame.time.get_ticks()

        self.centro_x, self.centro_y = self.largura // 2, self.altura // 2
        self.raio_centro = 50

        # Fontes
        self.fonte_score = pygame.font.SysFont(None, 36)
        self.fonte_ajuda = pygame.font.SysFont(None, 28)
        self.fonte_wave = pygame.font.SysFont(None, 48)
        self.fonte_mensagem = pygame.font.SysFont(None, 32)
        self.fonte_tooltip = pygame.font.SysFont(None, 24)

        # Preços e loja
        self.preco_torre_circulo = 30
        self.preco_torre_triangulo = 100
        self.preco_torre_super = 500
        self.preco_cura = 300
        self.preco_upgrade_azul = 100  # Preço inicial do upgrade para torre azul
        self.tamanho_loja = 100

        # Botões da loja (5 botões: torre verde, torre azul, torre super, item de cura, upgrade azul)
        self.botao_verde = pygame.Rect(20, self.altura - self.tamanho_loja + 20, 60, 60)
        self.botao_azul  = pygame.Rect(100, self.altura - self.tamanho_loja + 20, 60, 60)
        self.botao_super = pygame.Rect(180, self.altura - self.tamanho_loja + 20, 60, 60)
        self.botao_cura  = pygame.Rect(260, self.altura - self.tamanho_loja + 20, 60, 60)
        self.botao_upgrade = pygame.Rect(340, self.altura - self.tamanho_loja + 20, 60, 60)

        # Dificuldade e controle de ondas
        self.dificuldade = 1
        self.wave_active = False

        self.tempo_inicio = pygame.time.get_ticks()
        self.ultimo_spawn_powerup = pygame.time.get_ticks()

        # Upgrade para torre azul: dano extra
        self.upgrade_azul = 0

    def redimensionar(self, nova_largura, nova_altura):
        self.largura, self.altura = nova_largura, nova_altura
        self.tela = pygame.display.set_mode((self.largura, self.altura), pygame.RESIZABLE)
        self.centro_x, self.centro_y = self.largura // 2, self.altura // 2
        self.botao_verde = pygame.Rect(20, self.altura - self.tamanho_loja + 20, 60, 60)
        self.botao_azul  = pygame.Rect(100, self.altura - self.tamanho_loja + 20, 60, 60)
        self.botao_super = pygame.Rect(180, self.altura - self.tamanho_loja + 20, 60, 60)
        self.botao_cura  = pygame.Rect(260, self.altura - self.tamanho_loja + 20, 60, 60)
        self.botao_upgrade = pygame.Rect(340, self.altura - self.tamanho_loja + 20, 60, 60)

    def desenhar_estrela(self):
        pygame.draw.circle(self.tela, self.COR_ESTRELA, (self.centro_x, self.centro_y), self.raio_centro)

    def desenhar_formas(self):
        for forma in self.formas:
            if forma['tipo'] == 'resistente':
                cor = self.COR_RESISTENTE
            elif forma['tipo'] == 'rosa':
                cor = self.COR_ROSA
            else:
                cor = self.COR_INIMIGO
                if forma['vida'] <= 1 and random.random() < 0.5:
                    cor = (200, 200, 200)
            pygame.draw.rect(self.tela, cor, pygame.Rect(forma['x'], forma['y'], 30, 30))
            pygame.draw.rect(self.tela, (0, 0, 0), pygame.Rect(forma['x'], forma['y'], 30, 30), 1)

    def desenhar_torres(self):
        for torre in self.torres:
            if torre['tipo'] == 'circulo':
                pygame.draw.circle(self.tela, self.COR_CIRCULO_TORRE, (torre['x'], torre['y']), 30)
                pygame.draw.circle(self.tela, (0, 0, 0), (torre['x'], torre['y']), 30, 1)
            elif torre['tipo'] == 'triangulo':
                pontos = [
                    (torre['x'], torre['y'] - 30),
                    (torre['x'] - 30, torre['y'] + 30),
                    (torre['x'] + 30, torre['y'] + 30)
                ]
                pygame.draw.polygon(self.tela, self.COR_TRIANGULO_TORRE, pontos)
                pygame.draw.polygon(self.tela, (0, 0, 0), pontos, 1)
            elif torre['tipo'] == 'super':
                rect = pygame.Rect(torre['x'] - 30, torre['y'] - 30, 60, 60)
                pygame.draw.rect(self.tela, self.COR_SUPER_TORRE, rect)
                pygame.draw.rect(self.tela, (0, 0, 0), rect, 2)
            # Exibe a vida da torre acima dela
            vida_texto = self.fonte_tooltip.render(f"{torre.get('vida', 15)}", True, self.COR_TEXTO)
            self.tela.blit(vida_texto, (torre['x'] - vida_texto.get_width()//2, torre['y'] - 40))

    def desenhar_projeteis(self):
        for proj in self.projeteis:
            pygame.draw.circle(self.tela, self.COR_PROJETEIS, (int(proj['x']), int(proj['y'])), 5)

    def desenhar_loja(self):
        pygame.draw.rect(self.tela, (50, 50, 50), pygame.Rect(0, self.altura - self.tamanho_loja, self.largura, self.tamanho_loja))
        pygame.draw.rect(self.tela, self.COR_CIRCULO_TORRE, self.botao_verde)
        pygame.draw.rect(self.tela, (0, 0, 0), self.botao_verde, 2)
        pygame.draw.rect(self.tela, self.COR_TRIANGULO_TORRE, self.botao_azul)
        pygame.draw.rect(self.tela, (0, 0, 0), self.botao_azul, 2)
        pygame.draw.rect(self.tela, self.COR_SUPER_TORRE, self.botao_super)
        pygame.draw.rect(self.tela, (0, 0, 0), self.botao_super, 2)
        pygame.draw.rect(self.tela, self.COR_CURA, self.botao_cura)
        pygame.draw.rect(self.tela, (0, 0, 0), self.botao_cura, 2)
        pygame.draw.rect(self.tela, self.COR_UPGRADE, self.botao_upgrade)
        pygame.draw.rect(self.tela, (0, 0, 0), self.botao_upgrade, 2)
        txt_verde = self.fonte_ajuda.render(f"{self.preco_torre_circulo}", True, self.COR_TEXTO)
        txt_azul  = self.fonte_ajuda.render(f"{self.preco_torre_triangulo}", True, self.COR_TEXTO)
        txt_super = self.fonte_ajuda.render(f"{self.preco_torre_super}", True, self.COR_TEXTO)
        txt_cura  = self.fonte_ajuda.render(f"{self.preco_cura}", True, self.COR_TEXTO)
        txt_upgrade = self.fonte_ajuda.render(f"{int(self.preco_upgrade_azul)}", True, self.COR_TEXTO)
        self.tela.blit(txt_verde, (self.botao_verde.x + self.botao_verde.width//2 - txt_verde.get_width()//2,
                                     self.botao_verde.y - txt_verde.get_height() - 5))
        self.tela.blit(txt_azul, (self.botao_azul.x + self.botao_azul.width//2 - txt_azul.get_width()//2,
                                  self.botao_azul.y - txt_azul.get_height() - 5))
        self.tela.blit(txt_super, (self.botao_super.x + self.botao_super.width//2 - txt_super.get_width()//2,
                                   self.botao_super.y - txt_super.get_height()//2 - 10))
        self.tela.blit(txt_cura, (self.botao_cura.x + self.botao_cura.width//2 - txt_cura.get_width()//2,
                                  self.botao_cura.y - txt_cura.get_height() - 5))
        self.tela.blit(txt_upgrade, (self.botao_upgrade.x + self.botao_upgrade.width//2 - txt_upgrade.get_width()//2,
                                     self.botao_upgrade.y - txt_upgrade.get_height() - 5))
        txt_loja = self.fonte_ajuda.render(
            "Loja: 1=Verde, 2=Azul, 3=Super, 4=Cura, 5=Upgrade Azul", True, self.COR_TEXTO)
        self.tela.blit(txt_loja, (10, self.altura - self.tamanho_loja + 80))

    def desenhar_tooltips(self, mouse_x, mouse_y):
        offset = 30
        if self.botao_verde.collidepoint(mouse_x, mouse_y):
            tip = self.fonte_tooltip.render("Torre verde: dispara automaticamente", True, self.COR_TEXTO)
            pos_x = self.botao_verde.x + self.botao_verde.width//2 - tip.get_width()//2
            pos_y = self.botao_verde.y - tip.get_height() - offset
            if pos_x < 0:
                pos_x = 0
            elif pos_x + tip.get_width() > self.largura:
                pos_x = self.largura - tip.get_width()
            self.tela.blit(tip, (pos_x, pos_y))
        if self.botao_azul.collidepoint(mouse_x, mouse_y):
            tip = self.fonte_tooltip.render("Torre azul: dispara no clique (upgrade aumenta dano)", True, self.COR_TEXTO)
            pos_x = self.botao_azul.x + self.botao_azul.width//2 - tip.get_width()//2
            pos_y = self.botao_azul.y - tip.get_height() - offset
            if pos_x < 0:
                pos_x = 0
            elif pos_x + tip.get_width() > self.largura:
                pos_x = self.largura - tip.get_width()
            self.tela.blit(tip, (pos_x, pos_y))
        if self.botao_super.collidepoint(mouse_x, mouse_y):
            tip = self.fonte_tooltip.render("Torre super: dispara 15 direções, 5 de dano por tiro", True, self.COR_TEXTO)
            pos_x = self.botao_super.x + self.botao_super.width//2 - tip.get_width()//2
            pos_y = self.botao_super.y - tip.get_height() - offset
            if pos_x < 0:
                pos_x = 0
            elif pos_x + tip.get_width() > self.largura:
                pos_x = self.largura - tip.get_width()
            self.tela.blit(tip, (pos_x, pos_y))
        if self.botao_cura.collidepoint(mouse_x, mouse_y):
            tip = self.fonte_tooltip.render("Item de cura: +50 vida para o centro", True, self.COR_TEXTO)
            pos_x = self.botao_cura.x + self.botao_cura.width//2 - tip.get_width()//2
            pos_y = self.botao_cura.y - tip.get_height() - offset
            if pos_x < 0:
                pos_x = 0
            elif pos_x + tip.get_width() > self.largura:
                pos_x = self.largura - tip.get_width()
            self.tela.blit(tip, (pos_x, pos_y))
        if self.botao_upgrade.collidepoint(mouse_x, mouse_y):
            tip = self.fonte_tooltip.render("Upgrade azul: +2 de dano; Desbloqueia na onda 10", True, self.COR_TEXTO)
            pos_x = self.botao_upgrade.x + self.botao_upgrade.width//2 - tip.get_width()//2
            pos_y = self.botao_upgrade.y - tip.get_height() - offset
            if pos_x < 0:
                pos_x = 0
            elif pos_x + tip.get_width() > self.largura:
                pos_x = self.largura - tip.get_width()
            self.tela.blit(tip, (pos_x, pos_y))

    def criar_forma(self):
        tipos = ['básico', 'rápido', 'forte', 'gigante', 'resistente']
        # Inimigo rosa passa a aparecer a partir da onda 10
        if self.dificuldade >= 10:
            tipos.append('rosa')
        tipo_inimigo = random.choice(tipos)
        if tipo_inimigo == 'resistente':
            vida_inimigo = 10 + (self.dificuldade // 5) * 10
        elif tipo_inimigo == 'rosa':
            # Vida base 25, e ganha 5 a cada 5 ondas após a onda 10
            vida_inimigo = 25 + ((self.dificuldade - 10) // 5) * 5
        else:
            vida_inimigo = 1 + (self.score // 30)
            if tipo_inimigo == 'básico':
                vida_inimigo = 1
            elif tipo_inimigo == 'rápido':
                vida_inimigo = 2
            elif tipo_inimigo == 'forte':
                vida_inimigo = 4
            elif tipo_inimigo == 'gigante':
                vida_inimigo = 6
        velocidade = random.randint(1, 3) if tipo_inimigo not in ['forte', 'resistente', 'rosa'] else 1
        if tipo_inimigo == 'rosa':
            velocidade = 0.5
        forma = {
            'x': random.choice([-30, self.largura + 30]),
            'y': random.randint(0, self.altura),
            'tipo': tipo_inimigo,
            'velocidade': velocidade,
            'vida': vida_inimigo
        }
        if tipo_inimigo == 'rosa':
            forma['target_torre'] = None
            forma['ultimo_tiro'] = pygame.time.get_ticks()
        self.formas.append(forma)

    def verificar_colisao(self, mouse_x, mouse_y):
        for forma in self.formas[:]:
            dist = math.sqrt((forma['x'] - mouse_x)**2 + (forma['y'] - mouse_y)**2)
            if dist < 20:
                forma['vida'] -= 1
                if forma['vida'] <= 0:
                    self.explosions.append({
                        'x': forma['x'] + 15,
                        'y': forma['y'] + 15,
                        'radius': 0,
                        'max_radius': 30,
                        'alpha': 255
                    })
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
        elif tipo == 'super' and self.moedas >= self.preco_torre_super:
            self.moedas -= self.preco_torre_super
            self.posicionando_torre = 'super'

    def comprar_cura(self):
        if self.moedas >= self.preco_cura:
            self.moedas -= self.preco_cura
            self.vida_circulo += 50

    def comprar_upgrade_azul(self):
        if self.dificuldade >= 10 and self.moedas >= self.preco_upgrade_azul and self.preco_upgrade_azul < 1500:
            self.moedas -= self.preco_upgrade_azul
            self.upgrade_azul += 2
            self.preco_upgrade_azul = min(self.preco_upgrade_azul * 1.03, 1500)

    def posicionar_torre(self, x, y):
        if self.posicionando_torre == 'circulo':
            torre = {'x': x, 'y': y, 'tipo': 'circulo', 'vida': 15}
            self.torres.append(torre)
            self.posicionando_torre = None
        elif self.posicionando_torre == 'triangulo':
            torre = {'x': x, 'y': y, 'tipo': 'triangulo', 'vida': 15}
            self.torres.append(torre)
            self.posicionando_torre = None
        elif self.posicionando_torre == 'super':
            torre = {'x': x, 'y': y, 'tipo': 'super', 'vida': 15}
            self.torres.append(torre)
            self.posicionando_torre = None

    def atacar(self):
        tempo_atual = pygame.time.get_ticks()
        if tempo_atual - self.tempo_ultimo_disparo >= self.cooldown_torre:
            for torre in self.torres:
                if torre['tipo'] == 'circulo':
                    for forma in self.formas:
                        distancia = math.sqrt((torre['x'] - forma['x'])**2 + (torre['y'] - forma['y'])**2)
                        if distancia < 100:
                            dx = forma['x'] - torre['x']
                            dy = forma['y'] - torre['y']
                            d_total = math.sqrt(dx**2 + dy**2)
                            if d_total != 0:
                                dx /= d_total
                                dy /= d_total
                            proj = {
                                'x': torre['x'],
                                'y': torre['y'],
                                'dx': dx * 5,
                                'dy': dy * 5,
                                'alvo': forma,
                                'damage': 1
                            }
                            self.projeteis.append(proj)
                elif torre['tipo'] == 'super':
                    for i in range(15):
                        angle = math.radians(i * (360/15))
                        dx = math.cos(angle)
                        dy = math.sin(angle)
                        proj = {
                            'x': torre['x'],
                            'y': torre['y'],
                            'dx': dx * 5,
                            'dy': dy * 5,
                            'alvo': None,
                            'damage': 5
                        }
                        self.projeteis.append(proj)
            self.tempo_ultimo_disparo = tempo_atual

    def atacar_torres(self):
        # Inimigo rosa ataca a torre alvo assim que nasce.
        agora = pygame.time.get_ticks()
        for forma in self.formas:
            if forma['tipo'] == 'rosa':
                if self.torres:
                    if forma.get('target_torre') is None or forma['target_torre'] not in self.torres:
                        forma['target_torre'] = random.choice(self.torres)
                    dx = forma['target_torre']['x'] - forma['x']
                    dy = forma['target_torre']['y'] - forma['y']
                    d_total = math.sqrt(dx**2 + dy**2)
                    # Se estiver a 100 pixels ou menos, fica parado e ataca
                    if d_total < 1000 and agora - forma.get('ultimo_tiro', 0) >= 2000:
                        if d_total != 0:
                            dx /= d_total
                            dy /= d_total
                        proj = {
                            'x': forma['x'],
                            'y': forma['y'],
                            'dx': dx * 5,
                            'dy': dy * 5,
                            'alvo': forma['target_torre'],
                            'damage': 1
                        }
                        self.projeteis.append(proj)
                        forma['ultimo_tiro'] = agora
                # Se não houver torres, ele não ataca

    def mover_projeteis(self):
        for proj in self.projeteis[:]:
            proj['x'] += proj['dx']
            proj['y'] += proj['dy']
            if proj.get('alvo'):
                dist = math.sqrt((proj['x'] - proj['alvo']['x'])**2 + (proj['y'] - proj['alvo']['y'])**2)
                if dist < 20:
                    proj['alvo']['vida'] -= proj.get('damage', 1)
                    if proj['alvo']['vida'] <= 0:
                        if proj['alvo'] in self.torres:
                            self.torres.remove(proj['alvo'])
                        elif proj['alvo'] in self.formas:
                            self.formas.remove(proj['alvo'])
                        self.score += 3
                        self.moedas += 5
                        self.explosions.append({
                            'x': proj['alvo']['x'] + 15,
                            'y': proj['alvo']['y'] + 15,
                            'radius': 0,
                            'max_radius': 30,
                            'alpha': 255
                        })
                    if proj in self.projeteis:
                        self.projeteis.remove(proj)
            else:
                for forma in self.formas[:]:
                    dist = math.sqrt((proj['x'] - (forma['x']+15))**2 + (proj['y'] - (forma['y']+15))**2)
                    if dist < 20:
                        forma['vida'] -= proj.get('damage', 1)
                        if forma['vida'] <= 0:
                            self.formas.remove(forma)
                            self.score += 3
                            self.moedas += 5
                            self.explosions.append({
                                'x': forma['x'] + 15,
                                'y': forma['y'] + 15,
                                'radius': 0,
                                'max_radius': 30,
                                'alpha': 255
                            })
                        if proj in self.projeteis:
                            self.projeteis.remove(proj)
                        break
                if (proj['x'] < 0 or proj['x'] > self.largura or
                    proj['y'] < 0 or proj['y'] > self.altura):
                    if proj in self.projeteis:
                        self.projeteis.remove(proj)

    def mover_inimigos(self):
        for forma in self.formas[:]:
            if forma['tipo'] == 'rosa':
                # Inimigo rosa escolhe uma torre alvo e se move em direção a ela
                if self.torres:
                    if forma.get('target_torre') is None or forma['target_torre'] not in self.torres:
                        forma['target_torre'] = random.choice(self.torres)
                    dx = forma['target_torre']['x'] - forma['x']
                    dy = forma['target_torre']['y'] - forma['y']
                    d_total = math.sqrt(dx**2 + dy**2)
                    # Se estiver a mais de 100 pixels, continua se movendo; caso contrário, para.
                    if d_total > 100:
                        dx /= d_total
                        dy /= d_total
                        forma['x'] += dx * 0.5
                        forma['y'] += dy * 0.5
                else:
                    dx = self.centro_x - forma['x']
                    dy = self.centro_y - forma['y']
                    d_total = math.sqrt(dx**2 + dy**2)
                    if d_total != 0:
                        dx /= d_total
                        dy /= d_total
                    forma['x'] += dx * 0.5
                    forma['y'] += dy * 0.5
            else:
                dx = self.centro_x - forma['x']
                dy = self.centro_y - forma['y']
                d_total = math.sqrt(dx**2 + dy**2)
                if d_total != 0:
                    dx /= d_total
                    dy /= d_total
                forma['x'] += dx * forma['velocidade']
                forma['y'] += dy * forma['velocidade']
            if abs(forma['x'] - self.centro_x) < self.raio_centro and abs(forma['y'] - self.centro_y) < self.raio_centro:
                self.vida_circulo -= 5
                if forma in self.formas:
                    self.formas.remove(forma)

    def atualizar_explosions(self):
        for exp in self.explosions[:]:
            exp['radius'] += 1
            exp['alpha'] -= 8
            if exp['alpha'] <= 0 or exp['radius'] >= exp['max_radius']:
                self.explosions.remove(exp)

    def desenhar_explosions(self):
        for exp in self.explosions:
            s = pygame.Surface((exp['max_radius']*2, exp['max_radius']*2), pygame.SRCALPHA)
            cor = (255, 150, 0, max(exp['alpha'], 0))
            pygame.draw.circle(s, cor, (exp['max_radius'], exp['max_radius']), exp['radius'])
            self.tela.blit(s, (exp['x'] - exp['max_radius'], exp['y'] - exp['max_radius']))

    def spawn_powerup(self):
        tempo_atual = pygame.time.get_ticks()
        if tempo_atual - self.ultimo_spawn_powerup > 10000 and random.random() < 0.5:
            powerup = {
                'x': random.randint(50, self.largura - 50),
                'y': random.randint(50, self.altura - 50),
                'tipo': 'moeda'
            }
            self.powerups.append(powerup)
            self.ultimo_spawn_powerup = tempo_atual

    def desenhar_powerups(self):
        for p in self.powerups:
            pygame.draw.circle(self.tela, (255, 215, 0), (p['x'], p['y']), 15)
            pygame.draw.circle(self.tela, (0, 0, 0), (p['x'], p['y']), 15, 2)

    def verificar_powerups(self, mouse_x, mouse_y):
        for p in self.powerups[:]:
            dist = math.sqrt((p['x'] - mouse_x)**2 + (p['y'] - mouse_y)**2)
            if dist < 15:
                self.moedas += 20
                self.powerups.remove(p)
                break

    def desenhar_gameover(self):
        font = pygame.font.SysFont(None, 72)
        texto_gameover = font.render("GAME OVER", True, self.COR_TEXTO)
        self.tela.blit(texto_gameover, (self.largura//2 - texto_gameover.get_width()//2, self.altura//3))
        texto_score = self.fonte_score.render(f"Pontuação Final: {self.score}", True, self.COR_TEXTO)
        self.tela.blit(texto_score, (self.largura//2 - texto_score.get_width()//2, self.altura//2))

    def run(self):
        BRANCO = (255, 255, 255)
        self.wave_active = False

        while self.rodando:
            if self.vida_circulo <= 0:
                self.tela.fill(self.COR_FUNDO)
                self.desenhar_gameover()
                pygame.display.flip()
                pygame.time.delay(3000)
                break

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.rodando = False
                elif event.type == pygame.VIDEORESIZE:
                    self.redimensionar(event.w, event.h)
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        self.rodando = False
                    if event.key == pygame.K_1:
                        self.comprar_torre('circulo')
                    if event.key == pygame.K_2:
                        self.comprar_torre('triangulo')
                    if event.key == pygame.K_3:
                        self.comprar_torre('super')
                    if event.key == pygame.K_4:
                        self.comprar_cura()
                    if event.key == pygame.K_5:
                        self.comprar_upgrade_azul()
                    if event.key == pygame.K_RETURN:
                        if not self.wave_active:
                            self.wave_active = True
                            for _ in range(5 + self.dificuldade):
                                self.criar_forma()
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    mouse_x, mouse_y = pygame.mouse.get_pos()
                    if self.botao_verde.collidepoint(mouse_x, mouse_y):
                        self.comprar_torre('circulo')
                    elif self.botao_azul.collidepoint(mouse_x, mouse_y):
                        self.comprar_torre('triangulo')
                    elif self.botao_super.collidepoint(mouse_x, mouse_y):
                        self.comprar_torre('super')
                    elif self.botao_cura.collidepoint(mouse_x, mouse_y):
                        self.comprar_cura()
                    elif self.botao_upgrade.collidepoint(mouse_x, mouse_y):
                        self.comprar_upgrade_azul()
                    elif self.posicionando_torre:
                        self.posicionar_torre(mouse_x, mouse_y)
                    else:
                        for torre in self.torres:
                            if torre['tipo'] == 'triangulo':
                                dx = mouse_x - torre['x']
                                dy = mouse_y - torre['y']
                                d_total = math.sqrt(dx*dx + dy*dy)
                                if d_total != 0:
                                    dx /= d_total
                                    dy /= d_total
                                proj = {
                                    'x': torre['x'],
                                    'y': torre['y'],
                                    'dx': dx * 7,
                                    'dy': dy * 7,
                                    'alvo': None,
                                    'damage': 1 + self.upgrade_azul
                                }
                                self.projeteis.append(proj)
                        self.verificar_powerups(mouse_x, mouse_y)

            if self.wave_active:
                for forma in self.formas:
                    if forma['tipo'] == 'rosa':
                        # Inimigo rosa: se houver torres, escolhe uma torre alvo e se move até estar a 100px.
                        if self.torres:
                            if forma.get('target_torre') is None or forma['target_torre'] not in self.torres:
                                forma['target_torre'] = random.choice(self.torres)
                            dx = forma['target_torre']['x'] - forma['x']
                            dy = forma['target_torre']['y'] - forma['y']
                            d_total = math.sqrt(dx**2 + dy**2)
                            if d_total > 100:
                                dx /= d_total
                                dy /= d_total
                                forma['x'] += dx * 0.5
                                forma['y'] += dy * 0.5
                            # Se estiver a 100px ou menos, ele permanece parado (o ataque será feito em atacar_torres)
                        else:
                            dx = self.centro_x - forma['x']
                            dy = self.centro_y - forma['y']
                            d_total = math.sqrt(dx**2 + dy**2)
                            if d_total != 0:
                                dx /= d_total
                                dy /= d_total
                            forma['x'] += dx * 0.5
                            forma['y'] += dy * 0.5
                    else:
                        forma['x'] += forma['velocidade'] if forma['x'] < self.largura//2 else -forma['velocidade']
                self.mover_inimigos()
                self.atacar()         # Torres verdes e super disparam automaticamente
                self.atacar_torres()  # Inimigo rosa ataca torres a cada 2 segundos
                self.mover_projeteis()
                if not self.formas:
                    self.projeteis.clear()
                    self.wave_active = False
                    self.dificuldade += 1

            self.tela.fill(self.COR_FUNDO)
            self.desenhar_estrela()
            self.desenhar_formas()
            self.desenhar_torres()
            self.desenhar_projeteis()
            self.desenhar_loja()
            self.desenhar_powerups()
            self.desenhar_explosions()

            pygame.draw.rect(self.tela, self.COR_BARRA_VIDA, pygame.Rect(self.centro_x-50, self.centro_y+self.raio_centro+10, 100, 10))
            pygame.draw.rect(self.tela, (0, 255, 0), pygame.Rect(self.centro_x-50, self.centro_y+self.raio_centro+10, self.vida_circulo, 10))

            texto_score = self.fonte_score.render("Score: " + str(self.score), True, self.COR_TEXTO)
            texto_moedas = self.fonte_score.render("Moedas: " + str(self.moedas), True, self.COR_TEXTO)
            texto_wave = self.fonte_wave.render("Onda: " + str(self.dificuldade), True, self.COR_TEXTO)
            self.tela.blit(texto_score, (10, 10))
            self.tela.blit(texto_moedas, (10, 40))
            self.tela.blit(texto_wave, (self.largura - texto_wave.get_width() - 10, 10))
            
            if not self.wave_active:
                msg = self.fonte_mensagem.render("Após posicionar suas torres, pressione ENTER para iniciar", True, BRANCO)
                pos_x = self.largura//2 - msg.get_width()//2
                pos_y = self.altura - self.tamanho_loja - msg.get_height() - 10
                self.tela.blit(msg, (pos_x, pos_y))
            
            mouse_x, mouse_y = pygame.mouse.get_pos()
            self.desenhar_tooltips(mouse_x, mouse_y)

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
