"""
explosion.py

This module contains the animated Explosion sprite class, instantiated when
objects are hit.

Created on 14 Jun 2020

@author: steely_eyed_missile_man
"""

import pygame as pg


class Explosion(pg.sprite.Sprite):
    """
    Explosion sprite class
    """

    def __init__(self, app, center, size):
        """
        Class initialiser
        """

        self._app = app
        pg.sprite.Sprite.__init__(self)

        self._app.explosions.add(self)
        #         self._app.all_sprites.add(self)

        self.size = size
        self.image = self._app.explosion_anim[self.size][0]
        self.rect = self.image.get_rect()
        self.rect.center = center
        self.frame = 0
        self.last_update = pg.time.get_ticks()
        self.frame_rate = 50

        snd = 0 if size == "sm" else 1
        self._app.expl_sounds[snd].play()

    def update(self):
        """
        Update explosion sprite
        """

        now = pg.time.get_ticks()
        if now - self.last_update > self.frame_rate:
            self.last_update = now
            self.frame += 1
            if self.frame == len(self._app.explosion_anim[self.size]):
                self.kill()
            else:
                center = self.rect.center
                self.image = self._app.explosion_anim[self.size][self.frame]
                self.rect = self.image.get_rect()
                self.rect.center = center
