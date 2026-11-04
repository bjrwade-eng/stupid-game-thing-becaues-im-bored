"""Lunar terrain, craters, rocks, and landing pad."""

from __future__ import annotations

import math
import random
from dataclasses import dataclass


@dataclass
class Crater:
    x: float
    y: float
    radius: float


@dataclass
class Rock:
    x: float
    y: float
    size: int


@dataclass
class DistantRidge:
    """Parallax mountain silhouette points (x, y) across the sky."""

    points: list[tuple[int, int]]
    color: tuple[int, int, int]


class World:
    """Procedural height map with detail props and background ridges."""

    def __init__(self, width: int, height: int, seed: int | None = None) -> None:
        self.width = width
        self.height = height
        self.rng = random.Random(seed)
        self.heights: list[int] = [0] * width
        self.pad_left = 0
        self.pad_right = 0
        self.pad_y = 0
        self.craters: list[Crater] = []
        self.rocks: list[Rock] = []
        self.ridges: list[DistantRidge] = []
        self.stars: list[tuple[int, int, int, int]] = []  # x, y, size, brightness
        self._generate()

    def _generate(self) -> None:
        base = int(self.height * 0.68)
        amp = int(self.height * 0.16)
        pad_w = max(70, self.width // 7)
        self.pad_left = self.rng.randint(self.width // 5, self.width - self.width // 5 - pad_w)
        self.pad_right = self.pad_left + pad_w
        self.pad_y = base - amp // 4

        phase1 = self.rng.random() * math.tau
        phase2 = self.rng.random() * math.tau
        phase3 = self.rng.random() * math.tau
        for x in range(self.width):
            if self.pad_left <= x < self.pad_right:
                self.heights[x] = self.pad_y
                continue
            n = (
                math.sin(x * 0.012 + phase1) * amp
                + math.sin(x * 0.035 + phase2) * (amp * 0.45)
                + math.sin(x * 0.09 + phase3) * (amp * 0.18)
                + self.rng.randint(-3, 3)
            )
            h = int(base + n)
            self.heights[x] = max(int(self.height * 0.45), min(self.height - 24, h))

        blend = 18
        for i in range(blend):
            t = (i + 1) / (blend + 1)
            left = self.pad_left - blend + i
            right = self.pad_right + i
            if 0 <= left < self.width:
                self.heights[left] = int(self.heights[left] * (1 - t) + self.pad_y * t)
            if 0 <= right < self.width:
                self.heights[right] = int(self.heights[right] * (1 - t) + self.pad_y * t)

        self._generate_stars()
        self._generate_ridges()
        self._generate_craters_and_rocks()

    def _generate_stars(self) -> None:
        self.stars.clear()
        for _ in range(180):
            x = self.rng.randint(0, self.width - 1)
            y = self.rng.randint(0, int(self.height * 0.62))
            size = 1 if self.rng.random() < 0.82 else 2
            bright = self.rng.randint(140, 255)
            self.stars.append((x, y, size, bright))

    def _generate_ridges(self) -> None:
        self.ridges.clear()
        # Far ridge (darker, higher)
        self.ridges.append(self._make_ridge(0.42, 28, (42, 42, 52)))
        # Mid ridge
        self.ridges.append(self._make_ridge(0.50, 40, (58, 58, 68)))

    def _make_ridge(self, base_frac: float, amp: int, color: tuple[int, int, int]) -> DistantRidge:
        base = int(self.height * base_frac)
        phase = self.rng.random() * math.tau
        step = 8
        pts: list[tuple[int, int]] = [(0, self.height)]
        for x in range(0, self.width + 1, step):
            y = int(
                base
                + math.sin(x * 0.018 + phase) * amp
                + math.sin(x * 0.05 + phase * 1.7) * (amp * 0.35)
            )
            pts.append((x, y))
        pts.append((self.width, self.height))
        return DistantRidge(points=pts, color=color)

    def _generate_craters_and_rocks(self) -> None:
        self.craters.clear()
        self.rocks.clear()
        attempts = 28
        for _ in range(attempts):
            x = self.rng.randint(20, self.width - 20)
            if self.pad_left - 30 <= x <= self.pad_right + 30:
                continue
            gy = self.ground_height_at(x)
            r = self.rng.uniform(8, 28)
            self.craters.append(Crater(x=float(x), y=gy + r * 0.15, radius=r))

        for _ in range(55):
            x = self.rng.randint(4, self.width - 4)
            if self.pad_left - 8 <= x <= self.pad_right + 8:
                continue
            gy = self.ground_height_at(x)
            size = self.rng.randint(2, 6)
            self.rocks.append(Rock(x=float(x), y=gy - size * 0.3, size=size))

    def ground_height_at(self, x: float) -> float:
        ix = int(round(x))
        if ix < 0:
            return float(self.heights[0])
        if ix >= self.width:
            return float(self.heights[-1])
        return float(self.heights[ix])

    def is_on_pad(self, x: float) -> bool:
        margin = 10
        return self.pad_left + margin <= x <= self.pad_right - margin

    def altitude(self, feet_y: float, x: float) -> float:
        return max(0.0, self.ground_height_at(x) - feet_y)
