import pygame

import sys

import copy

import random

 

pygame.init()

 

# ==============================

# CONFIGURAÇÕES

# ==============================

LARGURA, ALTURA = 600, 700

DIMENSAO = 8

TAMANHO = 600 // DIMENSAO

 

janela = pygame.display.set_mode((LARGURA, ALTURA))

pygame.display.set_caption("Damas Portuguesas")

 

fonte = pygame.font.SysFont("Arial", 26)

 

# CORES

BEGE = (240, 217, 181)

MARROM = (181, 136, 99)

PRETO = (30, 30, 30)

BRANCO = (230, 230, 230)

VERDE = (0, 255, 0)

AZUL = (0, 150, 255)

FUNDO = (30, 30, 30)

OURO = (255, 215, 0)

 

# ==============================

# TABULEIRO

# ==============================

def reset_tabuleiro():

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

 

tabuleiro = reset_tabuleiro()

turno = 1

estado = "menu"

 

# ==============================

# DESENHO

# ==============================

def desenhar_tabuleiro():

    for l in range(8):

        for c in range(8):

            cor = BEGE if (l+c)%2==0 else MARROM

            pygame.draw.rect(janela, cor, (c*TAMANHO, l*TAMANHO, TAMANHO, TAMANHO))

 

def desenhar_pecas(sel):

    for l in range(8):

        for c in range(8):

            p = tabuleiro[l][c]

            if p != 0:

                cor = BRANCO if p in [1,3] else PRETO

                centro = (c*TAMANHO+TAMANHO//2, l*TAMANHO+TAMANHO//2)

                if sel == (l,c):

                    pygame.draw.circle(janela, VERDE, centro, TAMANHO//2-5)

                pygame.draw.circle(janela, cor, centro, TAMANHO//2-15)

                if p in [3,4]:  # dama

                    pygame.draw.circle(janela, OURO, centro, 10)

 

def mostrar_turno():

    txt = "Turno: Brancas" if turno == 1 else "IA (Pretas)"

    janela.blit(fonte.render(txt, True, BRANCO), (10, 610))

 

def contar_pecas():

    brancas = sum(p in [1,3] for linha in tabuleiro for p in linha)

    pretas = sum(p in [2,4] for linha in tabuleiro for p in linha)

    texto = f"Brancas: {brancas}    Pretas: {pretas}"

    render = fonte.render(texto, True, BRANCO)

    pygame.draw.rect(janela, FUNDO, (0,640,600,60))

    janela.blit(render,(150,650))

 

def desenhar_movimentos(movs):

    for l,c in movs:

        pygame.draw.circle(janela, AZUL, (c*TAMANHO+TAMANHO//2, l*TAMANHO+TAMANHO//2), 10)

 

# ==============================

# LÓGICA DAS DAMAS PORTUGUESAS

# ==============================

def capturas_possiveis(tab, l, c, p):

    capturas = []

    dirs = [(-1,-1),(-1,1),(1,-1),(1,1)]

    for dl, dc in dirs:

        nl, nc = l + dl, c + dc

        while 0 <= nl < 8 and 0 <= nc < 8:

            if tab[nl][nc]!=0 and (tab[nl][nc]%2)!=(p%2):

                salto_l = nl + dl

                salto_c = nc + dc

                if 0<=salto_l<8 and 0<=salto_c<8 and tab[salto_l][salto_c]==0:

                    capturas.append((salto_l, salto_c, nl, nc))

                break

            if tab[nl][nc]!=0: break

            if p in [1,2]: break

            nl += dl; nc += dc

    return capturas

 

def explorar_capturas(tab, l, c, p):

    caps = capturas_possiveis(tab, l, c, p)

    if not caps: return [([(l,c)], tab)]

    resultados = []

    for dest_l, dest_c, inim_l, inim_c in caps:

        novo = copy.deepcopy(tab)

        novo[l][c]=0

        novo[inim_l][inim_c]=0

        novo[dest_l][dest_c]=p

        # continuar captura múltipla

        seqs = explorar_capturas(novo, dest_l, dest_c, p)

        for seq, t in seqs:

            resultados.append(([(l,c)]+seq, t))

    return resultados

 

def movimentos_possiveis(l, c, tab):

    p = tab[l][c]

    caps = explorar_capturas(tab,l,c,p)

    if caps and any(len(seq)>1 for seq, _ in caps):

        return [seq[-1] for seq,_ in caps]

    dirs = []

    if p==1: dirs=[(-1,-1),(-1,1)]

    elif p==2: dirs=[(1,-1),(1,1)]

    else: dirs=[(-1,-1),(-1,1),(1,-1),(1,1)]

    movs=[]

    for dl,dc in dirs:

        nl,nc=l+dl,c+dc

        if 0<=nl<8 and 0<=nc<8 and tab[nl][nc]==0: movs.append((nl,nc))

    return movs

 

def mover(tab, orig, dest):

    l1,c1 = orig

    l2,c2 = dest

    p = tab[l1][c1]

    tab[l1][c1]=0

    tab[l2][c2]=p

    # remover peça capturada

    if abs(l2-l1)>=2:

        step_l = (l2-l1)//abs(l2-l1)

        step_c = (c2-c1)//abs(c2-c1)

        l, c = l1+step_l, c1+step_c

        while l != l2 and c != c2:

            tab[l][c]=0

            l+=step_l; c+=step_c

    # promover dama

    if p==1 and l2==0: tab[l2][c2]=3

    if p==2 and l2==7: tab[l2][c2]=4

 

# ==============================

# IA MINIMAX + ALPHABETA

# ==============================

def avaliar(tab):

    score=0

    for linha in tab:

        for p in linha:

            if p==2: score+=1

            elif p==1: score-=1

            elif p==4: score+=2

            elif p==3: score-=2

    return score

 

def todas_jogadas(tab, jogador):

    jogadas=[]

    capturas=[]

    for l in range(8):

        for c in range(8):

            p=tab[l][c]

            if p!=0 and (p%2)==(jogador%2):

                caps = explorar_capturas(tab,l,c,p)

                if caps and any(len(seq)>1 for seq,_ in caps):

                    capturas.extend(caps)

                else:

                    for m in movimentos_possiveis(l,c,tab):

                        jogadas.append(((l,c), m))

    if capturas: return [((seq[0], seq[-1]), t) for seq,t in capturas]

    return [((orig, dest), None) for orig,dest in jogadas]

 

def minimax(tab, depth, alpha, beta, max_player):

    if depth==0: return avaliar(tab), None

    if max_player:

        max_eval=-9999

        melhor=None

        for move, resultado in todas_jogadas(tab, 2):

            novo = copy.deepcopy(tab)

            if resultado: novo=resultado

            else: mover(novo, move[0], move[1])

            eval, _ = minimax(novo, depth-1, alpha, beta, False)

            if eval>max_eval: max_eval=eval; melhor=move

            alpha = max(alpha, eval)

            if beta <= alpha: break

        return max_eval, melhor

    else:

        min_eval=9999

        melhor=None

        for move, resultado in todas_jogadas(tab, 1):

            novo = copy.deepcopy(tab)

            if resultado: novo=resultado

            else: mover(novo, move[0], move[1])

            eval,_=minimax(novo, depth-1, alpha, beta, True)

            if eval<min_eval: min_eval=eval; melhor=move

            beta=min(beta,eval)

            if beta<=alpha: break

        return min_eval, melhor

 

def jogada_ia():

    global tabuleiro, turno

    _, j = minimax(tabuleiro, 3, -9999, 9999, True)

    if j:

        mover(tabuleiro,j[0],j[1])

        turno=1

 

# ==============================

# VITÓRIA

# ==============================

def verificar_vencedor():

    b=p=0

    for linha in tabuleiro:

        for x in linha:

            if x in [1,3]: b+=1

            if x in [2,4]: p+=1

    if b==0: return "Pretas venceram!"

    if p==0: return "Brancas venceram!"

    return None

 

def fim_jogo(msg):

    global estado, tabuleiro, turno

    while True:

        janela.fill(FUNDO)

        t=fonte.render(msg,True,BRANCO)

        janela.blit(t,(150,300))

        info=fonte.render("Clique para voltar ao menu",True,BRANCO)

        janela.blit(info,(80,350))

        for e in pygame.event.get():

            if e.type==pygame.QUIT: pygame.quit(); sys.exit()

            if e.type==pygame.MOUSEBUTTONDOWN:

                tabuleiro=reset_tabuleiro()

                turno=1

                estado="menu"

                return

        pygame.display.update()

 

# ==============================

# MENU / REGRAS

# ==============================

def menu():

    global estado

    while True:

        janela.fill(FUNDO)

        mouse=pygame.mouse.get_pos()

        titulo=pygame.font.SysFont("Arial",60).render("DAMAS",True,BRANCO)

        janela.blit(titulo,(200,100))

        def botao(txt,y):

            rect=pygame.Rect(200,y,200,60)

            cor=(100,100,100) if rect.collidepoint(mouse) else (70,70,70)

            pygame.draw.rect(janela,cor,rect,border_radius=10)

            t=fonte.render(txt,True,BRANCO)

            janela.blit(t,t.get_rect(center=rect.center))

            return rect

        b1=botao("JOGAR",250)

        b2=botao("REGRAS",330)

        b3=botao("SAIR",410)

        for e in pygame.event.get():

            if e.type==pygame.QUIT: pygame.quit(); sys.exit()

            if e.type==pygame.MOUSEBUTTONDOWN:

                if b1.collidepoint(mouse): estado="jogo"; return

                if b2.collidepoint(mouse): estado="regras"; return

                if b3.collidepoint(mouse): pygame.quit(); sys.exit()

        pygame.display.update()

 

def regras():

    global estado

    while True:

        janela.fill(FUNDO)

        linhas=["REGRAS",

                "Mover na diagonal",

                "Capturar obrigatoriamente",

                "Damas podem andar e comer todas direções",

                "Captura múltipla permitida",

                "ESC para voltar"]

        for i,l in enumerate(linhas):

            janela.blit(fonte.render(l,True,BRANCO),(80,100+i*40))

        for e in pygame.event.get():

            if e.type==pygame.QUIT: pygame.quit(); sys.exit()

            if e.type==pygame.KEYDOWN and e.key==pygame.K_ESCAPE:

                estado="menu"; return

        pygame.display.update()

 

# ==============================

# JOGO

# ==============================

def jogo():

    global turno, estado

    sel=None

    movs=[]

    while True:

        vencedor=verificar_vencedor()

        if vencedor: fim_jogo(vencedor); return

        if turno==2:

            pygame.time.delay(400)

            jogada_ia()

        for e in pygame.event.get():

            if e.type==pygame.QUIT: pygame.quit(); sys.exit()

            if e.type==pygame.KEYDOWN and e.key==pygame.K_ESCAPE: estado="menu"; return

            if e.type==pygame.MOUSEBUTTONDOWN:

                pos=pygame.mouse.get_pos()

                c=pos[0]//TAMANHO

                l=pos[1]//TAMANHO

                if sel is None:

                    if tabuleiro[l][c] in [1,3]:

                        sel=(l,c)

                        movs=movimentos_possiveis(l,c,tabuleiro)

                else:

                    if (l,c) in movs:

                        mover(tabuleiro,sel,(l,c))

                        turno=2

                    sel=None

                    movs=[]

        desenhar_tabuleiro()

        desenhar_pecas(sel)

        desenhar_movimentos(movs)

        mostrar_turno()

        contar_pecas()

        pygame.display.update()

 

# ==============================

# LOOP PRINCIPAL

# ==============================

while True:

    if estado=="menu": menu()

    elif estado=="jogo": jogo()

    elif estado=="regras": regras()

 