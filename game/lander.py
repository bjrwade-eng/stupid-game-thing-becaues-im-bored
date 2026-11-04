"""Lander body: position, velocity, attitude, fuel, and thruster state."""

from __future__ import annotations

import math


class Lander:
    """Apollo LM–flavored lander for arcade physics (HD scale)."""

    WIDTH = 28
    HEIGHT = 36
    MAX_FUEL = 100.0
    ROTATE_SPEED = 80.0  # degrees per second
    THRUST = 95.0  # px/s^2
    FUEL_BURN = 10.0  # fuel units per second while thrusting

    def __init__(self, x: float, y: float) -> None:
        self.x = x
        self.y = y
        self.vx = 32.0
        self.vy = 0.0
        self.angle = 0.0  # 0 = upright (nose up), degrees; positive = clockwise
        self.fuel = self.MAX_FUEL
        self.thrusting = False
        self.alive = True
        self.landed = False
        # After soft landing: ascent stage separates
        self.separated = False
        self.ascent_x = x
        self.ascent_y = y
        self.ascent_vy = 0.0
        self.descent_x = x
        self.descent_y = y

    def reset(self, x: float, y: float) -> None:
        self.__init__(x, y)

    def update_controls(self, rotate_dir: float, thrust: bool, dt: float) -> None:
        if not self.alive or self.landed or self.separated:
            self.thrusting = False
            return

        self.angle = (self.angle + rotate_dir * self.ROTATE_SPEED * dt) % 360.0
        self.thrusting = bool(thrust and self.fuel > 0.0)
        if self.thrusting:
            self.fuel = max(0.0, self.fuel - self.FUEL_BURN * dt)

    def apply_thrust(self, dt: float) -> None:
        if not self.thrusting:
            return
        # Angle 0 = up; convert to math angle (0 = right, CCW)
        rad = math.radians(self.angle - 90.0)
        self.vx += math.cos(rad) * self.THRUST * dt
        self.vy += math.sin(rad) * self.THRUST * dt

    def integrate(self, gravity: float, dt: float) -> None:
        if self.landed or self.separated:
            self.vx = 0.0
            self.vy = 0.0
            return
        if not self.alive:
            return
        self.vy += gravity * dt
        self.x += self.vx * dt
        self.y += self.vy * dt

    def begin_ascent(self) -> None:
        """Leave descent stage on the pad; launch ascent stage."""
        self.separated = True
        self.descent_x = self.x
        self.descent_y = self.y
        self.ascent_x = self.x
        self.ascent_y = self.y - 6.0
        self.ascent_vy = -40.0
        self.thrusting = False

    def update_ascent(self, dt: float) -> bool:
        """
        Animate ascent stage rising.
        Returns True once it has left the top of the screen.
        """
        if not self.separated:
            return False
        # Accelerate upward (celebration burn — ignore lunar gravity)
        self.ascent_vy -= 90.0 * dt
        self.ascent_y += self.ascent_vy * dt
        return self.ascent_y < -60.0

    @property
    def feet_y(self) -> float:
        return self.y + self.HEIGHT / 2

    @property
    def center(self) -> tuple[float, float]:
        return self.x, self.y

    def nose_tip(self) -> tuple[float, float]:
        rad = math.radians(self.angle - 90.0)
        length = self.HEIGHT / 2
        return self.x + math.cos(rad) * length, self.y + math.sin(rad) * length
