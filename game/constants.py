"""Game constants (nothing in this package depends on pygame)."""

TILE = 40                      # tile size in pixels (window = 1280x720)
S = TILE / 30                  # scale: pixel sizes below are tuned for TILE = 30 and multiplied by this
COLS, ROWS = 32, 18            # visible area in tiles
WIDTH, HEIGHT = COLS * TILE, ROWS * TILE

PLAYER_SIZE = round(22 * S)
PLAYER_SPEED = 150 * S         # pixels per second (5 tiles/s)
REACH = 2.2                    # mouse mining reach in tiles

# The wall chases the player. Its speed is a fraction of the player's TOP speed
# (base speed plus permanent boots upgrades; temporary speed power-ups are not counted),
# so buying boots never lets you simply outrun it.
WALL_START_X = TILE
WALL_START_RATIO = 0.15        # fraction of top speed at distance 0
WALL_RATIO_PER_TILE = 0.0025   # +25% of top speed every 100 m
WALL_MAX_RATIO = 1.0           # the wall can reach, but never exceed, the player's top speed

# Block types change with distance: dirt -> stone -> slate (hard rock)
BLOCK_TIER_DIST = 600          # tiles per tier: 0 = dirt, 600 = stone, 1200+ = slate
VEIN_CHANCE = 0.15             # chance that a gold vein starts in a column
VEIN_SIZE_MIN = 4              # vein size in tiles
VEIN_SIZE_MAX = 8

SAFE_COLS = 7

START_COL = 6                  # the player's start tile (distance = 0)

# block id -> (colour, seconds to mine, points, gold)
BLOCKS = {
    1: ((139, 105, 70), 0.05, 1, 0),     # dirt
    2: ((120, 120, 125), 0.25, 2, 0),    # stone
    3: ((70, 70, 85), 1.1, 4, 0),        # slate (hard rock)
    4: ((235, 190, 50), 0.1, 10, 1),     # gold (+1 gold as money)
    5: ((200, 25, 25), 0.0, 0, 0),       # lava: kills instantly, cannot be mined
    6: ((55, 115, 50), 1.5, 0, 0),       # brambles: slow the player, can be mined
    7: ((95, 85, 80), 0.4, 0, 0),        # bomb: mining it kills the player (unless shielded)
}
LAVA, BRAMBLES, BOMB = 5, 6, 7
NON_SOLID = {LAVA, BRAMBLES}   # the player can walk into these (lava kills, brambles slow)
UNBREAKABLE = {LAVA}           # cannot be mined at all
SPLASH_IMMUNE = {LAVA, BOMB}   # 3x3 and explosions neither damage nor detonate these

BRAMBLE_SLOW = 0.4             # movement speed inside brambles (40%)
SPLASH_DAMAGE = 0.25           # damage dealt by 3x3 and explosions, as a fraction of a block's health

# lava, brambles and bombs are generated like gold veins
LAVA_MIN_COL = 25              # no lava close to the start
LAVA_CHANCE_BASE = 0.04        # chance per column; grows with distance
LAVA_CHANCE_PER_TILE = 0.0001
LAVA_CHANCE_MAX = 0.15
LAVA_SIZE = (4, 8)
BRAMBLE_MIN_COL = 12
BRAMBLE_CHANCE = 0.07
BRAMBLE_SIZE = (3, 7)
BOMB_MIN_COL = 20              # bombs are single blocks hidden in the rock
BOMB_CHANCE_BASE = 0.004       # chance per rock tile; grows with distance
BOMB_CHANCE_PER_TILE = 0.00003
BOMB_CHANCE_MAX = 0.03
BOMB_BLAST_RADIUS = 2          # blocks within this many tiles (square) of a bomb are destroyed
BOMB_STUN_TIME = 1.5           # seconds the player cannot move or mine after a blast

# shops
SHOP_EVERY = 100               # a shop every 100 distance (tiles)
SHOP_HALF = 2                  # shop room: 2 tiles to each side of the counter
SHOP_PRICE_GROWTH_PER_100 = 0.25   # every price rises 25% per 100 m travelled, bought or not

# upgrades: key -> (name, base price, price increase per level bought, max level)
UPGRADES = {
    "pick": ("Pickaxe: faster mining", 3, 2, 999),
    "boots": ("Boots: faster movement", 3, 2, 999),
    "slowwall": ("Wall Brake: slows the wall", 4, 2, 15),
    "luck": ("Luck: more power-ups", 4, 3, 25),
}
POWERUP_LUCK_BONUS = 0.01      # +1% power-up chance per level
POWERUP_CHANCE_MAX = 0.5
PICK_FACTOR = 0.85             # mining time x 0.85 per level
BOOT_BONUS = 0.10              # +10% speed per level
WALL_SLOW_PER_LEVEL = 0.05     # wall speed -5% per level
WALL_SLOW_MIN_MULT = 0.25      # never slower than 25% of normal (15 levels)

# power-ups that rarely drop from mined blocks (and can stack)
POWERUP_CHANCE = 0.02          # chance that a mined block drops a power-up
POWERUP_DURATION = 10.0        # seconds per power-up "stack"
POWERUP_MAX_STACKS = 4         # maximum stacks of one kind
EFFECT_TTL = 0.35              # visual effect duration (seconds)
MESSAGE_TTL = 1.6              # on-screen message duration (seconds)
BLAST_BASE_RADIUS = 1          # explosion radius = 1 + number of stacks

# key -> (name, colour, mode)
#  mode "power": every pickup adds a stack (stronger effect, own timer)
#  mode "time":  every pickup extends the timer (same effect, longer duration)
#  "area"     - every directly mined block damages its neighbours: 1 stack = 3x3, 2 = 5x5, ...
#  "blast"    - every directly mined block explodes: 1 stack = radius 2, 2 = radius 3, ...
#  "speed"    - +25% movement speed per stack
#  "insta"    - blocks are mined instantly (bombs are not affected)
#  "goldrush" - every block YOU mine gives bonus gold (not blocks broken by 3x3/explosions)
#  "shield"   - protects you from bomb explosions
POWERUPS = {
    "area": ("3x3 Mining", (120, 220, 255), "power"),
    "blast": ("Explosion", (255, 150, 40), "power"),
    "speed": ("Speed", (120, 255, 140), "power"),
    "insta": ("Instant Mine", (230, 120, 255), "time"),
    "goldrush": ("Gold Rush", (255, 215, 80), "time"),
    "shield": ("Shield", (90, 180, 255), "time"),
}
SPEED_PU_BONUS = 0.25          # +25% speed per "Speed" stack
GOLDRUSH_GOLD = 0.5            # bonus gold per block you mine during Gold Rush
POWERUP_TIME_CAP = 40.0        # maximum total duration of a "time" power-up (s)
