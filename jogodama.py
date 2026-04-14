import pygame
import sys
import copy

pygame.init()

# =============================
# CONFIGURAÇÕES
# =============================
LARGURA, ALTURA = 1000, 750
DIMENSAO = 8
TAMANHO = 600 // DIMENSAO
OFFSET_X = 200
OFFSET_Y = 50
FPS = 60

# Tempo de jogo (10 minutos por jogada)
TEMPO_LIMITE = 600 

janela = pygame.display.set_mode((LARGURA, ALTURA))
pygame.display.set_caption("Damas Pro - IA com Cronômetro")
relogio = pygame.time.Clock()

fonte = pygame.font.SysFont("Arial", 26)
fonte_pequena = pygame.font.SysFont("Arial", 20)
fonte_grande = pygame.font.SysFont("Arial", 60, bold=True)

# CORES
BEGE, MARROM = (240, 217, 181), (181, 136, 99)
PRETO, BRANCO = (30, 30, 30), (230, 230, 230)
VERDE, AZUL, OURO = (46, 204, 113), (52, 152, 219), (241, 196, 15)
FUNDO, CINZA_ESC = (44, 62, 80), (30, 30, 30)

# =============================
# ESTADO GLOBAL
# =============================
tabuleiro = []
turno = 1
estado = "menu"
nome_jogador = ""
comidas_player = 0
comidas_ia = 0
animacao_ativa = None
tempo_turno_inicio = 0
tempo_restante = TEMPO_LIMITE

# =============================
# SISTEMA DE ANIMAÇÃO
# =============================
class AnimacaoMovimento:
    def __init__(self, peca, inicio, fim, duracao=10):
        self.peca = peca
        self.inicio = (OFFSET_X + inicio[1]*TAMANHO + TAMANHO//2, OFFSET_Y + inicio[0]*TAMANHO + TAMANHO//2)
        self.fim = (OFFSET_X + fim[1]*TAMANHO + TAMANHO//2, OFFSET_Y + fim[0]*TAMANHO + TAMANHO//2)
        self.duracao = duracao
        self.frame_atual = 0
        self.ativa = True

    def atualizar(self):
        if self.frame_atual < self.duracao:
            self.frame_atual += 1
            t = self.frame_atual / self.duracao
            curr_x = self.inicio[0] + (self.fim[0] - self.inicio[0]) * t
            curr_y = self.inicio[1] + (self.fim[1] - self.inicio[1]) * t
            return (int(curr_x), int(curr_y))
        self.ativa = False
        return self.fim

# =============================
# LÓGICA DE JOGO
# =============================
def reset_tabuleiro():
    global comidas_ia, comidas_player, turno, tempo_turno_inicio, tempo_restante
    comidas_ia, comidas_player, turno = 0, 0, 1
    tempo_turno_inicio = pygame.time.get_ticks()
    tempo_restante = TEMPO_LIMITE
    return [
        [0, 2, 0, 2, 0, 2, 0, 2],
        [2, 0, 2, 0, 2, 0, 2, 0],
        [0, 2, 0, 2, 0, 2, 0, 2],
        [0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0],
        [1, 0, 1, 0, 1, 0, 1, 0],
        [0, 1, 0, 1, 0, 1, 0, 1],
        [1, 0, 1, 0, 1, 0, 1, 0]
    ]

def movimentos_possiveis(l, c, tab, apenas_capturas=False):
    p = tab[l][c]
    if p in [3, 4]:
        movs = []
        for dl, dc in [(-1,-1), (-1,1), (1,-1), (1,1)]:
            nl, nc = l+dl, c+dc
            inimigo = False
            pos_inimigo = None
            while 0 <= nl < 8 and 0 <= nc < 8:
                if tab[nl][nc] == 0:
                    if not inimigo:
                        if not apenas_capturas: movs.append([(nl, nc)])
                    else:
                        novo = copy.deepcopy(tab); novo[l][c], novo[pos_inimigo[0]][pos_inimigo[1]], novo[nl][nc] = 0, 0, p
                        segs = movimentos_possiveis(nl, nc, novo, True)
                        if segs: 
                            for s in segs: movs.append([(nl, nc)] + s)
                        else: movs.append([(nl, nc)])
                else:
                    if (tab[nl][nc] % 2) != (p % 2):
                        if not inimigo: inimigo, pos_inimigo = True, (nl, nc)
                        else: break
                    else: break
                nl, nc = nl + dl, nc + dc
        return movs
    
    movs = []
    dirs = [(-1, -1), (-1, 1)] if p == 1 else [(1, -1), (1, 1)]
    if not apenas_capturas:
        for dl, dc in dirs:
            nl, nc = l+dl, c+dc
            if 0 <= nl < 8 and 0 <= nc < 8 and tab[nl][nc] == 0: movs.append([(nl, nc)])
    for dl, dc in dirs:
        nl, nc, nl2, nc2 = l+dl, c+dc, l+2*dl, c+2*dc
        if 0 <= nl2 < 8 and 0 <= nc2 < 8:
            if tab[nl][nc] != 0 and (tab[nl][nc] % 2) != (p % 2) and tab[nl2][nc2] == 0:
                novo = copy.deepcopy(tab); novo[l][c], novo[nl][nc], novo[nl2][nc2] = 0, 0, p
                segs = movimentos_possiveis(nl2, nc2, novo, True)
                if segs:
                    for s in segs: movs.append([(nl2, nc2)] + s)
                else: movs.append([(nl2, nc2)])
    return movs

def todas_jogadas(tab, jogador):
    caps, norms = [], []
    for l in range(8):
        for c in range(8):
            if tab[l][c] != 0 and (tab[l][c] % 2) == (jogador % 2):
                for m in movimentos_possiveis(l, c, tab):
                    if abs(m[0][0] - l) > 1: caps.append(((l, c), m))
                    else: norms.append(((l, c), m))
    return caps if caps else norms

def mover_silencioso(tab, orig, caminho):
    l, c = orig
    p = tab[l][c]
    tab[l][c] = 0
    for (nl, nc) in caminho:
        sl = 1 if nl > l else -1
        sc = 1 if nc > c else -1
        cl, cc = l + sl, c + sc
        while (cl, cc) != (nl, nc):
            tab[cl][cc] = 0
            cl, cc = cl + sl, cc + sc
        l, c = nl, nc
    tab[l][c] = p
    if p == 1 and l == 0: tab[l][c] = 3
    if p == 2 and l == 7: tab[l][c] = 4

def mover_com_animacao(tab, orig, caminho):
    global animacao_ativa, comidas_player, comidas_ia
    l, c = orig
    p = tab[l][c]
    animacao_ativa = AnimacaoMovimento(p, (l, c), caminho[-1])
    
    tab[l][c] = 0
    curr_l, curr_c = l, c
    for (nl, nc) in caminho:
        sl = 1 if nl > curr_l else -1
        sc = 1 if nc > curr_c else -1
        cl, cc = curr_l + sl, curr_c + sc
        while (cl, cc) != (nl, nc):
            if tab[cl][cc] != 0:
                if p in [1, 3]: comidas_player += 1
                else: comidas_ia += 1
            tab[cl][cc] = 0
            cl, cc = cl + sl, cc + sc
        curr_l, curr_c = nl, nc
    
    tab[curr_l][curr_c] = p
    if p == 1 and curr_l == 0: tab[curr_l][curr_c] = 3
    if p == 2 and curr_l == 7: tab[curr_l][curr_c] = 4

# =============================
# IA - MINIMAX
# =============================
def avaliar(tab):
    sc = 0
    for l in range(8):
        for c in range(8):
            p = tab[l][c]
            sc += (10 if p==2 else 25 if p==4 else -10 if p==1 else -25 if p==3 else 0)
    return sc

def minimax(tab, depth, alfa, beta, maxi):
    if depth == 0: return avaliar(tab), None
    jogadas = todas_jogadas(tab, 2 if maxi else 1)
    if not jogadas: return avaliar(tab), None
    melhor = None
    if maxi:
        mv = -9999
        for j in jogadas:
            novo = copy.deepcopy(tab); mover_silencioso(novo, j[0], j[1])
            v, _ = minimax(novo, depth-1, alfa, beta, False)
            if v > mv: mv, melhor = v, j
            alfa = max(alfa, v)
            if beta <= alfa: break
        return mv, melhor
    else:
        mv = 9999
        for j in jogadas:
            novo = copy.deepcopy(tab); mover_silencioso(novo, j[0], j[1])
            v, _ = minimax(novo, depth-1, alfa, beta, True)
            if v < mv: mv, melhor = v, j
            beta = min(beta, v)
            if beta <= alfa: break
        return mv, melhor

# =============================
# INTERFACE E DESENHO
# =============================
def desenhar_peca(cor_peca, centro, e_dama, selecionada=False):
    if selecionada:
        pygame.draw.circle(janela, VERDE, centro, TAMANHO//2-2, 5)
    pygame.draw.circle(janela, cor_peca, centro, TAMANHO//2-12)
    if e_dama:
        pygame.draw.circle(janela, OURO, centro, 12, 3)

def desenhar_tudo(sel, movs):
    janela.fill(FUNDO)
    pygame.draw.rect(janela, CINZA_ESC, (OFFSET_X-10, OFFSET_Y-10, 620, 620), 0, 10)
    
    # Desenhar Cronômetro
    minutos = int(tempo_restante // 60)
    segundos = int(tempo_restante % 60)
    cor_tempo = OURO if tempo_restante > 30 else (255, 50, 50)
    txt_timer = fonte.render(f"TEMPO: {minutos:02d}:{segundos:02d}", True, cor_tempo)
    janela.blit(txt_timer, (LARGURA//2 - txt_timer.get_width()//2, 10))

    pos_animada = None
    if animacao_ativa and animacao_ativa.ativa:
        pos_animada = animacao_ativa.atualizar()

    for l in range(8):
        for c in range(8):
            cor = BEGE if (l+c)%2==0 else MARROM
            pygame.draw.rect(janela, cor, (OFFSET_X + c*TAMANHO, OFFSET_Y + l*TAMANHO, TAMANHO, TAMANHO))
            p = tabuleiro[l][c]
            if p != 0:
                if animacao_ativa and animacao_ativa.ativa:
                    f_l, f_c = (animacao_ativa.fim[1]-OFFSET_Y)//TAMANHO, (animacao_ativa.fim[0]-OFFSET_X)//TAMANHO
                    if l == f_l and c == f_c: continue
                cp = BRANCO if p in [1, 3] else PRETO
                centro = (OFFSET_X + c*TAMANHO + TAMANHO//2, OFFSET_Y + l*TAMANHO + TAMANHO//2)
                desenhar_peca(cp, centro, p in [3, 4], sel == (l, c))

    if pos_animada:
        cp = BRANCO if animacao_ativa.peca in [1, 3] else PRETO
        desenhar_peca(cp, pos_animada, animacao_ativa.peca in [3, 4])

    for m in movs:
        pygame.draw.circle(janela, AZUL, (OFFSET_X + m[-1][1]*TAMANHO + TAMANHO//2, OFFSET_Y + m[-1][0]*TAMANHO + TAMANHO//2), 12)
    
    # Painéis Laterais
    pygame.draw.rect(janela, (70, 70, 70), (30, 150, 140, 400), border_radius=15)
    txt_n = fonte_pequena.render(nome_jogador.upper(), True, BRANCO)
    janela.blit(txt_n, (100 - txt_n.get_width()//2, 170))
    for i in range(comidas_player):
        row, col = divmod(i, 2); pygame.draw.circle(janela, PRETO, (65 + col*70, 230 + row*45), 20)

    pygame.draw.rect(janela, (70, 70, 70), (830, 150, 140, 400), border_radius=15)
    txt_ia = fonte_pequena.render("IA", True, BRANCO)
    janela.blit(txt_ia, (900 - txt_ia.get_width()//2, 170))
    for i in range(comidas_ia):
        row, col = divmod(i, 2); pygame.draw.circle(janela, BRANCO, (865 + col*70, 230 + row*45), 20)

# =============================
# TELAS DO JOGO
# =============================
def menu():
    global estado
    while estado == "menu":
        janela.fill(FUNDO)
        titulo = fonte_grande.render("DAMAS PRO", True, BRANCO)
        janela.blit(titulo, (LARGURA//2 - titulo.get_width()//2, 100))
        btns = [("JOGAR", 250), ("REGRAS", 330), ("SAIR", 410)]
        rects = []
        for txt, y in btns:
            r = pygame.Rect(LARGURA//2 - 100, y, 200, 60)
            rects.append((r, txt))
            cor = (100, 100, 100) if r.collidepoint(pygame.mouse.get_pos()) else (70, 70, 70)
            pygame.draw.rect(janela, cor, r, border_radius=10)
            t = fonte.render(txt, True, BRANCO)
            janela.blit(t, t.get_rect(center=r.center))
        for e in pygame.event.get():
            if e.type == pygame.QUIT: pygame.quit(); sys.exit()
            if e.type == pygame.MOUSEBUTTONDOWN:
                if rects[0][0].collidepoint(e.pos): estado = "nome"
                if rects[1][0].collidepoint(e.pos): estado = "regras"
                if rects[2][0].collidepoint(e.pos): pygame.quit(); sys.exit()
        pygame.display.update()

def input_nome():
    global estado, nome_jogador
    while estado == "nome":
        janela.fill(FUNDO)
        txt = fonte.render("DIGITE SEU NOME E PRESSIONE ENTER:", True, BRANCO)
        janela.blit(txt, (LARGURA//2 - txt.get_width()//2, 250))
        caixa = pygame.Rect(LARGURA//2 - 150, 320, 300, 50)
        pygame.draw.rect(janela, BRANCO, caixa, border_radius=5)
        txt_n = fonte.render(nome_jogador, True, PRETO)
        janela.blit(txt_n, (caixa.x + 10, caixa.y + 10))
        for e in pygame.event.get():
            if e.type == pygame.QUIT: pygame.quit(); sys.exit()
            if e.type == pygame.KEYDOWN:
                if e.key == pygame.K_RETURN and nome_jogador.strip(): 
                    reset_tabuleiro()
                    estado = "jogo"
                elif e.key == pygame.K_BACKSPACE: nome_jogador = nome_jogador[:-1]
                elif e.key == pygame.K_ESCAPE: estado = "menu"
                elif len(nome_jogador) < 10: nome_jogador += e.unicode
        pygame.display.update()

def regras():
    global estado
    while estado == "regras":
        janela.fill(FUNDO)
        linhas = ["REGRAS", "- Captura é obrigatória.", "- Damas movem-se várias casas.", "- Você tem 10 minutos por jogada.", "- IA usa Alpha-Beta Pruning.", "ESC para voltar."]
        for i, l in enumerate(linhas):
            janela.blit(fonte.render(l, True, BRANCO), (100, 150 + i*50))
        for e in pygame.event.get():
            if e.type == pygame.QUIT: pygame.quit(); sys.exit()
            if e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE: estado = "menu"
        pygame.display.update()

def tela_vitoria(msg):
    global estado, tabuleiro
    while True:
        janela.fill((20, 20, 20))
        t = fonte_grande.render(msg, True, VERDE)
        janela.blit(t, (LARGURA//2 - t.get_width()//2, 300))
        sub = fonte.render("Clique para voltar ao menu", True, BRANCO)
        janela.blit(sub, (LARGURA//2 - sub.get_width()//2, 400))
        for e in pygame.event.get():
            if e.type == pygame.QUIT: pygame.quit(); sys.exit()
            if e.type == pygame.MOUSEBUTTONDOWN:
                estado = "menu"; return
        pygame.display.update()

def jogo():
    global turno, estado, tabuleiro, tempo_turno_inicio, tempo_restante
    sel, movs_p = None, []
    tabuleiro = reset_tabuleiro()
    tempo_turno_inicio = pygame.time.get_ticks()

    while estado == "jogo":
        relogio.tick(FPS)
        
        # Lógica do Cronômetro
        tempo_passado = (pygame.time.get_ticks() - tempo_turno_inicio) // 1000
        tempo_restante = max(0, TEMPO_LIMITE - tempo_passado)

        if tempo_restante <= 0:
            msg = "IA VENCEU (TEMPO ESGOTADO)!" if turno == 1 else f"{nome_jogador.upper()} VENCEU!"
            tela_vitoria(msg)
            break

        if animacao_ativa and animacao_ativa.ativa:
            desenhar_tudo(sel, movs_p); pygame.display.update(); continue

        if comidas_player == 12 or comidas_ia == 12:
            tela_vitoria(f"{nome_jogador.upper()} VENCEU!" if comidas_player == 12 else "IA VENCEU!")
            break

        if turno == 2:
            pygame.time.delay(300)
            _, j = minimax(tabuleiro, 3, -999, 999, True)
            if j: 
                mover_com_animacao(tabuleiro, j[0], j[1])
            turno = 1
            tempo_turno_inicio = pygame.time.get_ticks() # Reset cronômetro para o Player

        for e in pygame.event.get():
            if e.type == pygame.QUIT: pygame.quit(); sys.exit()
            if e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE: estado = "menu"
            if e.type == pygame.MOUSEBUTTONDOWN and turno == 1:
                mx, my = e.pos
                c, l = (mx-OFFSET_X)//TAMANHO, (my-OFFSET_Y)//TAMANHO
                if 0 <= l < 8 and 0 <= c < 8:
                    if tabuleiro[l][c] in [1, 3]:
                        sel, movs_p = (l, c), []
                        for orig, dest in todas_jogadas(tabuleiro, 1):
                            if orig == (l, c): movs_p.append(dest)
                    elif sel:
                        for caminho in movs_p:
                            if caminho[-1] == (l, c):
                                mover_com_animacao(tabuleiro, sel, caminho)
                                turno = 2
                                tempo_turno_inicio = pygame.time.get_ticks() # Reset cronômetro para a IA
                                break
                        sel, movs_p = None, []

        desenhar_tudo(sel, movs_p)
        pygame.display.update()

# LOOP PRINCIPAL
while True:
    if estado == "menu": menu()
    elif estado == "nome": input_nome()
    elif estado == "regras": regras()
    elif estado == "jogo": jogo()