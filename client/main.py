"""pygame klients: ievade, zīmēšana, sakari ar API.
Palaist no mapes `spele/`:  python -m client.main
"""
import os

import pygame
from pygame.locals import *

from game import (BLOCKS, COLS, HEIGHT, PLAYER_SIZE, ROWS, TILE, UPGRADES,
                  WIDTH, Game, Input, shop_col_near)

from . import api_client

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEXTURE_FILES = {1: "dirt.png", 2: "stone.png", 3: "hard.png", 4: "gold.png"}
PLAYER_TEXTURE_FILE = "player.png"
EMPTY = (62, 56, 66)
MAX_NAME = 12


def load_textures():
    textures = {}
    for kind, name in TEXTURE_FILES.items():
        try:
            img = pygame.image.load(os.path.join(BASE_DIR, "textures", name)).convert_alpha()
            textures[kind] = pygame.transform.scale(img, (TILE, TILE))
        except (FileNotFoundError, pygame.error):
            textures[kind] = None
    try:
        img = pygame.image.load(os.path.join(BASE_DIR, "textures", PLAYER_TEXTURE_FILE)).convert_alpha()
        textures["player"] = pygame.transform.scale(img, (PLAYER_SIZE, PLAYER_SIZE))
    except (FileNotFoundError, pygame.error):
        textures["player"] = None
    return textures


def draw_centered(screen, surf, y):
    screen.blit(surf, surf.get_rect(centerx=WIDTH // 2, y=y))


def read_input(game, cam_x):
    keys = pygame.key.get_pressed()
    inp = Input(
        move_x=(keys[K_RIGHT] or keys[K_d]) - (keys[K_LEFT] or keys[K_a]),
        move_y=(keys[K_DOWN] or keys[K_s]) - (keys[K_UP] or keys[K_w]),
        mine_facing=bool(keys[K_SPACE]),
    )
    if pygame.mouse.get_pressed()[0]:
        mx, my = pygame.mouse.get_pos()
        inp.mine_tile = (int((mx + cam_x) // TILE), my // TILE)
    return inp


def camera_x(game):
    return max(0.0, game.player.centerx - WIDTH * 0.4)


def draw_shop_room(screen, col, cam_x, small):
    centre = shop_col_near(col)
    if centre is None:
        return
    x = col * TILE - cam_x
    pygame.draw.rect(screen, (78, 70, 92), (x, 0, TILE, HEIGHT))
    if col == centre:
        stall = pygame.Rect(x - TILE // 2, (ROWS // 2 - 1) * TILE, TILE * 2, TILE * 2)
        pygame.draw.rect(screen, (190, 120, 40), stall, border_radius=4)
        pygame.draw.rect(screen, (255, 220, 140), stall, 2, border_radius=4)
        label = small.render("VEIKALS", True, (255, 255, 255))
        screen.blit(label, label.get_rect(midbottom=(stall.centerx, stall.top - 4)))


def draw_game(screen, game, textures, cam_x, font, small):
    screen.fill(EMPTY)
    first = int(cam_x // TILE)
    for col in range(first, first + COLS + 2):
        draw_shop_room(screen, col, cam_x, small)
        for row in range(ROWS):
            kind = game.world.blocks.get((col, row))
            if kind is None:
                continue
            color = BLOCKS[kind][0]
            r = pygame.Rect(col * TILE - cam_x, row * TILE, TILE, TILE)
            tex = textures.get(kind)
            if tex:
                screen.blit(tex, r)
            else:
                pygame.draw.rect(screen, color, r)
                pygame.draw.rect(screen, tuple(max(0, c - 35) for c in color), r, 1)
                if kind == 4:
                    pygame.draw.circle(screen, (255, 235, 130), r.center, 5)

    if game.mine_target in game.world.blocks:
        hardness = BLOCKS[game.world.blocks[game.mine_target]][1]
        frac = min(1.0, game.mine_progress / hardness)
        c, r = game.mine_target
        rect = pygame.Rect(c * TILE - cam_x, r * TILE, TILE, TILE)
        for i in range(int(frac * 5) + 1):
            y = rect.top + 5 + i * 5
            pygame.draw.line(screen, (20, 20, 20), (rect.left + 3, y), (rect.right - 3, y + 3), 2)

    pl = game.player
    p = pygame.Rect(pl.x - cam_x, pl.y, pl.w, pl.h)
    fx, fy = game.facing
    sprite = textures.get("player")
    if sprite:
        if fx < 0:
            sprite = pygame.transform.flip(sprite, True, False)
        screen.blit(sprite, p)
    else:
        pygame.draw.rect(screen, (90, 170, 255), p, border_radius=4)
        pygame.draw.rect(screen, (30, 60, 110), p, 2, border_radius=4)
        pygame.draw.circle(screen, (255, 255, 255), (p.centerx + fx * 6, p.centery + fy * 6), 3)

    wx = int(game.wall_x - cam_x)
    if wx > 0:
        pygame.draw.rect(screen, (150, 30, 30), (0, 0, wx, HEIGHT))
    for y in range(0, HEIGHT, 20):
        pygame.draw.polygon(screen, (200, 50, 50), [(wx, y), (wx, y + 20), (wx + 12, y + 10)])

    screen.blit(font.render(f"Punkti: {game.score}", True, (255, 255, 255)), (WIDTH - 230, 10))
    screen.blit(font.render(f"Zelts: {game.gold}", True, (255, 215, 80)), (WIDTH - 230, 40))
    screen.blit(small.render(f"Distance: {game.distance} m", True, (220, 220, 220)), (WIDTH - 230, 72))
    screen.blit(small.render(f"Nākamais veikals: {game.next_shop_distance()} m", True, (170, 170, 180)), (WIDTH - 230, 94))
    screen.blit(small.render(f"Laiks: {game.time:0.1f}s", True, (170, 170, 180)), (WIDTH - 230, 116))

    if game.alive and game.shop_here() is not None:
        draw_centered(screen, font.render("Nospied E, lai atvērtu veikalu", True, (255, 230, 150)), HEIGHT - 70)

    if not game.alive:
        shade = pygame.Surface((WIDTH, HEIGHT), SRCALPHA)
        shade.fill((0, 0, 0, 170))
        screen.blit(shade, (0, 0))
        draw_centered(screen, font.render("SADRUMSTS!", True, (255, 90, 90)), HEIGHT // 2 - 50)
        draw_centered(screen, font.render(f"Rezultāts: {game.score}", True, (255, 255, 255)), HEIGHT // 2)
        draw_centered(screen, small.render("Enter: spēlēt vēlreiz    Esc: izvēlne", True, (220, 220, 220)), HEIGHT // 2 + 50)


SHOP_KEYS = [K_1, K_2, K_3]
UPGRADE_KEYS = list(UPGRADES)


def draw_shop(screen, game, font, small):
    shade = pygame.Surface((WIDTH, HEIGHT), SRCALPHA)
    shade.fill((0, 0, 0, 170))
    screen.blit(shade, (0, 0))
    panel = pygame.Rect(0, 0, 620, 340)
    panel.center = (WIDTH // 2, HEIGHT // 2)
    pygame.draw.rect(screen, (50, 46, 60), panel, border_radius=10)
    pygame.draw.rect(screen, (255, 220, 140), panel, 2, border_radius=10)
    screen.blit(font.render("VEIKALS", True, (255, 210, 80)), (panel.x + 24, panel.y + 18))
    gold = font.render(f"Zelts: {game.gold}", True, (255, 215, 80))
    screen.blit(gold, gold.get_rect(topright=(panel.right - 24, panel.y + 18)))
    for i, key in enumerate(UPGRADE_KEYS):
        name = UPGRADES[key][0]
        level = game.levels[key]
        cost = game.upgrade_cost(key)
        y = panel.y + 90 + i * 64
        affordable = cost is not None and game.gold >= cost
        color = (255, 255, 255) if affordable else (130, 130, 140)
        screen.blit(font.render(f"{i + 1}. {name}", True, color), (panel.x + 24, y))
        screen.blit(small.render(f"Līmenis: {level}", True, (170, 170, 180)), (panel.x + 44, y + 28))
        price = "MAKS." if cost is None else f"{cost} zelts"
        p = font.render(price, True, color)
        screen.blit(p, p.get_rect(topright=(panel.right - 24, y)))
    screen.blit(small.render("1-3: pirkt      E / Esc: aizvērt", True, (200, 200, 210)),
                (panel.x + 24, panel.bottom - 36))


def draw_menu(screen, fonts, buttons, name, board):
    title_font, font, small = fonts
    screen.fill((50, 50, 58))
    draw_centered(screen, title_font.render("RUSH JOB", True, (255, 210, 80)), 40)
    draw_centered(screen, small.render("Izrok ceļu, pirms siena tevi sasmalcina!", True, (210, 210, 210)), 105)

    mouse = pygame.mouse.get_pos()
    for rect, label in buttons:
        base = (110, 70, 70) if label == "Iziet" else (70, 110, 70)
        hover = (150, 90, 90) if label == "Iziet" else (90, 150, 90)
        pygame.draw.rect(screen, hover if rect.collidepoint(mouse) else base, rect, border_radius=8)
        pygame.draw.rect(screen, (255, 255, 255), rect, 2, border_radius=8)
        txt = font.render(label, True, (255, 255, 255))
        screen.blit(txt, txt.get_rect(center=rect.center))

    draw_centered(screen, small.render(f"Vārds: {name}_", True, (255, 255, 255)), 345)

    draw_centered(screen, small.render("Labākie rezultāti", True, (255, 210, 80)), 385)
    if board.error:
        draw_centered(screen, small.render("(serveris nav pieejams)", True, (170, 170, 180)), 412)
    for i, row in enumerate(board.rows[:5]):
        line = f"{i + 1}. {row['name']} - {row['score']}"
        draw_centered(screen, small.render(line, True, (220, 220, 220)), 412 + i * 22)
    draw_centered(screen, small.render(
        "Kustība: bultiņas/WASD   Racšana: Space vai pele   E: veikals", True, (150, 150, 160)), HEIGHT - 26)


def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Rush Job")
    clock = pygame.time.Clock()
    fonts = (pygame.font.Font(None, 100), pygame.font.Font(None, 44), pygame.font.Font(None, 26))
    font, small = fonts[1], fonts[2]

    start_btn = pygame.Rect(0, 0, 240, 54)
    start_btn.center = (WIDTH // 2, 195)
    quit_btn = pygame.Rect(0, 0, 240, 54)
    quit_btn.center = (WIDTH // 2, 262)
    buttons = [(start_btn, "Sākt"), (quit_btn, "Iziet")]

    textures = load_textures()
    game = Game()
    board = api_client.Leaderboard()
    board.refresh()
    name = os.environ.get("USERNAME") or os.environ.get("USER") or "Spēlētājs"
    name = name[:MAX_NAME]
    state = "menu"
    submitted = False

    def start():
        nonlocal state, submitted
        game.reset()
        submitted = False
        state = "playing"

    while True:
        dt = min(clock.tick(60) / 1000.0, 0.05)
        for event in pygame.event.get():
            if event.type == QUIT:
                return
            if state == "menu":
                if event.type == MOUSEBUTTONDOWN and event.button == 1:
                    if start_btn.collidepoint(event.pos):
                        start()
                    elif quit_btn.collidepoint(event.pos):
                        return
                elif event.type == KEYDOWN:
                    if event.key == K_RETURN:
                        start()
                    elif event.key == K_BACKSPACE:
                        name = name[:-1]
                    elif event.unicode and event.unicode.isprintable() and len(name) < MAX_NAME:
                        name += event.unicode
            elif state == "shop":
                if event.type == KEYDOWN:
                    if event.key in (K_ESCAPE, K_e):
                        state = "playing"
                    elif event.key in SHOP_KEYS:
                        game.buy(UPGRADE_KEYS[SHOP_KEYS.index(event.key)])
            elif event.type == KEYDOWN:
                if event.key == K_ESCAPE:
                    state = "menu"
                    board.refresh()
                elif event.key == K_RETURN and not game.alive:
                    start()
                elif event.key == K_e and game.alive and game.shop_here() is not None:
                    state = "shop"

        if state == "menu":
            draw_menu(screen, fonts, buttons, name, board)
        else:
            if state == "playing":
                game.update(dt, read_input(game, camera_x(game)))
                if not game.alive and not submitted:
                    submitted = True
                    api_client.submit_score(name.strip() or "Anonīms", game.score, game.time)
            draw_game(screen, game, textures, camera_x(game), font, small)
            if state == "shop":
                draw_shop(screen, game, font, small)
        pygame.display.flip()


if __name__ == "__main__":
    main()
