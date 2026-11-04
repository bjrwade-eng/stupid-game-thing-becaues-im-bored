"""Pixel framebuffer drawing: world, lander, HUD."""

from __future__ import annotations

import math

import pygame

from .lander import Lander
from .world import World

# Retro palette
BLACK = (8, 8, 12)
STAR = (200, 200, 210)
REGOLITH = (110, 110, 118)
REGOLITH_DARK = (70, 70, 78)
PAD = (160, 160, 150)
PAD_MARK = (220, 200, 80)
LANDER = (230, 230, 235)
LANDER_DARK = (150, 150, 160)
FLAME = (255, 140, 40)
FLAME_CORE = (255, 230, 120)
HUD = (255, 180, 60)
HUD_DIM = (140, 100, 40)
CRASH = (220, 60, 50)
OK = (80, 220, 120)
TITLE = (240, 220, 160)


def draw_world(surf: pygame.Surface, world: World) -> None:
    surf.fill(BLACK)
    # Sparse stars
    rng_seed = world.pad_left * 97 + world.pad_y
    rng = _TinyRng(rng_seed)
    for _ in range(40):
        sx = rng.randint(0, world.width - 1)
        sy = rng.randint(0, world.height // 2)
        surf.set_at((sx, sy), STAR)

    for x in range(world.width):
        gy = world.heights[x]
        pygame.draw.line(surf, REGOLITH, (x, gy), (x, world.height - 1))
        if gy + 3 < world.height:
            pygame.draw.line(surf, REGOLITH_DARK, (x, gy + 3), (x, world.height - 1))

    # Landing pad
    pygame.draw.line(
        surf, PAD, (world.pad_left, world.pad_y), (world.pad_right - 1, world.pad_y)
    )
    pygame.draw.line(
        surf,
        PAD_MARK,
        (world.pad_left, world.pad_y + 1),
        (world.pad_right - 1, world.pad_y + 1),
    )
    # Pad flags
    mid = (world.pad_left + world.pad_right) // 2
    pygame.draw.line(surf, PAD_MARK, (mid, world.pad_y - 6), (mid, world.pad_y))
    pygame.draw.rect(surf, OK, (mid + 1, world.pad_y - 6, 3, 2))


def draw_lander(surf: pygame.Surface, lander: Lander) -> None:
    cx, cy = lander.x, lander.y
    angle = lander.angle
    points = _rotated_body(cx, cy, angle)

    if not lander.alive:
        # Crash debris
        for dx, dy in ((-3, -1), (2, -2), (-1, 2), (3, 1), (0, -3)):
            surf.set_at((int(cx + dx), int(cy + dy)), CRASH)
        return

    pygame.draw.polygon(surf, LANDER, points)
    # Cabin window
    rad = math.radians(angle - 90.0)
    wx = cx + math.cos(rad) * 1.5
    wy = cy + math.sin(rad) * 1.5
    surf.set_at((int(wx), int(wy)), LANDER_DARK)

    # Legs
    left_leg = _rotate_point(cx, cy, -3, 4, angle)
    right_leg = _rotate_point(cx, cy, 3, 4, angle)
    foot_l = _rotate_point(cx, cy, -4, 5, angle)
    foot_r = _rotate_point(cx, cy, 4, 5, angle)
    pygame.draw.line(surf, LANDER, (int(cx), int(cy + 2)), (int(left_leg[0]), int(left_leg[1])))
    pygame.draw.line(surf, LANDER, (int(cx), int(cy + 2)), (int(right_leg[0]), int(right_leg[1])))
    surf.set_at((int(foot_l[0]), int(foot_l[1])), LANDER)
    surf.set_at((int(foot_r[0]), int(foot_r[1])), LANDER)

    if lander.thrusting:
        # Flame opposite nose (down relative to lander)
        fx, fy = _rotate_point(cx, cy, 0, 6, angle)
        fx2, fy2 = _rotate_point(cx, cy, 0, 9, angle)
        pygame.draw.line(surf, FLAME, (int(fx), int(fy)), (int(fx2), int(fy2)))
        core = _rotate_point(cx, cy, 0, 7, angle)
        surf.set_at((int(core[0]), int(core[1])), FLAME_CORE)


def draw_hud(
    surf: pygame.Surface,
    font: pygame.font.Font,
    lander: Lander,
    world: World,
) -> None:
    alt = world.altitude(lander.feet_y, lander.x)
    lines = [
        f"ALT {alt:5.0f}",
        f"VX  {lander.vx:5.1f}",
        f"VY  {lander.vy:5.1f}",
        f"ANG {lander.angle:5.0f}",
        f"FUEL{lander.fuel:5.0f}",
    ]
    y = 2
    for text in lines:
        color = HUD if lander.fuel > 20 else CRASH
        if text.startswith("FUEL") and lander.fuel > 20:
            color = HUD
        img = font.render(text, False, color)
        surf.blit(img, (2, y))
        y += 8

    # Fuel bar
    bar_x, bar_y, bar_w, bar_h = world.width - 36, 4, 30, 4
    pygame.draw.rect(surf, HUD_DIM, (bar_x, bar_y, bar_w, bar_h))
    fill = int(bar_w * (lander.fuel / lander.MAX_FUEL))
    pygame.draw.rect(surf, HUD, (bar_x, bar_y, fill, bar_h))


def draw_centered_text(
    surf: pygame.Surface,
    font: pygame.font.Font,
    lines: list[tuple[str, tuple[int, int, int]]],
    y_start: int,
) -> None:
    y = y_start
    for text, color in lines:
        img = font.render(text, False, color)
        x = (surf.get_width() - img.get_width()) // 2
        surf.blit(img, (x, y))
        y += img.get_height() + 4


def _rotated_body(cx: float, cy: float, angle: float) -> list[tuple[int, int]]:
    # Local points: nose up diamond-ish lander
    local = [(0, -4), (3, 1), (2, 3), (-2, 3), (-3, 1)]
    return [tuple(map(int, _rotate_point(cx, cy, px, py, angle))) for px, py in local]


def _rotate_point(cx: float, cy: float, lx: float, ly: float, angle: float) -> tuple[float, float]:
    rad = math.radians(angle)
    cos_a, sin_a = math.cos(rad), math.sin(rad)
    rx = lx * cos_a - ly * sin_a
    ry = lx * sin_a + ly * cos_a
    return cx + rx, cy + ry


class _TinyRng:
    def __init__(self, seed: int) -> None:
        self.state = seed & 0xFFFFFFFF

    def randint(self, a: int, b: int) -> int:
        self.state = (1664525 * self.state + 1013904223) & 0xFFFFFFFF
        return a + (self.state % (b - a + 1))
