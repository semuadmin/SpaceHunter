"""
armoury.py

This module contains the Armoury class which displays a pop-up panel
allowing the player to update their weapons payload from a selection
of available weapon classes, provided they are 'docked' with the
Supply Ship which 'owns' the Armoury.

Use arrow keys or joystick hat to navigate around the available 'slots', and
the 'A' keyboard key or 'B' (CROSS) joystick button to apply the current selection.

Created on 27 Jun 2020

@author: steely_eyed_missile_man
"""

from copy import deepcopy

import pygame as pg

from spacehunter.colors import (
    BLUEGREY,
    DARK_GREY,
    GREEN,
    GREY,
    LIGHT_GREY,
    MIDNIGHTBLUE,
    RED,
    WHITE,
)
from spacehunter.globals import ALIGN_BOTTOM, ALIGN_LEFT, ALIGN_MID
from spacehunter.helpers import draw_triangle, get_arrow_keys
from spacehunter.weapons import *

SLOT_H = 40
SLOT_W = 100
GAP_W = 40
GAP_H = 6
BORDER = 30
ARMOURY_ROWS = 5
PAYLOAD_ROWS = 5
TXN_ROWS = 4
ARMOURY_COL = 0
PAYLOAD_COL = 1
TRANSACTION_COL = 2
CURSOR_FLASH_INT = 250

# TODO consider automatically adding weapon classes from
# the weapons.module using inspect.get_member ... inspect.isclass
# but might be too clever for its own good
WPN_CLASSES = [Empty, Laser, UltraLaser, Gatling, Missile, Sidewinder, Mine]


class Armoury:
    """
    Armoury class
    """

    def __init__(self, app, surf, pos):
        """
        Constructor
        """

        self._app = app  # Pointer to main pygame application instance

        self.haticon_img = self._app.image_dict["haticon1.png"]
        # Adjust size according to active font height
        _, fh = self._app.fonts["sm"].size("N")
        self.header = fh
        self.width = (SLOT_W * 3) + (GAP_W * 2) + (BORDER * 2)
        self.height = (
            ((SLOT_H + GAP_H) * ARMOURY_ROWS) + (BORDER * 2) + self.header + (9 * fh)
        )

        self._surf = surf
        self.pos = pos
        x, y = self.pos
        self._background = pg.Rect(x, y, self.width, self.height)
        self._cursor = False
        self.armoury = []
        self._payload = None
        self._orig_payload = None
        self._transactions = ["APPLY", "SAVE", "RESET", "CANCEL"]
        self._last_cursor = 0
        self._sel_col = 0
        self._sel_armoury = 0
        self._sel_payload = 0
        self._sel_txn = 0
        self._cost = 0
        self._in_link_pos = ()
        self._py_link_pos = ()

        self.__init_armoury()

    def __init_armoury(self):
        """
        Initialise armoury
        """

        for wpn in WPN_CLASSES:
            self.armoury.append(
                {
                    "wpn_class": wpn.__name__,
                    "wpn_cost": wpn.wpn_cost,
                    "ammo_cost": wpn.ammo_cost,
                    "damage": wpn.damage,
                    "rate_of_fire": wpn.rate_of_fire,
                    "capacity": wpn.capacity,
                    "notes": wpn.notes,
                }
            )

    def draw(self):
        """
        Draw armoury panel
        """

        now = pg.time.get_ticks()
        if now - self._last_cursor > CURSOR_FLASH_INT:
            self._cursor = not self._cursor
            self._last_cursor = now

        x, y = self.pos
        pg.draw.rect(self._surf, MIDNIGHTBLUE, self._background, border_radius=8)
        pg.draw.rect(self._surf, GREY, self._background, 4, border_radius=8)
        pg.draw.rect(self._surf, DARK_GREY, self._background, 2, border_radius=8)
        self._surf.blit(
            self.haticon_img,
            (x - GAP_W + BORDER + (SLOT_W + GAP_W) * 2 + SLOT_W / 2, y + 270),
        )
        self._app.draw_text(
            self._surf,
            "ARMOURY",
            "sm",
            WHITE,
            x + BORDER + SLOT_W / 2,
            y + BORDER,
            ALIGN_BOTTOM,
        )
        self._app.draw_text(
            self._surf,
            "PAYLOAD",
            "sm",
            WHITE,
            x + BORDER + SLOT_W + GAP_W + SLOT_W / 2,
            y + BORDER,
            ALIGN_BOTTOM,
        )
        self._app.draw_text(
            self._surf,
            "TRANSACTION",
            "sm",
            WHITE,
            x + BORDER + (SLOT_W + GAP_W) * 2 + SLOT_W / 2,
            y + BORDER,
            ALIGN_BOTTOM,
        )
        self.draw_armoury(self._surf, x + BORDER, y + BORDER + self.header)
        if self._payload is not None:
            self.draw_payload(
                self._surf, x + +BORDER + SLOT_W + GAP_W, y + BORDER + self.header
            )
        self._draw_transaction(
            self._surf, x + BORDER + ((SLOT_W + GAP_W) * 2), y + BORDER + self.header
        )
        self._draw_link(self._surf)
        self._draw_desc(
            self._surf,
            x + BORDER - GAP_H,
            y + BORDER + self.header + ((SLOT_H + GAP_H) * ARMOURY_ROWS) + 15,
        )

    def on_event(self, event):
        """
        Handle events while armoury is visible
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
            if event.key == pg.K_RETURN and self._sel_col == TRANSACTION_COL:
                if self._transactions[self._sel_txn] == "SAVE":
                    self._on_save()
                if self._transactions[self._sel_txn] == "CANCEL":
                    self._on_quit()
                if self._transactions[self._sel_txn] == "RESET":
                    self._on_reset()
                if self._transactions[self._sel_txn] == "APPLY":
                    self._on_apply()
            x, y = get_arrow_keys(event)
        elif event.type == pg.JOYHATMOTION:
            x, y = self._app.joystick.get_hat(0)
            y = -y
        elif event.type == pg.JOYBUTTONDOWN:
            if (
                event.button == self._app.config["BTN_B"]
                and self._sel_col == TRANSACTION_COL
            ):
                if self._transactions[self._sel_txn] == "SAVE":
                    self._on_save()
                if self._transactions[self._sel_txn] == "CANCEL":
                    self._on_quit()
                if self._transactions[self._sel_txn] == "RESET":
                    self._on_reset()
                if self._transactions[self._sel_txn] == "APPLY":
                    self._on_apply()

        self._sel_col = (self._sel_col + x) % 3
        if self._sel_col == ARMOURY_COL:
            self._sel_armoury = self._sel_armoury + y
            if self._sel_armoury > len(WPN_CLASSES) - 1:
                self._sel_armoury = len(WPN_CLASSES) - 1
            elif self._sel_armoury < 0:
                self._sel_armoury = 0
        elif self._sel_col == PAYLOAD_COL:
            self._sel_payload = self._sel_payload + y
            if self._sel_payload > len(self._payload) - 1:
                self._sel_payload = len(self._payload) - 1
            elif self._sel_payload < 0:
                self._sel_payload = 0
        elif self._sel_col == TRANSACTION_COL:
            self._sel_txn = (self._sel_txn + y) % TXN_ROWS

    def set_payload(self):
        """
        Set current player weapons payload
        """

        self._orig_payload, _ = self._app.player.get_payload()
        self._payload = deepcopy(self._orig_payload)  # We want a copy, not a reference
        self._cost = 0

    def draw_armoury(self, surf, x, y):
        """
        Draw armoury slots
        """

        col = LIGHT_GREY if self._sel_col == ARMOURY_COL else BLUEGREY
        pg.draw.rect(
            self._surf,
            col,
            (
                x - GAP_H,
                y - GAP_H,
                SLOT_W + GAP_H * 2,
                (SLOT_H + GAP_H) * ARMOURY_ROWS + GAP_H * 2,
            ),
            0,
            border_radius=5,
        )

        if self._sel_armoury > ARMOURY_ROWS - 1:
            top_row = self._sel_armoury - (ARMOURY_ROWS - 1)
        else:
            top_row = 0
        for i in range(ARMOURY_ROWS):
            p = i + top_row
            wpn = self.armoury[p]
            img = self._app.image_dict[globals()[wpn["wpn_class"]].image]
            yi = y + (i * (SLOT_H + GAP_H))
            if p == self._sel_armoury:
                if self._sel_col == ARMOURY_COL:
                    col = WHITE if self._cursor else GREY
                else:
                    col = WHITE
                self._in_link_pos = (x + SLOT_W, yi + SLOT_H / 2)
            else:
                col = GREY

            pg.draw.rect(surf, col, (x, yi, SLOT_W, SLOT_H), 2, border_radius=5)
            if img is not None:
                self._surf.blit(img, (x + 3, yi + 3))

        if top_row > 0:
            draw_triangle(surf, "up", 10, WHITE, (x + SLOT_W / 2, y))
        if len(self.armoury) > ARMOURY_ROWS + top_row:
            draw_triangle(
                surf,
                "down",
                10,
                WHITE,
                (x + SLOT_W / 2, y + SLOT_H * (ARMOURY_ROWS + 1) - 16),
            )

    def draw_payload(self, surf, x, y):
        """
        Draw player payload slots
        """

        col = LIGHT_GREY if self._sel_col == PAYLOAD_COL else BLUEGREY
        pg.draw.rect(
            self._surf,
            col,
            (
                x - GAP_H,
                y - GAP_H,
                SLOT_W + GAP_H * 2,
                (SLOT_H + GAP_H) * PAYLOAD_ROWS + GAP_H * 2,
            ),
            0,
            border_radius=5,
        )

        if self._sel_payload > PAYLOAD_ROWS - 1:
            top_row = self._sel_payload - (PAYLOAD_ROWS - 1)
        else:
            top_row = 0
        for i in range(PAYLOAD_ROWS):
            p = i + top_row
            if len(self._payload) <= p:
                wpn = {"wpn_class": "Empty", "ammo": 0, "temp": 0}
            else:
                wpn = self._payload[p]
            img = self._app.image_dict[globals()[wpn["wpn_class"]].image]
            yi = y + (i * (SLOT_H + GAP_H))
            if p == self._sel_payload:
                if self._sel_col == PAYLOAD_COL:
                    col = WHITE if self._cursor else GREY
                else:
                    col = WHITE
                self._py_link_pos = (x, yi + SLOT_H / 2)
            else:
                col = GREY

            pg.draw.rect(surf, col, (x, yi, SLOT_W, SLOT_H), 2, border_radius=5)
            if img is not None:
                self._surf.blit(img, (x + 3, yi + 3))

        if top_row > 0:
            draw_triangle(surf, "up", 10, WHITE, (x + SLOT_W / 2, y))
        if len(self._payload) > PAYLOAD_ROWS + top_row:
            draw_triangle(
                surf,
                "down",
                10,
                WHITE,
                (x + SLOT_W / 2, y + SLOT_H * (PAYLOAD_ROWS + 1) - 16),
            )

    def _draw_transaction(self, surf, x, y):
        """
        Draw transaction type slots
        """

        col = LIGHT_GREY if self._sel_col == TRANSACTION_COL else BLUEGREY
        pg.draw.rect(
            self._surf,
            col,
            (
                x - GAP_H,
                y - GAP_H,
                SLOT_W + GAP_H * 2,
                (SLOT_H + GAP_H) * TXN_ROWS + (GAP_H * 2) + 20,
            ),
            0,
            border_radius=5,
        )

        for i, _ in enumerate(self._transactions):
            yi = y + (i * (SLOT_H + GAP_H))
            col = GREY
            if i == self._sel_txn:
                if self._sel_col == TRANSACTION_COL:
                    col = WHITE if self._cursor else GREY
            pg.draw.rect(surf, col, (x, yi, SLOT_W, SLOT_H), 2, border_radius=5)
            self._app.draw_text(
                surf,
                self._transactions[i],
                "sm",
                col,
                x + SLOT_W / 2,
                yi + SLOT_H / 2,
                ALIGN_MID,
            )
        self._app.draw_text(
            self._surf,
            "TOTAL: " + str(self._cost),
            "smi",
            RED,
            x + SLOT_W / 2,
            35 + yi + SLOT_H / 2,
            ALIGN_MID,
        )

    def _draw_link(self, surf):
        """
        Draw link between armoury and payload rows to signify where weapons
        are being transferred
        """

        pg.draw.circle(surf, WHITE, self._in_link_pos, 4)
        pg.draw.circle(surf, WHITE, self._py_link_pos, 4)
        pg.draw.line(surf, WHITE, self._in_link_pos, self._py_link_pos, 3)

    def _draw_desc(self, surf, x, y):
        """
        Helper function to draw weapon description
        """

        text = []
        text.append(
            str(self._sel_armoury + 1)
            + ": "
            + str(self.armoury[self._sel_armoury]["wpn_class"]).upper()
        )
        if self.armoury[self._sel_armoury]["wpn_class"] != "Empty":
            text.append(
                "Cost: Weapon - "
                + str(self.armoury[self._sel_armoury]["wpn_cost"])
                + ", Ammo - "
                + str(self.armoury[self._sel_armoury]["ammo_cost"])
            )
            text.append("Damage: " + str(self.armoury[self._sel_armoury]["damage"]))
            text.append(
                "Rate of Fire: " + str(self.armoury[self._sel_armoury]["rate_of_fire"])
            )
            text.append(
                "Payload capacity: " + str(self.armoury[self._sel_armoury]["capacity"])
            )
            notes = self._app.wrap_text(
                "Special characteristics: " + self.armoury[self._sel_armoury]["notes"],
                "sm",
                self.width - BORDER * 2,
            )
            for line in notes:
                text.append(line)
        for txt in text:
            _, h = self._app.draw_text(surf, txt, "sm", WHITE, x, y, ALIGN_LEFT)
            y += h

    def _on_quit(self):
        """
        Quit weapons trading
        """

        self._app.doing_armoury = False
        self._cost = 0

    def _on_save(self):
        """
        Confirm all selections and exit
        """

        if self._cost > self._app.player.score:
            self._app.set_warning("INSUFFICIENT POINTS - NEED " + str(self._cost), RED)
        else:
            self._app.player.update_score(-self._cost)
            self._app.player.update_payload(self._payload)
            self._app.set_warning(
                "WEAPONS UPDATED, " + str(self._cost) + " POINTS DEDUCTED", GREEN
            )
            self._on_quit()

    def _on_reset(self):
        """
        Reset back to original payload
        """

        self.set_payload()

    def _on_apply(self):
        """
        Provisionally transfer selected weapon into payload
        """

        new_wpn_class = self.armoury[self._sel_armoury]["wpn_class"]
        self._payload[self._sel_payload]["wpn_class"] = new_wpn_class
        self._payload[self._sel_payload]["ammo"] = globals()[new_wpn_class].capacity
        self._cost = self._calc_cost()

    def _calc_cost(self):
        """
        Calculate cost of weapons
        If loading a new weapon, cost = weapon cost
        If reloading the same weapon, cost = (ammo cost * remaining capacity)
        (No refunds for downgrading weapons!)
        """

        cost = 0
        for i, wpn in enumerate(self._payload):
            if i == self._sel_payload:
                wpn_class_name = wpn["wpn_class"]
                wpn_class = globals()[wpn_class_name]
                if wpn_class_name == self._orig_payload[i]["wpn_class"]:
                    itemcost = wpn_class.ammo_cost * (
                        wpn_class.capacity - self._orig_payload[i]["ammo"]
                    )
                    cost += itemcost
                else:
                    cost += wpn_class.wpn_cost

        return cost
