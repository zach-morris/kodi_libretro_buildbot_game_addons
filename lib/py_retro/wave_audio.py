"""
WAV-file output for libretro Audio.
"""

import wave
import ctypes
import struct


def open_wave(core, filenameOrHandle):
    res = wave.open(filenameOrHandle, "wb")
    res.setnchannels(2)
    res.setsampwidth(2)
    res.setframerate(core.get_av_info()['sample_rate'] or 32040)
    res.setcomptype('NONE', 'not compressed')
    return res


def set_audio_sink(core, filenameOrHandle):
    """
    Records audio to the given .wav file.

    "core" should be an instance of core.EmulatedSystem.

    "filenameOrHandle" should be either a string representing the filename
    where audio data should be written, or a file-handle opened in "wb" mode.

    Audio data will be written to the given file as a 16-bit stereo
    .wav file, using the 'wave' module from the Python standard library.

    Returns the wave.Wave_write instance used to write the audio.
    """
    res = open_wave(core, filenameOrHandle)
    sndstruct = struct.Struct('<hh')

    def wrapper(left, right):
        # We can safely use .writeframesraw() here because the header will be
        # corrected once we call .close()
        res.writeframesraw(sndstruct.pack(left, right))

    core.set_audio_sample_cb(wrapper)
    return res


def set_audio_sink_batch(core, filenameOrHandle):
    """
    Records audio to the given .wav file.

    "core" should be an instance of core.EmulatedSystem.

    "filenameOrHandle" should be either a string representing the filename
    where audio data should be written, or a file-handle opened in "wb" mode.

    Audio data will be written to the given file as a 16-bit stereo
    .wav file, using the 'wave' module from the Python standard library.

    Returns the wave.Wave_write instance used to write the audio.
    """
    res = open_wave(core, filenameOrHandle)

    def wrapper(data, frames):
        # We can safely use .writeframesraw() here because the header will be
        # corrected once we call .close()
        size = frames * res.getnchannels() * res.getsampwidth()
        res.writeframesraw(ctypes.string_at(data, size)[:size])
        return frames

    core.set_audio_sample_batch_cb(wrapper)
    return res
