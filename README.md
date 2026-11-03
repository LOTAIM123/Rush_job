# Rush Job

RTK practical training project on game design, built with pygame.

Dig through endless rock before the wall catches you. Collect gold, buy upgrades in the shops, grab power-ups, and avoid lava and bombs.

## Project layout

- `game/` - game rules and state, **no pygame** (can be tested and reused on its own)
- `client/` - the pygame client: input, drawing, sound, particles, `api_client.py`; textures in `client/textures/`, audio in `client/sounds/`
- `api/` - the FastAPI server (`db.py` - SQLite, `templates/` - Jinja page with scores and rules, `static/` - CSS)
- `Dizains.docx` - the game design document

## Running

Run every command from the project root (the folder that contains `api/`, `client/` and `game/`).

```bash
python -m venv .venv
.venv\Scripts\activate          # Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt

uvicorn api.main:app --reload   # terminal 1: server (http://127.0.0.1:8000)
python -m client.main           # terminal 2: the game
```

The server is optional: without it the game still works, it just cannot show or save the top scores.
Another server address: `RUSHJOB_API=http://host:8000`.

The server also serves a web page with the top scores and the full rules at `http://127.0.0.1:8000`, with a button to the API documentation (`/docs`).

## Controls

| Key | Action |
|---|---|
| Arrows / WASD | Move |
| Space | Mine the block you are facing (works even if you are not lined up with it) |
| Left mouse button | Mine the block under the cursor (nearby) |
| E | Open / close the shop (inside a shop room) |
| 1-4 | Buy in the shop |
| Esc | Back to the menu |
| Enter | Start / play again |
| M (in game) / F2 (anywhere) | Sound on / off |

## Gameplay

- **The wall** chases you from the left. Its speed is a share of *your top speed* (base speed plus boots upgrades): it starts at 15% and grows by 25% every 100 m, reaching 100% of your top speed at about 340 m. Boots make the wall faster too; the **Wall Brake** upgrade slows it (-5% per level, down to 25%). See `WALL_*` in `game/constants.py`.
- **Blocks** change with distance: dirt at the start, stone around 600 m, slate from 1200 m (`BLOCK_TIER_DIST`). **Gold** grows in veins (`VEIN_*`).
- **Distance** is measured in tiles (1 tile = 1 m) from the start.
- **Shops** appear every 100 m. **Every price rises by 25% for every 100 m travelled, even for items you never bought** (`SHOP_PRICE_GROWTH_PER_100`), and it also rises each time you buy that item.

### Hazards

- **Lava** kills instantly on contact. It cannot be mined and explosions do not affect it. It appears from about tile 25 and gets more common with distance.
- **Brambles** slow you to 40% speed. They can be mined.
- **Bombs** are dark balls hidden in the rock (from about tile 20). Mining one sets it off and kills you, unless you have a **Shield**. 3x3, Explosion and Instant Mine do not affect bombs, so they cannot be set off from a distance.

### Power-ups

Every block you mine yourself has a 2% chance (`POWERUP_CHANCE`, higher with the Luck upgrade) to drop a power-up. Only directly mined blocks can drop one, not blocks destroyed by an explosion.

- **3x3 Mining** - every block you mine also damages the blocks around it by 25% of their health. 1 stack = 3x3, 2 = 5x5, 3 = 7x7 ...
- **Explosion** - every block you mine explodes and damages its surroundings by 25%. 1 stack = radius 2, 2 = radius 3 ...
- **Speed** - +25% movement speed per stack.
- **Instant Mine** - blocks are mined instantly (bombs are not affected).
- **Gold Rush** - every block you mine yourself gives bonus gold (not blocks broken by 3x3 or explosions).
- **Shield** - protects you from bomb explosions.

"Power" power-ups (3x3, Explosion, Speed) add stacks, up to 4, each with its own 10 s timer. "Time" power-ups (Instant Mine, Gold Rush, Shield) add 10 s to a single timer, up to 40 s. Settings: `game/constants.py`.

## Sound (mp3 / ogg / wav)

Put your own files in `client/sounds/` (create the folder):

| File | Plays when |
|---|---|
| `music.mp3` | background music (loops) |
| `break.mp3` | any block breaking |
| `break_dirt.mp3`, `break_stone.mp3`, `break_slate.mp3`, `break_gold.mp3`, `break_brambles.mp3` | (optional) one specific block breaking, replaces `break.mp3` |
| `explosion.mp3` | a bomb going off |
| `death.mp3` | the player dying |
| `death_wall.mp3`, `death_lava.mp3`, `death_bomb.mp3` | (optional) one specific kind of death |

- A name can have several variants (`break1.mp3`, `break2.mp3` ...): one is picked at random each time.
- `.ogg` and `.wav` work too.
- If the folder has at least one file, the built-in synthesized sounds are not used: whatever has no file stays silent. If the folder is empty, the built-in sounds are used.
- The console shows which files were loaded at startup, and prints a warning if a file cannot be loaded.

## Textures (optional)

`client/textures/`: `dirt.png`, `stone.png`, `slate.png`, `gold.png`, `lava.png`, `brambles.png`, `bomb.png`, `player.png`. A missing texture is drawn as a plain coloured shape.

## API

- `GET /` - web page with the top scores and the rules
- `GET /api/scores?limit=10` - top scores (JSON)
- `POST /api/scores` - `{"name": "...", "score": 0, "seconds": 0}`
- `GET /docs` - interactive API documentation
