"""Title / playing / landed / crashed game states."""

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
    CRASHED = auto()


class Game:
    """Owns world/lander and current screen state."""

    INTERNAL_W = 320
    INTERNAL_H = 240

    def __init__(self) -> None:
        self.state = State.TITLE
        self.world = World(self.INTERNAL_W, self.INTERNAL_H)
        self.lander = Lander(self.INTERNAL_W * 0.2, 30)
        self.font: pygame.font.Font | None = None
        self.big_font: pygame.font.Font | None = None

    def ensure_fonts(self) -> None:
        if self.font is None:
            self.font = pygame.font.SysFont("consolas", 8)
        if self.big_font is None:
            self.big_font = pygame.font.SysFont("consolas", 14, bold=True)

    def start_run(self) -> None:
        self.world = World(self.INTERNAL_W, self.INTERNAL_H)
        self.lander = Lander(self.INTERNAL_W * 0.18, 28)
        self.state = State.PLAYING

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
            elif self.state in (State.LANDED, State.CRASHED) and event.key == pygame.K_r:
                self.start_run()
            elif self.state in (State.LANDED, State.CRASHED) and event.key == pygame.K_RETURN:
                self.state = State.TITLE
        return True

    def update(self, dt: float) -> None:
        if self.state != State.PLAYING:
            return

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
        elif result == "crashed":
            self.state = State.CRASHED

    def draw(self, canvas: pygame.Surface) -> None:
        self.ensure_fonts()
        assert self.font is not None and self.big_font is not None

        render.draw_world(canvas, self.world)

        if self.state == State.TITLE:
            render.draw_centered_text(
                canvas,
                self.big_font,
                [
                    ("APOLLO LANDER", render.TITLE),
                    ("PIXEL EDITION", render.HUD),
                ],
                y_start=70,
            )
            render.draw_centered_text(
                canvas,
                self.font,
                [
                    ("A/D or ARROWS  rotate", render.HUD_DIM),
                    ("W or UP  thrust", render.HUD_DIM),
                    ("ENTER / SPACE  start", render.HUD),
                    ("ESC  quit", render.HUD_DIM),
                ],
                y_start=120,
            )
            return

        render.draw_lander(canvas, self.lander)
        render.draw_hud(canvas, self.font, self.lander, self.world)

        if self.state == State.LANDED:
            render.draw_centered_text(
                canvas,
                self.big_font,
                [("THE EAGLE HAS LANDED", render.OK)],
                y_start=90,
            )
            render.draw_centered_text(
                canvas,
                self.font,
                [("R  try again   ENTER  title", render.HUD)],
                y_start=120,
            )
        elif self.state == State.CRASHED:
            render.draw_centered_text(
                canvas,
                self.big_font,
                [("CONTACT LIGHT... OOF", render.CRASH)],
                y_start=90,
            )
            render.draw_centered_text(
                canvas,
                self.font,
                [("R  retry   ENTER  title", render.HUD)],
                y_start=120,
            )
