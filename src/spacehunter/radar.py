"""
radar.py

This module contains the Radar class which displays a pop-up panel
simulating a 'radar' screen showing the position of sprites within
a designated set of sprite groups.

Created on 27 Jun 2020

@author: steely_eyed_missile_man
"""

import pygame as pg

from spacehunter.colors import BROWN, DARK_GREY, GREEN, GREY, RED, WHITE
from spacehunter.helpers import draw_triangle

MIN_RADAR_BLIP = 3
SCREEN_COL = (0, 50, 0)
FOCUS_COL = (0, 70, 0)


class Radar:
    """
    Radar screen class
    """

    def __init__(self, app, surf, pos, rng=2, size=10):
        """
        Constructor
        """

        self._app = app  # Pointer to main pygame application instance
        self._surf = surf
        self.pos = pos
        self.radar_range = rng
        self._size = size
        self._last_radar_alert = 0
        self._radar_flash = False

        x, y = pos
        self.width = self._surf.get_width() / self._size
        self.height = self._surf.get_height() / self._size
        self._rscreen = pg.Rect(x - self.width / 2, y, self.width, self.height)

    def draw(self):
        """
        Draw radar display
        """

        now = pg.time.get_ticks()
        if now - self._last_radar_alert > 500:
            self._radar_flash = not self._radar_flash
            self._last_radar_alert = now

        # Draw outer rect representing radar 'screen'
        pg.draw.rect(self._surf, SCREEN_COL, self._rscreen, border_radius=4)
        # Draw inner rect representing visible display extent
        m_x = -self._rscreen.width + self._rscreen.width / self.radar_range
        m_y = -self._rscreen.height + self._rscreen.height / self.radar_range
        pg.draw.rect(
            self._surf, FOCUS_COL, self._rscreen.inflate(m_x, m_y), border_radius=4
        )

        for enemy in self._app.enemies_group:
            self.show_radar_blip(enemy.pos, enemy.radius, "enemy", RED)

        for ast in self._app.spacejunk_group:
            self.show_radar_blip(ast.pos, ast.radius, "junk", BROWN)

        for wpn in self._app.weapons_group:
            self.show_radar_blip(wpn.pos, wpn.radius, "weapon", WHITE)

        for fnd in self._app.friends_group:
            self.show_radar_blip(fnd.pos, fnd.radius, "friend", GREEN)

        # Draw bordering rect which flashes if any enemies are in play
        col = (
            RED if len(self._app.enemies_group) > 0 and self._radar_flash else DARK_GREY
        )
        pg.draw.rect(self._surf, col, self._rscreen.inflate(3, 3), 3, border_radius=4)
        pg.draw.rect(self._surf, GREY, self._rscreen.inflate(5, 5), 2, border_radius=4)

    def show_radar_blip(self, bpos, rad, icon, col):
        """
        Draw radar blip if it's within range
        """

        rpos = self.get_rpos(bpos)
        if self._rscreen.collidepoint(rpos) and rad > MIN_RADAR_BLIP:
            if icon in {"junk", "weapon"}:
                pg.draw.circle(self._surf, col, rpos, 2)
            if icon in {"friend"}:
                draw_triangle(self._surf, "up", 5, col, rpos)
            if icon in {"enemy"}:
                draw_triangle(self._surf, "down", 5, col, rpos)

    def get_rpos(self, bpos):
        """
        Calculate blip coordinates
        """

        x, y = self.pos
        p_x, p_y = bpos
        mag = self.radar_range * self._size
        r_x = int(p_x / mag + (x - self._surf.get_width() / (mag * 2)))
        r_y = int(
            p_y / mag
            + (y - (self._surf.get_height() / (mag * 2)) + (self._rscreen.height / 2))
        )

        return (r_x, r_y)

    def set_range(self, rng):
        """
        Set radar range
        """

        self.radar_range = rng
