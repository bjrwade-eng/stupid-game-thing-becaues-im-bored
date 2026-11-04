"""Title / playing / landed / ascent / crashed game states."""

from __future__ import annotations

from enum import Enum, auto

import pygame

from .lander import Lander
from .physics import update_physics
from . import render
from .world import World


class State(Enum):
    TITLE = auto()
    PLAYING = auto()
    LANDED = auto()
    ASCENT = auto()
    CRASHED = auto()


class Game:
    """Owns world/lander and current screen state."""

    INTERNAL_W = 960
    INTERNAL_H = 540

    def __init__(self) -> None:
        self.state = State.TITLE
        self.world = World(self.INTERNAL_W, self.INTERNAL_H)
        self.lander = Lander(self.INTERNAL_W * 0.2, 50)
        self.font: pygame.font.Font | None = None
        self.big_font: pygame.font.Font | None = None
        self.time = 0.0
        self.landed_timer = 0.0
        self.ascent_done = False

    def ensure_fonts(self) -> None:
        if self.font is None:
            self.font = pygame.font.SysFont("consolas", 18)
        if self.big_font is None:
            self.big_font = pygame.font.SysFont("consolas", 32, bold=True)

    def start_run(self) -> None:
        self.world = World(self.INTERNAL_W, self.INTERNAL_H)
        self.lander = Lander(self.INTERNAL_W * 0.16, 48)
        self.state = State.PLAYING
        self.landed_timer = 0.0
        self.ascent_done = False

    def handle_event(self, event: pygame.event.Event) -> bool:
        """Return False to quit the app."""
        if event.type == pygame.QUIT:
            return False
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                return False
            if self.state == State.TITLE and event.key in (
                pygame.K_RETURN,
                pygame.K_SPACE,
            ):
                self.start_run()
            elif self.state in (State.ASCENT, State.CRASHED, State.LANDED) and event.key == pygame.K_r:
                self.start_run()
            elif self.state in (State.ASCENT, State.CRASHED) and event.key == pygame.K_RETURN:
                self.state = State.TITLE
        return True

    def update(self, dt: float) -> None:
        self.time += dt

        if self.state == State.PLAYING:
            keys = pygame.key.get_pressed()
            rotate = 0.0
            if keys[pygame.K_a] or keys[pygame.K_LEFT]:
                rotate -= 1.0
            if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
                rotate += 1.0
            thrust = keys[pygame.K_w] or keys[pygame.K_UP]

            self.lander.update_controls(rotate, thrust, dt)
            result = update_physics(self.lander, self.world, dt)
            if result == "landed":
                self.state = State.LANDED
                self.landed_timer = 0.0
            elif result == "crashed":
                self.state = State.CRASHED
            return

        if self.state == State.LANDED:
            self.landed_timer += dt
            # Brief celebration, then ascent stage liftoff
            if self.landed_timer >= 1.6:
                self.lander.begin_ascent()
                self.state = State.ASCENT
            return

        if self.state == State.ASCENT:
            if self.lander.update_ascent(dt):
                self.ascent_done = True

    def draw(self, canvas: pygame.Surface) -> None:
        self.ensure_fonts()
        assert self.font is not None and self.big_font is not None

        render.draw_world(canvas, self.world)

        if self.state == State.TITLE:
            render.draw_centered_text(
                canvas,
                self.big_font,
                [
                    ("APOLLO LUNAR MODULE", render.TITLE),
                    ("LANDING SIM", render.HUD),
                ],
                y_start=150,
            )
            render.draw_centered_text(
                canvas,
                self.font,
                [
                    ("A/D or ARROWS  rotate", render.HUD_DIM),
                    ("W or UP  descent engine", render.HUD_DIM),
                    ("Land gently on the lit pad", render.HUD_DIM),
                    ("ENTER / SPACE  start", render.HUD),
                    ("ESC  quit", render.HUD_DIM),
                ],
                y_start=260,
            )
            # Preview LEM on title
            render.draw_lander(
                canvas,
                _preview_lander(self.INTERNAL_W * 0.5, self.INTERNAL_H * 0.78),
                self.time,
            )
            return

        render.draw_lander(canvas, self.lander, self.time)

        if self.state == State.PLAYING:
            render.draw_hud(canvas, self.font, self.lander, self.world)

        if self.state == State.LANDED:
            render.draw_hud(canvas, self.font, self.lander, self.world)
            render.draw_centered_text(
                canvas,
                self.big_font,
                [("THE EAGLE HAS LANDED", render.OK)],
                y_start=120,
            )
            render.draw_centered_text(
                canvas,
                self.font,
                [("Preparing ascent stage...", render.HUD)],
                y_start=180,
            )
        elif self.state == State.ASCENT:
            if self.ascent_done:
                render.draw_centered_text(
                    canvas,
                    self.big_font,
                    [("ASCENT STAGE AWAY", render.OK)],
                    y_start=140,
                )
                render.draw_centered_text(
                    canvas,
                    self.font,
                    [
                        ("Houston, we are go for rendezvous.", render.TITLE),
                        ("R  try again    ENTER  title", render.HUD),
                    ],
                    y_start=200,
                )
            else:
                render.draw_centered_text(
                    canvas,
                    self.font,
                    [("ASCENT ENGINE IGNITION", render.HUD)],
                    y_start=40,
                )
        elif self.state == State.CRASHED:
            render.draw_centered_text(
                canvas,
                self.big_font,
                [("CONTACT LIGHT... OOF", render.CRASH)],
                y_start=160,
            )
            render.draw_centered_text(
                canvas,
                self.font,
                [("R  retry    ENTER  title", render.HUD)],
                y_start=220,
            )


def _preview_lander(x: float, y: float) -> Lander:
    lem = Lander(x, y)
    lem.vx = 0
    lem.vy = 0
    lem.angle = 0
    lem.thrusting = True
    return lem
