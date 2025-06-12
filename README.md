# SpaceHunter

 Python arcade-style space shooter game written entirely in pygame.


![app screenshot](https://github.com/semuadmin/spacehunter/blob/main/images/screenshot.png?raw=true)

## Current Status

# WORK IN PROGRESS

![Status](https://img.shields.io/pypi/status/spacehunter)
![GitHub Release](https://img.shields.io/github/v/release/semuadmin/spacehunter?include_prereleases)
![Build](https://img.shields.io/github/actions/workflow/status/semuadmin/spacehunter/main.yml?branch=main)
![Release Date](https://img.shields.io/github/release-date-pre/semuadmin/spacehunter)
![Last Commit](https://img.shields.io/github/last-commit/semuadmin/spacehunter)
![Contributors](https://img.shields.io/github/contributors/semuadmin/spacehunter.svg)
![Open Issues](https://img.shields.io/github/issues-raw/semuadmin/spacehunter)

Just a bit of fun with pygame. An attempt to create an simple arcade-style 2D space shooter with **real-world physics**, responsive enemy interactions and cool weapons.

It's still a work in progress, but is quite fun to play (with a suitable joystick) and is offered here for anyone who feels like taking it on for further development for just for yuks.

Developed using VSCode with the Python extension.

## <a name="installation">Installation</a>

`spacehunter` is compatible with Python 3.9 - 3.13. In the following, `python3` & `pip` refer to the Python 3 executables. You may need to substitute `python` for `python3`, depending on your particular environment (*on Windows it's generally `python`*).

**All platforms**:

- It is recommended to use the latest official Python.org installation package for your platform, rather than any pre-installed version.
- It is recommended that the Python 3 binaries and site_packages directories are included in your PATH (most standard Python 3 installation packages will do this automatically if you select the 'Add to PATH' option during installation).
- Recommended multi-platform joystick controller - [8BitDo SN30 Pro+](https://www.8bitdo.com/sn30-pro-g-classic-or-sn30-pro-sn/). The joystick controller assignments can be configured via `spacehunterconfig.json`.
- Game state is saved in `gamestate.json`.

To install (requires `build`, `setuptools` and `wheel` packages):

*If you don't have git, simply [download the zip file](https://github.com/semuadmin/SpaceHunter/archive/refs/heads/main.zip) and extract to a folder named SpaceHunter*.


```shell
python3 -m pip install build wheel setuptools
git clone https://github.com/semuadmin/SpaceHunter.git
cd SpaceHunter
python3 -m build . --wheel
cd dist
python3 -m pip install spacehunter-0.2.0-py3-none-any.whl
```

To run, type:

```shell
spacehunter
```

Or alternatively:

```shell
python3 -m spacehunter
```

## Gameplay

**Basic gameplay:**

- **Press H at any time to display Help. Press H repeatedly to scroll through Help pages**.
- **Press P to Pause**
- **Press Q to Quit**
- You're a lone spaceship out in deep space and you have to fend off hazards from asteroids and hostile spaceships.
- You score points for destroying asteroids and other space junk (the smaller and faster the target, the higher the score). But be careful - the debris from destroyed asteroids is itself a hazard!
- You score points for hitting or destroying hostile spaceships (the more powerful the hostile, the higher the score).
- The points you acquire allow you to replenish your ammunition or purchase more powerful and sophisticated weapons.
- Your ship has a defensive energy field but this is depleted if you're hit by asteroids, debris or enemy weapons.
- Your ship has multiple weapon bays, each of which can accommodate a variety of weapon types, but only one is occupied at the start of the game.
- You have a radar screen (with selectable range) which shows you the location and direction of incoming hazards. The radar will flash red when a hostile spaceship comes into range.
- Hostile spaceships can track and home into your location, but will normally retreat temporarily if they're fired upon. Be warned - some hostiles are more agile and/or aggressive than others.
- You can pause or save/quit a game at any point, and reload a saved game at a later date.
- You have 3 'lives'.

**Piloting the spaceship:**

- Your main engine and control thrusters allow you to accelerate and rotate in any direction, but **the laws of inertial physics apply**. In other words, if you fire the engine or thruster in a certain direction, you will continue to move or accelerate in that direction until you apply thrust in the opposite direction, or until your ship's inertial dampers eventually kill your velocity. This takes some getting used to.

**Weaponry:**

- At the start, your only weapon is a relatively low-powered laser, which automatically recharges slowly in the background. Caution - you need to actively select this weapon before using it.
- If you're running low on ammunition or need a more sophisticated weapon, and have a sufficient point score, you can summon a nearby weapon supply ship.
- The supply ship will automatically home into your location. When it arrives, you must dock with it (having first ensured all nearby hostiles are destroyed and your weapons are disabled). Once docked, you have access to the supply ship's armoury which contains a variety of weapon types. The more powerful the weapon, the higher the cost.
  1. Laser - a low-powered pulse energy weapon.
  1. Ultralaser - a higher-powered pulse energy weapon.
  1. Gatling gun - a kinetic-energy weapon with a high rate of fire but limited ammunition capacity.
  1. Missile - a dumb but powerful unguided missile.
  1. Sidewinder - a smart guided missile which will automatically home in on the nearest enemy spaceship. Can be fired beyond visual range.
  1. Mine - a proximity-triggered explosive device which can be deployed at a specific location (remember to kill your velocity before deploying, or the mine will simply fly off in whatever direction you happened to be heading in).
- Once you've replenished your arsenal, you can undock from the supply ship and continue on your way.
- Note that some weapons can overheat if they're fired continuously for more than a few seconds - you'll need to wait for them to cool off before firing again.

## Attributions and Acknowledgements

Object-orientated program structure originally based on:

* [Pygame Tutorials](http://pygametutorials.wikidot.com/tutorials-basic)
* Public domain

Graphics from:

* [opengameart.org](http://opengameart.org/content/space-shooter-redux)
* CC0 1.0 Universal Public Domain Dedication

## License

BSD 2-Clause License.

Copyright (c) 2020, semuadmin (aka steely_eyed_missile_man).

All rights reserved.

## To Do

* maybe generic way to load images and sounds from file directories
* fix collision scoring and damage - every collidable object should have a 'damage' attribute
* do armoury costing
* maybe rationalise spacejunk classes
* enemy shooting behaviour
* more enemy classes
* levels

