"""Pygame port of the original HTML/CSS/JavaScript Neon Tetris game."""

import random
import sys
from typing import List, Optional, Tuple

import pygame


WINDOW_WIDTH = 760
WINDOW_HEIGHT = 720
BOARD_COLUMNS = 10
BOARD_ROWS = 20
CELL_SIZE = 30
BOARD_WIDTH = BOARD_COLUMNS * CELL_SIZE
BOARD_HEIGHT = BOARD_ROWS * CELL_SIZE
BOARD_X = 48
BOARD_Y = 88
PANEL_X = BOARD_X + BOARD_WIDTH + 52

BACKGROUND = (12, 14, 16)
BOARD_BACKGROUND = (18, 20, 22)
PANEL_BACKGROUND = (22, 25, 29)
INK = (245, 241, 232)
MUTED = (145, 141, 134)
ORANGE = (255, 123, 56)
YELLOW = (255, 209, 102)
GRID = (33, 36, 38)
LINE = (52, 56, 58)
COLORS = [(0, 0, 0), (255, 95, 86), (255, 189, 46), (39, 201, 63),
          (90, 176, 255), (199, 125, 255), (255, 138, 61), (86, 224, 193)]

PIECES = (
    ((1, 1, 1, 1),),
    ((2, 2), (2, 2)),
    ((0, 3, 0), (3, 3, 3)),
    ((4, 0, 0), (4, 4, 4)),
    ((0, 0, 5), (5, 5, 5)),
    ((6, 6, 0), (0, 6, 6)),
    ((0, 7, 7), (7, 7, 0)),
)


class Piece:
    def __init__(self, shape: Tuple[Tuple[int, ...], ...]) -> None:
        self.shape = [list(row) for row in shape]
        self.x = BOARD_COLUMNS // 2 - len(self.shape[0]) // 2
        self.y = 0


class TetrisGame:
    def __init__(self) -> None:
        self.board: List[List[int]] = self.new_board()
        self.current: Optional[Piece] = None
        self.next_piece: Optional[Piece] = None
        self.score = 0
        self.lines = 0
        self.level = 1
        self.state = "ready"
        self.drop_event = pygame.USEREVENT + 1
        self.start_game()
        self.state = "ready"

    @staticmethod
    def new_board() -> List[List[int]]:
        return [[0 for _ in range(BOARD_COLUMNS)] for _ in range(BOARD_ROWS)]

    @staticmethod
    def random_piece() -> Piece:
        return Piece(random.choice(PIECES))

    def start_game(self) -> None:
        self.board = self.new_board()
        self.current = self.random_piece()
        self.next_piece = self.random_piece()
        self.score = 0
        self.lines = 0
        self.level = 1
        self.state = "playing"
        self.update_drop_speed()

    def update_drop_speed(self) -> None:
        interval = max(100, 800 - (self.level - 1) * 65)
        pygame.time.set_timer(self.drop_event, interval)

    def collides(self, piece: Piece, dx: int = 0, dy: int = 0,
                 shape: Optional[List[List[int]]] = None) -> bool:
        shape = shape or piece.shape
        for y, row in enumerate(shape):
            for x, value in enumerate(row):
                if not value:
                    continue
                board_x = piece.x + x + dx
                board_y = piece.y + y + dy
                if board_x < 0 or board_x >= BOARD_COLUMNS or board_y >= BOARD_ROWS:
                    return True
                if board_y >= 0 and self.board[board_y][board_x]:
                    return True
        return False

    @staticmethod
    def rotated(shape: List[List[int]]) -> List[List[int]]:
        return [list(row) for row in zip(*shape[::-1])]

    def move(self, dx: int) -> None:
        if self.state == "playing" and self.current and not self.collides(self.current, dx):
            self.current.x += dx

    def rotate(self) -> None:
        if self.state != "playing" or not self.current:
            return
        rotated = self.rotated(self.current.shape)
        if not self.collides(self.current, shape=rotated):
            self.current.shape = rotated

    def drop(self) -> None:
        if self.state != "playing" or not self.current:
            return
        if not self.collides(self.current, dy=1):
            self.current.y += 1
        else:
            self.lock_piece()

    def hard_drop(self) -> None:
        if self.state != "playing" or not self.current:
            return
        while not self.collides(self.current, dy=1):
            self.current.y += 1
            self.score += 2
        self.lock_piece()

    def lock_piece(self) -> None:
        if not self.current:
            return
        for y, row in enumerate(self.current.shape):
            for x, value in enumerate(row):
                if value and self.current.y + y >= 0:
                    self.board[self.current.y + y][self.current.x + x] = value
        self.clear_lines()
        self.current = self.next_piece
        self.next_piece = self.random_piece()
        if self.current and self.collides(self.current):
            self.state = "over"
            pygame.time.set_timer(self.drop_event, 0)

    def clear_lines(self) -> None:
        complete = [row for row in self.board if all(row)]
        if not complete:
            return
        self.board = [row for row in self.board if not all(row)]
        self.board = [[0] * BOARD_COLUMNS for _ in range(len(complete))] + self.board
        cleared = len(complete)
        self.score += (0, 100, 300, 500, 800)[cleared] * self.level
        self.lines += cleared
        self.level = self.lines // 10 + 1
        self.update_drop_speed()

    def toggle_pause(self) -> None:
        if self.state == "playing":
            self.state = "paused"
            pygame.time.set_timer(self.drop_event, 0)
        elif self.state == "paused":
            self.state = "playing"
            self.update_drop_speed()


def make_fonts() -> Tuple[pygame.font.Font, pygame.font.Font, pygame.font.Font]:
    return (
        pygame.font.SysFont("arial", 58, bold=True),
        pygame.font.SysFont("consolas", 16, bold=True),
        pygame.font.SysFont("consolas", 12),
    )


def draw_text(surface: pygame.Surface, text: str, position: Tuple[int, int],
              font: pygame.font.Font, color: Tuple[int, int, int]) -> None:
    surface.blit(font.render(text, True, color), position)


def draw_cell(surface: pygame.Surface, x: int, y: int, color_index: int) -> None:
    rect = pygame.Rect(BOARD_X + x * CELL_SIZE + 1, BOARD_Y + y * CELL_SIZE + 1,
                       CELL_SIZE - 2, CELL_SIZE - 2)
    pygame.draw.rect(surface, COLORS[color_index], rect)
    pygame.draw.rect(surface, tuple(min(255, channel + 55) for channel in COLORS[color_index]),
                     (rect.x + 2, rect.y + 2, rect.width - 8, 3))
    pygame.draw.rect(surface, tuple(max(0, channel - 35) for channel in COLORS[color_index]),
                     (rect.x + 2, rect.bottom - 5, rect.width - 4, 3))


def draw_board(surface: pygame.Surface, game: TetrisGame) -> None:
    board_rect = pygame.Rect(BOARD_X, BOARD_Y, BOARD_WIDTH, BOARD_HEIGHT)
    pygame.draw.rect(surface, BOARD_BACKGROUND, board_rect)
    for x in range(BOARD_COLUMNS + 1):
        pygame.draw.line(surface, GRID, (BOARD_X + x * CELL_SIZE, BOARD_Y),
                         (BOARD_X + x * CELL_SIZE, BOARD_Y + BOARD_HEIGHT))
    for y in range(BOARD_ROWS + 1):
        pygame.draw.line(surface, GRID, (BOARD_X, BOARD_Y + y * CELL_SIZE),
                         (BOARD_X + BOARD_WIDTH, BOARD_Y + y * CELL_SIZE))
    for y, row in enumerate(game.board):
        for x, value in enumerate(row):
            if value:
                draw_cell(surface, x, y, value)
    if game.current:
        for y, row in enumerate(game.current.shape):
            for x, value in enumerate(row):
                if value:
                    draw_cell(surface, game.current.x + x, game.current.y + y, value)
    pygame.draw.rect(surface, LINE, board_rect, 2)


def draw_panel(surface: pygame.Surface, game: TetrisGame, fonts: Tuple[pygame.font.Font, ...]) -> None:
    _, stat_font, small_font = fonts
    draw_text(surface, "NEON", (BOARD_X, 25), fonts[0], INK)
    draw_text(surface, "TETRIS", (BOARD_X + 155, 25), fonts[0], ORANGE)
    status_color = YELLOW if game.state != "over" else ORANGE
    pygame.draw.circle(surface, status_color, (PANEL_X + 8, 43), 4)
    draw_text(surface, game.state.upper(), (PANEL_X + 20, 36), small_font, MUTED)

    stats = (("SCORE", f"{game.score:06d}"), ("LEVEL", f"{game.level:02d}"),
             ("LINES", f"{game.lines:03d}"))
    for index, (label, value) in enumerate(stats):
        x = PANEL_X + index * 102
        draw_text(surface, label, (x, 115), small_font, MUTED)
        draw_text(surface, value, (x, 137), stat_font, INK)
    pygame.draw.line(surface, LINE, (PANEL_X, 106), (WINDOW_WIDTH - 48, 106))
    pygame.draw.line(surface, LINE, (PANEL_X, 169), (WINDOW_WIDTH - 48, 169))

    draw_text(surface, "NEXT BLOCK", (PANEL_X, 198), small_font, MUTED)
    pygame.draw.rect(surface, PANEL_BACKGROUND, (PANEL_X, 220, 220, 110))
    if game.next_piece:
        size = 25
        shape = game.next_piece.shape
        start_x = PANEL_X + (220 - len(shape[0]) * size) // 2
        start_y = 220 + (110 - len(shape) * size) // 2
        for y, row in enumerate(shape):
            for x, value in enumerate(row):
                if value:
                    pygame.draw.rect(surface, COLORS[value],
                                     (start_x + x * size + 1, start_y + y * size + 1, size - 2, size - 2))

    draw_text(surface, "CONTROLS", (PANEL_X, 372), small_font, MUTED)
    controls = (("ARROWS", "MOVE"), ("UP", "ROTATE"), ("SPACE", "HARD DROP"), ("P", "PAUSE"))
    for index, (key, action) in enumerate(controls):
        y = 405 + index * 31
        pygame.draw.rect(surface, PANEL_BACKGROUND, (PANEL_X, y - 3, 82, 23))
        draw_text(surface, key, (PANEL_X + 8, y), small_font, INK)
        draw_text(surface, action, (PANEL_X + 98, y), small_font, MUTED)

    pygame.draw.rect(surface, PANEL_BACKGROUND, (PANEL_X, 555, 220, 42))
    pygame.draw.rect(surface, LINE, (PANEL_X, 555, 220, 42), 1)
    draw_text(surface, "Ⅱ  PAUSE (P)", (PANEL_X + 58, 568), small_font, INK)
    draw_text(surface, "Clear lines. Chase the high score.", (PANEL_X, 625), small_font, MUTED)


def draw_overlay(surface: pygame.Surface, game: TetrisGame, fonts: Tuple[pygame.font.Font, ...]) -> None:
    if game.state == "playing":
        return
    title_font, _, small_font = fonts
    overlay = pygame.Surface((BOARD_WIDTH, BOARD_HEIGHT), pygame.SRCALPHA)
    overlay.fill((12, 14, 16, 225))
    surface.blit(overlay, (BOARD_X, BOARD_Y))
    title = "READY?" if game.state == "ready" else "PAUSED" if game.state == "paused" else "GAME OVER"
    message = "Press ENTER to start" if game.state == "ready" else "Press P to resume" if game.state == "paused" else f"FINAL SCORE {game.score:06d}"
    title_surface = title_font.render(title, True, YELLOW)
    message_surface = small_font.render(message, True, MUTED)
    surface.blit(title_surface, (BOARD_X + (BOARD_WIDTH - title_surface.get_width()) // 2, BOARD_Y + 230))
    surface.blit(message_surface, (BOARD_X + (BOARD_WIDTH - message_surface.get_width()) // 2, BOARD_Y + 305))


def main() -> None:
    pygame.init()
    pygame.display.set_caption("NEON TETRIS - DemoSnake.py")
    screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
    clock = pygame.time.Clock()
    fonts = make_fonts()
    game = TetrisGame()
    running = True

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == game.drop_event:
                game.drop()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN and game.state in ("ready", "over"):
                    game.start_game()
                elif event.key == pygame.K_LEFT:
                    game.move(-1)
                elif event.key == pygame.K_RIGHT:
                    game.move(1)
                elif event.key == pygame.K_DOWN:
                    game.drop()
                elif event.key == pygame.K_UP:
                    game.rotate()
                elif event.key == pygame.K_SPACE:
                    game.hard_drop()
                elif event.key == pygame.K_p:
                    game.toggle_pause()

        screen.fill(BACKGROUND)
        draw_board(screen, game)
        draw_panel(screen, game, fonts)
        draw_overlay(screen, game, fonts)
        draw_text(screen, "PYTHON / PYGAME  •  BUILD YOUR RUN", (BOARD_X, 680), fonts[2], MUTED)
        pygame.display.flip()
        clock.tick(60)

    pygame.time.set_timer(game.drop_event, 0)
    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()