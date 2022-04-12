# -*- coding: utf-8 -*-
r"""Buffon's Needle simulation with graphical user-interface.

The Buffon's Needle problem is a Monte Carlo experiment to find the value
of pi. Learn more: https://en.wikipedia.org/wiki/Buffon%27s_needle_problem

This program creates a user-defined Buffon's Needle board and allows the
user to cumulatively drop a inputted number of "needles" to see how that changes the
calculation of pi. The program renders the "needles" on the board with
hits and misses displayed in different colors.

Attributes
----------
column_space : int
    Distance between columns in pixels.
column_count : int
    Number of columns drawn.
needle_length : float
    Length of needles dropped in pixels. Must be less than or equal to
     `column_space`.
window_height : int
    Overall window height in pixels.
sidebar_width : int
    Width of information sidebar on left in pixels.
column_line_thickness : int
    Width of lines drawn separating columns in pixels.
needle_thickness : int
    Width of needles dropped in pixels.
needle_hit_location_size : float
    Radius of hit location dots in pixels.
mark_hit_locations_limit : int, optional
    Maximum number of needles that hit locations will continue to be rendered.
    Set to `None` to remove limit. Set to `0` to hide hit locations.
draw_limit : int
    Maximum number of needles that can be rendered. After this value, only
    the most recent needles, up to `draw_limit` will be rendered.
default_target_fps : float
    FPS goal when the simulation is not trying to create large numbers of
    new needles.
font : pygame.font.Font
    Universal UI display font.
background_color, needle_hit_color, needle_miss_color, needle_hit_location_color,
column_line_color, sidebar_color, display_font_color : ColorType
    Variables storing the color of different display elements.
log_file : str
    Path of logging file. Note that running this file overrides the last
    log.

Notes
-----
Pressing `Escape` will stop any current needle dropping.
Pressing `Delete` will erase current drops.

The formula used to approximate pi is:
    .. math:: \pi  \approx  \frac{2ln}{th}
Where `l` is the needle length, `n` is the number of needles dropped,
`t` is the space between columns, and `h` is the number of needles crossing
column lines.

"""

from typing import NamedTuple, Optional, NoReturn, Iterable

import random
import math
import logging

import pygame

from ui_classes import InputBox, InfoText, ColorType

column_space = 100
column_count = 8
needle_length = 75
window_height = 400

sidebar_width = 200
column_line_thickness = 3
needle_thickness = 2
needle_hit_location_size = 4

mark_hit_locations_limit = 0
draw_limit = 10_000

default_target_fps = 100

pygame.font.init()
font = pygame.font.SysFont('ebrima', 24)

background_color = pygame.Color('white')
needle_hit_color = pygame.Color('red')
needle_miss_color = pygame.Color('blue')
needle_hit_location_color = pygame.Color('green')
column_line_color = pygame.Color('black')
sidebar_color = pygame.Color('lightgray')
display_font_color = pygame.Color('black')

# Set up logging:
log_file = 'latest.log'
logging.basicConfig(format=r'%(asctime)s.%(msecs)03d [%(lineno)d] %(levelname)s: %(message)s',
                    filename=log_file,
                    datefmt='%d %b %Y %H:%M:%S',
                    level=logging.DEBUG)
open(log_file, 'w').close()
logging.debug('Logging setup complete.')

# UI elements:
fps_counter = InfoText(5, 0, font, display_font_color)
drops_counter = InfoText(5, font.get_height(), font, display_font_color)
hits_counter = InfoText(5, font.get_height() * 2, font, display_font_color)
pi_counter = InfoText(5, font.get_height() * 3, font, display_font_color)
drops_input = InputBox(5, font.get_height() * 4.1, 175, 30, empty_text='Enter drop count: ')

window_width = column_count * column_space + sidebar_width  # Get window window_width

# Correct needle length, if needed:
if needle_length > column_space:
    logging.error(
            "`needle_length` can't be greater than `column_space`. Setting `needle_length` to "
            "`column_space`.")
    needle_length = column_space

Cords = NamedTuple('Cords', (('x', float), ('y', float)))


class TheoreticalNeedle:
    """A Numerical representation of a needle of length `length` with its
    center at a random location on a board `board_width` by `board_height`.

    """

    def __init__(self, board_width: int, board_height: int, length: int, columns: Iterable[int]):
        self.column_values = columns

        self.center = Cords(random.uniform(0, board_width),
                            random.uniform(0, board_height))

        self.angle = random.uniform(0, 2 * math.pi)

        self.point1 = Cords(
                self.center.x + (length / 2 * math.cos(self.angle)),
                self.center.y + (length / 2 * math.sin(self.angle)))

        self.point2 = Cords(
                self.center.x - (length / 2 * math.cos(self.angle)),
                self.center.y - (length / 2 * math.sin(self.angle)))

    @property
    def hit(self) -> Optional[Cords]:
        """If needle is a hit (crosses an x value in `columns`) returns the hit location."""
        for column_value in self.column_values:
            if (self.point1.x <= column_value <= self.point2.x) or (
                    self.point1.x >= column_value >= self.point2.x):
                break
        else:
            return None

        # Find intercept point of needle and column:
        slope = (self.point2.y - self.point1.y) / (self.point2.x - self.point1.x)
        y_int = self.point1.y - slope * self.point1.x  # y int of needle and board origin
        y = slope * column_value + y_int

        return Cords(column_value, y)


class Needle(TheoreticalNeedle):
    """A UI representation of a needle.

    Note
    ----
    Only arguments only relating to UI display have defaults provided.

    """
    needles = []  # List of all instances.

    def __init__(self, surface: pygame.Surface,
                 board_width: int, board_height: int, board_x_offset: int,
                 length: int, column_values: Iterable[int],
                 thickness: int = needle_thickness,
                 hit_color: ColorType = needle_hit_color,
                 miss_color: ColorType = needle_miss_color,
                 hit_location_color: ColorType = needle_hit_location_color,
                 hit_location_size: int = needle_hit_location_size):

        super().__init__(board_width, board_height, length, column_values)

        self.surface = surface
        self.board_x_offset = board_x_offset
        self.thickness = thickness
        self.hit_location_color = hit_location_color
        self.hit_location_size = hit_location_size

        self.color = hit_color if self.hit else miss_color
        self.needles.append(self)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}('__dict__': {self.__dict__})"

    def draw(self, mark_hit: bool) -> None:
        """Draw needle on `surface`."""
        pygame.draw.line(self.surface,
                         self.color,
                         (self.point1.x + sidebar_width, self.point1.y),
                         (self.point2.x + sidebar_width, self.point2.y),
                         self.thickness)
        if self.hit and mark_hit:
            pygame.draw.circle(self.surface, self.hit_location_color,
                               (self.hit.x + self.board_x_offset, self.hit.y),
                               self.hit_location_size)

    @classmethod
    def draw_all(cls, limit: Optional[int] = None, mark_hits_limit: Optional[int] = None) -> None:
        """Draw all objects in `needles` up to `limit`. See `draw_limit`."""
        first_drawn_index = len(cls.needles) - limit
        mark_hits = True if mark_hits_limit is None or len(
                cls.needles) <= mark_hits_limit else False
        for i, needle in enumerate(cls.needles):
            if not limit or i >= first_drawn_index:
                needle.draw(mark_hits)


def get_rates(drops_left: int) -> tuple[int, int]:
    """Return `drops_per_frame` and `target_fps` based on `drops_left`.
    Algorithm attempts to optimize time spent dropping and maintaining accruing
    needle drops.

    """
    # Set drops per frame:
    if drops_left == 0:
        drops_per_frame = 0
    elif drops_left <= 100:
        drops_per_frame = 1
    else:
        drops_per_frame = int(drops_left / 10)

    # Set target fps:
    try:
        target_fps = int(default_target_fps ** (0.75 * drops_left - 100 / drops_left) + 9)
    except OverflowError:
        target_fps = 0
        logging.debug('`target_fps` is too large, removing fps limit.')
    except ZeroDivisionError:
        target_fps = default_target_fps

    if drops_per_frame:
        logging.debug(
                f'Set `drops_per_frame` to {drops_per_frame} and `target_fps` to {target_fps}.')

    return drops_per_frame, target_fps


def draw_columns(surface: pygame.Surface) -> None:
    """Draw lines for all columns."""
    for column_x in range(0, column_count + 1):
        x = sidebar_width + column_x * column_space
        pygame.draw.line(surface, column_line_color, (x, 0), (x, window_height),
                         column_line_thickness)


def draw_screen(surface: pygame.Surface, drops: int, hits: int, fps: float, pi: float) -> None:
    """All steps to draw screen."""
    surface.fill(background_color)

    Needle.draw_all(draw_limit, mark_hit_locations_limit)

    draw_columns(surface)

    pygame.draw.rect(surface, sidebar_color,
                     (0, 0, sidebar_width - 2, window_height))  # Draw sidebar

    fps_counter.draw(surface, f'FPS: {fps:.1f}')
    drops_counter.draw(surface, f'Drops: {drops}')
    hits_counter.draw(surface, f'Hits: {hits}')
    pi_counter.draw(surface, f'Pi: {pi:.5f}')
    drops_input.draw(surface)


def main() -> NoReturn:
    hits = 0
    drops = 0
    fps = 0
    target_drops = 0
    drops_left = 0
    target_fps = default_target_fps
    drops_per_frame = 0
    reset_rates = True

    columns_x_values = tuple(
            column_space * n for n in range(0, column_count + 1))  # Column line's x values

    # Pygame setup
    pygame.init()
    screen = pygame.display.set_mode((window_width, window_height))
    pygame.display.set_caption("Buffon's Needle")
    logging.debug('Pygame setup complete.')
    clock = pygame.time.Clock()

    logging.info('Starting window...')
    while True:
        # Handle events:
        for event in pygame.event.get():
            # Quit program:
            if event.type == pygame.QUIT:
                logging.info('Closing window...')
                pygame.quit()
                raise SystemExit
            if event.type == pygame.KEYDOWN:
                # Stop adding drops if escape is pressed:
                if event.key == pygame.K_ESCAPE:
                    if drops_left:
                        target_drops = drops
                        logging.info('Escape pressed, stopping drops.')
                        logging.debug(f'Setting `target_drops` to `drops`. ({drops})')
                # Reset if delete is pressed:
                if event.key == pygame.K_DELETE:
                    Needle.needles = []
                    hits = 0
                    drops = 0
                    target_drops = 0
                    logging.info('Delete pressed, erased drops.')
            # Input boxes events:
            if input_value := drops_input.handle_event(event):
                try:
                    target_drops += int(input_value)
                    logging.info(f'Adding {input_value} to `target_drops`.')
                    reset_rates = True
                except ValueError:
                    logging.error(f'Invalid input box input, expected an int, got: "{input_value}"')

        drops_left = target_drops - drops

        # If reset is allowed, change fps and drop rate:
        if reset_rates:
            drops_per_frame, target_fps = get_rates(drops_left)

        reset_rates = False if drops_left else True  # Change if reset is allowed for next frame.

        # Add new needles:
        if drops_left:
            # Drop remaining needles.
            drops_per_frame = drops_left if drops_left < drops_per_frame else drops_per_frame
            for _ in range(drops_per_frame):
                new_needle = Needle(screen, column_count * column_space, window_height,
                                    sidebar_width,
                                    needle_length, columns_x_values)
                drops += 1
                hits += 1 if new_needle.hit else 0

        pi = (2 * drops * needle_length) / (hits * column_space) if hits else 0

        draw_screen(screen, drops, hits, fps, pi)
        pygame.display.flip()
        pygame.display.update()

        clock.tick(target_fps)
        fps = clock.get_fps()


if __name__ == '__main__':
    main()
