"""
helpers.py

Various generic helper functions

Created on 1 Jul 2020

@author: steely_eyed_missile_man
"""

from math import pi, sin

import pygame as pg


def draw_triangle(surf, orientation, size, col, pos):
    """
    Helper to draw indicator triangle centered on x,y
    """

    if orientation not in {"up", "down", "left", "right"}:
        return

    x, y = pos
    siz = size / 2
    sizs = sin(60 * pi / 180) * siz

    if orientation == "up":
        pgon = [(x - siz, y + sizs), (x, y - sizs), (x + siz, y + siz)]
    elif orientation == "down":
        pgon = [(x - siz, y - sizs), (x, y + sizs), (x + siz, y - siz)]
    elif orientation == "left":
        pgon = [(x - sizs, y), (x + sizs, y - siz), (x + siz, y + siz)]
    elif orientation == "right":
        pgon = [(x + sizs, y), (x - sizs, y - siz), (x - sizs, y + siz)]
    pg.draw.polygon(surf, col, pgon, 0)


def get_arrow_keys(event):
    """
    Helper function to process keyboard arrow keys like joystick hat events
    """

    x = 0
    y = 0
    if event.type == pg.KEYDOWN:
        if event.key == pg.K_LEFT:
            x = -1
        if event.key == pg.K_RIGHT:
            x = 1
        if event.key == pg.K_UP:
            y = -1
        if event.key == pg.K_DOWN:
            y = 1

    return (x, y)
