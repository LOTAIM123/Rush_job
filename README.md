RTK praktiskās mācības projekts par game design uz platformas pygame

## Power-up

Izrakti bloki retumis (`POWERUP_CHANCE`, pēc noklusējuma 2%) dod power-up. Tie ir uz laiku (10 s) un **sakrājas**:

- **3x3 racšana** — katrs izrakts bloks bojā arī apkārtējos (puse no bloka izturības, tāpēc tie parasti salūst ar otro triecienu). 1 kaudzīte = 3x3, 2 = 5x5, 3 = 7x7 ...
- **Sprādziens** — katrs izrakts bloks uzsprāgst un bojā apkārtni (puse no izturības). 1 kaudzīte = rādiuss 2, 2 = rādiuss 3 ...
- **Ātrums** — +25% kustības ātruma par kaudzīti.
- **Acumirklīga racšana** — bloki tiek izrakti uzreiz. Jauns pickup pagarina laiku par 10 s (līdz 40 s).
- **Zelta drudzis** — katrs tieši izrakts bloks dod +1 zelta (sprādzienā/3x3 salauztie bloki nedod). Jauns pickup pagarina laiku par 10 s (līdz 40 s).

Katrs jauns power-up pievieno jaunu kaudzīti ar savu 10 s taimeri (maks. 4 no viena veida); abi veidi var darboties reizē.
Power-up var izkrist tikai no tieši izrakta bloka, nevis no sprādzienā izpostītajiem. Iestatījumi: `game/constants.py`.

## Distance

- **Bloki** mainās līdz ar distanci (lēni): sākumā zeme, ap 600 rūtīm akmens, no 1200 rūtīm slate (ciets akmens), ar vienmērīgu pāreju (`BLOCK_TIER_DIST`).
- **Zelts** veidojas dzīslās (4–8 savienotas rūtis, `VEIN_CHANCE`, `VEIN_SIZE_*`).
- **Siena** kļūst ātrāka līdz ar nogājušo distanci: 18 px/s + 0,2 px/s par rūti, līdz 140 px/s (`WALL_SPEED_PER_TILE`, `WALL_SPEED_MAX`). Laiks vairs neietekmē sienas ātrumu.
- Veikalā var nopirkt **Veiksmi** (+1% power-up varbūtības par līmeni, maks. 25 līmeņi).

## Bīstamība

- **Lava** — nogalina uzreiz, ja tai pieskaries; to nevar izrakt, un sprādzieni to neskar. Parādās no ~25. rūts, ar distanci aizvien biežāk.
- **Ērkšķu krūmi** — palēnina kustību līdz 40%; tos var ātri izrakt.

## Skaņa (mp3 / ogg / wav)

Ieliec savus failus mapē `client/sounds/` (mapi izveido pats):

| Fails | Kad skan |
|---|---|
| `music.mp3` | fona mūzika (cikliski) |
| `break.mp3` | jebkura bloka salūšana |
| `break_dirt.mp3`, `break_stone.mp3`, `break_slate.mp3`, `break_gold.mp3`, `break_brambles.mp3` | (neobligāti) konkrēta bloka salūšana, aizstāj `break.mp3` |
| `death.mp3` | spēlētāja nāve |
| `death_wall.mp3`, `death_lava.mp3` | (neobligāti) nāve no sienas / lavas |

- Vienam nosaukumam var būt vairākas versijas (`break1.mp3`, `break2.mp3` ...): katru reizi tiek izvēlēta nejauša.
- Der arī `.ogg` un `.wav`.
- Ja mapē ir kaut viens fails, sintezētās skaņas netiek lietotas: kam nav faila, tas paliek kluss. Ja mape ir tukša, spēle lieto iebūvētās sintezētās skaņas.
- **M** (spēlē) vai **F2** (jebkur) — ieslēgt/izslēgt skaņu.
- Konsolē startā redzams, kuri faili ielādēti; ja fails nelādējas, tiek izvadīts brīdinājums.
