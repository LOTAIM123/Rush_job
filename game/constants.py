TILE = 30
COLS, ROWS = 32, 18            # redzamais laukums rūtīs
WIDTH, HEIGHT = COLS * TILE, ROWS * TILE

PLAYER_SIZE = 22
PLAYER_SPEED = 150             # pikseļi sekundē
REACH = 2.2                    # peles sasniedzamība rūtīs

WALL_START_X = TILE
WALL_SPEED_START = 18          # sienas sākuma ātrums (px/s)
WALL_SPEED_PER_TILE = 0.2      # +px/s par katru nogājušo rūti (distanci)
WALL_SPEED_MAX = 140           # augšējā robeža (spēlētājs bez zābakiem iet 150 px/s)

# bloku veidi mainās līdz ar distanci: zeme -> akmens -> slate (ciets akmens)
BLOCK_TIER_DIST = 150          # rūtis starp pakāpēm: 0 = zeme, 150 = akmens, 300+ = slate
GOLD_CHANCE = 0.05             # zelta bloka varbūtība jebkurā distancē

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
    "pick": ("Kaplis: ātrāka racšana", 3, 2, 999),
    "boots": ("Zābaki: ātrāka kustība", 3, 2, 999),
    "pushback": ("Sienas atgrūšana", 4, 2, 999),
    "luck": ("Veiksme: biežāki power-up", 4, 3, 25),
}
POWERUP_LUCK_BONUS = 0.01      # +1% power-up varbūtības par līmeni
POWERUP_CHANCE_MAX = 0.5
PICK_FACTOR = 0.85             # racšanas laiks * 0.85 par līmeni
BOOT_BONUS = 0.10              # +10% ātruma par līmeni
PUSHBACK_TILES = 5             # cik rūtis siena tiek atgrūsta

# power-up, kas retumis izkrīt no izraktiem blokiem (un var sakrāties)
POWERUP_CHANCE = 0.02          # varbūtība, ka izrakts bloks dod power-up
POWERUP_DURATION = 10.0        # sekundes katram power-up "kaudzītim"
POWERUP_MAX_STACKS = 4         # cik maksimāli var sakrāties no viena veida
EFFECT_TTL = 0.35              # vizuālā efekta ilgums (sekundes)
MESSAGE_TTL = 1.6              # paziņojuma ilgums (sekundes)
BLAST_BASE_RADIUS = 1          # sprādziena rādiuss = 1 + kaudzīšu skaits

# veids -> (nosaukums, krāsa)
#  "area"  - katrs izrakts bloks izrok arī apkārtējos: 1 kaudzīte = 3x3, 2 = 5x5, ...
#  "blast" - katrs izrakts bloks uzsprāgst: 1 kaudzīte = rādiuss 2, 2 = rādiuss 3, ...
POWERUPS = {
    "area": ("3x3 racšana", (120, 220, 255)),
    "blast": ("Sprādziens", (255, 150, 40)),
}
