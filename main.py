"""Tinta e Esquecimento — Alfa, plataforma lateral em Pygame.

Executar: python main.py | Testar: python main.py --smoke-test --scene chefe
"""
from __future__ import annotations
import argparse
import json
import math
import os
from pathlib import Path
import random
import sys
import traceback

if '--smoke-test' in sys.argv:
    os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
    os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')
os.environ.setdefault('PYGAME_HIDE_SUPPORT_PROMPT', '1')
import pygame

W, H, FPS = 1152, 720, 60
GOLD = (222, 175, 98)
TEAL = (102, 205, 186)
PAPER = (239, 224, 192)
DARK = (17, 24, 34)
MUTED = (172, 185, 184)
RED = (226, 116, 124)
ROOT = Path(sys.executable).resolve().parent if getattr(sys, 'frozen', False) else Path(__file__).resolve().parent
ASSETS = ROOT / 'assets'
SAVE_DIR = (Path(os.environ['LOCALAPPDATA']) / 'TintaEEsquecimento') if os.environ.get('LOCALAPPDATA') else (Path.home() / '.tinta_e_esquecimento')
CHAPTERS = [
    ('Sala de Contos Infantis', 'Toda historia comeca com um pequeno risco.', 'Recolha os tres livros e entre no portal.'),
    ('Arquivo dos Versos e Mapas', 'Onde falta chao, invente um caminho.', 'Atravesse o arquivo; B desenha uma ponte de tinta.'),
    ('A Ultima Pagina', 'Uma historia lembrada nao pode ser apagada.', 'Reuna tres livros e ative o pedestal com F.'),
]


def load_save():
    data = {'music': 0.7, 'effects': 0.8, 'rankings': []}
    try:
        loaded = json.loads((SAVE_DIR / 'progresso.json').read_text(encoding='utf-8'))
        if isinstance(loaded, dict):
            for key in ('music', 'effects'):
                if isinstance(loaded.get(key), (int, float)):
                    data[key] = max(0.0, min(1.0, float(loaded[key])))
            scores = loaded.get('rankings', [])
            if isinstance(scores, list):
                data['rankings'] = sorted([
                    {'name': str(s['name'])[:18], 'score': max(0, int(s['score']))}
                    for s in scores if isinstance(s, dict) and 'name' in s and 'score' in s
                ], key=lambda x: x['score'], reverse=True)[:5]
    except (ValueError, OSError, KeyError, TypeError):
        pass
    return data


def save_settings(data):
    try:
        SAVE_DIR.mkdir(parents=True, exist_ok=True)
        target = SAVE_DIR / 'progresso.json'
        tmp = target.with_suffix('.tmp')
        tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')
        tmp.replace(target)
    except OSError:
        pass  # Permissoes restritas nao impedem jogar.


def clamp(n, lo, hi):
    return min(hi, max(lo, n))


class Audio:
    def __init__(self, settings):
        self.settings = settings
        self.current = None
        self.available = pygame.mixer.get_init() is not None
        self.sounds = {}
        if not self.available:
            return
        try:
            self.sounds['confirm'] = pygame.mixer.Sound(str(ASSETS / 'audio' / 'confirm.wav'))
        except (pygame.error, FileNotFoundError):
            pass
        for name, pitch in [('ink', 270), ('page', 580), ('hurt', 110), ('spell', 410)]:
            # Sintese pequena, sem exigir um arquivo separado.
            from array import array
            samples = array('h')
            for i in range(4000):
                t = i / 22050
                samples.append(int(4200 * (1-t/.19)**2 * math.sin(2*math.pi*pitch*t)))
            try:
                self.sounds[name] = pygame.mixer.Sound(buffer=samples.tobytes())
            except pygame.error:
                pass

    def play(self, name):
        if self.available and name in self.sounds:
            self.sounds[name].set_volume(self.settings['effects'])
            self.sounds[name].play()

    def music(self, scene):
        if not self.available:
            return
        track = {0: 'menu_music.ogg', 1: 'forest.ogg', 2: 'bells.ogg'}.get(scene, 'menu_music.ogg')
        if track != self.current:
            self.current = track
            path = ASSETS / 'audio' / track
            if not path.exists():
                # Com repositorios antigos, aproveitar trilha antiga se disponivel.
                fallback = ASSETS / 'audio' / {'menu_music.ogg': 'ambiente_contos.ogg',
                                               'forest.ogg': 'ambiente_mapas.ogg',
                                               'bells.ogg': 'sinos_revisor.ogg'}[track]
                path = fallback
            try:
                pygame.mixer.music.load(str(path))
                pygame.mixer.music.play(-1, fade_ms=250)
            except (pygame.error, FileNotFoundError):
                self.current = None
        pygame.mixer.music.set_volume(self.settings['music'] * 0.55)


class Player:
    def __init__(self):
        self.x, self.y = 80.0, 560.0
        self.vy = 0.0
        self.w, self.h = 30, 50
        self.face = 1
        self.on_ground = False
        self.crouch = False
        self.hp = 100.0
        self.ink = 100.0
        self.shield = 0.0
        self.invul = 0.0
        self.shot_cd = 0.0
        self.anim = 0.0

    @property
    def rect(self):
        return pygame.Rect(round(self.x), round(self.y), self.w, self.h)


class Enemy:
    def __init__(self, x, y, boss=False):
        self.x = float(x)
        self.y = float(y)
        self.boss = boss
        self.hp = 220 if boss else 52
        self.max_hp = self.hp
        self.speed = 60 if boss else 75
        self.w, self.h = (80, 98) if boss else (38, 51)
        self.invul = 0.0
        self.cooldown = 1.8
        self.face = -1

    @property
    def rect(self):
        return pygame.Rect(round(self.x), round(self.y), self.w, self.h)


class World:
    FLOOR = 605
    def __init__(self, chapter=0, score=0):
        self.chapter = chapter
        self.width = [2580, 2880, 2680][chapter]
        self.player = Player()
        self.score = score
        self.time = 0.0
        self.camera = 0.0
        self.collected = 0
        self.boss_unlocked = False
        self.projectiles = []
        self.effects = []
        self.message = 'A/D: mover   W: pular   S: agachar   Q: tinta   F: interagir'
        self.message_timer = 6
        self.portal = self.width - 125
        self.pedestal = 1940
        self.bridge = 0.0
        self.gap = (1190, 1350) if chapter == 1 else None
        self.books = []  # (x, y) no topo de plataformas / superficie
        self.platforms = [pygame.Rect(0, self.FLOOR, self.width, H-self.FLOOR)]
        # Plataformas progressivas; salto maximo >100px para evitar becos sem saida.
        if chapter == 0:
            self.platforms += [pygame.Rect(390, 505, 260, 20), pygame.Rect(850, 475, 230, 20),
                               pygame.Rect(1500, 490, 260, 20)]
            self.books = [[485, 470], [946, 440], [1630, 455]]
            enemy_x = [710, 1230, 1910]
        elif chapter == 1:
            self.platforms += [pygame.Rect(355, 502, 250, 20), pygame.Rect(960, 498, 195, 20),
                               pygame.Rect(1560, 505, 240, 20), pygame.Rect(2130, 487, 220, 20)]
            self.books = [[465, 465], [1690, 470], [2220, 450]]
            enemy_x = [770, 1470, 1990, 2550]
        else:
            self.platforms += [pygame.Rect(370, 502, 265, 20), pygame.Rect(950, 500, 270, 20),
                               pygame.Rect(1470, 500, 250, 20)]
            self.books = [[470, 466], [1055, 464], [1585, 464]]
            enemy_x = [775, 1360, 1820]
        self.enemies = [Enemy(x, self.FLOOR-51) for x in enemy_x]
        if chapter == 2:
            self.enemies.append(Enemy(2355, self.FLOOR-98, True))
        self.healing_books = [260, 1150, 1860] if chapter != 1 else [260, 1090, 2050]
        self.heal_ready = [0.0] * len(self.healing_books)

    def tell(self, msg, duration=3.2):
        self.message, self.message_timer = msg, duration

    def near(self, x, dist=84):
        return abs(self.player.x + self.player.w / 2 - x) < dist

    def interact(self):
        p = self.player
        if self.chapter == 2 and self.near(self.pedestal, 95):
            if self.collected == 3:
                if not self.boss_unlocked:
                    self.boss_unlocked = True
                    p.ink = 100
                    self.score += 250
                    self.tell('Escudo do Revisor desativado para toda a batalha!', 5)
                    return 'unlock'
                self.tell('O escudo ja foi desativado. Derrote o Revisor!')
            else:
                self.tell(f'O pedestal precisa dos 3 livros. Faltam {3-self.collected}.', 4)
            return 'interact'
        for i, x in enumerate(self.healing_books):
            if self.near(x, 78):
                if self.heal_ready[i] > 0:
                    self.tell(f'O livro repousa por {math.ceil(self.heal_ready[i])} segundos.')
                    return 'interact'
                p.ink = min(100, p.ink+65)
                p.hp = min(100, p.hp+25)
                self.heal_ready[i] = 7.0
                self.tell('Palavras recuperadas: +65 tinta e +25 vida.')
                return 'page'
        if self.chapter < 2 and self.near(self.portal, 90):
            if self.collected == 3:
                self.score += 500 + round(p.hp * 2)
                return 'next'
            self.tell(f'Recolha os 3 livros antes de avancar. Faltam {3-self.collected}.')
            return 'interact'
        self.tell('Use F perto dos livros verdes, do portal ou do pedestal.')
        return 'interact'

    def move_x(self, dx):
        p = self.player
        p.x = clamp(p.x + dx, 0, self.width-p.w)
        if self.chapter == 1 and self.gap:
            a, b = self.gap
            # Ponte temporaria alternativa a um salto; sem buraco mortal.
            if p.rect.centerx > a and p.rect.centerx < b and self.bridge <= 0 and p.on_ground:
                p.x = a-p.w if dx > 0 else b
                self.tell('Uma fenda! B cria ponte por 8s, ou pule para atravessar.')
        for plat in self.platforms[1:]:
            if p.rect.colliderect(plat) and p.rect.bottom > plat.top+5:
                if dx > 0:
                    p.x = plat.left-p.w
                elif dx < 0:
                    p.x = plat.right

    def jump(self):
        p = self.player
        if p.on_ground and not p.crouch:
            p.vy = -560
            p.on_ground = False
            return True
        return False

    def shoot(self, diagonal=False):
        p = self.player
        if p.shot_cd > 0 or p.ink < 9:
            if p.ink < 9:
                self.tell('Tinta insuficiente. F perto dos livros verdes para recarregar.')
            return False
        dx, dy = (p.face * 0.78, -0.63) if diagonal else (p.face, 0)
        self.projectiles.append([p.x+p.w/2, p.y+21, dx*510, dy*510, 1.6, True, 30])
        p.ink -= 9
        p.shot_cd = 0.25
        return True

    def melee(self):
        p = self.player
        if p.shot_cd > 0 or p.ink < 5:
            return False
        p.ink -= 5
        p.shot_cd = 0.3
        for e in self.enemies:
            if abs((e.x+e.w/2)-(p.x+p.w/2)) < 83 and abs(e.rect.centery-p.rect.centery) < 80 and (e.x-p.x)*p.face >= -5:
                self.damage_enemy(e, 19)
        return True

    def cast_shield(self):
        p = self.player
        if p.ink < 24 or p.shield > 0:
            return False
        p.ink -= 24
        p.shield = 2.7
        return True

    def draw_bridge(self):
        if self.chapter != 1 or self.gap is None:
            return False
        if not (self.gap[0]-110 <= self.player.x <= self.gap[1]+90):
            self.tell('Aproxime-se da fenda para desenhar a ponte.')
            return False
        if self.player.ink < 20:
            self.tell('Faltam 20 pontos de tinta. Leia um livro verde com F.')
            return False
        self.bridge = 8.0
        self.player.ink -= 20
        self.tell('Ponte pronta por 8 segundos!')
        return True

    def hurt(self, amount):
        p = self.player
        if p.invul > 0 or p.shield > 0:
            return False
        p.hp = max(0, p.hp-amount)
        p.invul = 1.1
        return True

    def damage_enemy(self, e, amount):
        if e.boss and not self.boss_unlocked:
            self.tell('O Revisor esta protegido! 3 livros + F no pedestal.', 3.4)
            return False
        e.hp -= amount
        e.invul = 0.18
        if e.hp <= 0:
            self.score += 1500 if e.boss else 80
            self.player.ink = min(100, self.player.ink+10)
        return True

    def update(self, dt, keys):
        dt = min(dt, 0.04)
        self.time += dt
        p = self.player
        for name in ('invul', 'shot_cd', 'shield'):
            setattr(p, name, max(0, getattr(p, name)-dt))
        self.message_timer = max(0, self.message_timer-dt)
        self.heal_ready = [max(0, t-dt) for t in self.heal_ready]
        self.bridge = max(0, self.bridge-dt)
        move = int(keys[pygame.K_d] or keys[pygame.K_RIGHT])-int(keys[pygame.K_a] or keys[pygame.K_LEFT])
        p.crouch = bool(keys[pygame.K_s] or keys[pygame.K_DOWN]) and p.on_ground
        if move:
            p.face = move
            if not p.crouch:
                self.move_x(move * 245 * dt)
                p.anim += dt
        old_bottom = p.rect.bottom
        p.vy = min(820, p.vy + 1300 * dt)
        p.y += p.vy * dt
        p.on_ground = False
        if p.vy >= 0:
            for plat in self.platforms:
                if p.rect.colliderect(plat) and old_bottom <= plat.top + 12:
                    # Fenda no chao so bloqueia ao andar; o pulo sempre e seguro.
                    p.y = plat.top-p.h
                    p.vy = 0
                    p.on_ground = True
                    break
        elif p.vy < 0:
            for plat in self.platforms[1:]:
                if p.rect.colliderect(plat):
                    p.y = plat.bottom
                    p.vy = 10
        if p.y > H + 100:
            p.x, p.y, p.vy = max(45, p.x-140), self.FLOOR-p.h, 0
            self.hurt(12)
        for book in self.books[:]:
            if abs(p.rect.centerx-book[0]) < 31 and abs(p.rect.centery-book[1]) < 58:
                self.books.remove(book)
                self.collected += 1
                self.score += 125
                p.ink = min(100, p.ink+18)
                self.tell(f'Livro recuperado! {self.collected}/3.')
        for e in self.enemies[:]:
            if e.hp <= 0:
                self.enemies.remove(e)
                continue
            e.invul = max(0, e.invul-dt)
            dx = p.x-e.x
            if abs(dx) < (520 if e.boss else 355):
                e.face = 1 if dx > 0 else -1
                e.x += e.face * e.speed * dt
                e.x = clamp(e.x, 35, self.width-e.w-25)
            if e.rect.colliderect(p.rect):
                self.hurt(17 if e.boss else 12)
            if e.boss:
                e.cooldown -= dt
                if e.cooldown <= 0:
                    e.cooldown = 2.15 if self.boss_unlocked else 3.1
                    face = e.face
                    self.projectiles.append([e.x+e.w/2, e.y+52, face*220, 0, 3.3, False, 14])
        for shot in self.projectiles[:]:
            shot[0] += shot[2]*dt
            shot[1] += shot[3]*dt
            shot[4] -= dt
            x,y,vx,vy,ttl,friendly,damage = shot
            hit = ttl <= 0 or x < 0 or x > self.width or y < 0 or y > H
            if friendly:
                for e in self.enemies:
                    if e.rect.inflate(12,12).collidepoint(x,y):
                        self.damage_enemy(e, damage)
                        hit = True
                        break
            elif p.rect.inflate(10,10).collidepoint(x,y):
                self.hurt(damage)
                hit = True
            if hit and shot in self.projectiles:
                self.projectiles.remove(shot)
        self.camera += (clamp(p.x-W*.40, 0, self.width-W)-self.camera)*min(1, dt*8)
        if p.hp <= 0:
            return 'defeat'
        if self.chapter == 2 and not any(e.boss and e.hp > 0 for e in self.enemies):
            self.score += 750 + int(p.hp*3)
            return 'name'
        return None


class Draw:
    def __init__(self, screen):
        self.s = screen
        self.fonts = {}
        self.scenes = []
        for name in ('scene_1.png', 'scene_2.png', 'scene_3.png'):
            path = ASSETS / 'images' / name
            try:
                self.scenes.append(pygame.image.load(str(path)).convert())
            except (pygame.error, FileNotFoundError):
                self.scenes.append(None)
        self.hero = []
        try:
            sheet = pygame.image.load(str(ASSETS/'images'/'classic_hero.png')).convert()
            bg = sheet.get_at((0,0))
            for i in (1,2,3,4):
                frame = pygame.Surface((16,16),pygame.SRCALPHA)
                for y in range(16):
                    for x in range(16):
                        c = sheet.get_at((i*16+x,16+y))
                        if c != bg:
                            frame.set_at((x,y),c)
                self.hero.append(frame)
        except (pygame.error, FileNotFoundError, IndexError):
            self.hero = []

    def font(self, size):
        if size not in self.fonts:
            self.fonts[size] = pygame.font.Font(None,size)
        return self.fonts[size]

    def text(self, txt, x, y, size=24, color=PAPER, center=False):
        image = self.font(size).render(str(txt),True,color)
        self.s.blit(image,image.get_rect(center=(int(x),int(y))) if center else (int(x),int(y)))

    def panel(self, rect, selected=False):
        pygame.draw.rect(self.s,(43,73,75) if selected else (24,34,44),rect,border_radius=7)
        pygame.draw.rect(self.s,TEAL if selected else (55,74,79),rect,2,border_radius=7)

    def image(self, image, rect, shade=0):
        if image is None:
            pygame.draw.rect(self.s,(39,61,67),rect)
            return
        iw,ih=image.get_size()
        factor=max(rect.w/iw, rect.h/ih)
        scaled=pygame.transform.scale(image,(max(1,round(iw*factor)), max(1,round(ih*factor))))
        self.s.blit(scaled,(rect.x+(rect.w-scaled.get_width())//2, rect.y+(rect.h-scaled.get_height())//2))
        if shade:
            veil=pygame.Surface(rect.size, pygame.SRCALPHA)
            veil.fill((9,19,30,shade))
            self.s.blit(veil,rect.topleft)

    def book(self,x,y,scale=1,color=GOLD):
        points=[(-17,-10),(-2,-6),(0,-3),(2,-6),(17,-10),(17,10),(3,14),(0,17),(-3,14),(-17,10)]
        pts=[(int(x+dx*scale),int(y+dy*scale)) for dx,dy in points]
        pygame.draw.polygon(self.s,color,pts)
        pygame.draw.line(self.s,(70,75,70),(x,y-3*scale),(x,y+14*scale),2)

    def hero_at(self,x,y,t,face=1,move=False,scale=3.0,hurt=False):
        if self.hero:
            idx=(1+int(t*8)%3) if move else 0
            sprite=pygame.transform.scale(self.hero[idx],(round(16*scale),round(16*scale)))
            if face<0:
                sprite=pygame.transform.flip(sprite,True,False)
            if hurt:
                sprite.set_alpha(110)
            self.s.blit(sprite,(int(x),int(y)))
        else:
            pygame.draw.rect(self.s,TEAL,(x,y,32,50),border_radius=5)
        pygame.draw.line(self.s,GOLD,(x+24,y+28),(x+24+face*17,y+5),3)

    def title_bg(self,t):
        # Preserva a ilustracao original da arvore na capa.
        self.s.fill(DARK)
        self.image(self.scenes[0],pygame.Rect(0,0,W,H),195)
        pygame.draw.rect(self.s,(73,86,82),(25,25,W-50,H-50),2)

    def menu(self,game):
        self.title_bg(game.time)
        self.text('UM RPG SOBRE O QUE PERMANECE',80,96,24,TEAL)
        self.text('Tinta e',75,145,84)
        self.text('Esquecimento',75,216,84,GOLD)
        self.text('Uma historia pode vencer o Vazio.',80,322,30,MUTED)
        options=['Comecar a historia','Configuracoes','Ranking Top 5','Creditos','Sair']
        for i,label in enumerate(options):
            r=pygame.Rect(80,387+i*47,400,41)
            self.panel(r,game.selection==i)
            self.text(label,100,r.y+9,28)
        pygame.draw.circle(self.s,(24,39,48),(842,310),185)
        pygame.draw.circle(self.s,GOLD,(842,310),186,2)
        self.image(self.scenes[0],pygame.Rect(690,229,304,178))
        pygame.draw.rect(self.s,GOLD,(690,229,304,178),2)
        self.book(841,411,5,PAPER)
        self.hero_at(807,258,game.time,scale=5)
        self.text('ILO',845,116,26,TEAL,True)
        self.text('3 capitulos  |  plataforma lateral',845,555,25,MUTED,True)
        self.text('A/D: mover  W: pular  S: agachar  Q: tinta  F: interagir  ESC: pausa',80,676,21,PAPER)

    def overlay(self,title,lines,footer='ENTER: continuar'):
        veil=pygame.Surface((W,H),pygame.SRCALPHA)
        veil.fill((7,12,22,210))
        self.s.blit(veil,(0,0))
        panel=pygame.Rect(185,148,785,415)
        self.panel(panel)
        self.text(title,235,190,47,GOLD)
        for i,line in enumerate(lines):
            self.text(line,235,277+i*37,27,PAPER)
        self.text(footer,235,519,24,TEAL)

    def game(self,world):
        w=world
        self.s.fill((22,32,43))
        self.image(self.scenes[w.chapter],pygame.Rect(0,105,W,H-105),55)
        camera=w.camera
        # Chao continuo: atravesse o mapa sem quedas impossiveis.
        pygame.draw.rect(self.s,(54,69,62),(0,w.FLOOR,W,H-w.FLOOR))
        pygame.draw.rect(self.s,(115,140,112),(0,w.FLOOR,W,11))
        for x in range(0, w.width,80):
            sx=x-camera
            if -80<sx<W:
                pygame.draw.line(self.s,(64,81,70),(sx,w.FLOOR+22),(sx+38,w.FLOOR+37),2)
        if w.gap:
            a,b=w.gap
            if w.bridge>0:
                pygame.draw.rect(self.s,TEAL,(a-camera,w.FLOOR-8,b-a,12))
            else:
                pygame.draw.rect(self.s,(30,37,51),(a-camera,w.FLOOR-8,b-a,15))
                self.text('B / PULE', (a+b)/2-camera,w.FLOOR-37,22,GOLD,True)
        for p in w.platforms[1:]:
            pygame.draw.rect(self.s,(92,105,88),p.move(-camera,0),border_radius=5)
            pygame.draw.rect(self.s,(152,161,124),pygame.Rect(p.x-camera,p.y,p.w,7))
        for i,x in enumerate(w.healing_books):
            px=x-camera
            pygame.draw.circle(self.s,(24,71,69),(int(px),w.FLOOR-22),30)
            color=TEAL if w.heal_ready[i]<=0 else MUTED
            self.book(px,w.FLOOR-26,0.8,color)
            self.text('F',px,w.FLOOR-68,20,color,True)
        for x,y in w.books:
            sx=x-camera
            self.book(sx,y+math.sin(w.time*4+x)*5,1.2,GOLD)
            pygame.draw.circle(self.s,GOLD,(int(sx),int(y)),26,1)
        if w.chapter<2:
            px=w.portal-camera
            pygame.draw.circle(self.s,(44,77,83),(int(px),w.FLOOR-47),45)
            self.book(px,w.FLOOR-48,1.2,GOLD if w.collected==3 else MUTED)
            self.text('F: PORTAL',px,w.FLOOR-101,22,GOLD,True)
        else:
            px=w.pedestal-camera
            color=TEAL if w.boss_unlocked else GOLD
            pygame.draw.ellipse(self.s,color,(px-70,w.FLOOR-18,140,24),3)
            pygame.draw.circle(self.s,color,(int(px),w.FLOOR-67),36,2)
            self.book(px,w.FLOOR-68,1.3,color)
            self.text('F: PEDESTAL',px,w.FLOOR-133,22,color,True)
        for e in w.enemies:
            x,y=e.x-camera,e.y
            if e.boss:
                shade=PAPER if e.invul>0 else (189,197,188)
                pygame.draw.polygon(self.s,shade,[(x,y+e.h),(x+7,y+17),(x+e.w/2,y-7),(x+e.w-7,y+17),(x+e.w,y+e.h)])
                if not w.boss_unlocked:
                    pygame.draw.ellipse(self.s,GOLD,(x-15,y-22,e.w+30,e.h+43),3)
                self.text('O REVISOR',x+e.w/2,y-52,25,GOLD,True)
                pygame.draw.rect(self.s,RED,(x,y-30,e.w*max(0,e.hp)/e.max_hp,8))
            else:
                shade=PAPER if e.invul>0 else (170,182,171)
                pygame.draw.polygon(self.s,shade,[(x,y+e.h),(x+5,y+7),(x+e.w/2,y-5),(x+e.w-5,y+7),(x+e.w,y+e.h)])
                pygame.draw.circle(self.s,DARK,(int(x+e.w*.35),int(y+20)),3)
                pygame.draw.circle(self.s,DARK,(int(x+e.w*.68),int(y+20)),3)
        p=w.player
        self.hero_at(p.x-camera,p.y,w.time,p.face,bool(p.anim and pygame.time.get_ticks()%650<450),3.3,p.invul>0 and int(w.time*12)%2==0)
        if p.crouch:
            pygame.draw.arc(self.s,TEAL,(p.x-camera,p.y+23,40,25),0,math.pi,3)
        if p.shield>0:
            pygame.draw.ellipse(self.s,TEAL,(p.x-camera-16,p.y-10,66,76),3)
        for x,y,vx,vy,ttl,friendly,damage in w.projectiles:
            pygame.draw.circle(self.s,TEAL if friendly else RED,(int(x-camera),int(y)),7)
        pygame.draw.rect(self.s,DARK,(0,0,W,105))
        self.text('CAPITULO '+str(w.chapter+1)+'/3  '+CHAPTERS[w.chapter][0],31,10,31,GOLD)
        self.text('LIVROS '+str(w.collected)+'/3     SCORE '+str(w.score),760,18,26,TEAL)
        for i,(name,val,col) in enumerate([('VIDA',p.hp,RED),('TINTA',p.ink,TEAL)]):
            x=32+i*265
            self.text(name,x,57,19,MUTED)
            pygame.draw.rect(self.s,(46,55,65),(x+52,59,160,13))
            pygame.draw.rect(self.s,col,(x+52,59,max(0,int(160*val/100)),13))
        self.text('ESC: pausa  Q: tiro  ESPACO: ataque  E: escudo  B: ponte',625,68,19,PAPER)
        if w.message_timer>0:
            self.panel(pygame.Rect(75,638,1000,43))
            self.text(w.message,W/2,657,25,TEAL,True)


class Game:
    def __init__(self):
        if not (ASSETS/'images'/'scene_1.png').exists():
            from preparar_assets import main as prepare
            prepare()
        pygame.mixer.pre_init(22050,-16,1,512)
        pygame.init()
        self.screen = pygame.display.set_mode((W,H))
        pygame.display.set_caption('Tinta e Esquecimento — Alfa')
        self.draw = Draw(self.screen)
        if self.draw.hero:
            pygame.display.set_icon(pygame.transform.scale(self.draw.hero[0],(32,32)))
        self.save = load_save()
        self.audio=Audio(self.save)
        self.world=World()
        self.state='menu'
        self.selection=0
        self.settings_sel=0
        self.clock=pygame.time.Clock()
        self.time=0
        self.running=True
        self.name=''
        self.last_name=''

    def start(self,level=0,score=0):
        self.world=World(level,score)
        self.state='chapter'
        self.audio.play('confirm')

    def event(self,event):
        if event.type==pygame.QUIT:
            self.running=False
            return
        if event.type==pygame.TEXTINPUT and self.state=='name':
            self.name=(self.name+''.join(c for c in event.text if c.isprintable()))[:18]
            return
        if event.type==pygame.MOUSEBUTTONDOWN and event.button==1 and self.state=='menu':
            for i in range(5):
                if pygame.Rect(80,387+i*47,400,41).collidepoint(event.pos):
                    self.selection=i
                    self.menu_action()
                    break
        if event.type!=pygame.KEYDOWN:
            return
        k=event.key
        if self.state=='menu':
            if k in (pygame.K_w,pygame.K_UP):self.selection=(self.selection-1)%5
            elif k in (pygame.K_s,pygame.K_DOWN):self.selection=(self.selection+1)%5
            elif k in (pygame.K_RETURN,pygame.K_SPACE):self.menu_action()
            elif k==pygame.K_ESCAPE:self.running=False
        elif self.state=='config':
            if k in (pygame.K_UP,pygame.K_w):self.settings_sel=(self.settings_sel-1)%2
            elif k in (pygame.K_DOWN,pygame.K_s):self.settings_sel=(self.settings_sel+1)%2
            elif k in (pygame.K_RIGHT,pygame.K_d,pygame.K_LEFT,pygame.K_a):
                name=['music','effects'][self.settings_sel]
                self.save[name]=clamp(round(self.save[name]+(.05 if k in (pygame.K_RIGHT,pygame.K_d) else -.05),2),0,1)
                save_settings(self.save)
                self.audio.play('confirm')
            elif k in (pygame.K_ESCAPE,pygame.K_RETURN):self.state='menu'
        elif self.state=='play':
            if k==pygame.K_ESCAPE:self.state='pause'
            elif k in (pygame.K_w,pygame.K_UP,pygame.K_SPACE) and k!=pygame.K_SPACE:
                self.world.jump()
            elif k==pygame.K_q:
                keys=pygame.key.get_pressed()
                # Segurar W + direcao e Q ativa tiro diagonal para cima.
                if self.world.shoot(bool(keys[pygame.K_w] or keys[pygame.K_UP])):
                    self.audio.play('ink')
            elif k==pygame.K_SPACE:
                if self.world.melee():self.audio.play('ink')
            elif k==pygame.K_e:
                if self.world.cast_shield():self.audio.play('spell')
            elif k==pygame.K_b:
                if self.world.draw_bridge():self.audio.play('spell')
            elif k==pygame.K_f:
                outcome=self.world.interact()
                if outcome=='next':
                    self.start(self.world.chapter+1,self.world.score)
                elif outcome in ('page','unlock'):
                    self.audio.play('page' if outcome=='page' else 'spell')
        elif self.state=='chapter':
            if k in (pygame.K_RETURN,pygame.K_SPACE):self.state='play'
            elif k==pygame.K_ESCAPE:self.state='menu'
        elif self.state=='pause':
            if k in (pygame.K_RETURN,pygame.K_ESCAPE):self.state='play'
            elif k==pygame.K_r:self.start(self.world.chapter,self.world.score)
            elif k==pygame.K_BACKSPACE:self.state='menu'
        elif self.state=='defeat':
            if k in (pygame.K_r,pygame.K_RETURN):self.start(self.world.chapter,self.world.score)
            elif k==pygame.K_ESCAPE:self.state='menu'
        elif self.state=='name':
            if k==pygame.K_BACKSPACE:self.name=self.name[:-1]
            elif k==pygame.K_RETURN:
                pygame.key.stop_text_input()
                name=self.name.strip() or 'Ilo'
                self.last_name=name
                self.save['rankings'].append({'name':name,'score':self.world.score})
                self.save['rankings']=sorted(self.save['rankings'],key=lambda row:row['score'],reverse=True)[:5]
                save_settings(self.save)
                self.state='ending'
        elif k in (pygame.K_RETURN,pygame.K_ESCAPE,pygame.K_BACKSPACE):
            self.state='menu'

    def menu_action(self):
        self.audio.play('confirm')
        if self.selection==0:self.start(0)
        elif self.selection==1:self.state='config'
        elif self.selection==2:self.state='ranking'
        elif self.selection==3:self.state='credits'
        else:self.running=False

    def update(self,dt):
        self.time+=dt
        self.audio.music(0 if self.state in ('menu','config','credits','ranking','chapter','name','ending') else (2 if self.world.chapter==2 else 1))
        if self.state=='play':
            outcome=self.world.update(dt,pygame.key.get_pressed())
            if outcome:
                self.state=outcome
                if outcome=='name':
                    self.name=''
                    pygame.key.start_text_input()

    def draw_frame(self):
        d=self.draw
        if self.state in ('menu','config','ranking','credits'):
            d.menu(self)
            if self.state=='config':
                d.overlay('CONFIGURACOES',[
                    ('> ' if self.settings_sel==0 else '  ')+f'Musica: {round(self.save["music"]*100)}%   [A/D ou setas]',
                    ('> ' if self.settings_sel==1 else '  ')+f'Efeitos: {round(self.save["effects"]*100)}%   [A/D ou setas]',
                    'Volume salvo automaticamente no computador.',
                ], 'ESC ou ENTER: voltar')
            elif self.state=='ranking':
                scores=self.save['rankings'][:5]
                lines=[f'{i+1:>2}. {score["name"]:<18}   {score["score"]} pontos' for i,score in enumerate(scores)]
                d.overlay('RANKING TOP 5',lines or ['Ainda nao ha pontos registrados.'], 'ENTER ou ESC: voltar')
            elif self.state=='credits':
                d.overlay('CREDITOS',[
                    'Conceito original: Emerson. Assistencia de programacao: IA.',
                    'Arte e cenarios: arquivos enviados / CraftPix Freebies.',
                    'Personagem: GrafxKid (CC0). Ver CREDITOS.md.',
                    'Audio: Packsmithy, newlocknew, benson_arizona, kevp888.',
                ],'ENTER ou ESC: voltar')
        elif self.state=='ending':
            d.title_bg(self.time)
            d.overlay('A HISTORIA FOI SALVA!',[
                'O Revisor foi derrotado. A biblioteca resistiu.',
                'Jogador: '+self.last_name,
                'Pontuacao: '+str(self.world.score),
                'A pontuacao foi registrada no ranking Top 5.'
            ],'ENTER: voltar ao menu')
        else:
            d.game(self.world)
            if self.state=='chapter':
                i=self.world.chapter
                d.overlay(CHAPTERS[i][0],[
                    CHAPTERS[i][1],CHAPTERS[i][2],
                    'A/D ou setas: andar  |  W ou cima: pular  |  S: agachar',
                    'Q: tinta  |  W+Q: tiro diagonal  |  F: interagir',
                    'Espaco: ataque curto  |  E: escudo  |  ESC: pausa'
                ],'ENTER: iniciar capitulo')
            elif self.state=='pause':
                d.overlay('JOGO PAUSADO',[
                    'Uma historia tambem pode descansar.',
                    'Use os livros verdes para restaurar vida e tinta.'
                ],'ENTER ou ESC: voltar  |  R: reiniciar  |  BACKSPACE: menu')
            elif self.state=='defeat':
                d.overlay('PAGINA APAGADA',[
                    'O Vazio venceu desta vez, mas a historia continua.',
                    'Revise a rota, desvie e recupere energia nos livros verdes.'
                ],'ENTER ou R: tentar novamente  |  ESC: menu')
        pygame.display.flip()

    def run(self,frames=None,screenshot=None):
        counter=0
        while self.running:
            dt=self.clock.tick(FPS)/1000
            for ev in pygame.event.get():self.event(ev)
            self.update(dt)
            self.draw_frame()
            counter+=1
            if frames and counter>=frames:break
        if screenshot:
            pygame.image.save(self.screen,screenshot)
        pygame.quit()


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--smoke-test',action='store_true')
    parser.add_argument('--frames',type=int)
    parser.add_argument('--screenshot')
    parser.add_argument('--scene',choices=['menu','fase1','fase2','chefe','final'],default='menu')
    args=parser.parse_args()
    game=Game()
    if args.scene in ('fase1','fase2','chefe'):
        level={'fase1':0,'fase2':1,'chefe':2}[args.scene]
        game.start(level)
        game.state='play'
    elif args.scene=='final':
        game.state='ending'
        game.last_name='Ilo'
    game.run(args.frames or (3 if args.smoke_test else None),args.screenshot)

if __name__=='__main__':
    try:
        main()
    except Exception as err:
        root=Path(os.environ.get('LOCALAPPDATA',str(Path.home()))) / 'TintaEEsquecimento'
        try:
            root.mkdir(parents=True, exist_ok=True)
            (root/'erro-jogo.txt').write_text(traceback.format_exc(),encoding='utf-8')
        except OSError:
            pass
        print('Erro no jogo:',err, file=sys.stderr)
        traceback.print_exc()
        raise SystemExit(1)