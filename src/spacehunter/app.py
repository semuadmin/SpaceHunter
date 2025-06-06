"""
app.py

This module contains the game's main App class which implements a standardised
pygame structure centered around the _on_execute() method.

Created on 10 Jun 2020

@author: steely_eyed_missile_man

Originally inspired by:
http://pygametutorials.wikidot.com/tutorials-basic
http://kidscancode.org/blog/2016/08/pygame_shmup_part_1/
© 2019 KidsCanCode LLC.

Some graphics from:
http://opengameart.org/content/space-shooter-redux
CC0 1.0 Universal Public Domain Dedication
"""

from json import JSONDecodeError, dump, load, loads
from os import path, sep, walk
from random import randint, randrange
from re import compile as regxcompile
from time import gmtime, strftime

import pygame as pg
from pygame.constants import DOUBLEBUF, FULLSCREEN, HWSURFACE

from spacehunter.automaton import FLEE
from spacehunter.colors import BLACK, BLUE, GREEN, ORANGE, RED, WHITE, YELLOW
from spacehunter.communications import Communications
from spacehunter.controllers import DEFAULT_CONFIG
from spacehunter.enemy import MAX_SPEED as EMY_MAX_SPEED
from spacehunter.enemy import Enemy
from spacehunter.globals import (
    ALIGN_BOTTOM,
    ALIGN_CENTER,
    ALIGN_LEFT,
    ALIGN_MID,
    ALIGN_RIGHT,
    ASTEROIDS,
    ASTMAX,
    ASTMIN,
    ASTSTORM,
    CONFIGFILE,
    DEFAULT_USER,
    ENEMIES,
    ENEMYMAX,
    ENEMYMIN,
    ENEMYSTORM,
    FONTDIR,
    FPS,
    FULLSCREEN,
    GAMEOVER,
    HEIGHT,
    IMGDIR,
    INPLAYRANGE,
    LIVES,
    MUSVOL,
    NEWGAME,
    PAUSED,
    PLAYING,
    SNDDIR,
    SNDVOL,
    STATEFILE,
    WIDTH,
)
from spacehunter.helpers import draw_triangle, get_arrow_keys
from spacehunter.levels import LEVELS_MATRIX
from spacehunter.player import MAX_SHIELD, Player
from spacehunter.radar import Radar
from spacehunter.spacejunk import Asteroid, Wreckage
from spacehunter.supplyship import SupplyShip
from spacehunter.weapons import *

vec = pg.math.Vector2

ICON = path.join(IMGDIR, "icons", "spacer.png")


class SpaceHunter:
    """
    Main game application class
    """

    def __init__(self):
        """
        PyGame application initialisation
        """

        # Read controller assignments from config file
        self.config = self._read_config()

        self.clock = pg.time.Clock()
        pg.init()

        pg.mixer.init()
        pg.joystick.init()
        if pg.joystick.get_count() > 0:
            self.joystick = pg.joystick.Joystick(0)
            self.joystick.init()
        else:
            self.joystick = None
        program_icon = pg.image.load(path.join(IMGDIR, "icons", "spacer.png"))
        pg.display.set_icon(program_icon)
        pg.display.set_caption("SpaceShooter!")
        display_info = pg.display.Info()
        if FULLSCREEN:
            self._size = self.width, self.height = (
                display_info.current_w,
                display_info.current_h,
            )
            self._display_surf = pg.display.set_mode(
                self._size, FULLSCREEN | HWSURFACE | DOUBLEBUF
            )
        else:
            self._size = self.width, self.height = (WIDTH, HEIGHT)
            self._display_surf = pg.display.set_mode(self._size, HWSURFACE | DOUBLEBUF)

        self.image_dict = {}
        self.sound_dict = {}
        self.in_play_range = self.width * INPLAYRANGE
        self._highscore = 0
        self._username = DEFAULT_USER
        self._saved_gamestate = NEWGAME
        self._gamedata = None
        self._quitconfirm = False
        self._running = True
        self._doing_help = 0
        self._help_panels = 0
        self.player = None
        self.radar_range = 2  # 0 = off
        self.doing_armoury = False
        self.doing_supply = False
        self.doing_comms = False
        self.supply_ship = None
        self.round_type = 0  # Keep track of Gatling gun rounds

    def __on_init(self):
        """
        Initialise images, sprites, sprite groups, sounds and event timers
        """

        # Set initial game state
        self.gamestate = NEWGAME

        # Set up sprite groups
        self.hazards_group = pg.sprite.Group()
        self.spacejunk_group = pg.sprite.Group()
        self.weapons_group = pg.sprite.Group()
        self.enemy_weapons_group = pg.sprite.Group()
        self.enemies_group = pg.sprite.Group()
        self.friends_group = pg.sprite.Group()
        self.wreckage_group = pg.sprite.Group()
        self.explosions = pg.sprite.Group()
        self.players_group = pg.sprite.Group()

        # Initialise game
        self.__init_fonts()
        self.__init_images()
        self.__init_sounds()
        self.__init_explosions()
        self.__init_player()

        # Read saved game state from gamestate file
        self._gamedata = self._read_gamedata(self._username)
        self._orig_highscore = self._highscore

        # Initialise event timers and intervals
        self._asteroid_interval = randrange(ASTMIN, ASTMAX)
        self._enemy_interval = randrange(ENEMYMIN, ENEMYMAX)
        self._last_asteroid_storm = 0
        self._last_enemy_storm = 0
        self._last_radar_alert = 0
        self._last_warning = 0
        self._radar_flash = False
        self.warning_msg = ""
        self.warning_msg_col = RED

        # Initialise supply ship
        self.supply_ship = SupplyShip(self)
        self.friends_group.add(self.supply_ship)

        # Initialise communications panel
        self._comms = Communications(
            self, self._display_surf, (self.width / 2 - 130, self.height / 2 - 100)
        )

        # Initialise radar panel
        self._radar = Radar(self, self._display_surf, (self.width / 2, 5))

    def __init_fonts(self):
        """
        Initialise fonts, scaled to screen dimensions
        """

        norm = path.join(FONTDIR, "Roboto-Medium.ttf")
        italic = path.join(FONTDIR, "Roboto-Mediumitalic.ttf")
        self.fonts = {
            "sm": pg.font.Font(norm, int(min(16, self.height / 50))),
            "md": pg.font.Font(norm, int(min(28, self.height / 28))),
            "lg": pg.font.Font(norm, int(min(36, self.height / 22))),
            "smi": pg.font.Font(italic, int(min(16, self.height / 50))),
            "mdi": pg.font.Font(italic, int(min(28, self.height / 28))),
            "lgi": pg.font.Font(italic, int(min(36, self.height / 22))),
        }

    def __init_images(self):
        """
        Find all images in designated folders and subfolders, convert them
        to game-friendly format, add to image dict and, where appropriate,
        the relevant image category list
        """

        # Image category filenames must follow these regx conventions
        help_regx = regxcompile("help_([0-9]|[1-9][0-9]).png")
        wreckage_regx = regxcompile("wreckage_([0-9]|[1-9][0-9]).png")
        asteroid_regx = regxcompile("asteroid_([0-9]|[1-9][0-9]).png")
        debris_regx = regxcompile("debris_([0-9]|[1-9][0-9]).png")
        self.help_images = []
        self.wreckage_images = []
        self.asteroid_images = []
        self.debris_images = []

        for subdir, _, files in walk(IMGDIR):
            for filename in files:
                filepath = subdir + sep + filename

                if filepath.endswith(".jpg") or filepath.endswith(".png"):
                    img = pg.image.load(filepath).convert()
                    img.set_colorkey(BLACK)
                    self.image_dict[filename] = img

                    if help_regx.fullmatch(filename):  # Image is a help panel
                        self.help_images.append(img)
                    if wreckage_regx.fullmatch(filename):  # Image is wreckage
                        self.wreckage_images.append(img)
                    if asteroid_regx.fullmatch(filename):  # Image is asteroid
                        self.asteroid_images.append(img)
                    if debris_regx.fullmatch(filename):  # Image is debris
                        self.debris_images.append(img)

        self.background_img = pg.transform.scale(
            self.image_dict["starfield4.jpg"], (self.width, self.height)
        )

    def __init_sounds(self):
        """
        Find all sound files in designated folders and subfolders, set mixer volume
        and add to sound dict
        """

        for subdir, _, files in walk(SNDDIR):
            for filename in files:
                filepath = subdir + sep + filename

                if (
                    filepath.endswith(".wav")
                    or filepath.endswith(".ogg")
                    or filepath.endswith(".mid")
                ):
                    snd = pg.mixer.Sound(filepath)
                    snd.set_volume(SNDVOL)
                    self.sound_dict[filename] = snd

        pg.mixer.music.load(path.join(SNDDIR, "frozen-jam-seamless-loop.ogg"))
        pg.mixer.music.set_volume(MUSVOL)

    def __init_explosions(self):
        """
        Set up explosion animation image arrays
        """

        self.explosion_anim = {}
        self.explosion_anim["lg"] = []
        self.explosion_anim["sm"] = []
        self.explosion_anim["death"] = []
        for i in range(9):
            filename = "regularExplosion0{}.png".format(i)
            img = self.image_dict[filename]
            img_lg = pg.transform.scale(img, (75, 75))
            self.explosion_anim["lg"].append(img_lg)
            img_sm = pg.transform.scale(img, (32, 32))
            self.explosion_anim["sm"].append(img_sm)
            filename = "sonicExplosion0{}.png".format(i)
            img = self.image_dict[filename]
            self.explosion_anim["death"].append(img)

        self.expl_sounds = []
        for snd in ["expl3.wav", "expl6.wav"]:
            expl = self.sound_dict[snd]
            expl.set_volume(SNDVOL)
            self.expl_sounds.append(expl)

    def __init_player(self):
        """
        Initialise player
        """

        # Limited weapons payload at start
        weapons = [
            {"wpn_class": "Laser", "ammo": Laser.capacity, "temp": 0},
            {"wpn_class": "Gatling", "ammo": Gatling.capacity, "temp": 0},
            {"wpn_class": "Missile", "ammo": Missile.capacity, "temp": 0},
            {"wpn_class": "Sidewinder", "ammo": Sidewinder.capacity, "temp": 0},
            {"wpn_class": "Mine", "ammo": Mine.capacity, "temp": 0},
        ]

        self.player = Player(
            self,
            vec(self.width / 2, self.height - 20),
            0,
            0,
            0,
            MAX_SHIELD,
            LIVES,
            weapons,
        )
        self.players_group.add(self.player)

    def _on_execute(self):
        """
        !!! MAIN GAME LOOP !!!

        It should not normally be necessary to change anything in this method
        """

        if self.__on_init() is False:
            self._running = False

        while self._running:
            # Check running status before each step in case of mid-game quit
            if self._running:
                for event in pg.event.get():
                    self._on_event(event)
            if self._running:
                if self.gamestate == PLAYING:
                    self._on_loop()
            if self._running:
                self._on_render()

        self._on_cleanup()

    def _on_event(self, event):
        """
        Handle all user input events
        """

        if event.type == pg.QUIT:
            self._on_quit()

        # If in armoury (weapons trading) mode, let the armoury class handle events
        if self.doing_armoury:
            self.supply_ship.armoury.on_event(event)
            return

        # If in comms mode, let the comms class handle events
        if self.doing_comms:
            self._comms.on_event(event)
            return

        if event.type in {pg.KEYUP, pg.KEYDOWN}:
            self._on_keyboard_event(event)

        if self.joystick is not None:
            if event.type in {
                pg.JOYBUTTONDOWN,
                pg.JOYBUTTONUP,
                pg.JOYAXISMOTION,
                pg.JOYHATMOTION,
                pg.JOYBALLMOTION,
            }:
                self._on_gamepad_event(event)

    def _on_keyboard_event(self, event):
        """
        Handle keyboard events
        """

        # Keyboard events
        if event.type == pg.KEYDOWN:
            # Press 'Q' to quit
            if event.key == pg.K_q:
                self._on_quit()
            # Press'H' to toggle through help panel(s)
            if event.key == pg.K_h:
                self._doing_help = (self._doing_help + 1) % (len(self.help_images) + 1)
                if self._doing_help and self.gamestate == PLAYING:
                    self.gamestate = PAUSED
                if not self._doing_help and self.gamestate == PAUSED:
                    self.gamestate = PLAYING
            # Press 'S' to save current state
            if event.key == pg.K_s:
                self._save_gamedata(self._username)
            # Press 'N' for new game
            if event.key == pg.K_n and self.gamestate == GAMEOVER:
                self._on_execute()
            # Press 'G' to start new game
            if event.key == pg.K_g and self.gamestate == NEWGAME:
                self._on_start()
            # Press 'R' to restart saved game
            if (
                event.key == pg.K_r
                and self.gamestate == NEWGAME
                and self._gamedata is not None
            ):
                self._on_restart()
            # Press 'D' to toggle _radar
            if event.key == pg.K_d and self.gamestate in {PLAYING, PAUSED}:
                self.radar_range = (self.radar_range + 1) % 5
                self._radar.set_range(self.radar_range)
            # Press 'P' to toggle pause
            if event.key == pg.K_p and self.gamestate in {PLAYING, PAUSED}:
                self._quitconfirm = False
                self._on_pause()
            if self.gamestate == PLAYING:
                # Press 'C' to display communications panel
                if event.key == pg.K_c:
                    self.doing_comms = True
                # Press 'W' to cycle selected weapon
                if event.key == pg.K_w:
                    self.player.cycle_weapon()
                # Press 'SPACE' to _shoot
                if event.key == pg.K_SPACE:
                    self.player.shoot()
                # Press arrow keys to accelerate player
                x, y = get_arrow_keys(event)
                self.player.accelerate(thrust=y, sideways=x)
        elif event.type == pg.KEYUP:
            if self.gamestate == PLAYING:
                if event.key in {pg.K_LEFT, pg.K_RIGHT, pg.K_UP, pg.K_DOWN}:
                    x, y = get_arrow_keys(event)
                    self.player.accelerate(thrust=y, sideways=x)

    def _on_gamepad_event(self, event):
        """
        Handle gamepad / joystick events
        Gamepad axis & button assignments can be set in controllers file
        """

        if event.type == pg.JOYBUTTONDOWN:
            # Press Start button to pause or start the game
            if event.button == self.config["BTN_START"]:
                if self.gamestate == NEWGAME:
                    self._on_start()
                elif self.gamestate in {PLAYING, PAUSED}:
                    self._quitconfirm = False
                    self._on_pause()
            # Press A button to toggle radar range and visibility
            if event.button == self.config["BTN_A"] and self.gamestate in {
                PLAYING,
                PAUSED,
            }:
                self.radar_range = (self.radar_range + 1) % 5
                self._radar.set_range(self.radar_range)
            # Press X button to display communications panel
            if event.button == self.config["BTN_X"]:
                self.doing_comms = True
            if event.button == self.config["BTN_SELECT"]:
                self._on_quit()
            # Press L2 to toggle through help panel(s)
            if event.button == self.config["BTN_L1"]:
                self._doing_help = (self._doing_help + 1) % (len(self.help_images) + 1)
                if self._doing_help and self.gamestate == PLAYING:
                    self.gamestate = PAUSED
                if not self._doing_help and self.gamestate == PAUSED:
                    self.gamestate = PLAYING
            if self.gamestate == PLAYING:
                # Press R1 to shoot
                if event.button == self.config["BTN_R1"]:
                    self.player.shoot()
                # Press Y button to cycle weapons
                if event.button == self.config["BTN_Y"]:
                    self.player.cycle_weapon()
        elif event.type == pg.JOYAXISMOTION:
            if self.gamestate == PLAYING:
                thrust = round(self.joystick.get_axis(self.config["JOYL_Y"]), 1)
                sideways = round(self.joystick.get_axis(self.config["JOYL_X"]), 1)
                yaw = round(self.joystick.get_axis(self.config["JOYR_X"]), 1)
                self.player.accelerate(thrust=thrust, sideways=sideways, yaw=yaw)

    def _on_loop(self):
        """
        Handle all running game dynamics
        (timed events, sprite group updates, scoring, messages, etc.)

        NB: Collisions are handled by the 'owning' objects i.e. the object being hit
        """

        # Keep loop running at the right speed
        self.clock.tick(FPS)

        # No new hazards during communications or supply runs
        # (BUT any existing in-play hazards will still be a threat)
        if not self.doing_supply and not self.doing_armoury:
            # Generate random asteroid storms
            if ASTEROIDS:
                self.do_asteroids()

            # Generate random enemy swarms
            if ENEMIES:
                self.do_enemies()

        # Rapid fire if _shoot button held down
        if self.gamestate == PLAYING:
            keys = pg.key.get_pressed()
            if keys[pg.K_SPACE]:
                self.player.auto_shoot()
            if self.joystick is not None:
                if self.joystick.get_button(self.config["BTN_R1"]):
                    self.player.auto_shoot()

        # Update all sprite groups
        #         self.all_sprites.update()
        self.spacejunk_group.update()
        self.weapons_group.update()
        self.enemy_weapons_group.update()
        self.enemies_group.update()
        self.friends_group.update()
        self.explosions.update()
        self.wreckage_group.update()
        self.players_group.update()

        # Update high score
        score = self.player.score
        if score > self._highscore:
            self._highscore = score

        # Clear any expired warning messages
        now = pg.time.get_ticks()
        if self.warning_msg != "" and (now - self._last_warning > 2000):
            self.warning_msg = ""
            self._last_warning = now

    def _on_render(self):
        """
        Render all objects on display surface
        """

        self._display_surf.fill(BLACK)
        self._display_surf.blit(self.background_img, self.background_img.get_rect())
        #         self.all_sprites.draw(self._display_surf)
        self.spacejunk_group.draw(self._display_surf)
        self.weapons_group.draw(self._display_surf)
        self.enemy_weapons_group.draw(self._display_surf)
        self.explosions.draw(self._display_surf)
        self.wreckage_group.draw(self._display_surf)
        self.enemies_group.draw(self._display_surf)
        self.friends_group.draw(self._display_surf)
        self.players_group.draw(self._display_surf)

        if self.player is not None:
            self.draw_scores((self.width - 5, 35))
            self.draw_bar(self._display_surf, 5, 10, 100, self.player.shield)
            wpn_class, ammo = self.player.get_ammo()
            wpn_class = globals()[wpn_class]
            self.draw_bar(self._display_surf, 5, 22, wpn_class.capacity, ammo)
            self.draw_lives(self._display_surf, self.width - 35, 5)
            self.draw_payload(self._display_surf, 5, 40)

        # Gamestate-dependent screen prompts
        center_x, center_y = int(self.width / 2), int(self.height / 2)
        if self._quitconfirm is True:
            self.draw_text(
                self._display_surf,
                "PRESS Q AGAIN TO CONFIRM QUIT",
                "lg",
                RED,
                center_x,
                center_y + 50,
            )
            self.draw_text(
                self._display_surf,
                "OR P TO CONTINUE",
                "md",
                GREEN,
                center_x,
                center_y + 100,
            )
        if self.gamestate == NEWGAME:
            self.draw_text(
                self._display_surf,
                "PRESS G TO START NEW GAME",
                "lg",
                GREEN,
                center_x,
                center_y,
            )
            if (
                self._saved_gamestate == PLAYING or self._saved_gamestate == PAUSED
            ) and self._gamedata is not None:
                self.draw_text(
                    self._display_surf,
                    "OR R TO RESTART SAVED GAME",
                    "md",
                    ORANGE,
                    center_x,
                    center_y + 50,
                )
        if self.gamestate == PAUSED:
            self.draw_text(
                self._display_surf, "PAUSED", "lg", ORANGE, center_x, center_y
            )
        if self.gamestate == GAMEOVER:
            self.draw_text(
                self._display_surf, "GAME OVER", "lg", YELLOW, center_x, center_y
            )
            self.draw_text(
                self._display_surf,
                "PRESS N FOR NEW GAME",
                "lg",
                ORANGE,
                center_x,
                center_y + 50,
            )

        if self.radar_range:  # Value of 0 means 'off'
            self._radar.draw()

        if self.doing_armoury:
            self.supply_ship.armoury.draw()

        if self.doing_comms:
            self._comms.draw()

        if self._doing_help:
            self.draw_help()

        self.draw_warning()

        # *After* drawing everything, flip the display
        pg.display.flip()

    def _on_cleanup(self):
        """
        Cleanup prior to quitting
        """

        if self.player is not None:
            self._save_gamedata(self._username)
        pg.quit()

    def _on_start(self):
        """
        Initialise new game game state
        """

        self.gamestate = PLAYING
        pg.mixer.music.play(loops=-1)

    def _on_restart(self):
        """
        Restore saved game state
        """

        score = self._gamedata.get("score", 0)
        lives = self._gamedata.get("lives", LIVES)
        level = self._gamedata.get("level", 0)
        shield = self._gamedata.get("shield", 100)

        weapons = []
        for wpn in self._gamedata.get("weapons_group"):
            weapons.append(
                {
                    "wpn_class": wpn["wpn_class"],
                    "ammo": wpn["ammo"],
                    "temp": wpn["temp"],
                }
            )

        print("weapons = ", weapons)
        self.player.restore(level, score, shield, lives, weapons)

        self.gamestate = PLAYING
        pg.mixer.music.play(loops=-1)

    def _on_pause(self):
        """
        Pause game actions
        """

        if self.gamestate == PLAYING:
            pg.mixer.music.stop()
            self.gamestate = PAUSED
        else:
            pg.mixer.music.play(loops=-1)
            self.gamestate = PLAYING

    def _on_quit(self):
        """
        Quit confirmation actions ('Are you sure?')
        """

        if self._quitconfirm is False:
            self.gamestate = PAUSED
            pg.mixer.music.stop()
            self._quitconfirm = True
        else:
            self._running = False

    def _read_config(self):
        """
        Read joystick controller assignments from config file.
        If file cannot be read, return default values.
        """

        try:
            with open(CONFIGFILE, "r", encoding="UTF-8") as infile:
                return load(infile)
        except (OSError, JSONDecodeError):
            return DEFAULT_CONFIG

    def _read_gamedata(self, username=DEFAULT_USER):
        """
        Read last saved game state from json file
        """

        try:
            with open(STATEFILE, "r") as infile:
                jsondata = infile.read()
                gamedata = loads(jsondata).get(username)
                self._highscore = gamedata.get("highscore", 0)
                self._saved_gamestate = gamedata.get("gamestate", NEWGAME)
                return gamedata
        except (OSError, JSONDecodeError):
            return None

    def _save_gamedata(self, username=DEFAULT_USER):
        """
        Save current game and player state as json file
        """

        # Get serializable weapons payload
        weapons = []
        if self.player is not None:
            wpns, swpn = self.player.get_payload()
            for wpn in wpns:
                weapons.append(
                    {
                        "wpn_class": wpn["wpn_class"],
                        "ammo": wpn["ammo"],
                        "temp": wpn["temp"],
                    }
                )

        # Create json data structure
        jsondata = {
            username: {
                "saved": strftime("%b %d %Y %H:%M:%S %Z", gmtime()),
                "gamestate": self.gamestate,
                "highscore": self._highscore,
                "score": self.player.score,
                "lives": self.player.lives,
                "level": self.player.level,
                "shield": self.player.shield,
                "selected_wpn": swpn,
                "weapons_group": weapons,
            }
        }
        try:
            with open(STATEFILE, "w") as outfile:
                dump(jsondata, outfile)
        except OSError:
            return

    def draw_help(self):
        """
        Display series of help panels
        """

        img = self.help_images[self._doing_help - 1]
        img_rect = img.get_rect()
        img_rect.centerx = self.width / 2
        img_rect.centery = self.height / 2
        self._display_surf.blit(img, img_rect)

    def do_asteroids(self):
        """
        Create asteroid swarm at random intervals
        """

        now = pg.time.get_ticks()
        if (
            now - self._last_asteroid_storm > self._asteroid_interval
            and len(self.spacejunk_group) < 20
        ):  # Too many active sprites slows game down
            self._last_asteroid_storm = now
            for _ in range(ASTSTORM):
                ast = Asteroid(self)
                self.spacejunk_group.add(ast)
            self._asteroid_interval = randint(ASTMIN, ASTMAX)

    def do_enemies(self):
        """
        Create enemy swarm at random intervals

        Enemies will enter from random points outside the display
        area on a centre-bound trajectory. Once 'in play' they
        they will adopt their designed hunt/flee/wander behaviour
        """

        for levels in LEVELS_MATRIX:
            if levels["level"] == self.player.level:
                swarm = levels["enemy_swarm"]

        # TODO make this more sophisticated with different enemy swarms at
        # with different weapons at different levels via LEVELS_MATRIX
        now = pg.time.get_ticks()
        if len(self.enemies_group) > 0:
            self._last_enemy_storm = now
            return

        center = vec(self.width / 2, self.height / 2)

        if now - self._last_enemy_storm > self._enemy_interval:
            self._last_enemy_storm = now
            for _ in range(randint(1, ENEMYSTORM)):
                entry_pos = vec()
                entry_pos.from_polar((self.width / 2 + 1000, randint(0, 360)))
                entry_pos += center
                emy = Enemy(
                    self,
                    entry_pos,
                    maxvel=randint(1, EMY_MAX_SPEED),
                    instinct=FLEE + SEEK,
                    seek_target=self.player,
                    flee_target=self.weapons_group,
                )
                self.enemies_group.add(emy)

            self._enemy_interval = randint(ENEMYMIN, ENEMYMAX)

    def do_wreckage(self, pos, vel):
        """
        Create wreckage field from enemy hit
        """

        for img in self.wreckage_images:
            wrk = Wreckage(self, pos, vel, img)
            self.wreckage_group.add(wrk)

    def on_new_life(self):
        """
        Empty all sprite groups and reset status flags
        """

        self.weapons_group.empty()
        self.enemy_weapons_group.empty()
        self.spacejunk_group.empty()
        self.wreckage_group.empty()
        self.enemies_group.empty()
        self.supply_ship.park()
        self.doing_armoury = False
        self.doing_comms = False
        self.doing_supply = False
        self.player.docked = False

    def on_gameover(self):
        """
        Game over actions
        """

        self.set_warning("ALL YOUR BASE ARE BELONG TO US", BLUE)
        self.gamestate = GAMEOVER
        self._save_gamedata(self._username)
        if MUSVOL > 0:
            pg.mixer.music.stop()

    def on_screen(self, pos):
        """
        Check if object is within visible display area
        """

        x, y = pos
        if 0 < x < self.width and 0 < y < self.height:
            return True
        return False

    def draw_text(self, surf, text, font_size, col, x, y, align=ALIGN_CENTER):
        """
        Draw text helper function
        Returns size of drawn text surface
        """

        font = self.fonts[font_size]

        text_surface = font.render(text, True, col)
        text_rect = text_surface.get_rect()
        if align == ALIGN_LEFT:
            text_rect.topleft = (x, y)
        elif align == ALIGN_RIGHT:
            text_rect.topright = (x, y)
        elif align == ALIGN_BOTTOM:
            text_rect.midbottom = (x, y)
        elif align == ALIGN_MID:
            text_rect.center = (x, y)
        else:
            text_rect.midtop = (x, y)
        surf.blit(text_surface, text_rect)

        return font.size(text)

    def wrap_text(self, text, font_size, wrap_width):
        """
        Helper function to wrap text to specified width
        Returns array of strings each truncated where possible
        at the last space character
        """

        lines = []
        w, _ = self.fonts[font_size].size(text)
        if w <= wrap_width:
            lines.append(text)
        else:
            for i in range(len(text)):
                w, _ = self.fonts[font_size].size(text[:i])
                if w > wrap_width:
                    split = text[:i].rfind(" ")
                    if split != -1:
                        lines.append(text[:split])
                        text = text[split + 1 :]
                        i = split
                    else:
                        lines.append(text[:i])
                        text = text[i:]
            if len(text[:i]) > 0:
                lines.append(text[:i])

        return lines

    def set_warning(self, msg, col=RED, sound=False):
        """
        Sets temporary warning message
        """

        self.warning_msg = msg
        self.warning_msg_col = col
        self._last_warning = pg.time.get_ticks()
        if sound:
            self.sound_dict["warning.wav"].play()

    def draw_warning(self):
        """
        Draw temporary warning message on screen
        """

        if self.warning_msg != "":
            self.draw_text(
                self._display_surf,
                self.warning_msg,
                "lg",
                self.warning_msg_col,
                self.width / 2,
                self.height - 50,
                ALIGN_BOTTOM,
            )

    def draw_scores(self, pos):
        """
        Draw current level, score and high score
        """

        x, y = pos
        score = self.player.score
        level = self.player.level
        _, h = self.draw_text(
            self._display_surf, str(level), "md", GREEN, x, y, ALIGN_RIGHT
        )
        y += h
        _, h = self.draw_text(
            self._display_surf,
            str(score),
            "sm",
            YELLOW if score > self._orig_highscore else WHITE,
            x,
            y,
            ALIGN_RIGHT,
        )
        y += h
        _, h = self.draw_text(
            self._display_surf,
            str(self._orig_highscore),
            "sm",
            YELLOW,
            x,
            y,
            ALIGN_RIGHT,
        )

    def draw_bar(self, surf, x, y, top, lev):
        """
        Draw bar level indicator helper function
        """

        if lev < 0:
            lev = 0
        if lev / top < 0.15:
            col = RED
        elif lev / top < 0.50:
            col = ORANGE
        else:
            col = GREEN
        bar_length = 100
        bar_height = 10
        fill = int((lev / top) * (bar_length - 1))
        outline_rect = pg.Rect(x + 35, y, bar_length, bar_height)
        fill_rect = pg.Rect(x + 36, y + 1, fill, bar_height - 1)
        pg.draw.rect(surf, col, fill_rect)
        pg.draw.rect(surf, WHITE, outline_rect, 2)

    def draw_lives(self, surf, x, y):
        """
        Draw player lives icons
        """

        for i in range(self.player.lives):
            img = self.image_dict[self.player.icon]
            img_rect = img.get_rect()
            img_rect.x = x - (img_rect.width + 5) * i
            img_rect.y = y
            surf.blit(img, img_rect)

    def draw_payload(self, surf, x, y):
        """
        Draw icons for current weapons payload and indicate currently selected weapon
        """

        wpns, swpn = self.player.get_payload()
        for count, wpn in enumerate(wpns):
            wpn_class = wpn["wpn_class"]
            img = self.image_dict[globals()[wpn_class].image]
            img = pg.transform.rotate(img, 90)
            img_rect = img.get_rect()
            img_rect.left, img_rect.top = x + 35, y
            surf.blit(img, img_rect)
            if count == swpn:
                draw_triangle(surf, "right", 10, YELLOW, (20, y + img_rect.height / 2))
            y += img_rect.height + 2

    def out_of_play(self, pos):
        """
        Check if object is beyond nominal playing range
        """

        centre = vec(self.width / 2, self.height / 2)
        if pos.distance_to(centre) > self.in_play_range:
            return True
        return False
