import pygame

from .retro_globals import *

MAP_NONE = 0
MAP_BTN = 1
MAP_AXIS = 2
MAP_HAT = 3


class joymapping:
    map_type = 0  # see enum above
    map_index = 0  # index within the device of the button/axis/hat
    extra = 0  # the SDL_HAT_x map for hats. for axes, +1 or -1 for positive or negative only.


maptypes = {
    'a': MAP_AXIS,
    'b': MAP_BTN,
    'h': MAP_HAT,
    'n': MAP_NONE,
}

hatdirs = {
    'c': (0, 0),
    'u': (0, 1),
    'r': (1, 0),
    'd': (0, -1),
    'l': (-1, 0),
    'ru': (1, 1),
    'ur': (1, 1),
    'rd': (1, -1),
    'dr': (1, -1),
    'lu': (-1, 1),
    'ul': (-1, 1),
    'ld': (-1, -1),
    'dl': (-1, -1),
}

MAX_PLAYERS = 8
MAX_MAPPINGS = 20

padcache = [[0] * MAX_MAPPINGS for i in range(MAX_PLAYERS)]
joy_mappings = [[joymapping() for i in range(MAX_MAPPINGS)] for j in range(MAX_PLAYERS)]
sdl_joy = [None] * MAX_PLAYERS
num_players = 0


def input_poll_cb():
    global padcache, joy_mappings, sdl_joy, num_players

    for player in range(num_players):
        if sdl_joy[player]:
            for m in range(MAX_MAPPINGS):
                idx = joy_mappings[player][m].map_index
                if joy_mappings[player][m].map_type == MAP_NONE:
                    continue
                elif joy_mappings[player][m].map_type == MAP_BTN:
                    if 0 <= idx < sdl_joy[player].get_numbuttons():
                        padcache[player][m] = int(sdl_joy[player].get_button(idx))
                elif joy_mappings[player][m].map_type == MAP_AXIS:
                    if 0 <= idx < sdl_joy[player].get_numaxes():
                        padcache[player][m] = int(32767 * sdl_joy[player].get_axis(idx))
                        if padcache[player][m] * joy_mappings[player][m].extra < 0:
                            padcache[player][m] = 0
                elif joy_mappings[player][m].map_type == MAP_HAT:
                    if 0 <= idx < sdl_joy[player].get_numhats():
                        hat = sdl_joy[player].get_hat(idx)
                        padcache[player][m] = int(hat == joy_mappings[player][m].extra)


def input_state_cb(port, device, index, id):
    global padcache
    return padcache[port][id]


def set_input_poll_joystick(core, mapping=None, joyindex=0, player=0):
    if mapping is None:
        # default map suitable for xpad on linux
        mapping = {
            DEVICE_ID_JOYPAD_B: ('b', 0),
            DEVICE_ID_JOYPAD_Y: ('b', 2),
            DEVICE_ID_JOYPAD_SELECT: ('b', 6),
            DEVICE_ID_JOYPAD_START: ('b', 7),
            DEVICE_ID_JOYPAD_UP: ('h', 0, 'u'),
            DEVICE_ID_JOYPAD_DOWN: ('h', 0, 'd'),
            DEVICE_ID_JOYPAD_LEFT: ('h', 0, 'l'),
            DEVICE_ID_JOYPAD_RIGHT: ('h', 0, 'r'),
            DEVICE_ID_JOYPAD_A: ('b', 1),
            DEVICE_ID_JOYPAD_X: ('b', 3),
            DEVICE_ID_JOYPAD_L: ('b', 4),
            DEVICE_ID_JOYPAD_R: ('b', 5),
            DEVICE_ID_JOYPAD_L2: ('a', 2, +1),
            DEVICE_ID_JOYPAD_R2: ('a', 5, +1),
            DEVICE_ID_JOYPAD_L3: ('b', 9),
            DEVICE_ID_JOYPAD_R3: ('b', 10),
            (DEVICE_INDEX_ANALOG_LEFT, DEVICE_ID_ANALOG_X): ('a', 0, 0),
            (DEVICE_INDEX_ANALOG_LEFT, DEVICE_ID_ANALOG_Y): ('a', 1, 0),
            (DEVICE_INDEX_ANALOG_RIGHT, DEVICE_ID_ANALOG_X): ('a', 3, 0),
            (DEVICE_INDEX_ANALOG_RIGHT, DEVICE_ID_ANALOG_Y): ('a', 4, 0),
        }
    global joy_mappings, sdl_joy, num_players

    if player >= MAX_PLAYERS: return

    for k, v in list(mapping.items()):
        if type(k) is tuple:
            stick, axis = k
            k = 16 | (stick << 1) | axis  # hack!
        joy_mappings[player][k].map_type = maptypes[v[0]]
        joy_mappings[player][k].map_index = v[1]
        joy_mappings[player][k].extra = 0
        if len(v) > 2:
            if v[0] == 'h':
                joy_mappings[player][k].extra = hatdirs[v[2]]
            else:
                joy_mappings[player][k].extra = v[2]

    pygame.joystick.init()
    sdl_joy[player] = pygame.joystick.Joystick(joyindex)
    sdl_joy[player].init()

    # if this is the first call
    if not num_players:
        core.set_input_poll_cb(input_poll_cb)
        core.set_input_state_cb(input_state_cb)

    if num_players <= player:
        num_players = player + 1
