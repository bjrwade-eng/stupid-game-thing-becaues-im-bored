"""Apollo Lunar Lander — retro pixel Windows game entry point."""

from __future__ import annotations

import sys

import pygame

from game.states import Game

# Window is a nearest-neighbor scale of the internal pixel canvas
SCALE = 3
FPS = 60


def main() -> int:
    pygame.init()
    pygame.display.set_caption("Apollo Lunar Lander")

    game = Game()
    window_size = (game.INTERNAL_W * SCALE, game.INTERNAL_H * SCALE)
    screen = pygame.display.set_mode(window_size)
    canvas = pygame.Surface((game.INTERNAL_W, game.INTERNAL_H))
    clock = pygame.time.Clock()

    running = True
    while running:
        dt = clock.tick(FPS) / 1000.0
        # Cap huge stalls (alt-tab) so physics don't explode
        dt = min(dt, 1.0 / 20.0)

        for event in pygame.event.get():
            if not game.handle_event(event):
                running = False
                break

        game.update(dt)
        game.draw(canvas)

        pygame.transform.scale(canvas, window_size, screen)
        pygame.display.flip()

    pygame.quit()
    return 0


if __name__ == "__main__":
    sys.exit(main())
