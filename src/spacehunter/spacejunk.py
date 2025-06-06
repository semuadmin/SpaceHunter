"""
spacejunk.py

This module contains a set of classes representing passive 'spacejunk'
sprites, including asteroids, debris and wreckage.

Created on 10 Jun 2020

@author: steely_eyed_missile_man
"""

# TODO consolidate these classes where possible

from random import choice, randint, randrange, uniform

import pygame as pg

from spacehunter.explosion import Explosion
from spacehunter.globals import ASTSPEED, ASTSPEEDR

vec = pg.math.Vector2


class Asteroid(pg.sprite.Sprite):
    """
    Meteor sprite class
    """

    def __init__(self, app, pos=None, vel=None):
        self._app = app  # Pointer to main application class
        pg.sprite.Sprite.__init__(self)

        self.image_orig = choice(self._app.asteroid_images)
        self.image = self.image_orig.copy()
        self.rect = self.image.get_rect()
        if pos is None:
            self.pos = vec(
                randint(-self._app.width * 2, self._app.width * 2),
                (-self._app.height * 3),
            )
        else:
            self.pos = pos
        if vel is None:
            self.vel = vec(
                randint(int(-ASTSPEED / 4), int(ASTSPEED / 4)), randint(1, ASTSPEED)
            )
        else:
            self.vel = vel
        self.rect.center = self.pos
        self.radius = int(self.rect.width * 0.85 / 2)
        self.rot = 0
        self._rot_speed = randint(-8, 8)
        self._last_update = pg.time.get_ticks()

        # Nominal kinetic energy damage rating for collisions
        self.damage = int(self.radius * (self.vel.magnitude() ** 2) / 4)

    def update(self):
        """
        Update asteroid sprite
        """

        self.rotate()
        self.pos += self.vel
        self.rect.center = self.pos

        if self._app.out_of_play(self.pos):
            self.kill()

    def rotate(self):
        """
        Rotate asteroid sprite
        """

        now = pg.time.get_ticks()
        if now - self._last_update > ASTSPEEDR:
            self._last_update = now
            self.rot = (self.rot + self._rot_speed) % 360
            new_image = pg.transform.rotate(self.image_orig, self.rot)
            old_center = self.rect.center
            self.image = new_image
            self.rect = self.image.get_rect()
            self.rect.center = old_center

    def disintegrate(self):
        """
        Disintegrate and create debris
        """

        choice(self._app.expl_sounds).play()
        Explosion(self._app, self.rect.center, "lg")
        for _ in range(int(self.radius / 4)):
            deb = Debris(self._app, self.rect.center, self.radius, self.vel)
            self._app.spacejunk_group.add(deb)
        self.kill()


class Debris(pg.sprite.Sprite):
    """
    Debris sprite class
    """

    def __init__(self, app, pos, radius, vel):
        self._app = app  # Pointer to main application class
        pg.sprite.Sprite.__init__(self)

        self.image_orig = choice(self._app.debris_images)
        max1 = randrange(round(min(1, radius / 5)), round(radius / 2))
        max2 = randrange(round(min(1, radius / 5)), round(radius / 2))
        self.image_orig = pg.transform.scale(self.image_orig, (max1, max2))
        self.image = self.image_orig.copy()
        self.rect = self.image.get_rect()
        self.pos = pos
        self.vel = vel + vec(
            randrange(-ASTSPEED, ASTSPEED), randrange(-ASTSPEED, ASTSPEED)
        )
        self.rect.center = self.pos
        self.radius = int(self.rect.width * 0.85 / 2)
        self.rot = 0
        self._rot_speed = randrange(-15, 15)
        self._last_update = pg.time.get_ticks()
        self._in_play_range = self._app.width * 4

        # Nominal kinetic energy damage rating for collisions
        self.damage = int(self.radius * (self.vel.magnitude() ** 2) / 4)

    def update(self):
        """
        Update debris sprite
        """

        self.rotate()
        self.pos += self.vel
        self.rect.center = self.pos

        if self._app.out_of_play(self.pos):
            self.kill()

    def rotate(self):
        """
        Rotate debris sprite
        """

        now = pg.time.get_ticks()
        if now - self._last_update > ASTSPEEDR:
            self._last_update = now
            self.rot = (self.rot + self._rot_speed) % 360
            new_image = pg.transform.rotate(self.image_orig, self.rot)
            old_center = self.rect.center
            self.image = new_image
            self.rect = self.image.get_rect()
            self.rect.center = old_center

    def disintegrate(self):
        """
        Disintegrate and create more debris
        """

        choice(self._app.expl_sounds).play()
        Explosion(self._app, self.rect.center, "sm")
        for _ in range(int(self.radius / 4)):
            Debris(self._app, self.rect.center, self.radius, self.vel)
        self.kill()


class Wreckage(pg.sprite.Sprite):
    """
    Wreckage sprite class
    """

    def __init__(self, app, pos, vel, img):
        self._app = app  # Pointer to main application class
        pg.sprite.Sprite.__init__(self)

        #         self._app.all_sprites.add(self)

        self.image_orig = img
        self.image = self.image_orig.copy()
        self.rect = self.image.get_rect()
        self.pos = pos
        self.vel = vel + vec(uniform(-ASTSPEED, ASTSPEED), uniform(-ASTSPEED, ASTSPEED))
        self.rect.center = self.pos
        self.radius = int(self.rect.width * 0.85 / 2)
        self.rot = 0
        self._rot_speed = randrange(-15, 15)
        self._last_update = pg.time.get_ticks()

        # Nominal kinetic energy damage rating for collisions
        self.damage = int(self.radius * (self.vel.magnitude() ** 2) / 8)

    def update(self):
        """
        Update debris sprite
        """

        self.rotate()
        self.pos += self.vel
        self.rect.center = self.pos

        if self._app.out_of_play(self.pos):
            self.kill()

    def rotate(self):
        """
        Rotate debris sprite
        """

        now = pg.time.get_ticks()
        if now - self._last_update > ASTSPEEDR:
            self._last_update = now
            self.rot = (self.rot + self._rot_speed) % 360
            new_image = pg.transform.rotate(self.image_orig, self.rot)
            old_center = self.rect.center
            self.image = new_image
            self.rect = self.image.get_rect()
            self.rect.center = old_center

    def disintegrate(self):
        """
        Disintegrate and create debris
        """

        choice(self._app.expl_sounds).play()
        Explosion(self._app, self.rect.center, "sm")
        for _ in range(int(self.radius / 4)):
            Debris(self._app, self.rect.center, self.radius, self.vel)
        self.kill()
