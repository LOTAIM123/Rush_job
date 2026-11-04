"""FastAPI server.  Run from the project root:  uvicorn api.main:app --reload"""
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, Query, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field

from game import constants as C   # game constants (the game/ package has no pygame in it)

from . import db

HERE = os.path.dirname(os.path.abspath(__file__))


@asynccontextmanager
async def lifespan(app):
    db.init_db()
    yield


app = FastAPI(title="Rush Job", lifespan=lifespan)
app.mount("/static", StaticFiles(directory=os.path.join(HERE, "static")), name="static")
templates = Jinja2Templates(directory=os.path.join(HERE, "templates"))


class ScoreIn(BaseModel):
    name: str = Field(min_length=1, max_length=16)
    score: int = Field(ge=0, le=1_000_000)
    seconds: float = Field(ge=0, le=86_400)


@app.post("/api/scores", status_code=201)
def post_score(s: ScoreIn):
    db.add_score(s.name.strip(), s.score, s.seconds)
    return {"ok": True}


@app.get("/api/scores")
def get_scores(limit: int = Query(10, ge=1, le=100)):
    return db.top_scores(limit)


def pct(x):
    return f"{x * 100:.0f}%"


def build_rules():
    """Data for the rules section. All numbers come from game/constants.py,
    so the page can never drift out of sync with the game."""
    tile = C.TILE
    block_info = {
        1: ("Dirt", "The most common block at the start."),
        2: ("Stone", "Becomes more common the further you go."),
        3: ("Slate (hard rock)", "Very far from the start almost every block is slate."),
        4: ("Gold", "Grows in veins. Gives gold to spend in the shop."),
        5: ("Lava", "Kills instantly if you touch it. Cannot be mined; explosions do not affect it."),
        6: ("Brambles", f"Slow you down to {pct(C.BRAMBLE_SLOW)} speed. Can be mined."),
        7: ("Bomb", f"Looks like a dark ball in the rock. Mining it makes it explode: all blocks within {C.BOMB_BLAST_RADIUS} tiles are destroyed "
                    f"(other bombs chain-react) and you are stunned for {C.BOMB_STUN_TIME:g} s unless you have a Shield. "
                    "Not affected by 3x3, Explosion or Instant Mine, so it cannot be set off from a distance."),
    }
    blocks = []
    for kind, (name, note) in block_info.items():
        _, seconds, points, gold = C.BLOCKS[kind]
        blocks.append({
            "name": name, "note": note,
            "time": "—" if kind in C.UNBREAKABLE else f"{seconds:g} s",
            "points": points, "gold": f"{gold:g}",
        })

    pu_text = {
        "area": f"Every block you mine also damages the blocks around it by {pct(C.SPLASH_DAMAGE)} of their health. "
                "1 stack = 3x3, 2 = 5x5, 3 = 7x7 ...",
        "blast": f"Every block you mine explodes and damages its surroundings by {pct(C.SPLASH_DAMAGE)} of their health. "
                 f"1 stack = radius {C.BLAST_BASE_RADIUS + 1}, each further stack +1.",
        "speed": f"+{pct(C.SPEED_PU_BONUS)} movement speed per stack.",
        "insta": "Blocks are mined instantly (except bombs).",
        "goldrush": f"Every block you mine yourself gives +{C.GOLDRUSH_GOLD:g} bonus gold "
                    "(blocks broken by 3x3, explosions or bombs do not count).",
        "shield": "Protects you from the stun of bomb explosions while it lasts.",
    }
    powerups = []
    for key, (name, color, mode) in C.POWERUPS.items():
        how = (f"stacks (up to {C.POWERUP_MAX_STACKS}), each with its own timer" if mode == "power"
               else f"each pickup adds {C.POWERUP_DURATION:g} s (up to {C.POWERUP_TIME_CAP:g} s in total)")
        powerups.append({"name": name, "color": "#%02x%02x%02x" % color, "text": pu_text[key], "how": how})

    up_text = {
        "pick": f"Mining time x{C.PICK_FACTOR:g} per level (-{pct(1 - C.PICK_FACTOR)}).",
        "boots": f"+{pct(C.BOOT_BONUS)} movement speed per level. The wall speeds up with your top speed too.",
        "slowwall": f"The wall moves {pct(C.WALL_SLOW_PER_LEVEL)} slower per level (down to {pct(C.WALL_SLOW_MIN_MULT)} of normal).",
        "luck": f"+{pct(C.POWERUP_LUCK_BONUS)} power-up chance per level (maximum {pct(C.POWERUP_CHANCE_MAX)}).",
    }
    upgrades = []
    for key, (name, base, step, max_level) in C.UPGRADES.items():
        upgrades.append({
            "name": name, "text": up_text.get(key, ""),
            "cost": f"{base} gold, +{step} for every level bought",
            "max": "unlimited" if max_level >= 999 else f"up to level {max_level}",
        })

    return {
        "blocks": blocks, "powerups": powerups, "upgrades": upgrades,
        "player_speed": f"{C.PLAYER_SPEED / tile:g}",
        "wall_start": pct(C.WALL_START_RATIO),
        "wall_per_100": pct(C.WALL_RATIO_PER_TILE * 100),
        "wall_max": pct(C.WALL_MAX_RATIO),
        "wall_full_at": round((C.WALL_MAX_RATIO - C.WALL_START_RATIO) / C.WALL_RATIO_PER_TILE),
        "price_growth": pct(C.SHOP_PRICE_GROWTH_PER_100),
        "tier_stone": C.BLOCK_TIER_DIST, "tier_slate": 2 * C.BLOCK_TIER_DIST,
        "powerup_chance": pct(C.POWERUP_CHANCE), "powerup_duration": f"{C.POWERUP_DURATION:g}",
        "shop_every": C.SHOP_EVERY, "lava_min": C.LAVA_MIN_COL - C.START_COL,
        "bramble_min": C.BRAMBLE_MIN_COL - C.START_COL, "bomb_min": C.BOMB_MIN_COL - C.START_COL,
    }


@app.get("/", response_class=HTMLResponse)
def leaderboard(request: Request):
    return templates.TemplateResponse(request, "index.html", {
        "scores": db.top_scores(20),
        "rules": build_rules(),
        "docs_url": f"{request.base_url}docs",      # e.g. http://127.0.0.1:8000/docs
    })
