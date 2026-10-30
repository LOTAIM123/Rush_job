import random

from .constants import ROWS, SAFE_COLS, SHOP_EVERY, SHOP_HALF, START_COL


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
                    self.blocks[(col, row)] = 2
                continue
            if self.rng.random() < 0.15:
                kind = 2
            t = self.rng.random()
            if t < 0.45:
                kind = 2
            elif t < 0.80:
                kind = 2
            elif t < 0.95:
                kind = 2
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
