"""Moon gravity and soft-land / crash checks."""

from __future__ import annotations

from .lander import Lander
from .world import World

# Arcade-tuned lunar gravity (px/s^2) — weaker than Earth feel
MOON_GRAVITY = 18.0

# Soft landing thresholds
MAX_LAND_SPEED_Y = 18.0
MAX_LAND_SPEED_X = 14.0
MAX_LAND_TILT = 18.0  # degrees from upright


def update_physics(lander: Lander, world: World, dt: float) -> str | None:
    """
    Advance physics one step.

    Returns:
        None while still flying,
        "landed" on soft pad touchdown,
        "crashed" on hard/bad contact or leaving the world.
    """
    if not lander.alive or lander.landed:
        return None

    lander.apply_thrust(dt)
    lander.integrate(MOON_GRAVITY, dt)

    # Wrap-ish clamp so you don't fly forever sideways
    if lander.x < -20 or lander.x > world.width + 20 or lander.y < -40:
        lander.alive = False
        return "crashed"

    ground = world.ground_height_at(lander.x)
    if lander.feet_y < ground:
        return None

    # Contact
    lander.y = ground - lander.HEIGHT / 2
    on_pad = world.is_on_pad(lander.x)
    tilt = _tilt_from_upright(lander.angle)
    soft = (
        on_pad
        and abs(lander.vy) <= MAX_LAND_SPEED_Y
        and abs(lander.vx) <= MAX_LAND_SPEED_X
        and tilt <= MAX_LAND_TILT
    )

    if soft:
        lander.landed = True
        lander.alive = True
        lander.vx = 0.0
        lander.vy = 0.0
        lander.thrusting = False
        return "landed"

    lander.alive = False
    lander.thrusting = False
    return "crashed"


def _tilt_from_upright(angle: float) -> float:
    a = angle % 360.0
    if a > 180.0:
        a -= 360.0
    return abs(a)
