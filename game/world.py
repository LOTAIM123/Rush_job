import random

from .constants import (BLOCK_TIER_DIST, BRAMBLE_CHANCE, BRAMBLE_MIN_COL,
                        BRAMBLE_SIZE, BRAMBLES, LAVA, LAVA_CHANCE_BASE,
                        LAVA_CHANCE_MAX, LAVA_CHANCE_PER_TILE, LAVA_MIN_COL,
                        LAVA_SIZE, NON_SOLID, ROWS, SAFE_COLS, SHOP_EVERY,
                        SHOP_HALF, START_COL, VEIN_CHANCE, VEIN_SIZE_MAX,
                        VEIN_SIZE_MIN)


def shop_col_near(col):
    """Ja `col` ir veikala telpā, atgriež veikala centra rūti, citādi None."""
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
        self.patch_tiles = {}           # nākamo kolonnu plankumi: (col, row) -> bloka veids

    def seed_patch(self, col, kind, size_min, size_max):
        """Plankums (zelta dzīsla, lava, krūmi): saaugusi rūšu grupa, kas stiepjas pa labi."""
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

    def generate_column(self, col):
        shop = shop_col_near(col) is not None
        if not shop and col >= SAFE_COLS:
            if self.rng.random() < VEIN_CHANCE:
                self.seed_patch(col, 4, VEIN_SIZE_MIN, VEIN_SIZE_MAX)
            if col >= BRAMBLE_MIN_COL and self.rng.random() < BRAMBLE_CHANCE:
                self.seed_patch(col, BRAMBLES, *BRAMBLE_SIZE)
            if col >= LAVA_MIN_COL and self.rng.random() < self.lava_chance(col):
                self.seed_patch(col, LAVA, *LAVA_SIZE)     # pēdējā: pārraksta citus
        if not shop:
            for row in range(ROWS):
                if col < SAFE_COLS:
                    if self.rng.random() < 0.08:
                        self.blocks[(col, row)] = 1
                    continue
                kind = self.patch_tiles.get((col, row)) or self.pick_tier(col)
                self.blocks[(col, row)] = kind
        # veikala telpa paliek tukša; izlietotie plankumi vairs nav vajadzīgi
        self.patch_tiles = {t: k for t, k in self.patch_tiles.items() if t[0] > col}

    def pick_tier(self, col):
        """Zeme (1) sākumā, tad akmens (2), tālāk slate (3): vienmērīga pāreja."""
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
