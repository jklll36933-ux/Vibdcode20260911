"""A small Snake game built with pygame."""

import random
import sys
from typing import List, Tuple

import pygame


WINDOW_WIDTH = 640
WINDOW_HEIGHT = 640
CELL_SIZE = 32
GRID_COLUMNS = WINDOW_WIDTH // CELL_SIZE
GRID_ROWS = WINDOW_HEIGHT // CELL_SIZE
FPS = 12

BACKGROUND = (16, 21, 26)
GRID_COLOR = (27, 35, 40)
SNAKE_HEAD = (112, 221, 141)
SNAKE_BODY = (55, 174, 101)
FOOD_COLOR = (242, 93, 93)
TEXT_COLOR = (238, 242, 239)
MUTED_TEXT = (157, 172, 165)

Point = Tuple[int, int]


def random_food(snake: List[Point]) -> Point:
    """Return an unoccupied grid position for the food."""
    available = [
        (x, y)
        for y in range(GRID_ROWS)
        for x in range(GRID_COLUMNS)
        if (x, y) not in snake
    ]
    return random.choice(available)


def draw_centered_text(
    surface: pygame.Surface, text: str, font: pygame.font.Font, color: Tuple[int, int, int],
    y: int,
) -> None:
    rendered = font.render(text, True, color)
    surface.blit(rendered, rendered.get_rect(center=(WINDOW_WIDTH // 2, y)))


def draw_game(
    screen: pygame.Surface,
    snake: List[Point],
    food: Point,
    score: int,
    state: str,
    title_font: pygame.font.Font,
    body_font: pygame.font.Font,
) -> None:
    screen.fill(BACKGROUND)

    for x in range(0, WINDOW_WIDTH, CELL_SIZE):
        pygame.draw.line(screen, GRID_COLOR, (x, 0), (x, WINDOW_HEIGHT))
    for y in range(0, WINDOW_HEIGHT, CELL_SIZE):
        pygame.draw.line(screen, GRID_COLOR, (0, y), (WINDOW_WIDTH, y))

    food_rect = pygame.Rect(
        food[0] * CELL_SIZE + 5, food[1] * CELL_SIZE + 5, CELL_SIZE - 10, CELL_SIZE - 10
    )
    pygame.draw.ellipse(screen, FOOD_COLOR, food_rect)

    for index, (x, y) in enumerate(snake):
        rect = pygame.Rect(x * CELL_SIZE + 2, y * CELL_SIZE + 2, CELL_SIZE - 4, CELL_SIZE - 4)
        pygame.draw.rect(screen, SNAKE_HEAD if index == 0 else SNAKE_BODY, rect, border_radius=7)

    score_text = body_font.render(f"SCORE  {score:04d}", True, TEXT_COLOR)
    screen.blit(score_text, (16, 14))

    if state != "playing":
        overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
        overlay.fill((5, 9, 12, 205))
        screen.blit(overlay, (0, 0))
        message = "GAME OVER" if state == "game_over" else "PAUSED"
        draw_centered_text(screen, message, title_font, TEXT_COLOR, WINDOW_HEIGHT // 2 - 40)
        draw_centered_text(
            screen,
            "Press R to restart" if state == "game_over" else "Press P to continue",
            body_font,
            MUTED_TEXT,
            WINDOW_HEIGHT // 2 + 22,
        )


def new_game() -> Tuple[List[Point], Point, Point, int, str]:
    center = (GRID_COLUMNS // 2, GRID_ROWS // 2)
    snake = [center, (center[0] - 1, center[1]), (center[0] - 2, center[1])]
    return snake, random_food(snake), (1, 0), 0, "playing"


def main() -> None:
    pygame.init()
    pygame.display.set_caption("My Snake")
    screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
    clock = pygame.time.Clock()
    title_font = pygame.font.SysFont("consolas", 42, bold=True)
    body_font = pygame.font.SysFont("consolas", 20, bold=True)

    snake, food, direction, score, state = new_game()
    next_direction = direction

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    pygame.quit()
                    sys.exit()
                if event.key == pygame.K_r and state == "game_over":
                    snake, food, direction, score, state = new_game()
                    next_direction = direction
                elif event.key == pygame.K_p and state != "game_over":
                    state = "paused" if state == "playing" else "playing"
                elif state == "playing":
                    key_directions = {
                        pygame.K_UP: (0, -1),
                        pygame.K_w: (0, -1),
                        pygame.K_DOWN: (0, 1),
                        pygame.K_s: (0, 1),
                        pygame.K_LEFT: (-1, 0),
                        pygame.K_a: (-1, 0),
                        pygame.K_RIGHT: (1, 0),
                        pygame.K_d: (1, 0),
                    }
                    candidate = key_directions.get(event.key)
                    if candidate and candidate != (-direction[0], -direction[1]):
                        next_direction = candidate

        if state == "playing":
            direction = next_direction
            head_x, head_y = snake[0]
            new_head = (head_x + direction[0], head_y + direction[1])
            hits_wall = not (0 <= new_head[0] < GRID_COLUMNS and 0 <= new_head[1] < GRID_ROWS)
            grows = new_head == food
            hits_body = new_head in (snake if grows else snake[:-1])

            if hits_wall or hits_body:
                state = "game_over"
            else:
                snake.insert(0, new_head)
                if grows:
                    score += 10
                    food = random_food(snake)
                else:
                    snake.pop()

        draw_game(screen, snake, food, score, state, title_font, body_font)
        pygame.display.flip()
        clock.tick(FPS)


if __name__ == "__main__":
    main()