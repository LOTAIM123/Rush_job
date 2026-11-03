"""FastAPI serveris.  Palaist no `spele/`:  uvicorn api.main:app --reload"""
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, Query, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field

from game import constants as C   # spēles konstantes (game/ nesatur pygame)

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


def lv(text):
    """Latviešu decimālzīme: 0.5 -> 0,5"""
    return str(text).replace(".", ",")


def build_rules():
    """Noteikumu lapas dati. Skaitļi tiek ņemti no game/constants.py, lai lapa nekad neatpaliek no spēles."""
    tile = C.TILE
    block_info = {
        1: ("Zeme", "Sākumā visbiežākais bloks."),
        2: ("Akmens", "Parādās aizvien biežāk, jo tālāk dodies."),
        3: ("Slate (ciets akmens)", "Ļoti tālu no starta gandrīz visi bloki ir slate."),
        4: ("Zelts", "Veidojas dzīslās. Dod zeltu, ko tērēt veikalā."),
        5: ("Lava", "Nogalina uzreiz, ja tai pieskaries. Neizrokama, sprādzieni to neskar."),
        6: ("Ērkšķu krūmi", f"Palēnina kustību līdz {pct(C.BRAMBLE_SLOW)}. Var izrakt."),
    }
    blocks = []
    for kind, (name, note) in block_info.items():
        _, seconds, points, gold = C.BLOCKS[kind]
        blocks.append({
            "name": name, "note": note,
            "time": "—" if kind in C.UNBREAKABLE else lv(f"{seconds:g} s"),
            "points": points, "gold": lv(f"{gold:g}"),
        })

    pu_text = {
        "area": f"Katrs tieši izrakts bloks bojā apkārtējos par {pct(C.SPLASH_DAMAGE)} no to izturības. "
                "1 kaudzīte = 3×3, 2 = 5×5, 3 = 7×7 …",
        "blast": f"Katrs izrakts bloks uzsprāgst un bojā apkārtni par {pct(C.SPLASH_DAMAGE)} no izturības. "
                 f"1 kaudzīte = rādiuss {C.BLAST_BASE_RADIUS + 1}, katra nākamā +1.",
        "speed": f"+{pct(C.SPEED_PU_BONUS)} kustības ātruma par kaudzīti.",
        "insta": "Bloki tiek izrakti acumirklī.",
        "goldrush": f"Katrs tieši izrakts bloks dod papildus +{lv(f"{C.GOLDRUSH_GOLD:g}")} zelta "
                    "(sprādzienā vai 3×3 salauztie bloki nedod).",
    }
    powerups = []
    for key, (name, color, mode) in C.POWERUPS.items():
        how = (f"kaudzītes (līdz {C.POWERUP_MAX_STACKS}), katrai savs taimeris" if mode == "power"
               else f"jauns pickup pagarina laiku par {C.POWERUP_DURATION:g} s (līdz {C.POWERUP_TIME_CAP:g} s)")
        powerups.append({"name": name, "color": "#%02x%02x%02x" % color, "text": pu_text[key], "how": how})

    up_text = {
        "pick": f"Racšanas laiks ×{lv(f'{C.PICK_FACTOR:g}')} par līmeni (−{pct(1 - C.PICK_FACTOR)}).",
        "boots": f"+{pct(C.BOOT_BONUS)} kustības ātruma par līmeni.",
        "slowwall": f"Siena kustas par {pct(C.WALL_SLOW_PER_LEVEL)} lēnāk par līmeni (ne lēnāk kā līdz {pct(C.WALL_SLOW_MIN_MULT)}).",
        "luck": f"+{pct(C.POWERUP_LUCK_BONUS)} power-up izredžu par līmeni (maksimums {pct(C.POWERUP_CHANCE_MAX)}).",
    }
    upgrades = []
    for key, (name, base, step, max_level) in C.UPGRADES.items():
        upgrades.append({
            "name": name, "text": up_text.get(key, ""),
            "cost": f"{base} zelts, +{step} par katru nākamo līmeni",
            "max": "bez ierobežojuma" if max_level >= 999 else f"līdz {max_level}. līmenim",
        })

    return {
        "blocks": blocks, "powerups": powerups, "upgrades": upgrades,
        "player_speed": lv(f"{C.PLAYER_SPEED / tile:g}"),
        "wall_start": lv(f"{C.WALL_SPEED_START / tile:.1f}"),
        "wall_per_100": lv(f"{C.WALL_SPEED_PER_TILE * 100 / tile:.1f}"),
        "wall_max": lv(f"{C.WALL_SPEED_MAX / tile:.1f}"),
        "tier_stone": C.BLOCK_TIER_DIST, "tier_slate": 2 * C.BLOCK_TIER_DIST,
        "powerup_chance": pct(C.POWERUP_CHANCE), "powerup_duration": f"{C.POWERUP_DURATION:g}",
        "shop_every": C.SHOP_EVERY, "lava_min": C.LAVA_MIN_COL - C.START_COL,
        "bramble_min": C.BRAMBLE_MIN_COL - C.START_COL,
    }


@app.get("/", response_class=HTMLResponse)
def leaderboard(request: Request):
    return templates.TemplateResponse(request, "index.html", {
        "scores": db.top_scores(20),
        "rules": build_rules(),
        "docs_url": f"{request.base_url}docs",      # piem., http://127.0.0.1:8000/docs
    })
