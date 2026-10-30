"""Spēles loģika. Nezina neko par pygame: ievade tiek padota kā Input."""
from dataclasses import dataclass
from typing import Optional, Tuple

from .constants import (BLAST_BASE_RADIUS, BLOCKS, BOOT_BONUS, COLS,
                        POWERUP_CHANCE_MAX, POWERUP_LUCK_BONUS,
                        EFFECT_TTL, MESSAGE_TTL, PICK_FACTOR, PLAYER_SIZE,
                        PLAYER_SPEED, POWERUP_CHANCE, POWERUP_DURATION,
                        POWERUP_MAX_STACKS, POWERUPS, PUSHBACK_TILES, REACH,
                        ROWS, START_COL, TILE, UPGRADES, WALL_SPEED_MAX,
                        WALL_SPEED_PER_TILE, WALL_SPEED_START, WALL_START_X)
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
        self.powerups = {key: [] for key in POWERUPS}   # atlikušie laiki katrai kaudzītei
        self.effects = []      # vizuālie efekti: {"kind", "col", "row", "r", "ttl"}
        self.messages = []     # paziņojumi: [teksts, ttl]

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

        hardness = self.mine_time(target)
        self.mine_progress += dt
        if self.mine_progress >= hardness:
            self.break_block(target)
            self.apply_powerups(target)
            self.roll_powerup_drop()
            self.mine_target, self.mine_progress = None, 0.0

    # -- galvenais atjauninājums --------------------------------------
    def update(self, dt, inp):
        if not self.alive:
            return
        self.time += dt
        self.tick_effects(dt)
        self.update_player(dt, inp)
        self.distance = max(self.distance, self.player.centerx // TILE - START_COL)
        self.update_mining(dt, inp)

        speed = self.wall_speed()
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

    # -- power-up -----------------------------------------------------
    def break_block(self, tile):
        """Salauž bloku un piešķir punktus/zeltu. Atgriež True, ja bloks bija."""
        kind = self.world.blocks.pop(tile, None)
        if kind is None:
            return False
        _, _, value, gold = BLOCKS[kind]
        self.score += value
        self.gold += gold
        return True

    def stacks(self, key):
        return len(self.powerups[key])

    def apply_powerups(self, centre):
        """Aktīvie power-up salauž blokus ap tikko izraktā bloka rūti."""
        cx, cy = centre
        n = self.stacks("area")
        if n:
            for dx in range(-n, n + 1):
                for dy in range(-n, n + 1):
                    self.break_block((cx + dx, cy + dy))
            self.effects.append({"kind": "area", "col": cx, "row": cy, "r": n, "ttl": EFFECT_TTL})
        n = self.stacks("blast")
        if n:
            r = BLAST_BASE_RADIUS + n
            for dx in range(-r, r + 1):
                for dy in range(-r, r + 1):
                    if dx * dx + dy * dy <= r * r + 1:
                        self.break_block((cx + dx, cy + dy))
            self.effects.append({"kind": "blast", "col": cx, "row": cy, "r": r, "ttl": EFFECT_TTL})

    def roll_powerup_drop(self):
        """Tikai tieši izraktie bloki (ne sprādzienā izpostītie) var dot power-up."""
        rng = self.world.rng
        if rng.random() < self.powerup_chance():
            self.add_powerup(rng.choice(list(POWERUPS)))

    def add_powerup(self, key):
        timers = self.powerups[key]
        if len(timers) >= POWERUP_MAX_STACKS:
            timers.sort()
            timers[0] = POWERUP_DURATION          # pilns: atjauno īsāko
        else:
            timers.append(POWERUP_DURATION)
        self.messages.append([f"{POWERUPS[key][0]}! x{len(timers)}", MESSAGE_TTL])

    def tick_effects(self, dt):
        for key in self.powerups:
            self.powerups[key] = [t - dt for t in self.powerups[key] if t - dt > 0]
        for e in self.effects:
            e["ttl"] -= dt
        self.effects = [e for e in self.effects if e["ttl"] > 0]
        for m in self.messages:
            m[1] -= dt
        self.messages = [m for m in self.messages if m[1] > 0]

    # -- sienas ātrums un veiksme -----------------------------
    def mine_time(self, tile):
        """Sekundes, kas vajadzīgas, lai izrakt bloku šajā rūtī."""
        base = BLOCKS[self.world.blocks[tile]][1]
        return base * self.mine_mult()

    def wall_speed(self):
        """Sienas ātrums (px/s) aug ar nogājušo distanci."""
        return min(WALL_SPEED_MAX, WALL_SPEED_START + WALL_SPEED_PER_TILE * self.distance)

    def powerup_chance(self):
        return min(POWERUP_CHANCE_MAX, POWERUP_CHANCE + POWERUP_LUCK_BONUS * self.levels["luck"])
