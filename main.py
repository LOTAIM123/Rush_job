import random
import pygame
from pygame.locals import *

#settings
TILE = 30
COLS, ROWS = 32, 18
WIDTH, HEIGHT = COLS * TILE, ROWS * TILE  # 960 x 540, same as the original window

PLAYER_SIZE = 22
PLAYER_SPEED = 150          # pixels per second
REACH = 2.2                 # mouse mining reach, in tiles

WALL_START_X = TILE         # right edge of the wall at the start (world pixels)
WALL_SPEED_START = 18       # pixels per second
WALL_SPEED_GAIN = 0.8       # extra px/s per second survived
WALL_SPEED_MAX = 90

SAFE_COLS = 7               # mostly empty columns around the spawn point

# block id -> (colour, seconds to mine, score value)
BLOCKS = {
    1: ((139, 105, 70), 0.25, 1),    # dirt
    2: ((120, 120, 125), 0.55, 2),   # stone
    3: ((70, 70, 85), 1.1, 4),       # hard rock
    4: ((235, 190, 50), 0.8, 10),    # gold
}

BG = (40, 36, 44)
EMPTY = (62, 56, 66)


#world
class World:
    """Grid of breakable blocks that keeps generating to the right forever."""

    def __init__(self):
        self.blocks = {}
        self.generated_to = -1

    def generate_column(self, col):
        for row in range(ROWS):
            if col < SAFE_COLS:
                if random.random() < 0.08:
                    self.blocks[(col, row)] = 1
                continue
            r = random.random()
            if r < 0.15:
                continue                       # empty pocket
            t = random.random()
            if t < 0.45:
                kind = 1
            elif t < 0.80:
                kind = 2
            elif t < 0.95:
                kind = 3
            else:
                kind = 4
            self.blocks[(col, row)] = kind

    def ensure(self, max_col):
        while self.generated_to < max_col:
            self.generated_to += 1
            self.generate_column(self.generated_to)

    def prune(self, min_col):
        for key in [k for k in self.blocks if k[0] < min_col]:
            del self.blocks[key]

    def solid_at(self, col, row):
        if row < 0 or row >= ROWS:
            return True
        return (col, row) in self.blocks


#game
class Game:
    def __init__(self):
        self.reset()

    def reset(self):
        self.world = World()
        self.world.ensure(COLS + 4)
        self.player = pygame.Rect(0, 0, PLAYER_SIZE, PLAYER_SIZE)
        self.player.center = (6 * TILE + TILE // 2, ROWS // 2 * TILE + TILE // 2)
        self.facing = (1, 0)
        self.wall_x = float(WALL_START_X)
        self.time = 0.0
        self.score = 0
        self.mine_target = None
        self.mine_progress = 0.0
        self.cam_x = 0.0
        self.alive = True

    #movement
    def collides(self, rect):
        c0, c1 = rect.left // TILE, (rect.right - 1) // TILE
        r0, r1 = rect.top // TILE, (rect.bottom - 1) // TILE
        for c in range(c0, c1 + 1):
            for r in range(r0, r1 + 1):
                if self.world.solid_at(c, r):
                    return True
        return False

    def move_axis(self, dx, dy):
        self.player.x += dx
        self.player.y += dy
        if self.collides(self.player):
            if dx > 0:
                self.player.right = (self.player.right // TILE) * TILE
            elif dx < 0:
                self.player.left = (self.player.left // TILE + 1) * TILE
            if dy > 0:
                self.player.bottom = (self.player.bottom // TILE) * TILE
            elif dy < 0:
                self.player.top = (self.player.top // TILE + 1) * TILE

    def update_player(self, dt, keys):
        dx = (keys[K_RIGHT] or keys[K_d]) - (keys[K_LEFT] or keys[K_a])
        dy = (keys[K_DOWN] or keys[K_s]) - (keys[K_UP] or keys[K_w])
        if dx:
            self.facing = (dx, 0)
        elif dy:
            self.facing = (0, dy)
        step = PLAYER_SPEED * dt
        # use whole pixels, carry nothing over: fine at 60 fps
        self.move_axis(round(dx * step), 0)
        self.move_axis(0, round(dy * step))

    # -- mining -------------------------------------------------------
    def keyboard_target(self):
        fx, fy = self.facing
        px = self.player.centerx + fx * (PLAYER_SIZE // 2 + 4)
        py = self.player.centery + fy * (PLAYER_SIZE // 2 + 4)
        return (px // TILE, py // TILE)

    def mouse_target(self):
        mx, my = pygame.mouse.get_pos()
        col = int((mx + self.cam_x) // TILE)
        row = my // TILE
        cx, cy = col * TILE + TILE / 2, row * TILE + TILE / 2
        dist = ((cx - self.player.centerx) ** 2 + (cy - self.player.centery) ** 2) ** 0.5
        return (col, row) if dist <= REACH * TILE else None

    def update_mining(self, dt, keys):
        target = None
        if keys[K_SPACE]:
            target = self.keyboard_target()
        elif pygame.mouse.get_pressed()[0]:
            target = self.mouse_target()

        if target is None or target not in self.world.blocks:
            self.mine_target, self.mine_progress = None, 0.0
            return
        if target != self.mine_target:
            self.mine_target, self.mine_progress = target, 0.0

        kind = self.world.blocks[target]
        _, hardness, value = BLOCKS[kind]
        self.mine_progress += dt
        if self.mine_progress >= hardness:
            del self.world.blocks[target]
            self.score += value
            self.mine_target, self.mine_progress = None, 0.0

    # -- main update --------------------------------------------------
    def update(self, dt):
        if not self.alive:
            return
        keys = pygame.key.get_pressed()
        self.time += dt

        self.update_player(dt, keys)
        self.update_mining(dt, keys)

        speed = min(WALL_SPEED_MAX, WALL_SPEED_START + WALL_SPEED_GAIN * self.time)
        self.wall_x += speed * dt
        if self.player.left < self.wall_x:
            self.alive = False

        self.cam_x = max(0.0, self.player.centerx - WIDTH * 0.4)
        self.world.ensure(int(self.cam_x // TILE) + COLS + 4)
        self.world.prune(int(self.wall_x // TILE) - 2)

    # -- drawing ------------------------------------------------------
    def draw(self, screen, font, small):
        screen.fill(EMPTY)
        first = int(self.cam_x // TILE)
        for col in range(first, first + COLS + 2):
            for row in range(ROWS):
                kind = self.world.blocks.get((col, row))
                if kind is None:
                    continue
                color = BLOCKS[kind][0]
                r = pygame.Rect(col * TILE - self.cam_x, row * TILE, TILE, TILE)
                pygame.draw.rect(screen, color, r)
                pygame.draw.rect(screen, tuple(max(0, c - 35) for c in color), r, 1)
                if kind == 4:
                    pygame.draw.circle(screen, (255, 235, 130), r.center, 5)

        # crack overlay on the block being mined
        if self.mine_target in self.world.blocks:
            hardness = BLOCKS[self.world.blocks[self.mine_target]][1]
            frac = min(1.0, self.mine_progress / hardness)
            c, r = self.mine_target
            rect = pygame.Rect(c * TILE - self.cam_x, r * TILE, TILE, TILE)
            for i in range(int(frac * 5) + 1):
                y = rect.top + 5 + i * 5
                pygame.draw.line(screen, (20, 20, 20), (rect.left + 3, y), (rect.right - 3, y + 3), 2)

        # facing indicator + player
        p = self.player.move(-self.cam_x, 0)
        pygame.draw.rect(screen, (90, 170, 255), p, border_radius=4)
        pygame.draw.rect(screen, (30, 60, 110), p, 2, border_radius=4)
        fx, fy = self.facing
        pygame.draw.circle(screen, (255, 255, 255), (p.centerx + fx * 6, p.centery + fy * 6), 3)

        # closing wall on the left
        wx = int(self.wall_x - self.cam_x)
        if wx > 0:
            pygame.draw.rect(screen, (150, 30, 30), (0, 0, wx, HEIGHT))
        for y in range(0, HEIGHT, 20):
            pygame.draw.polygon(screen, (200, 50, 50), [(wx, y), (wx, y + 20), (wx + 12, y + 10)])

        screen.blit(font.render(f"Score: {self.score}", True, (255, 255, 255)), (WIDTH - 180, 10))
        screen.blit(small.render(f"Time: {self.time:0.1f}s", True, (220, 220, 220)), (WIDTH - 180, 40))

        if not self.alive:
            shade = pygame.Surface((WIDTH, HEIGHT), SRCALPHA)
            shade.fill((0, 0, 0, 170))
            screen.blit(shade, (0, 0))
            draw_centered(screen, font.render("CRUSHED!", True, (255, 90, 90)), HEIGHT // 2 - 50)
            draw_centered(screen, font.render(f"Final score: {self.score}", True, (255, 255, 255)), HEIGHT // 2)
            draw_centered(screen, small.render("Enter: play again    Esc: main menu", True, (220, 220, 220)), HEIGHT // 2 + 50)


# ---------------------------------------------------------------- helpers
def draw_centered(screen, surf, y):
    screen.blit(surf, surf.get_rect(centerx=WIDTH // 2, y=y))


def draw_menu(screen, title_font, font, small, start_btn, quit_btn):
    screen.fill((50, 50, 58))
    draw_centered(screen, title_font.render("RUSH JOB", True, (255, 210, 80)), 90)
    draw_centered(screen, small.render("Mine through the rock before the wall catches you!", True, (210, 210, 210)), 160)
    mouse = pygame.mouse.get_pos()
    for rect, label in ((start_btn, "Start"), (quit_btn, "Quit")):
        color = (90, 150, 90) if rect.collidepoint(mouse) else (70, 110, 70)
        if label == "Quit":
            color = (150, 90, 90) if rect.collidepoint(mouse) else (110, 70, 70)
        pygame.draw.rect(screen, color, rect, border_radius=8)
        pygame.draw.rect(screen, (255, 255, 255), rect, 2, border_radius=8)
        txt = font.render(label, True, (255, 255, 255))
        screen.blit(txt, txt.get_rect(center=rect.center))
    draw_centered(screen, small.render("Move: arrows / WASD    Mine: hold Space (facing) or left-click nearby blocks", True, (170, 170, 180)), HEIGHT - 60)


# ---------------------------------------------------------------- main
def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption('Rush Job')
    clock = pygame.time.Clock()

    title_font = pygame.font.Font(None, 110)
    font = pygame.font.Font(None, 48)
    small = pygame.font.Font(None, 28)

    start_btn = pygame.Rect(0, 0, 240, 60)
    start_btn.center = (WIDTH // 2, 260)
    quit_btn = pygame.Rect(0, 0, 240, 60)
    quit_btn.center = (WIDTH // 2, 340)

    state = "menu"
    game = Game()

    while True:
        dt = min(clock.tick(60) / 1000.0, 0.05)

        for event in pygame.event.get():
            if event.type == QUIT:
                return
            if state == "menu":
                if event.type == MOUSEBUTTONDOWN and event.button == 1:
                    if start_btn.collidepoint(event.pos):
                        game.reset()
                        state = "playing"
                    elif quit_btn.collidepoint(event.pos):
                        return
                elif event.type == KEYDOWN and event.key in (K_RETURN, K_SPACE):
                    game.reset()
                    state = "playing"
            elif state == "playing":
                if event.type == KEYDOWN:
                    if event.key == K_ESCAPE:
                        state = "menu"
                    elif event.key == K_RETURN and not game.alive:
                        game.reset()

        if state == "menu":
            draw_menu(screen, title_font, font, small, start_btn, quit_btn)
        else:
            game.update(dt)
            game.draw(screen, font, small)
        pygame.display.flip()


if __name__ == '__main__':
    main()