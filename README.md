RTK praktiskās mācības projekts par game design uz platformas pygame

## Power-up

Izrakti bloki retumis (`POWERUP_CHANCE`, pēc noklusējuma 2%) dod power-up. Tie ir uz laiku (10 s) un **sakrājas**:

- **3x3 racšana** — katrs izrakts bloks izrok arī apkārtējos. 1 kaudzīte = 3x3, 2 = 5x5, 3 = 7x7 ...
- **Sprādziens** — katrs izrakts bloks uzsprāgst. 1 kaudzīte = rādiuss 2, 2 = rādiuss 3 ...

Katrs jauns power-up pievieno jaunu kaudzīti ar savu 10 s taimeri (maks. 4 no viena veida); abi veidi var darboties reizē.
Power-up var izkrist tikai no tieši izrakta bloka, nevis no sprādzienā izpostītajiem. Iestatījumi: `game/constants.py`.

## Distance

- **Bloki** mainās līdz ar distanci: sākumā zeme, ap 150 rūtīm akmens, no 300 rūtīm slate (ciets akmens), ar vienmērīgu pāreju (`BLOCK_TIER_DIST`). Zelts izkrīt jebkurā distancē (`GOLD_CHANCE`).
- **Siena** kļūst ātrāka līdz ar nogājušo distanci: 18 px/s + 0,2 px/s par rūti, līdz 140 px/s (`WALL_SPEED_PER_TILE`, `WALL_SPEED_MAX`). Laiks vairs neietekmē sienas ātrumu.
- Veikalā var nopirkt **Veiksmi** (+1% power-up varbūtības par līmeni, maks. 25 līmeņi).
