"""Spēles konstantes (bez pygame)."""

TILE = 30
COLS, ROWS = 32, 18            # redzamais laukums rūtīs
WIDTH, HEIGHT = COLS * TILE, ROWS * TILE

PLAYER_SIZE = 22
PLAYER_SPEED = 150             # pikseļi sekundē
REACH = 2.2                    # peles sasniedzamība rūtīs

WALL_START_X = TILE
WALL_SPEED_START = 18
WALL_SPEED_GAIN = 0.8
WALL_SPEED_MAX = 90

SAFE_COLS = 7

START_COL = 6                  # spēlētāja starta rūts (distance = 0)

# bloka id -> (krāsa, sekundes, kas jāizrok, punkti, zelts)
BLOCKS = {
    1: ((139, 105, 70), 0.05, 1, 0),     # zeme
    2: ((120, 120, 125), 0.25, 2, 0),    # akmens
    3: ((70, 70, 85), 1.1, 4, 0),        # ciets akmens
    4: ((235, 190, 50), 0.1, 10, 1),     # zelts (+1 zelts kā nauda)
}

# veikali
SHOP_EVERY = 100               # veikals ik pēc 100 distances (rūtīm)
SHOP_HALF = 2                  # veikala telpa: 2 rūtis katrā pusē

# uzlabojumi: atslēga -> (nosaukums, bāzes cena, cenas pieaugums par līmeni, maks. līmenis)
UPGRADES = {
    "pick": ("Kaplis: ātrāka racšana", 3, 2, 8),
    "boots": ("Zābaki: ātrāka kustība", 3, 2, 5),
    "pushback": ("Sienas atgrūšana", 4, 2, 99),
}
PICK_FACTOR = 0.85             # racšanas laiks * 0.85 par līmeni
BOOT_BONUS = 0.10              # +10% ātruma par līmeni
PUSHBACK_TILES = 5             # cik rūtis siena tiek atgrūsta
