# -*- coding: utf-8 -*-
"""Contains all pygame UI classes used in main.py."""

from typing import Optional, Union
import pygame

default_color_inactive = pygame.Color('lightskyblue3')
default_color_active = pygame.Color('dodgerblue2')

ColorType = Union[pygame.Color, str, list[int], tuple[int, int, int], tuple[int, int, int, int]]

class InfoText:
	"""Updatable display text."""
	def __init__(self, x: float, y: float, font: pygame.font.SysFont, color: ColorType, text: Optional[str] = None):
		self.x = x
		self.y = y
		self.font = font
		self.color = color
		self.text = text

	@property
	def surface(self) -> pygame.Surface:
		"""Returns the text surface."""
		return self.font.render(self.text, True, self.color)

	def draw(self, surface: pygame.Surface, text: Optional[str] = None) -> None:
		"""Draws the display text. Specify `text` to update."""
		if text is not None:
			self.text = text
		surface.blit(self.surface, (self.x, self.y))


class InputBox:
	"""Input text box, adapted from: http://bit.ly/38xQ4qL"""

	def __init__(self, x: float, y: float, width: float, height: float,
	             font_name: str = 'ebrima',
	             empty_text: str = 'Type here:',
	             active_color: ColorType = default_color_active,
	             inactive_color: ColorType = default_color_inactive,
	             border_width: int = 3,
	             antialias: bool = True):

		self.active_color = active_color
		self.inactive_color = inactive_color
		self.border_width = border_width
		self.color = inactive_color

		self.rect = pygame.Rect(x, y, width, height)
		self.font_name = font_name
		self.empty_text = empty_text
		self.antialias = antialias

		self.font = pygame.font.SysFont(self.font_name, int(self.rect.h * 0.7))

		self.active = False
		self.text = ''

	@property
	def text_surface(self) -> pygame.Surface:
		"""Returns the text box surface."""
		display_text = self.text
		if display_text == '':
			display_text = self.empty_text
		return self.font.render(display_text, self.antialias, self.color)

	def handle_event(self, event: pygame.event.Event) -> Optional[str]:
		"""Handles pygame events if applicable to the text box."""
		if event.type == pygame.MOUSEBUTTONDOWN:
			# If the user clicked on the input_box rect:
			if self.rect.collidepoint(event.pos):
				self.active = not self.active
			else:
				self.active = False

		if event.type == pygame.KEYDOWN:
			if self.active:
				if event.key == pygame.K_RETURN:
					return self.text
				elif event.key == pygame.K_BACKSPACE:
					self.text = self.text[:-1]
				else:
					self.text += event.unicode

		self.color = self.active_color if self.active else self.inactive_color

	def draw(self, screen: pygame.Surface) -> None:
		"""Draws the text box."""
		screen.blit(self.text_surface, (self.rect.x + 5, self.rect.y))
		pygame.draw.rect(screen, self.color, self.rect, self.border_width)
