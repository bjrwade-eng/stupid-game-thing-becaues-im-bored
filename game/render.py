"""HD framebuffer drawing: sky, terrain detail, LEM, HUD, ascent."""

from __future__ import annotations

import math

import pygame

from .lander import Lander
from .world import World

# Palette
SPACE_TOP = (4, 6, 18)
SPACE_MID = (10, 12, 28)
SPACE_HORIZON = (22, 24, 40)
REGOLITH = (128, 128, 132)
REGOLITH_MID = (98, 98, 104)
REGOLITH_DARK = (62, 62, 70)
REGOLITH_EDGE = (168, 168, 172)
CRATER_RIM = (150, 150, 156)
CRATER_FLOOR = (78, 78, 86)
PAD = (170, 170, 160)
PAD_MARK = (230, 210, 90)
PAD_SHADOW = (90, 90, 85)
FOIL = (196, 168, 72)
FOIL_DARK = (140, 110, 40)
ASCENT = (220, 222, 228)
ASCENT_SHADE = (150, 154, 164)
WINDOW = (40, 70, 110)
WINDOW_GLOW = (120, 170, 210)
LEG = (190, 190, 198)
FOOTPAD = (210, 210, 215)
FLAME = (255, 140, 40)
FLAME_CORE = (255, 235, 140)
FLAME_OUTER = (220, 70, 20)
HUD = (255, 190, 70)
HUD_DIM = (150, 110, 45)
CRASH = (230, 70, 55)
OK = (90, 230, 130)
TITLE = (245, 230, 170)
EARTH_OCEAN = (50, 90, 170)
EARTH_LAND = (70, 140, 90)
EARTH_CLOUD = (220, 230, 240)
EARTH_GLOW = (80, 120, 200)


def draw_world(surf: pygame.Surface, world: World) -> None:
    _draw_sky(surf, world)
    _draw_earth(surf, world)
    _draw_stars(surf, world)
    for ridge in world.ridges:
        if len(ridge.points) >= 3:
            pygame.draw.polygon(surf, ridge.color, ridge.points)

    # Main terrain fill
    terrain_pts = [(0, world.height)]
    for x, h in enumerate(world.heights):
        terrain_pts.append((x, h))
    terrain_pts.append((world.width - 1, world.height))
    pygame.draw.polygon(surf, REGOLITH_MID, terrain_pts)

    # Surface highlight band
    for x in range(world.width):
        gy = world.heights[x]
        pygame.draw.line(surf, REGOLITH, (x, gy), (x, min(world.height - 1, gy + 10)))
        pygame.draw.line(
            surf, REGOLITH_DARK, (x, gy + 14), (x, world.height - 1)
        )
        # Lit rim
        if 0 <= gy < world.height:
            surf.set_at((x, gy), REGOLITH_EDGE)

    _draw_craters(surf, world)
    _draw_rocks(surf, world)
    _draw_pad(surf, world)


def draw_lander(surf: pygame.Surface, lander: Lander, t: float = 0.0) -> None:
    if lander.separated:
        _draw_descent_stage(surf, lander.descent_x, lander.descent_y, 0.0, thrusting=False)
        _draw_ascent_stage(
            surf,
            lander.ascent_x,
            lander.ascent_y,
            0.0,
            thrusting=True,
            flame_phase=t,
        )
        return

    if not lander.alive:
        _draw_crash(surf, lander.x, lander.y)
        return

    _draw_full_lem(
        surf,
        lander.x,
        lander.y,
        lander.angle,
        thrusting=lander.thrusting,
        flame_phase=t,
    )


def draw_hud(
    surf: pygame.Surface,
    font: pygame.font.Font,
    lander: Lander,
    world: World,
) -> None:
    alt = world.altitude(lander.feet_y, lander.x)
    lines = [
        f"ALT  {alt:6.0f}",
        f"VX   {lander.vx:6.1f}",
        f"VY   {lander.vy:6.1f}",
        f"ANG  {lander.angle:6.0f}",
        f"FUEL {lander.fuel:6.0f}",
    ]
    y = 8
    for text in lines:
        color = HUD
        if text.startswith("FUEL") and lander.fuel <= 20:
            color = CRASH
        img = font.render(text, True, color)
        surf.blit(img, (10, y))
        y += img.get_height() + 2

    bar_x, bar_y, bar_w, bar_h = world.width - 120, 12, 100, 10
    pygame.draw.rect(surf, HUD_DIM, (bar_x, bar_y, bar_w, bar_h), border_radius=2)
    fill = int(bar_w * (lander.fuel / lander.MAX_FUEL))
    if fill > 0:
        pygame.draw.rect(surf, HUD, (bar_x, bar_y, fill, bar_h), border_radius=2)
    pygame.draw.rect(surf, HUD, (bar_x, bar_y, bar_w, bar_h), width=1, border_radius=2)


def draw_centered_text(
    surf: pygame.Surface,
    font: pygame.font.Font,
    lines: list[tuple[str, tuple[int, int, int]]],
    y_start: int,
) -> None:
    y = y_start
    for text, color in lines:
        img = font.render(text, True, color)
        x = (surf.get_width() - img.get_width()) // 2
        # Soft shadow for readability
        shadow = font.render(text, True, (0, 0, 0))
        surf.blit(shadow, (x + 2, y + 2))
        surf.blit(img, (x, y))
        y += img.get_height() + 8


def _draw_sky(surf: pygame.Surface, world: World) -> None:
    # Vertical gradient
    h = world.height
    for y in range(h):
        t = y / max(1, h - 1)
        if t < 0.55:
            u = t / 0.55
            c = _lerp_color(SPACE_TOP, SPACE_MID, u)
        else:
            u = (t - 0.55) / 0.45
            c = _lerp_color(SPACE_MID, SPACE_HORIZON, u)
        pygame.draw.line(surf, c, (0, y), (world.width, y))


def _draw_stars(surf: pygame.Surface, world: World) -> None:
    for x, y, size, bright in world.stars:
        col = (bright, bright, min(255, bright + 10))
        if size <= 1:
            if 0 <= x < world.width and 0 <= y < world.height:
                surf.set_at((x, y), col)
        else:
            pygame.draw.circle(surf, col, (x, y), size)


def _draw_earth(surf: pygame.Surface, world: World) -> None:
    # Crescent Earth hanging in the sky
    cx, cy, r = int(world.width * 0.82), int(world.height * 0.16), 34
    pygame.draw.circle(surf, EARTH_GLOW, (cx, cy), r + 4)
    pygame.draw.circle(surf, EARTH_OCEAN, (cx, cy), r)
    pygame.draw.ellipse(surf, EARTH_LAND, (cx - 18, cy - 10, 22, 14))
    pygame.draw.ellipse(surf, EARTH_LAND, (cx - 4, cy + 4, 16, 10))
    pygame.draw.ellipse(surf, EARTH_CLOUD, (cx - 12, cy - 16, 20, 8))
    # Shadow for crescent
    pygame.draw.circle(surf, SPACE_TOP, (cx + 12, cy - 2), r)


def _draw_craters(surf: pygame.Surface, world: World) -> None:
    for crater in world.craters:
        x, y, r = int(crater.x), int(crater.y), int(crater.radius)
        pygame.draw.circle(surf, CRATER_FLOOR, (x, y), r)
        pygame.draw.circle(surf, CRATER_RIM, (x, y), r, width=2)
        # Inner shadow
        pygame.draw.arc(
            surf,
            REGOLITH_DARK,
            (x - r, y - r, r * 2, r * 2),
            math.pi * 0.1,
            math.pi * 0.9,
            2,
        )


def _draw_rocks(surf: pygame.Surface, world: World) -> None:
    for rock in world.rocks:
        x, y, s = int(rock.x), int(rock.y), rock.size
        pts = [(x, y - s), (x + s, y), (x + s // 2, y + s // 2), (x - s, y + s // 3)]
        pygame.draw.polygon(surf, REGOLITH_DARK, pts)
        pygame.draw.line(surf, REGOLITH_EDGE, pts[0], pts[1])


def _draw_pad(surf: pygame.Surface, world: World) -> None:
    y = world.pad_y
    left, right = world.pad_left, world.pad_right
    pygame.draw.rect(surf, PAD_SHADOW, (left, y, right - left, 6))
    pygame.draw.rect(surf, PAD, (left, y - 2, right - left, 4))
    # Centerline marks
    for mx in range(left + 8, right - 8, 16):
        pygame.draw.rect(surf, PAD_MARK, (mx, y - 1, 8, 2))
    # Beacon poles
    mid = (left + right) // 2
    for px in (left + 10, right - 10):
        pygame.draw.line(surf, PAD_MARK, (px, y - 18), (px, y))
        pygame.draw.polygon(surf, OK, [(px, y - 18), (px + 8, y - 14), (px, y - 10)])
    pygame.draw.circle(surf, PAD_MARK, (mid, y - 3), 3)


def _draw_full_lem(
    surf: pygame.Surface,
    x: float,
    y: float,
    angle: float,
    *,
    thrusting: bool,
    flame_phase: float,
) -> None:
    _draw_descent_stage(surf, x, y, angle, thrusting=thrusting, flame_phase=flame_phase)
    _draw_ascent_stage(surf, x, y - 2, angle, thrusting=False, flame_phase=flame_phase)


def _draw_descent_stage(
    surf: pygame.Surface,
    x: float,
    y: float,
    angle: float,
    *,
    thrusting: bool,
    flame_phase: float = 0.0,
) -> None:
    # Gold-foil octagonal descent body
    body = [(-10, -2), (-8, 6), (-3, 9), (3, 9), (8, 6), (10, -2), (6, -5), (-6, -5)]
    pts = [_rp(x, y, px, py, angle) for px, py in body]
    pygame.draw.polygon(surf, FOIL, pts)
    pygame.draw.polygon(surf, FOIL_DARK, pts, width=1)
    # Panel seam
    a = _rp(x, y, 0, -4, angle)
    b = _rp(x, y, 0, 8, angle)
    pygame.draw.line(surf, FOIL_DARK, a, b, 1)

    # Engine bell
    bell = [(-4, 8), (4, 8), (3, 12), (-3, 12)]
    pygame.draw.polygon(surf, ASCENT_SHADE, [_rp(x, y, *p, angle) for p in bell])

    # Four landing legs
    for lx, ly, fx, fy in (
        (-11, 2, -16, 16),
        (11, 2, 16, 16),
        (-7, 4, -10, 16),
        (7, 4, 10, 16),
    ):
        p0 = _rp(x, y, lx, ly, angle)
        p1 = _rp(x, y, fx, fy, angle)
        pygame.draw.line(surf, LEG, p0, p1, 2)
        pygame.draw.circle(surf, FOOTPAD, (int(p1[0]), int(p1[1])), 3)

    if thrusting:
        _draw_flame(surf, x, y, angle, flame_phase, length=18)


def _draw_ascent_stage(
    surf: pygame.Surface,
    x: float,
    y: float,
    angle: float,
    *,
    thrusting: bool,
    flame_phase: float = 0.0,
) -> None:
    # Boxy crew cabin / ascent stage
    cabin = [(-8, -14), (8, -14), (9, -2), (5, 2), (-5, 2), (-9, -2)]
    pts = [_rp(x, y, px, py, angle) for px, py in cabin]
    pygame.draw.polygon(surf, ASCENT, pts)
    pygame.draw.polygon(surf, ASCENT_SHADE, pts, width=1)

    # Forward window
    w0 = _rp(x, y, -3, -10, angle)
    w1 = _rp(x, y, 3, -10, angle)
    w2 = _rp(x, y, 3, -5, angle)
    w3 = _rp(x, y, -3, -5, angle)
    pygame.draw.polygon(surf, WINDOW, [w0, w1, w2, w3])
    pygame.draw.line(surf, WINDOW_GLOW, w0, w1, 1)

    # RCS quads
    for sx, sy in ((-9, -8), (9, -8), (-9, -4), (9, -4)):
        p = _rp(x, y, sx, sy, angle)
        pygame.draw.circle(surf, ASCENT_SHADE, (int(p[0]), int(p[1])), 2)

    # Antenna / docking target
    tip = _rp(x, y, 0, -18, angle)
    base = _rp(x, y, 0, -14, angle)
    pygame.draw.line(surf, LEG, base, tip, 1)
    pygame.draw.circle(surf, OK, (int(tip[0]), int(tip[1])), 2)

    # Hatch outline
    hx = _rp(x, y, 0, -1, angle)
    pygame.draw.circle(surf, ASCENT_SHADE, (int(hx[0]), int(hx[1])), 3, 1)

    if thrusting:
        _draw_flame(surf, x, y + 2, angle, flame_phase, length=22)


def _draw_flame(
    surf: pygame.Surface,
    x: float,
    y: float,
    angle: float,
    phase: float,
    *,
    length: int,
) -> None:
    flicker = 1.0 + 0.15 * math.sin(phase * 28.0)
    L = length * flicker
    outer = [
        _rp(x, y, -5, 10, angle),
        _rp(x, y, 5, 10, angle),
        _rp(x, y, 0, 10 + L, angle),
    ]
    mid = [
        _rp(x, y, -3, 10, angle),
        _rp(x, y, 3, 10, angle),
        _rp(x, y, 0, 10 + L * 0.75, angle),
    ]
    core = [
        _rp(x, y, -1.5, 10, angle),
        _rp(x, y, 1.5, 10, angle),
        _rp(x, y, 0, 10 + L * 0.45, angle),
    ]
    pygame.draw.polygon(surf, FLAME_OUTER, outer)
    pygame.draw.polygon(surf, FLAME, mid)
    pygame.draw.polygon(surf, FLAME_CORE, core)


def _draw_crash(surf: pygame.Surface, x: float, y: float) -> None:
    for dx, dy, r in (
        (-12, -4, 4),
        (10, -6, 3),
        (-4, 8, 5),
        (8, 6, 4),
        (0, -10, 3),
        (-16, 4, 2),
        (14, 2, 2),
    ):
        pygame.draw.circle(surf, CRASH, (int(x + dx), int(y + dy)), r)
    pygame.draw.circle(surf, FOIL_DARK, (int(x), int(y)), 6)


def _rp(cx: float, cy: float, lx: float, ly: float, angle: float) -> tuple[float, float]:
    rad = math.radians(angle)
    cos_a, sin_a = math.cos(rad), math.sin(rad)
    rx = lx * cos_a - ly * sin_a
    ry = lx * sin_a + ly * cos_a
    return cx + rx, cy + ry


def _lerp_color(
    a: tuple[int, int, int], b: tuple[int, int, int], t: float
) -> tuple[int, int, int]:
    t = max(0.0, min(1.0, t))
    return (
        int(a[0] + (b[0] - a[0]) * t),
        int(a[1] + (b[1] - a[1]) * t),
        int(a[2] + (b[2] - a[2]) * t),
    )
