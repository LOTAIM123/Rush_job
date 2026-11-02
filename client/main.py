import os

import pygame
from pygame.locals import *

from game import (BLOCKS, COLS, EFFECT_TTL, HEIGHT, PLAYER_SIZE, POWERUPS,
                  ROWS, TILE, UPGRADES, WIDTH, Game, Input, shop_col_near)

from . import api_client, audio

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEXTURE_FILES = {1: "dirt.png", 2: "stone.png", 3: "hard.png", 4: "gold.png",
                 5: "lava.png", 6: "brambles.png"}
PLAYER_TEXTURE_FILE = "player.png"
EMPTY = (62, 56, 66)
MENU_OY = (HEIGHT - 540) // 2     # izvēlne ir veidota 540 px augstumam: centrējam
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


def draw_shop_floor(screen, col, cam_x):
    if shop_col_near(col) is not None:
        pygame.draw.rect(screen, (78, 70, 92), (col * TILE - cam_x, 0, TILE, HEIGHT))


def draw_shop_stall(screen, col, cam_x, small):
    # letes platums pārsniedz vienu rūti, tāpēc zīmējama PĒC visām grīdām
    # (citādi nākamās kolonnas grīda pārklāj pusi letes)
    if shop_col_near(col) == col:
        x = col * TILE - cam_x
        stall = pygame.Rect(x - TILE // 2, (ROWS // 2 - 1) * TILE, TILE * 2, TILE * 2)
        pygame.draw.rect(screen, (190, 120, 40), stall, border_radius=4)
        pygame.draw.rect(screen, (255, 220, 140), stall, 2, border_radius=4)
        label = small.render("VEIKALS", True, (255, 255, 255))
        screen.blit(label, label.get_rect(midbottom=(stall.centerx, stall.top - 4)))


def draw_effects(screen, game, cam_x):
    for e in game.effects:
        frac = 1 - e["ttl"] / EFFECT_TTL            # 0 -> 1
        alpha = max(0, int(220 * (1 - frac)))
        size = (2 * e["r"] + 1) * TILE
        centre = (e["col"] * TILE + TILE // 2 - cam_x, e["row"] * TILE + TILE // 2)
        surf = pygame.Surface((size, size), SRCALPHA)
        if e["kind"] == "blast":
            rad = int(size / 2 * (0.35 + 0.65 * frac))
            pygame.draw.circle(surf, (255, 150, 40, alpha), (size // 2, size // 2), rad)
            pygame.draw.circle(surf, (255, 240, 160, alpha), (size // 2, size // 2), rad, 3)
        else:
            pygame.draw.rect(surf, (120, 220, 255, alpha // 2), surf.get_rect())
            pygame.draw.rect(surf, (210, 245, 255, alpha), surf.get_rect(), 3)
        screen.blit(surf, surf.get_rect(center=centre))


def draw_game(screen, game, textures, cam_x, font, small):
    screen.fill(EMPTY)
    first = int(cam_x // TILE)
    for col in range(first, first + COLS + 2):
        draw_shop_floor(screen, col, cam_x)
    for col in range(first, first + COLS + 2):
        draw_shop_stall(screen, col, cam_x, small)
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
                elif kind == 5:      # lava: spilgti plankumi
                    for ox, oy in ((0.3, 0.3), (0.7, 0.55), (0.4, 0.8)):
                        pygame.draw.circle(screen, (255, 200, 60), (r.x + r.w * ox, r.y + r.h * oy), 4)
                elif kind == 6:      # krūmi: ērkšķi
                    pygame.draw.line(screen, (150, 210, 110), r.topleft, r.bottomright, 2)
                    pygame.draw.line(screen, (150, 210, 110), r.topright, r.bottomleft, 2)

    for (c, r), dmg in game.damage.items():       # plaisas uz sabojātajiem blokiem
        if dmg <= 0 or not first - 1 <= c <= first + COLS + 1:
            continue
        rect = pygame.Rect(c * TILE - cam_x, r * TILE, TILE, TILE)
        for i in range(int(min(dmg, 0.99) * 5) + 1):
            y = rect.top + 6 + i * 7
            pygame.draw.line(screen, (20, 20, 20), (rect.left + 4, y), (rect.right - 4, y + 4), 2)

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

    draw_effects(screen, game, cam_x)

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

    screen.blit(small.render(f"Siena: {game.wall_speed():.0f} px/s", True, (230, 120, 120)), (WIDTH - 230, 138))
    y = 166
    for key, (pname, pcolor, mode) in POWERUPS.items():
        timers = game.powerups[key]
        if timers:
            stack = f" x{len(timers)}" if mode == "power" else ""
            screen.blit(small.render(f"{pname}{stack}  {max(timers):0.1f}s", True, pcolor),
                        (WIDTH - 230, y))
            y += 22
    for i, (text, _) in enumerate(game.messages):
        draw_centered(screen, font.render(text, True, (255, 255, 255)), HEIGHT // 4 + i * 34)

    if game.alive and game.shop_here() is not None:
        draw_centered(screen, font.render("Nospied E, lai atvērtu veikalu", True, (255, 230, 150)), HEIGHT - 70)

    if not game.alive:
        shade = pygame.Surface((WIDTH, HEIGHT), SRCALPHA)
        shade.fill((0, 0, 0, 170))
        screen.blit(shade, (0, 0))
        title = "SADEGA LAVĀ!" if game.death_cause == "lava" else "SADRUMSTS!"
        draw_centered(screen, font.render(title, True, (255, 90, 90)), HEIGHT // 2 - 50)
        draw_centered(screen, font.render(f"Rezultāts: {game.score}", True, (255, 255, 255)), HEIGHT // 2)
        draw_centered(screen, small.render("Enter: spēlēt vēlreiz    Esc: izvēlne", True, (220, 220, 220)), HEIGHT // 2 + 50)


SHOP_KEYS = [K_1, K_2, K_3, K_4]
UPGRADE_KEYS = list(UPGRADES)


def draw_shop(screen, game, font, small):
    shade = pygame.Surface((WIDTH, HEIGHT), SRCALPHA)
    shade.fill((0, 0, 0, 170))
    screen.blit(shade, (0, 0))
    panel = pygame.Rect(0, 0, 620, 410)
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
    screen.blit(small.render("1-4: pirkt      E / Esc: aizvērt", True, (200, 200, 210)),
                (panel.x + 24, panel.bottom - 36))


def draw_menu(screen, fonts, buttons, name, board):
    title_font, font, small = fonts
    screen.fill((50, 50, 58))
    draw_centered(screen, title_font.render("RUSH JOB", True, (255, 210, 80)), 40 + MENU_OY)
    draw_centered(screen, small.render("Izrok ceļu, pirms siena tevi sasmalcina!", True, (210, 210, 210)), 105 + MENU_OY)

    mouse = pygame.mouse.get_pos()
    for rect, label in buttons:
        base = (110, 70, 70) if label == "Iziet" else (70, 110, 70)
        hover = (150, 90, 90) if label == "Iziet" else (90, 150, 90)
        pygame.draw.rect(screen, hover if rect.collidepoint(mouse) else base, rect, border_radius=8)
        pygame.draw.rect(screen, (255, 255, 255), rect, 2, border_radius=8)
        txt = font.render(label, True, (255, 255, 255))
        screen.blit(txt, txt.get_rect(center=rect.center))

    draw_centered(screen, small.render(f"Vārds: {name}_", True, (255, 255, 255)), 345 + MENU_OY)

    draw_centered(screen, small.render("Labākie rezultāti", True, (255, 210, 80)), 385 + MENU_OY)
    if board.error:
        draw_centered(screen, small.render("(serveris nav pieejams)", True, (170, 170, 180)), 412 + MENU_OY)
    for i, row in enumerate(board.rows[:5]):
        line = f"{i + 1}. {row['name']} - {row['score']}"
        draw_centered(screen, small.render(line, True, (220, 220, 220)), 412 + MENU_OY + i * 22)
    draw_centered(screen, small.render(
        "Kustība: bultiņas/WASD   Racšana: Space vai pele   E: veikals   M/F2: skaņa", True, (150, 150, 160)), HEIGHT - 26)


def main():
    pygame.mixer.pre_init(44100, -16, 2, 512)
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Rush Job")
    clock = pygame.time.Clock()
    sfx = audio.Audio(BASE_DIR)
    sfx.play_music()
    fonts = (pygame.font.Font(None, 100), pygame.font.Font(None, 44), pygame.font.Font(None, 26))
    font, small = fonts[1], fonts[2]

    start_btn = pygame.Rect(0, 0, 240, 54)
    start_btn.center = (WIDTH // 2, 195 + MENU_OY)
    quit_btn = pygame.Rect(0, 0, 240, 54)
    quit_btn.center = (WIDTH // 2, 262 + MENU_OY)
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
        sfx.play_music()

    while True:
        dt = min(clock.tick(60) / 1000.0, 0.05)
        sfx.update()
        for event in pygame.event.get():
            if event.type == QUIT:
                return
            if event.type == KEYDOWN and (event.key == K_F2 or (state != "menu" and event.key == K_m)):
                sfx.toggle_mute()          # M (spēlē) vai F2 (jebkur): skaņa ieslēgta/izslēgta
                continue
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
                    sfx.play_music()
                elif event.key == K_RETURN and not game.alive:
                    start()
                elif event.key == K_e and game.alive and game.shop_here() is not None:
                    state = "shop"

        if state == "menu":
            draw_menu(screen, fonts, buttons, name, board)
        else:
            if state == "playing":
                game.update(dt, read_input(game, camera_x(game)))
                sfx.handle(game.pop_events())
                if not game.alive and not submitted:
                    submitted = True
                    api_client.submit_score(name.strip() or "Anonīms", game.score, game.time)
            draw_game(screen, game, textures, camera_x(game), font, small)
            if state == "shop":
                draw_shop(screen, game, font, small)
        pygame.display.flip()


if __name__ == "__main__":
    main()
