"""Daļiņas: gruži, kas izlido no salauzta bloka (tikai attēlošanai, spēles loģika tās nepazīst)."""
import math
import random

import pygame

from game import BLOCKS, S, TILE

MAX_PARTICLES = 500             # drošības robeža (piem., liels sprādziens)
DRAG = 5.0                      # bremzēšana: daļiņas izlido un apstājas


class Particles:
    def __init__(self, textures):
        self.items = []
        self.rng = random.Random()
        self.colors = {}
        for kind, spec in BLOCKS.items():
            color = spec[0]
            tex = textures.get(kind)
            if tex:                                  # gruži ņem tekstūras vidējo krāsu
                try:
                    color = tuple(pygame.transform.average_color(tex))[:3]
                except pygame.error:
                    pass
            self.colors[kind] = color

    def clear(self):
        self.items.clear()

    def handle(self, events):
        """Katram salauztam blokam izlido gruži (sprādzienā - mazāk katram, lai nav pārblīvēts)."""
        breaks = [e for e in events if e[0] == "break"]
        per_block = 10 if len(breaks) <= 4 else 4
        for _, kind, (col, row) in breaks:
            self.spawn(kind, col, row, per_block)

    def spawn(self, kind, col, row, n):
        rng = self.rng
        base = self.colors.get(kind, (150, 150, 150))
        cx, cy = col * TILE + TILE / 2, row * TILE + TILE / 2
        for _ in range(n):
            if len(self.items) >= MAX_PARTICLES:
                return
            ang = rng.uniform(0, 2 * math.pi)
            speed = rng.uniform(90, 300) * S
            shade = rng.uniform(0.7, 1.25)
            life = rng.uniform(0.35, 0.7)
            self.items.append({
                "x": cx + rng.uniform(-TILE / 3, TILE / 3),
                "y": cy + rng.uniform(-TILE / 3, TILE / 3),
                "vx": math.cos(ang) * speed, "vy": math.sin(ang) * speed,
                "life": life, "max": life, "size": rng.uniform(3, 7) * S,
                "color": tuple(min(255, int(c * shade)) for c in base),
            })
        if kind == 4:                                # zelts: papildus mirdzoši dzirksteles
            for _ in range(n // 2 + 2):
                if len(self.items) >= MAX_PARTICLES:
                    return
                ang = rng.uniform(0, 2 * math.pi)
                speed = rng.uniform(60, 220) * S
                life = rng.uniform(0.5, 0.9)
                self.items.append({
                    "x": cx, "y": cy,
                    "vx": math.cos(ang) * speed, "vy": math.sin(ang) * speed,
                    "life": life, "max": life, "size": rng.uniform(2, 4) * S,
                    "color": (255, 245, 170),
                })

    def update(self, dt):
        drag = max(0.0, 1.0 - DRAG * dt)
        alive = []
        for p in self.items:
            p["life"] -= dt
            if p["life"] <= 0:
                continue
            p["x"] += p["vx"] * dt
            p["y"] += p["vy"] * dt
            p["vx"] *= drag
            p["vy"] *= drag
            alive.append(p)
        self.items = alive

    def draw(self, screen, cam_x):
        for p in self.items:
            frac = p["life"] / p["max"]
            size = max(1, int(p["size"] * (0.4 + 0.6 * frac)))      # saraujas, kad izdziest
            rect = pygame.Rect(int(p["x"] - cam_x - size / 2), int(p["y"] - size / 2), size, size)
            pygame.draw.rect(screen, p["color"], rect)
