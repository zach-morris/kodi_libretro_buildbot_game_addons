"""
Pygame output for SNES Audio.
"""

import pygame
import struct
import ctypes

from .retro_globals import HACK_need_audio_sample_batch

g_stereo_channels = 2
g_sizeof_int16 = 2
g_num_samples = 512

# 512 stereo samples of 16-bits each
g_sound_size = g_num_samples * g_stereo_channels * g_sizeof_int16

# arbitrarily chosen maximum buffer length - in case the playback can't keep up
g_buffer_max = 16384

g_buffer = b''
g_channel = None


def _enqueue_sound(snd):
    global g_channel
    if g_channel:
        g_channel.queue(snd)


def pygame_mixer_init(core):
    global g_channel
    if not pygame.mixer.get_init():
        freq = int(core.get_av_info()['sample_rate'] or 32040)
        pygame.mixer.init(frequency=freq, size=-16, channels=g_stereo_channels,
                          buffer=g_num_samples)
        g_channel = pygame.mixer.Channel(0)
        g_channel.set_volume(0.5)


def set_audio_sample_cb(core, callback=_enqueue_sound):
    """
    Sets the callback that will handle updated audio samples.

    Unlike core.EmulatedSNES.set_audio_sample_cb, the callback passed to this
    function should accept only one parameter:

        "snd" is an instance of pygame.mixer.Sound containing the last 512
        samples.

    If no callback function is provided, the default implementation of
    snd.play() is used.
    """
    pygame_mixer_init(core)

    stereo_struct = struct.Struct('<hh')

    def wrapper(left, right):
        global g_buffer, g_sound_size

        if len(g_buffer) > g_buffer_max:
            g_buffer = b''

        g_buffer += stereo_struct.pack(left, right)

        if len(g_buffer) >= g_sound_size:
            callback(pygame.mixer.Sound(buffer=g_buffer[:g_sound_size]))
            g_buffer = g_buffer[g_sound_size:]

    core.set_audio_sample_cb(wrapper)


def set_audio_sample_batch_cb(core, callback=_enqueue_sound):
    """
    Sets the callback that will handle updated audio samples.

    Unlike core.EmulatedSNES.set_audio_sample_cb, the callback passed to this
    function should accept only one parameter:

        "snd" is an instance of pygame.mixer.Sound containing the last 512
        samples.

    If no callback function is provided, the default implementation of
    snd.play() is used.
    """
    pygame_mixer_init(core)

    def wrapper(data, frames):
        global g_buffer, g_sound_size, g_buffer_max

        if len(g_buffer) > g_buffer_max:
            g_buffer = b''

        g_buffer += ctypes.string_at(data, frames * g_sizeof_int16 * g_stereo_channels)

        if len(g_buffer) >= g_sound_size:
            callback(pygame.mixer.Sound(buffer=g_buffer[:g_sound_size]))
            g_buffer = g_buffer[g_sound_size:]

        return frames

    core.set_audio_sample_batch_cb(wrapper)


def set_audio_sample_internal(core):
    if core.name in HACK_need_audio_sample_batch:
        set_audio_sample_batch_cb(core)
    else:
        set_audio_sample_cb(core)
