import random

from .constants import (BLOCK_TIER_DIST, BOMB, BOMB_CHANCE_BASE,
                        BOMB_CHANCE_MAX, BOMB_CHANCE_PER_TILE, BOMB_MIN_COL,
                        BRAMBLE_CHANCE, BRAMBLE_MIN_COL, BRAMBLE_SIZE,
                        BRAMBLES, LAVA, LAVA_CHANCE_BASE, LAVA_CHANCE_MAX,
                        LAVA_CHANCE_PER_TILE, LAVA_MIN_COL, LAVA_SIZE,
                        NON_SOLID, ROWS, SAFE_COLS, SHOP_EVERY, SHOP_HALF,
                        START_COL, VEIN_CHANCE, VEIN_SIZE_MAX, VEIN_SIZE_MIN)


def shop_col_near(col):
    """If `col` is inside a shop room, return the shop's centre column, otherwise None."""
    n = round((col - START_COL) / SHOP_EVERY)
    if n >= 1:
        centre = START_COL + n * SHOP_EVERY
        if abs(col - centre) <= SHOP_HALF:
            return centre
    return None


class World:
    def __init__(self, rng=None):
        self.rng = rng or random.Random()
        self.blocks = {}
        self.generated_to = -1
        self.patch_tiles = {}           # patches reaching into later columns: (col, row) -> block kind

    def seed_patch(self, col, kind, size_min, size_max):
        """A patch (gold vein, lava, brambles): a connected group of tiles growing to the right."""
        size = self.rng.randint(size_min, size_max)
        tiles = {(col, self.rng.randrange(ROWS))}
        for _ in range(size * 8):
            if len(tiles) >= size:
                break
            c, r = self.rng.choice(sorted(tiles))
            dc, dr = self.rng.choice(((1, 0), (1, 0), (0, 1), (0, -1)))
            if 0 <= r + dr < ROWS:
                tiles.add((c + dc, r + dr))
        for t in tiles:
            self.patch_tiles[t] = kind

    def lava_chance(self, col):
        d = max(0, col - START_COL)
        return min(LAVA_CHANCE_MAX, LAVA_CHANCE_BASE + LAVA_CHANCE_PER_TILE * d)

    def bomb_chance(self, col):
        d = max(0, col - START_COL)
        return min(BOMB_CHANCE_MAX, BOMB_CHANCE_BASE + BOMB_CHANCE_PER_TILE * d)

    def generate_column(self, col):
        shop = shop_col_near(col) is not None
        if not shop and col >= SAFE_COLS:
            if self.rng.random() < VEIN_CHANCE:
                self.seed_patch(col, 4, VEIN_SIZE_MIN, VEIN_SIZE_MAX)
            if col >= BRAMBLE_MIN_COL and self.rng.random() < BRAMBLE_CHANCE:
                self.seed_patch(col, BRAMBLES, *BRAMBLE_SIZE)
            if col >= LAVA_MIN_COL and self.rng.random() < self.lava_chance(col):
                self.seed_patch(col, LAVA, *LAVA_SIZE)     # last: overwrites the others
        if not shop:
            for row in range(ROWS):
                if col < SAFE_COLS:
                    if self.rng.random() < 0.08:
                        self.blocks[(col, row)] = 1
                    continue
                kind = self.patch_tiles.get((col, row))
                if not kind:
                    if col >= BOMB_MIN_COL and self.rng.random() < self.bomb_chance(col):
                        kind = BOMB
                    else:
                        kind = self.pick_tier(col)
                self.blocks[(col, row)] = kind
        # the shop room stays empty; used-up patch tiles are no longer needed
        self.patch_tiles = {t: k for t, k in self.patch_tiles.items() if t[0] > col}

    def pick_tier(self, col):
        """Dirt (1) at the start, then stone (2), later slate (3), blended smoothly."""
        x = max(0, col - START_COL) / BLOCK_TIER_DIST
        w_dirt = max(0.0, 1 - x)
        w_stone = max(0.0, 1 - abs(x - 1))
        w_slate = min(1.0, max(0.0, x - 1))
        t = self.rng.random() * (w_dirt + w_stone + w_slate)
        if t < w_dirt:
            return 1
        if t < w_dirt + w_stone:
            return 2
        return 3

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
        kind = self.blocks.get((col, row))
        return kind is not None and kind not in NON_SOLID
