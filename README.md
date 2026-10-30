RTK praktiskās mācības projekts par game design uz platformas pygame

## Power-up

Izrakti bloki retumis (`POWERUP_CHANCE`, pēc noklusējuma 2%) dod power-up. Tie ir uz laiku (10 s) un **sakrājas**:

- **3x3 racšana** — katrs izrakts bloks izrok arī apkārtējos. 1 kaudzīte = 3x3, 2 = 5x5, 3 = 7x7 ...
- **Sprādziens** — katrs izrakts bloks uzsprāgst. 1 kaudzīte = rādiuss 2, 2 = rādiuss 3 ...
- **Ātrums** — +25% kustības ātruma par kaudzīti.
- **Acumirklīga racšana** — bloki tiek izrakti uzreiz. Jauns pickup pagarina laiku par 10 s (līdz 40 s).
- **Zelta drudzis** — katrs salauztais bloks (arī sprādzienā) dod +1 zelta. Jauns pickup pagarina laiku par 10 s (līdz 40 s).

Katrs jauns power-up pievieno jaunu kaudzīti ar savu 10 s taimeri (maks. 4 no viena veida); abi veidi var darboties reizē.
Power-up var izkrist tikai no tieši izrakta bloka, nevis no sprādzienā izpostītajiem. Iestatījumi: `game/constants.py`.

## Distance

- **Bloki** mainās līdz ar distanci (lēni): sākumā zeme, ap 600 rūtīm akmens, no 1200 rūtīm slate (ciets akmens), ar vienmērīgu pāreju (`BLOCK_TIER_DIST`).
- **Zelts** veidojas dzīslās (4–8 savienotas rūtis, `VEIN_CHANCE`, `VEIN_SIZE_*`).
- **Siena** kļūst ātrāka līdz ar nogājušo distanci: 18 px/s + 0,2 px/s par rūti, līdz 140 px/s (`WALL_SPEED_PER_TILE`, `WALL_SPEED_MAX`). Laiks vairs neietekmē sienas ātrumu.
- Veikalā var nopirkt **Veiksmi** (+1% power-up varbūtības par līmeni, maks. 25 līmeņi).
