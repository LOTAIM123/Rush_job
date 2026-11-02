TILE = 40                      # rūts izmērs pikseļos (logs = 1280x720)
S = TILE / 30                  # mērogs: visi pikseļu lielumi ir pielāgoti rūts izmēram
COLS, ROWS = 32, 18            # redzamais laukums rūtīs
WIDTH, HEIGHT = COLS * TILE, ROWS * TILE

PLAYER_SIZE = round(22 * S)
PLAYER_SPEED = 150 * S         # pikseļi sekundē (5 rūtis/s)
REACH = 2.2                    # peles sasniedzamība rūtīs

WALL_START_X = TILE
WALL_SPEED_START = 18 * S      # sienas sākuma ātrums (px/s)
WALL_SPEED_PER_TILE = 0.2 * S  # +px/s par katru nogājušo rūti (distanci)
WALL_SPEED_MAX = 140 * S       # augšējā robeža (spēlētājs bez zābakiem iet 150 * S px/s)

# bloku veidi mainās līdz ar distanci: zeme -> akmens -> slate (ciets akmens)
BLOCK_TIER_DIST = 600          # rūtis starp pakāpēm: 0 = zeme, 600 = akmens, 1200+ = slate
VEIN_CHANCE = 0.15             # varbūtība, ka kolonnā sākas zelta dzīsla
VEIN_SIZE_MIN = 4              # dzīslas izmērs (rūtis)
VEIN_SIZE_MAX = 8

SAFE_COLS = 7

START_COL = 6                  # spēlētāja starta rūts (distance = 0)

# bloka id -> (krāsa, sekundes, kas jāizrok, punkti, zelts)
BLOCKS = {
    1: ((139, 105, 70), 0.05, 1, 0),     # zeme
    2: ((120, 120, 125), 0.25, 2, 0),    # akmens
    3: ((70, 70, 85), 1.1, 4, 0),        # ciets akmens
    4: ((235, 190, 50), 0.1, 10, 1),     # zelts (+1 zelts kā nauda)
    5: ((200, 25, 25), 0.0, 0, 0),       # lava: nogalina uzreiz, nav izrokama
    6: ((55, 115, 50), 1.5, 0, 0),       # ērkšķu krūmi: palēnina, ātri izrokami
}
LAVA, BRAMBLES = 5, 6
NON_SOLID = {LAVA, BRAMBLES}   # pa tiem var iet (lava nogalina, krūmi palēnina)
UNBREAKABLE = {LAVA}           # neizrokami un sprādzieni tos neskar

BRAMBLE_SLOW = 0.4             # kustības ātrums krūmos (40%)
SPLASH_DAMAGE = 0.25            # 3x3 un sprādziena bojājums: puse no bloka izturības

# lava un krūmi veidojas ģenerētos plankumos (kā zelta dzīslas)
LAVA_MIN_COL = 25              # lavas nav tuvu startam
LAVA_CHANCE_BASE = 0.04        # varbūtība kolonnā; aug ar distanci
LAVA_CHANCE_PER_TILE = 0.0001
LAVA_CHANCE_MAX = 0.15
LAVA_SIZE = (4, 8)
BRAMBLE_MIN_COL = 12
BRAMBLE_CHANCE = 0.07
BRAMBLE_SIZE = (3, 7)

# veikali
SHOP_EVERY = 100               # veikals ik pēc 100 distances (rūtīm)
SHOP_HALF = 2                  # veikala telpa: 2 rūtis katrā pusē

# uzlabojumi: atslēga -> (nosaukums, bāzes cena, cenas pieaugums par līmeni, maks. līmenis)
UPGRADES = {
    "pick": ("Kaplis: ātrāka racšana", 3, 2, 999),
    "boots": ("Zābaki: ātrāka kustība", 3, 2, 999),
    "slowwall": ("Siena: lēnāka kustība", 4, 2, 15),
    "luck": ("Veiksme: biežāki power-up", 4, 3, 25),
}
POWERUP_LUCK_BONUS = 0.01      # +1% power-up varbūtības par līmeni
POWERUP_CHANCE_MAX = 0.5
PICK_FACTOR = 0.85             # racšanas laiks * 0.85 par līmeni
BOOT_BONUS = 0.10              # +10% ātruma par līmeni
WALL_SLOW_PER_LEVEL = 0.05     # sienas ātrums -5% par līmeni
WALL_SLOW_MIN_MULT = 0.25      # ne lēnāk kā 25% no parastā (15 līmeņi)

# power-up, kas retumis izkrīt no izraktiem blokiem (un var sakrāties)
POWERUP_CHANCE = 0.02          # varbūtība, ka izrakts bloks dod power-up
POWERUP_DURATION = 10.0        # sekundes katram power-up "kaudzītim"
POWERUP_MAX_STACKS = 4         # cik maksimāli var sakrāties no viena veida
EFFECT_TTL = 0.35              # vizuālā efekta ilgums (sekundes)
MESSAGE_TTL = 1.6              # paziņojuma ilgums (sekundes)
BLAST_BASE_RADIUS = 1          # sprādziena rādiuss = 1 + kaudzīšu skaits

# veids -> (nosaukums, krāsa, režīms)
#  režīms "power": katra paņemšana pievieno kaudzīti (stiprāks efekts, savs taimeris)
#  režīms "time":  katra paņemšana pagarina taimeri (efekts nemainās, tikai ilgums)
#  "speed" - +25% kustības ātruma par kaudzīti; "insta" - bloki tiek izrakti uzreiz;
#  "goldrush" - katrs TIEŠI IZRAKTAIS bloks dod +1 zelta (ne sprādzienā/3x3 salauztie)
#  "area"  - katrs izrakts bloks bojā apkārtējos (puse bojājuma): 1 kaudzīte = 3x3, 2 = 5x5, ...
#  "blast" - katrs izrakts bloks uzsprāgst un bojā (puse bojājuma): 1 kaudzīte = rādiuss 2, 2 = rādiuss 3, ...
POWERUPS = {
    "area": ("3x3 racšana", (120, 220, 255), "power"),
    "blast": ("Sprādziens", (255, 150, 40), "power"),
    "speed": ("Ātrums", (120, 255, 140), "power"),
    "insta": ("Acumirklīga racšana", (230, 120, 255), "time"),
    "goldrush": ("Zelta drudzis", (255, 215, 80), "time"),
}
SPEED_PU_BONUS = 0.25         
GOLDRUSH_GOLD = 0.5              
POWERUP_TIME_CAP = 40.0       
