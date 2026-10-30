import random

from .constants import (BLOCK_TIER_DIST, GOLD_CHANCE, ROWS, SAFE_COLS,
                        SHOP_EVERY, SHOP_HALF, START_COL)


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

    def generate_column(self, col):
        if shop_col_near(col) is not None:
            return                      # veikala telpa paliek tukša
        for row in range(ROWS):
            if col < SAFE_COLS:
                if self.rng.random() < 0.08:
                    self.blocks[(col, row)] = 1
                continue
            if self.rng.random() < GOLD_CHANCE:
                kind = 4
            else:
                kind = self.pick_tier(col)
            self.blocks[(col, row)] = kind

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
        return (col, row) in self.blocks
