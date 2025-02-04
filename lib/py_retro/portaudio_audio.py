"""
PortAudio output for SNES Audio.
"""

import pyaudio
import ctypes
import struct
import time

from .retro_globals import HACK_need_audio_sample_batch

g_pyaudio = None
g_stream = None

g_buffer = b''

g_sizeof_int16 = 2
g_stereo_channels = 2

# arbitrarily chosen maximum buffer length - in case the playback can't keep up
g_buffer_max = 16384

# to be adjusted if g_buffer_max is met
g_freq = None


def _consume(in_data, frame_count, time_info, status):
    global g_buffer
    size = frame_count * g_sizeof_int16 * g_stereo_channels
    while len(g_buffer) < size:
        time.sleep(0)
    data, g_buffer = g_buffer[:size], g_buffer[size:]
    return data, pyaudio.paContinue


def _transpose_frequency():
    """
    re-initialize the stream, transposed up by a fortieth of a (musical) step such that the consumer
    might keep up with the sample producer by running a bit faster. yes, this is a bit of a hack.
    """
    global g_pyaudio, g_stream, g_buffer, g_freq
    g_freq = int(g_freq * 2 ** (1/12 / 20))
    g_buffer = b''
    print('buffer overrun, adjusting frequency to', g_freq, 'Hz')
    g_stream.close()
    g_stream = g_pyaudio.open(format=pyaudio.paInt16, channels=2, rate=g_freq, output=True,
                              stream_callback=_consume)
    g_stream.start_stream()


def pyaudio_init(core):
    global g_pyaudio, g_stream, g_freq
    if g_pyaudio is None:
        g_freq = int(core.get_av_info()['sample_rate']) or 32040
        g_pyaudio = pyaudio.PyAudio()
        g_stream = g_pyaudio.open(format=pyaudio.paInt16, channels=g_stereo_channels, rate=g_freq,
                                  output=True, stream_callback=_consume)
        g_stream.start_stream()


def set_audio_sample_cb(core):
    pyaudio_init(core)
    stereo_struct = struct.Struct('<hh')

    def wrapper(left, right):
        global g_buffer, g_buffer_max
        if len(g_buffer) < g_buffer_max:
            g_buffer += stereo_struct.pack(left, right)
        else:
            _transpose_frequency()

    core.set_audio_sample_cb(wrapper)


def set_audio_sample_batch_cb(core):
    pyaudio_init(core)

    def wrapper(data, frames):
        global g_buffer, g_buffer_max
        if len(g_buffer) < g_buffer_max:
            g_buffer += ctypes.string_at(data, frames * g_sizeof_int16 * g_stereo_channels)
        else:
            _transpose_frequency()
        return frames

    core.set_audio_sample_batch_cb(wrapper)


def set_audio_sample_internal(core):
    if core.name in HACK_need_audio_sample_batch:
        set_audio_sample_batch_cb(core)
    else:
        set_audio_sample_cb(core)
