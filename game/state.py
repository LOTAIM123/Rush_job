"""Spēles loģika. Nezina neko par pygame: ievade tiek padota kā Input."""
from dataclasses import dataclass
from typing import Optional, Tuple

from .constants import (BLOCKS, BOOT_BONUS, COLS, PICK_FACTOR, PLAYER_SIZE,
                        PLAYER_SPEED, PUSHBACK_TILES, REACH, ROWS, START_COL,
                        TILE, UPGRADES, WALL_SPEED_GAIN, WALL_SPEED_MAX,
                        WALL_SPEED_START, WALL_START_X)
from .world import World, shop_col_near


@dataclass
class Rect:
    x: int
    y: int
    w: int
    h: int

    @property
    def left(self): return self.x
    @property
    def right(self): return self.x + self.w
    @property
    def top(self): return self.y
    @property
    def bottom(self): return self.y + self.h
    @property
    def centerx(self): return self.x + self.w // 2
    @property
    def centery(self): return self.y + self.h // 2


@dataclass
class Input:
    move_x: int = 0                       # -1, 0, 1
    move_y: int = 0
    mine_facing: bool = False             # taustiņš: racī bloku, uz kuru skatās
    mine_tile: Optional[Tuple[int, int]] = None   # pele: rūts (col, row)


class Game:
    def __init__(self, rng=None):
        self.rng = rng
        self.reset()

    def reset(self):
        self.world = World(self.rng)
        self.world.ensure(COLS + 4)
        self.player = Rect(START_COL * TILE + TILE // 2 - PLAYER_SIZE // 2,
                           ROWS // 2 * TILE + TILE // 2 - PLAYER_SIZE // 2,
                           PLAYER_SIZE, PLAYER_SIZE)
        self.facing = (1, 0)
        self.wall_x = float(WALL_START_X)
        self.time = 0.0
        self.score = 0
        self.mine_target = None
        self.mine_progress = 0.0
        self.alive = True
        self.gold = 0
        self.distance = 0
        self.levels = {key: 0 for key in UPGRADES}

    # -- kustība ------------------------------------------------------
    def collides(self, r):
        for c in range(r.left // TILE, (r.right - 1) // TILE + 1):
            for row in range(r.top // TILE, (r.bottom - 1) // TILE + 1):
                if self.world.solid_at(c, row):
                    return True
        return False

    def move_axis(self, dx, dy):
        p = self.player
        p.x += dx
        p.y += dy
        if self.collides(p):
            if dx > 0:
                p.x = (p.right // TILE) * TILE - p.w
            elif dx < 0:
                p.x = (p.left // TILE + 1) * TILE
            if dy > 0:
                p.y = (p.bottom // TILE) * TILE - p.h
            elif dy < 0:
                p.y = (p.top // TILE + 1) * TILE

    def update_player(self, dt, inp):
        if inp.move_x:
            self.facing = (inp.move_x, 0)
        elif inp.move_y:
            self.facing = (0, inp.move_y)
        step = PLAYER_SPEED * self.speed_mult() * dt
        self.move_axis(round(inp.move_x * step), 0)
        self.move_axis(0, round(inp.move_y * step))

    # -- racšana ------------------------------------------------------
    def facing_tile(self):
        fx, fy = self.facing
        px = self.player.centerx + fx * (PLAYER_SIZE // 2 + 4)
        py = self.player.centery + fy * (PLAYER_SIZE // 2 + 4)
        return (px // TILE, py // TILE)

    def in_reach(self, tile):
        cx, cy = tile[0] * TILE + TILE / 2, tile[1] * TILE + TILE / 2
        d = ((cx - self.player.centerx) ** 2 + (cy - self.player.centery) ** 2) ** 0.5
        return d <= REACH * TILE

    def update_mining(self, dt, inp):
        target = None
        if inp.mine_facing:
            target = self.facing_tile()
        elif inp.mine_tile is not None and self.in_reach(inp.mine_tile):
            target = inp.mine_tile

        if target is None or target not in self.world.blocks:
            self.mine_target, self.mine_progress = None, 0.0
            return
        if target != self.mine_target:
            self.mine_target, self.mine_progress = target, 0.0

        _, hardness, value, gold = BLOCKS[self.world.blocks[target]]
        hardness *= self.mine_mult()
        self.mine_progress += dt
        if self.mine_progress >= hardness:
            del self.world.blocks[target]
            self.score += value
            self.gold += gold
            self.mine_target, self.mine_progress = None, 0.0

    # -- galvenais atjauninājums --------------------------------------
    def update(self, dt, inp):
        if not self.alive:
            return
        self.time += dt
        self.update_player(dt, inp)
        self.distance = max(self.distance, self.player.centerx // TILE - START_COL)
        self.update_mining(dt, inp)

        speed = min(WALL_SPEED_MAX, WALL_SPEED_START + WALL_SPEED_GAIN * self.time)
        self.wall_x += speed * dt
        if self.player.left < self.wall_x:
            self.alive = False

        self.world.ensure(self.player.centerx // TILE + COLS + 4)
        self.world.prune(int(self.wall_x // TILE) - 2)

    # -- uzlabojumi un veikals ----------------------------------------
    def mine_mult(self):
        return PICK_FACTOR ** self.levels["pick"]

    def speed_mult(self):
        return 1 + BOOT_BONUS * self.levels["boots"]

    def shop_here(self):
        """Veikala centra rūts, ja spēlētājs atrodas veikala telpā, citādi None."""
        return shop_col_near(self.player.centerx // TILE)

    def next_shop_distance(self):
        return (self.distance // 100 + 1) * 100

    def upgrade_cost(self, key):
        _, base, step, max_level = UPGRADES[key]
        level = self.levels[key]
        return None if level >= max_level else base + step * level

    def buy(self, key):
        """Nopērk uzlabojumu, ja spēlētājs ir veikalā un pietiek zelta."""
        cost = self.upgrade_cost(key)
        if self.shop_here() is None or cost is None or self.gold < cost:
            return False
        self.gold -= cost
        self.levels[key] += 1
        if key == "pushback":
            self.wall_x = max(0.0, self.wall_x - PUSHBACK_TILES * TILE)
        return True
