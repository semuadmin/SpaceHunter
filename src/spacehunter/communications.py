"""
communications.py

This module contains the Communications class which displays a pop-up panel
allowing the player to send 'messages' which instigate one or more
game events e.g. requesting and docking with a supply ship.

Communications class

Created on 06 Jul 2020

@author: steely_eyed_missile_man
"""

import pygame as pg

from spacehunter.colors import (
    BLUEGREY,
    DARK_GREY,
    GREEN,
    GREY,
    LIGHT_GREY,
    MIDNIGHTBLUE,
    WHITE,
)

# from spaceshooter.controllers import BTN_B, HAT_DOWN, HAT_UP
from spacehunter.globals import ALIGN_BOTTOM, ALIGN_MID
from spacehunter.helpers import draw_triangle, get_arrow_keys

SLOT_H = 40
SLOT_W = 225
GAP_W = 40
GAP_H = 6
BORDER = 30
COMMS_ROWS = 4
COMMS_COL = 0
CURSOR_FLASH_INT = 250

COMMS_LIST = [
    "REQUEST SUPPLY SHIP",
    "DOCK WITH SUPPLY SHIP",
    "GET SUPPLIES",
    "UNDOCK FROM SUPPLY SHIP",
    "CALL FOR BACKUP",
    "CALL FOR TRUCE",
    "ANOTHER MESSAGE",
    "YET ANOTHER MESSAGE",
    "CANCEL",
]


class Communications:
    """
    Communications class
    """

    def __init__(self, app, surf, pos):
        """
        Constructor
        """

        self._app = app  # Pointer to main pygame application instance

        # Adjust size according to active font height
        _, fh = self._app.fonts["sm"].size("N")
        self.header = fh
        self.width = (SLOT_W * 1) + (BORDER * 2)
        self.height = ((SLOT_H + GAP_H) * COMMS_ROWS) + (BORDER * 2) + self.header
        self._surf = surf
        self.pos = pos
        x, y = self.pos
        self._background = pg.Rect(x, y, self.width, self.height)
        self._cursor = False
        self._last_cursor = 0
        self._sel_col = 0
        self._sel_comms = 0

    def draw(self):
        """
        Draw communications panel
        """

        now = pg.time.get_ticks()
        if now - self._last_cursor > CURSOR_FLASH_INT:
            self._cursor = not self._cursor
            self._last_cursor = now

        x, y = self.pos
        pg.draw.rect(self._surf, MIDNIGHTBLUE, self._background, border_radius=8)
        pg.draw.rect(self._surf, GREY, self._background, 4, border_radius=8)
        pg.draw.rect(self._surf, DARK_GREY, self._background, 2, border_radius=8)
        self._app.draw_text(
            self._surf,
            "Communications",
            "sm",
            WHITE,
            x + BORDER + SLOT_W / 2,
            y + BORDER,
            ALIGN_BOTTOM,
        )
        self._draw_comms(self._surf, x + BORDER, y + BORDER + self.header)

    def on_event(self, event):
        """
        Handle events while comms panel is visible
        Navigate slots using arrow keys or gamepad hat
        Apply selected transaction using RETURN key or 'B' (CROSS) gamepad button
        """

        x = 0
        y = 0

        if event.type == pg.QUIT:
            self._on_quit()
        elif event.type == pg.KEYDOWN:
            if event.key == pg.K_q:
                self._on_quit()
            if event.key == pg.K_RETURN and self._sel_col == COMMS_COL:
                self._on_send()
            x, y = get_arrow_keys(event)
        elif event.type == pg.JOYHATMOTION:
            x, y = self._app.joystick.get_hat(0)
            y = -y
        elif event.type == pg.JOYBUTTONDOWN:
            if event.button == self._app.config["HAT_UP"]:
                x = 0
                y = 1
            if event.button == self._app.config["HAT_DOWN"]:
                x = 0
                y = -1
            if event.button == self._app.config["BTN_B"] and self._sel_col == COMMS_COL:
                self._on_send()
        self._sel_col = (self._sel_col + x) % 1
        if self._sel_col == COMMS_COL:
            self._sel_comms = self._sel_comms + y
            if self._sel_comms > len(COMMS_LIST) - 1:
                self._sel_comms = len(COMMS_LIST) - 1
            elif self._sel_comms < 0:
                self._sel_comms = 0

    def _draw_comms(self, surf, x, y):
        """
        Draw message slots
        """

        col = LIGHT_GREY if self._sel_col == COMMS_COL else BLUEGREY
        pg.draw.rect(
            self._surf,
            col,
            (
                x - GAP_H,
                y - GAP_H,
                SLOT_W + GAP_H * 2,
                (SLOT_H + GAP_H) * COMMS_ROWS + GAP_H * 2,
            ),
            0,
            border_radius=5,
        )

        if self._sel_comms > COMMS_ROWS - 1:
            top_row = self._sel_comms - (COMMS_ROWS - 1)
        else:
            top_row = 0
        for i in range(COMMS_ROWS):
            p = i + top_row
            msg = COMMS_LIST[p]
            yi = y + (i * (SLOT_H + GAP_H))
            if p == self._sel_comms:
                if self._sel_col == COMMS_COL:
                    col = WHITE if self._cursor else GREY
                else:
                    col = WHITE
            else:
                col = GREY

            pg.draw.rect(surf, col, (x, yi, SLOT_W, SLOT_H), 2, border_radius=5)
            self._app.draw_text(
                surf, msg, "sm", col, x + SLOT_W / 2, yi + SLOT_H / 2, ALIGN_MID
            )

        if top_row > 0:
            draw_triangle(surf, "up", 10, WHITE, (x + SLOT_W / 2, y))
        if len(COMMS_LIST) > COMMS_ROWS + top_row:
            draw_triangle(
                surf,
                "down",
                10,
                WHITE,
                (x + SLOT_W / 2, y + SLOT_H * (COMMS_ROWS + 1) - 22),
            )

    def _on_quit(self):
        """
        Quit weapons trading
        """

        self._app.doing_comms = False

    def _on_send(self):
        """
        Send selected message
        """

        comm = COMMS_LIST[self._sel_comms]
        if comm == "CANCEL":
            pass
        if comm == "REQUEST SUPPLY SHIP":
            if not self._app.doing_supply:
                self._app.set_warning("SUPPLY SHIP REQUESTED", GREEN)
                self._app.supply_ship.summon()
        if comm == "DOCK WITH SUPPLY SHIP":
            if self._app.doing_supply:
                self._app.supply_ship.dock()
        if comm == "UNDOCK FROM SUPPLY SHIP":
            if self._app.doing_supply:
                self._app.supply_ship.undock()
        if comm == "GET SUPPLIES":
            if not self._app.doing_armoury:
                self._app.supply_ship.do_supplies()

        self._on_quit()
