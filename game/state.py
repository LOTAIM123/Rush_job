"""Game logic. It knows nothing about pygame: input is passed in as an Input object."""
import math
from dataclasses import dataclass
from typing import Optional, Tuple

from .constants import (BLAST_BASE_RADIUS, BLOCKS, BOMB, BOMB_BLAST_RADIUS, BOMB_STUN_TIME,
                        BOOT_BONUS, BRAMBLE_SLOW, BRAMBLES, COLS, EFFECT_TTL,
                        GOLDRUSH_GOLD, LAVA, MESSAGE_TTL, NON_SOLID,
                        PICK_FACTOR, PLAYER_SIZE, PLAYER_SPEED, POWERUP_CHANCE,
                        POWERUP_CHANCE_MAX, POWERUP_DURATION,
                        POWERUP_LUCK_BONUS, POWERUP_MAX_STACKS,
                        POWERUP_TIME_CAP, POWERUPS, REACH, ROWS, S,
                        SHOP_PRICE_GROWTH_PER_100, SPEED_PU_BONUS,
                        SPLASH_DAMAGE, SPLASH_IMMUNE, START_COL, TILE,
                        UNBREAKABLE, UPGRADES, WALL_MAX_RATIO,
                        WALL_RATIO_PER_TILE, WALL_SLOW_MIN_MULT,
                        WALL_SLOW_PER_LEVEL, WALL_START_RATIO, WALL_START_X)
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
    mine_facing: bool = False             # key held: mine the block the player is facing
    mine_tile: Optional[Tuple[int, int]] = None   # mouse: tile (col, row) under the cursor


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
        self.damage = {}       # damage to blocks: (col, row) -> 0..1 (1 = breaks)
        self.alive = True
        self.stun = 0.0
        self.death_cause = None    # "wall", "lava" or "bomb"
        self.events = []           # for sound/particles: ("break", kind, (col, row)), ("explode", (col, row)), ("death", cause)
        self.gold = 0
        self.distance = 0
        self.levels = {key: 0 for key in UPGRADES}
        self.powerups = {key: [] for key in POWERUPS}   # remaining seconds for every stack
        self.effects = []      # visual effects: {"kind", "col", "row", "r", "ttl", "max"}
        self.messages = []     # on-screen messages: [text, ttl]

    # -- movement -----------------------------------------------------
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
        step = PLAYER_SPEED * self.speed_mult() * self.terrain_slow() * dt
        self.move_axis(round(inp.move_x * step), 0)
        self.move_axis(0, round(inp.move_y * step))

    # -- mining -------------------------------------------------------
    def facing_tile(self):
        """The tile to mine with the keyboard.

        The player is smaller than a tile and is rarely centred on one, so the block in front
        may be split across two tiles. All tiles touched by the player's front edge are
        considered: solid blocks first, then the one overlapping the player the most.
        """
        fx, fy = self.facing
        p = self.player
        probe = PLAYER_SIZE // 2 + round(4 * S)
        px, py = p.centerx + fx * probe, p.centery + fy * probe
        if fx:      # facing left/right: one column, every row the player overlaps
            col = px // TILE
            candidates = [((col, r), min(p.bottom, (r + 1) * TILE) - max(p.top, r * TILE))
                          for r in range(p.top // TILE, (p.bottom - 1) // TILE + 1)]
        else:       # facing up/down: one row, every column the player overlaps
            row = py // TILE
            candidates = [((c, row), min(p.right, (c + 1) * TILE) - max(p.left, c * TILE))
                          for c in range(p.left // TILE, (p.right - 1) // TILE + 1)]
        best, best_key = None, None
        for tile, overlap in candidates:
            kind = self.world.blocks.get(tile)
            if kind is None or kind in UNBREAKABLE:
                continue
            key = (kind not in NON_SOLID, overlap)
            if best_key is None or key > best_key:
                best, best_key = tile, key
        return best if best is not None else (px // TILE, py // TILE)

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

        kind = self.world.blocks.get(target) if target is not None else None
        if kind is None or kind in UNBREAKABLE:
            return
        t = self.mine_time(target)
        self.damage[target] = self.damage.get(target, 0.0) + (dt / t if t > 0 else 1.0)
        if self.damage[target] >= 1.0:
            self.break_block(target, direct=True)
            if kind == BOMB:
                self.detonate(target)            # bombs ignore every mining power-up
            else:
                self.apply_powerups(target)
                self.roll_powerup_drop()

    # -- main update --------------------------------------------------
    def update(self, dt, inp):
        if not self.alive:
            return
        self.time += dt
        if len(self.events) > 200:           # safety net if nobody reads them
            self.events = self.events[-50:]
        self.tick_effects(dt)
        if self.stun > 0:
            self.stun = max(0.0, self.stun - dt)
            inp = Input()                    # stunned: no movement, no mining
        self.update_player(dt, inp)
        self.distance = max(self.distance, self.player.centerx // TILE - START_COL)
        self.update_mining(dt, inp)

        self.wall_x += self.wall_speed() * dt
        if self.alive:
            if self.player.left < self.wall_x:
                self.kill("wall")
            elif LAVA in self.kinds_under(self.player, inset=round(4 * S)):
                self.kill("lava")

        self.world.ensure(self.player.centerx // TILE + COLS + 4)
        self.world.prune(int(self.wall_x // TILE) - 2)
        self.damage = {k: v for k, v in self.damage.items() if k in self.world.blocks}

    def kill(self, cause):
        self.alive, self.death_cause = False, cause
        self.events.append(("death", cause))

    # -- upgrades and shop --------------------------------------------
    def mine_mult(self):
        return PICK_FACTOR ** self.levels["pick"]

    def speed_mult(self):
        return 1 + BOOT_BONUS * self.levels["boots"] + SPEED_PU_BONUS * self.stacks("speed")

    def shop_here(self):
        """Centre column of the shop the player is standing in, otherwise None."""
        return shop_col_near(self.player.centerx // TILE)

    def next_shop_distance(self):
        return (self.distance // 100 + 1) * 100

    def price_multiplier(self):
        """Every price rises with the distance travelled, whether or not it was ever bought."""
        return 1 + SHOP_PRICE_GROWTH_PER_100 * self.distance / 100

    def upgrade_cost(self, key):
        _, base, step, max_level = UPGRADES[key]
        level = self.levels[key]
        if level >= max_level:
            return None
        return math.ceil((base + step * level) * self.price_multiplier())

    def buy(self, key):
        """Buys an upgrade if the player is in a shop and has enough gold."""
        cost = self.upgrade_cost(key)
        if self.shop_here() is None or cost is None or self.gold < cost:
            return False
        self.gold -= cost
        self.levels[key] += 1
        return True

    # -- blocks, power-ups, bombs ---------------------------------------
    def break_block(self, tile, direct=False):
        """Breaks a block and awards points/gold. `direct` = the player mined it
        (only then Gold Rush gives bonus gold). Returns True if there was a block."""
        kind = self.world.blocks.pop(tile, None)
        self.damage.pop(tile, None)
        if kind is None:
            return False
        self.events.append(("break", kind, tile))
        _, _, value, gold = BLOCKS[kind]
        self.score += value
        self.gold += gold
        if direct and self.stacks("goldrush"):
            self.gold += GOLDRUSH_GOLD
        return True

    def damage_block(self, tile, amount):
        """Damages a block (explosion, 3x3); it breaks when damage reaches 1."""
        kind = self.world.blocks.get(tile)
        if kind is None or kind in UNBREAKABLE or kind in SPLASH_IMMUNE:
            return
        self.damage[tile] = self.damage.get(tile, 0.0) + amount
        if self.damage[tile] >= 1.0:
            self.break_block(tile)

    def detonate(self, tile):
        """A bomb goes off: every breakable block around it is destroyed (chain-detonating other
        bombs) and the player is stunned for a moment unless a Shield is active."""
        queue, done = [tile], set()
        while queue:
            col, row = queue.pop()
            if (col, row) in done:
                continue
            done.add((col, row))
            self.world.blocks.pop((col, row), None)
            self.damage.pop((col, row), None)
            self.events.append(("explode", (col, row)))
            ttl = EFFECT_TTL * 1.5
            self.effects.append({"kind": "bomb", "col": col, "row": row, "r": BOMB_BLAST_RADIUS,
                                 "ttl": ttl, "max": ttl})
            for dx in range(-BOMB_BLAST_RADIUS, BOMB_BLAST_RADIUS + 1):
                for dy in range(-BOMB_BLAST_RADIUS, BOMB_BLAST_RADIUS + 1):
                    t = (col + dx, row + dy)
                    kind = self.world.blocks.get(t)
                    if kind is None or kind in UNBREAKABLE:
                        continue
                    if kind == BOMB:
                        queue.append(t)
                    else:
                        self.break_block(t)
        if self.stacks("shield"):
            self.messages.append(["The shield absorbed the stun!", MESSAGE_TTL])
        else:
            self.stun = BOMB_STUN_TIME
            self.messages.append(["Stunned!", MESSAGE_TTL])

    def pop_events(self):
        """Returns the accumulated events (for sound and particles) and clears the list."""
        events, self.events = self.events, []
        return events

    def stacks(self, key):
        return len(self.powerups[key])

    def apply_powerups(self, centre):
        """Active power-ups damage the blocks around the block that was just mined."""
        cx, cy = centre
        n = self.stacks("area")
        if n:
            for dx in range(-n, n + 1):
                for dy in range(-n, n + 1):
                    self.damage_block((cx + dx, cy + dy), SPLASH_DAMAGE)
            self.effects.append({"kind": "area", "col": cx, "row": cy, "r": n,
                                 "ttl": EFFECT_TTL, "max": EFFECT_TTL})
        n = self.stacks("blast")
        if n:
            r = BLAST_BASE_RADIUS + n
            for dx in range(-r, r + 1):
                for dy in range(-r, r + 1):
                    if dx * dx + dy * dy <= r * r + 1:
                        self.damage_block((cx + dx, cy + dy), SPLASH_DAMAGE)
            self.effects.append({"kind": "blast", "col": cx, "row": cy, "r": r,
                                 "ttl": EFFECT_TTL, "max": EFFECT_TTL})

    def roll_powerup_drop(self):
        """Only blocks the player mined directly (not ones broken by explosions) can drop a power-up."""
        rng = self.world.rng
        if rng.random() < self.powerup_chance():
            self.add_powerup(rng.choice(list(POWERUPS)))

    def add_powerup(self, key):
        timers = self.powerups[key]
        if POWERUPS[key][2] == "time":            # extends the single timer
            total = min(POWERUP_TIME_CAP, (timers[0] if timers else 0.0) + POWERUP_DURATION)
            self.powerups[key] = [total]
            self.messages.append([f"{POWERUPS[key][0]}! +{POWERUP_DURATION:.0f}s", MESSAGE_TTL])
            return
        if len(timers) >= POWERUP_MAX_STACKS:
            timers.sort()
            timers[0] = POWERUP_DURATION          # full: refresh the shortest one
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

    # -- mining time, wall speed, luck ----------------------------------
    def mine_time(self, tile):
        """Seconds needed to mine the block on this tile."""
        kind = self.world.blocks[tile]
        if self.stacks("insta") and kind != BOMB:
            return 0.0                           # Instant Mine (bombs are not affected)
        return BLOCKS[kind][1] * self.mine_mult()

    def top_speed(self):
        """The player's top speed in px/s: base speed with permanent boots upgrades."""
        return PLAYER_SPEED * (1 + BOOT_BONUS * self.levels["boots"])

    def wall_ratio(self):
        """Wall speed as a fraction of the player's top speed; grows with distance."""
        return min(WALL_MAX_RATIO, WALL_START_RATIO + WALL_RATIO_PER_TILE * self.distance)

    def wall_slow_mult(self):
        return max(WALL_SLOW_MIN_MULT, 1 - WALL_SLOW_PER_LEVEL * self.levels["slowwall"])

    def wall_speed(self):
        """Wall speed in px/s: scales with distance and with the player's top speed;
        the Wall Brake upgrade slows it down."""
        return self.top_speed() * self.wall_ratio() * self.wall_slow_mult()

    def kinds_under(self, r, inset=0):
        """Block kinds covered by a rectangle (shrunk by `inset` pixels)."""
        kinds = set()
        for c in range((r.left + inset) // TILE, (r.right - 1 - inset) // TILE + 1):
            for row in range((r.top + inset) // TILE, (r.bottom - 1 - inset) // TILE + 1):
                k = self.world.blocks.get((c, row))
                if k is not None:
                    kinds.add(k)
        return kinds

    def terrain_slow(self):
        return BRAMBLE_SLOW if BRAMBLES in self.kinds_under(self.player) else 1.0

    def powerup_chance(self):
        return min(POWERUP_CHANCE_MAX, POWERUP_CHANCE + POWERUP_LUCK_BONUS * self.levels["luck"])
