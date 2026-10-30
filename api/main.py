"""FastAPI serveris.  Palaist no `spele/`:  uvicorn api.main:app --reload"""
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, Query, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field

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


@app.get("/", response_class=HTMLResponse)
def leaderboard(request: Request):
    return templates.TemplateResponse(
        request, "index.html", {"scores": db.top_scores(20)})
