"""Lunar terrain silhouette and landing pad."""

from __future__ import annotations

import math
import random


class World:
    """Procedural 1D height map with one flat landing pad."""

    def __init__(self, width: int, height: int, seed: int | None = None) -> None:
        self.width = width
        self.height = height
        self.rng = random.Random(seed)
        self.heights: list[int] = [0] * width
        self.pad_left = 0
        self.pad_right = 0
        self.pad_y = 0
        self._generate()

    def _generate(self) -> None:
        base = int(self.height * 0.72)
        amp = int(self.height * 0.12)
        pad_w = max(28, self.width // 8)
        self.pad_left = self.rng.randint(self.width // 5, self.width - self.width // 5 - pad_w)
        self.pad_right = self.pad_left + pad_w
        self.pad_y = base - amp // 3

        phase1 = self.rng.random() * math.tau
        phase2 = self.rng.random() * math.tau
        for x in range(self.width):
            if self.pad_left <= x < self.pad_right:
                self.heights[x] = self.pad_y
                continue
            n = (
                math.sin(x * 0.04 + phase1) * amp
                + math.sin(x * 0.11 + phase2) * (amp * 0.45)
                + self.rng.randint(-2, 2)
            )
            self.heights[x] = int(base + n)
            # Keep terrain below sky but above bottom strip
            self.heights[x] = max(self.height // 2, min(self.height - 8, self.heights[x]))

        # Blend edges into pad height so the pad isn't a cliff trap
        blend = 6
        for i in range(blend):
            t = (i + 1) / (blend + 1)
            left = self.pad_left - blend + i
            right = self.pad_right + i
            if 0 <= left < self.width:
                self.heights[left] = int(
                    self.heights[left] * (1 - t) + self.pad_y * t
                )
            if 0 <= right < self.width:
                self.heights[right] = int(
                    self.heights[right] * (1 - t) + self.pad_y * t
                )

    def ground_height_at(self, x: float) -> float:
        ix = int(round(x))
        if ix < 0:
            return float(self.heights[0])
        if ix >= self.width:
            return float(self.heights[-1])
        return float(self.heights[ix])

    def is_on_pad(self, x: float) -> bool:
        return self.pad_left + 2 <= x <= self.pad_right - 2

    def altitude(self, feet_y: float, x: float) -> float:
        return max(0.0, self.ground_height_at(x) - feet_y)
