import ctypes

import collections
from .game_info_reader import GameInfoReader

from .retro_globals import *

debug = False


def null_video_refresh(data, width, height, pitch):
    global debug
    if debug:
        print(('video_refresh({}, {}, {}, {})'.format(data, width, height, pitch)))


def null_audio_sample(left, right):
    global debug
    if debug:
        print(('audio_sample({}, {})'.format(left, right)))


def null_audio_sample_batch(data, frames):
    global debug
    if debug:
        print(('audio_sample_batch({}, {})'.format(data, frames)))
    return frames


def null_input_poll():
    global debug
    if debug:
        print('input_poll()')


def null_input_state(port, device, index, id_):
    global debug
    if debug:
        print(('input_state({}, {}, {}, {})'.format(port, device, index, id_)))
    return 0


class LowLevelWrapper(ctypes.CDLL):
    def __init__(self, libpath):
        ctypes.CDLL.__init__(self, libpath)

        self.retro_set_environment.restype = None
        self.retro_set_environment.argtypes = [retro_environment_t]

        self.retro_set_video_refresh.restype = None
        self.retro_set_video_refresh.argtypes = [retro_video_refresh_t]

        self.retro_set_audio_sample.restype = None
        self.retro_set_audio_sample.argtypes = [retro_audio_sample_t]

        self.retro_set_audio_sample_batch.restype = None
        self.retro_set_audio_sample_batch.argtypes = [retro_audio_sample_batch_t]

        self.retro_set_input_poll.restype = None
        self.retro_set_input_poll.argtypes = [retro_input_poll_t]

        self.retro_set_input_state.restype = None
        self.retro_set_input_state.argtypes = [retro_input_state_t]

        self.retro_init.restype = None
        self.retro_init.argtypes = []

        self.retro_deinit.restype = None
        self.retro_deinit.argtypes = []

        self.retro_api_version.restype = ctypes.c_uint
        self.retro_api_version.argtypes = []

        self.retro_get_system_info.restype = None
        self.retro_get_system_info.argtypes = [ctypes.POINTER(retro_system_info)]

        self.retro_get_system_av_info.restype = None
        self.retro_get_system_av_info.argtypes = [ctypes.POINTER(retro_system_av_info)]

        self.retro_set_controller_port_device.restype = None
        self.retro_set_controller_port_device.argtypes = [ctypes.c_uint, ctypes.c_uint]

        self.retro_reset.restype = None
        self.retro_reset.argtypes = []

        self.retro_run.restype = None
        self.retro_run.argtypes = []

        self.retro_serialize_size.restype = ctypes.c_size_t
        self.retro_serialize_size.argtypes = []

        self.retro_serialize.restype = ctypes.c_bool
        self.retro_serialize.argtypes = [ctypes.c_void_p, ctypes.c_size_t]

        self.retro_unserialize.restype = ctypes.c_bool
        self.retro_unserialize.argtypes = [ctypes.c_void_p, ctypes.c_size_t]

        self.retro_cheat_reset.restype = None
        self.retro_cheat_reset.argtypes = []

        self.retro_cheat_set.restype = None
        self.retro_cheat_set.argtypes = [ctypes.c_uint, ctypes.c_bool, ctypes.c_char_p]

        self.retro_load_game.restype = ctypes.c_bool
        self.retro_load_game.argtypes = [ctypes.POINTER(retro_game_info)]

        self.retro_load_game_special.restype = ctypes.c_bool
        self.retro_load_game_special.argtypes = [ctypes.c_uint,
                                                 ctypes.POINTER(retro_game_info),
                                                 ctypes.c_size_t]

        self.retro_unload_game.restype = None
        self.retro_unload_game.argtypes = []

        self.retro_get_region.restype = ctypes.c_uint
        self.retro_get_region.argtypes = []

        self.retro_get_memory_data.restype = ctypes.c_void_p
        self.retro_get_memory_data.argtypes = [ctypes.c_uint]

        self.retro_get_memory_size.restype = ctypes.c_size_t
        self.retro_get_memory_size.argtypes = [ctypes.c_uint]

        # set "retro_"-less aliases for brevity
        self.set_environment = self.retro_set_environment
        self.set_video_refresh = self.retro_set_video_refresh
        self.set_audio_sample = self.retro_set_audio_sample
        self.set_audio_sample_batch = self.retro_set_audio_sample_batch
        self.set_input_poll = self.retro_set_input_poll
        self.set_input_state = self.retro_set_input_state
        self.init = self.retro_init
        self.deinit = self.retro_deinit
        self.api_version = self.retro_api_version
        self.get_system_info = self.retro_get_system_info
        self.get_system_av_info = self.retro_get_system_av_info
        self.set_controller_port_device = self.retro_set_controller_port_device
        self.reset = self.retro_reset
        self.run = self.retro_run
        self.serialize_size = self.retro_serialize_size
        self.serialize = self.retro_serialize
        self.unserialize = self.retro_unserialize
        self.cheat_reset = self.retro_cheat_reset
        self.cheat_set = self.retro_cheat_set
        self.load_game = self.retro_load_game
        self.load_game_special = self.retro_load_game_special
        self.unload_game = self.retro_unload_game
        self.get_region = self.retro_get_region
        self.get_memory_data = self.retro_get_memory_data
        self.get_memory_size = self.retro_get_memory_size


class EmulatedSystem:
    _video_refresh_wrapper = None
    _audio_sample_wrapper = None
    _audio_sample_batch_wrapper = None
    _input_poll_wrapper = None
    _input_state_wrapper = None
    _environment_wrapper = None

    def __init__(self, libpath):
        self._game_loaded = False
        # todo: move libpath to a temp file and load that, for multithread
        self.llw = LowLevelWrapper(libpath)
        self.name = self.get_library_info()['name']
        self._reset_vars()
        self.set_null_callbacks()
        self.llw.init()
        self.av_info = retro_system_av_info()
        self.av_info_changed = True
        # simple default WRAM-only address space if the env isn't called
        self.memory_map = collections.OrderedDict()

    # is it okay to assign an audio_sample_batch and replace it with an
    # audio_sample afterward?

    def _reset_vars(self):
        self._loaded_cheats = {}
        self._game_loaded = False
        self.env_props = {}
        self.env_vars = {}
        # HACK: just put this in for software frames 'til we support SET_HW_RENDER
        # self.env_vars[b'parallel-n64-gfxplugin'] = b'angrylion'

    def __del__(self):
        self.llw.deinit()

    def _reload_cheats(self):
        """ Internal method.
        Reloads cheats in the emulated console from the _loaded_cheats variable.
        """
        self.llw.cheat_reset()
        for index, (code, enabled) in list(self._loaded_cheats.items()):
            self.llw.cheat_set(index, enabled, code)

    def _find_memory_bank(self, offset, length, bank_switch):
        if not self.memory_map:
            mem_size = self.llw.get_memory_size(MEMORY_WRAM)
            mem_data = self.llw.get_memory_data(MEMORY_WRAM)
            self.memory_map[(0, mem_size)] = mem_data
        for (begin, end), pointer in self.memory_map.items():
            if begin <= offset < end:
                if offset + length > end:
                    raise IndexError(f'({hex(offset)}, {hex(length)}) '
                                     f'overruns ({hex(begin)}, {hex(end)}) memory bank')
                bank_size = end - begin
                relative_offset = offset - begin + (bank_size * bank_switch)
                return pointer + relative_offset
        raise IndexError(f'({hex(offset)}, {hex(length)}) '
                         'address range not found in any memory map region')

    def peek_memory_region(self, offset, length, bank_switch=0):
        pointer = self._find_memory_bank(offset, length, bank_switch)
        buffer = ctypes.create_string_buffer(length)
        ctypes.memmove(buffer, pointer, length)
        return buffer.raw

    def poke_memory_region(self, offset, data, bank_switch=0):
        pointer = self._find_memory_bank(offset, len(data), bank_switch)
        ctypes.memmove(pointer, data, len(data))

    def memory_to_string(self, mem_type):
        """
        Copies data from the given libretro memory buffer into a new string.
        """
        mem_size = self.llw.get_memory_size(mem_type)
        mem_data = self.llw.get_memory_data(mem_type)

        if mem_size == 0:
            return None

        buf = ctypes.create_string_buffer(mem_size)
        ctypes.memmove(buf, mem_data, mem_size)

        return buf.raw

    def string_to_memory(self, data, mem_type):
        """
        Copies the given data into the libretro memory buffer of the given type.
        """
        mem_size = self.llw.get_memory_size(mem_type)
        mem_data = self.llw.get_memory_data(mem_type)

        if len(data) != mem_size:
            raise Exception(
                "This game requires {} bytes of memory type {}, not {} bytes".format(
                    mem_size, mem_type, len(data)
                )
            )
        ctypes.memmove(mem_data, data, mem_size)

    def _require_game_loaded(self):
        """ Raise an exception if a game is not loaded. """
        if not self._game_loaded:
            raise Exception("This method requires that a game be loaded!")

    def _require_game_not_loaded(self):
        """ Raise an exception if a game is already loaded. """
        if self._game_loaded:
            raise Exception("This method requires that no game be loaded!")

    def set_controller_port_device(self, port, device):
        """ Connects the given device to the given controller port.

        Connecting a device to a port implicitly removes any device previously
        connected to that port. To remove a device without connecting a new
        one, pass DEVICE_NONE as the device parameter. From this point onward,
        the callback passed to set_input_state_cb() will be called with the
        appropriate device, index and id parameters.

        Whenever you call a load_game_* function a DEVICE_JOYPAD will be
        connected to both ports, and devices previously connected using this
        function will be disconnected.
        """
        self.llw.set_controller_port_device(port, device)

    def reset(self):
        """ Press the reset button on the emulated console.
        Requires that a game be loaded.
        """
        self._require_game_loaded()
        self.llw.reset()

    def run(self, frames=1):
        """ Run the emulated console for a given number of frames (default 1).
        Before this function returns, the registered callbacks will be called
        at least once each.
        Requires that a game be loaded.
        """
        self._require_game_loaded()
        while frames > 0:
            frames -= 1
            self.llw.run()

    def unload(self):
        """ Remove the game and return its non-volatile storage contents.

        Returns a list with an entry for each MEMORY_* constant in
        VALID_MEMORY_TYPES. If the current game uses that type of storage,
        the corresponding index in the list will be a string containing the
        storage contents, which can later be passed to load_game_*.
        Otherwise, the corresponding index is None.

        Requires that a game be loaded.
        """
        VALID_MEMORY_TYPES = [MEMORY_SAVE_RAM, MEMORY_RTC]

        self._require_game_loaded()

        res = [self.memory_to_string(t) for t in VALID_MEMORY_TYPES]

        self.llw.unload_game()
        self._reset_vars()

        return res

    def get_refresh_rate(self):
        """ Return the intended refresh-rate of the loaded game. """
        self._require_game_loaded()
        return float(self.av_info.timing.fps)

    def serialize(self):
        """ Serializes the state of the emulated console to a string.
        Requires that a game be loaded.
        """
        size = self.llw.serialize_size()
        buf = ctypes.create_string_buffer(size)
        res = self.llw.serialize(ctypes.cast(buf, ctypes.c_void_p), size)
        if not res:
            raise Exception("problem in serialize")
        return buf.raw

    def unserialize(self, state):
        """ Restores the state of the emulated console from a string.
        Note that the game's SRAM data is part of the saved state.
        Requires that the same game that was loaded when serialize was
        called, be loaded before unserialize is called.
        """
        res = self.llw.unserialize(ctypes.cast(state, ctypes.c_void_p), len(state))
        if not res:
            raise Exception("problem in unserialize")

    def cheat_add(self, index, code, enabled=True):
        """ Stores the given cheat code at the given index in the cheat list.
        "index" must be an integer. Only one cheat can be stored per index.
        "code" must be a string containing one or more codes delimited by '+'.
        "enabled" must be a boolean describing whether the cheat code is active.
        """
        self._loaded_cheats[index] = (code, enabled)
        self._reload_cheats()

    def cheat_remove(self, index):
        """ Removes the cheat at the given index from the cheat list.
        "index" must be an integer previously passed to cheat_add.
        """
        del self._loaded_cheats[index]
        self._reload_cheats()

    def cheat_set_enabled(self, index, enabled):
        """ Enables or disables the cheat at the given index in the cheat list.
        "index" must be an integer previously passed to cheat_add.
        "enabled" must be a boolean describing whether the cheat code is active.
        """
        code, _ = self._loaded_cheats[index]
        self._loaded_cheats[index] = (code, enabled)
        self._reload_cheats()

    def cheat_is_enabled(self, index):
        """ Returns true if the cheat at the given index is enabled.
        "index" must be an integer previously passed to cheat_add.
        """
        _, enabled = self._loaded_cheats[index]
        return enabled

    def load_game_normal(self, data=None, sram=None, rtc=None, path=None, get_data_from_path=True):
        """ Load an ordinary game into the emulated console.
        "data" should be a string containing the raw game image.
            If None, you must provide 'path'.
        "sram" should be a string containing the persistent SRAM data.
            If None, the game will be given an empty SRAM to start.
        "rtc" should be a string containing the real-time-clock data.
            If None, the game will be given a fresh, blank RTC region.
        "path" should be a string containing the file path to the game.
            If None, you must provide 'data'.
        "get_data_from_path" will read the file into 'data' if 'data' is None.
        """
        self._require_game_not_loaded()

        gameinfo = retro_game_info()
        sysinfo = retro_system_info()

        self.llw.get_system_info(ctypes.byref(sysinfo))

        if path:
            if isinstance(path, str):
                path = path.encode('utf-8')

            gameinfo.path = ctypes.cast(path, ctypes.c_char_p)
            if get_data_from_path and not data:
                data = open(path, 'rb').read()

        elif sysinfo.need_fullpath:
            raise Exception('The loaded libretro needs a full path to the ROM')

        if data:
            gameinfo.data = ctypes.cast(data, ctypes.c_void_p)
            gameinfo.size = len(data)
        elif not path:
            raise Exception('Must provide either file path or raw loaded game!')

        self.llw.load_game(ctypes.byref(gameinfo))
        self.llw.get_system_av_info(ctypes.byref(self.av_info))
        # get useful info about the game from the rom's header
        # self.gameinfo = GameInfoReader().get_info(data, self.name)
        self._game_loaded = True

        if sram:
            self.string_to_memory(sram, MEMORY_SAVE_RAM)
        if rtc:
            self.string_to_memory(rtc, MEMORY_RTC)

    def get_library_info(self):
        info = retro_system_info()
        self.llw.get_system_info(ctypes.byref(info))
        return {
            'api': int(self.llw.api_version()),
            'name': info.library_name.decode("utf-8"),
            'ver': info.library_version.decode("utf-8"),
            'exts': info.valid_extensions.decode("utf-8"),
        }

    def get_av_info(self):
        self._require_game_loaded()
        self.av_info_changed = False
        return {
            'base_size': (
                int(self.av_info.geometry.base_width), int(self.av_info.geometry.base_height)
            ),
            'max_size': (
                int(self.av_info.geometry.max_width), int(self.av_info.geometry.max_height)
            ),
            'aspect_ratio': float(self.av_info.geometry.aspect_ratio),
            'fps': float(self.av_info.timing.fps),
            'sample_rate': float(self.av_info.timing.sample_rate),
        }

    def close(self):
        """ Release all resources associated with this library instance. """
        self.llw.deinit()
        self._video_refresh_wrapper = None
        self._audio_sample_wrapper = None
        self._audio_sample_batch_wrapper = None
        self._input_poll_wrapper = None
        self._input_state_wrapper = None
        self._environment_wrapper = None

    def set_video_refresh_cb(self, callback):
        """ Sets the callback that will handle updated video frames.
        The callback should accept the following parameters:
            "data" is a pointer to the top-left of an array of pixels.
            "width" is the number of pixels in each row of the frame.
            "height" is the number of pixel-rows in the frame.
            "pitch" is the number of bytes between the start of each row.
        The callback should return nothing.
        """
        self._video_refresh_wrapper = retro_video_refresh_t(callback)
        self.llw.set_video_refresh(self._video_refresh_wrapper)

    def set_audio_sample_cb(self, callback):
        """ Sets the callback that will handle updated audio frames.
        The callback should accept the following parameters:
            "left" is an int16 that specifies the left audio channel volume.
            "right" is an int16 that specifies the right audio channel volume.
        The callback should return nothing.
        """
        if self.name in HACK_need_audio_sample_batch:
            def sample_in_terms_of_batch(data, frames):
                for i in range(frames):
                    callback(data[i * 2], data[i * 2 + 1])
                return frames

            self.set_audio_sample_batch_cb(sample_in_terms_of_batch)
        else:
            self._audio_sample_wrapper = retro_audio_sample_t(callback)
            self.llw.set_audio_sample(self._audio_sample_wrapper)

    def set_audio_sample_batch_cb(self, callback):
        """ Sets the callback that will handle updated audio frames.
        The callback should accept the following parameters:
            "data" is an int16* containing stereo audio sample data
            "frames" is a size_t that specifies the number of {l,r} samples.
        The callback should return nothing.
        """
        if self.name in HACK_need_audio_sample:
            # noinspection PyUnresolvedReferences
            def batch_in_terms_of_sample(left, right):
                f = batch_in_terms_of_sample
                f.arr[f.i * 2] = left
                f.arr[f.i * 2 + 1] = right
                f.i += 1
                if f.i >= 512:
                    res = callback(f.arr, f.i)
                    f.i -= res if res else f.i

            batch_in_terms_of_sample.arr = (ctypes.c_int16 * (512 * 2))()
            batch_in_terms_of_sample.i = 0
            self.set_audio_sample_cb(batch_in_terms_of_sample)
        else:
            self._audio_sample_batch_wrapper = retro_audio_sample_batch_t(callback)
            self.llw.set_audio_sample_batch(self._audio_sample_batch_wrapper)

    def set_input_poll_cb(self, callback):
        """ Sets the callback that will check for updated input events.
        The callback should accept no parameters and return nothing.
        It should just read new input events and store them somewhere so they
        can be returned by the input state callback.
        """
        self._input_poll_wrapper = retro_input_poll_t(callback)
        self.llw.set_input_poll(self._input_poll_wrapper)

    def set_input_state_cb(self, callback):
        """ Sets the callback that reports the current state of input devices.
        The callback should accept the following parameters:
            "port" is an int describing which controller port is being reported.
            "device" a DEVICE_* constant specifying the device type.
            "index" is a number specifying a device on a multitap.
            "id" is a DEVICE_ID_* constant specifying the button or axis.
        If "id" represents an analogue input (such as DEVICE_ID_MOUSE_X and
        DEVICE_ID_MOUSE_Y), you should return a value between -32768 and 32767.
        """
        self._input_state_wrapper = retro_input_state_t(callback)
        self.llw.set_input_state(self._input_state_wrapper)

    def set_environment_cb(self, callback):
        self._environment_wrapper = retro_environment_t(callback)
        self.llw.set_environment(self._environment_wrapper)

    def basic_environment(self, cmd, data):
        global debug
        if cmd == ENVIRONMENT_GET_CAN_DUPE:
            b_data = ctypes.cast(data, ctypes.POINTER(ctypes.c_bool))
            b_data[0] = True
            return True
        elif cmd == ENVIRONMENT_SET_PIXEL_FORMAT:
            fmt = ctypes.cast(data, ctypes.POINTER(ctypes.c_int))
            if fmt[0] == PIXEL_FORMAT_RGB565:
                self.env_props['pixel_format'] = 'rgb565'
                return True
            elif fmt[0] == PIXEL_FORMAT_0RGB1555:
                self.env_props['pixel_format'] = '0rgb1555'
                return True
            elif fmt[0] == PIXEL_FORMAT_XRGB8888:
                self.env_props['pixel_format'] = 'xrgb8888'
                return True
            return False
        elif cmd == ENVIRONMENT_SET_MEMORY_MAPS:
            # FIXME: partial implementation good enough for Gambatte
            maps = ctypes.cast(data, ctypes.POINTER(retro_memory_map))
            desc_list = []
            for i in range(maps[0].num_descriptors):
                desc = maps[0].descriptors[i]
                length = desc.len
                if desc.select:  # FIXME: hack for oversized SRAM eating addr space...
                    length = (~desc.select + 1) & 0xffffffff
                    print(f'truncating memory region {hex(desc.start)} from size {hex(desc.len)} '
                          f'to {desc.len//length} banks of size {hex(length)}')
                desc_list.append(((desc.start, desc.start + length), desc.ptr))
            desc_list.sort()
            self.memory_map = collections.OrderedDict(desc_list)
            if debug: print(self.memory_map)
            return True
        elif cmd == ENVIRONMENT_GET_VARIABLE:
            variable = ctypes.cast(data, ctypes.POINTER(retro_variable))[0]
            variable.value = self.env_vars.get(variable.key)
            return True
        elif cmd == ENVIRONMENT_SET_VARIABLES or cmd == ENVIRONMENT_SET_CORE_OPTIONS:
            variables = ctypes.cast(data, ctypes.POINTER(retro_variable))
            idx = 0
            current = variables[idx]
            print('getting variableS')
            print(data)
            print(variables)
            assert(isinstance(current, retro_variable))

            while current.key is not None:
                print(current)
                description, _, options = current.value.partition(b'; ')
                options = options.split(b'|')
                val = self.env_vars.setdefault(current.key, options[0])
                assert val in options, f'{val} invalid for {current.key}, expected {options}'
                idx += 1
                current = variables[idx]
            return True
        elif cmd == ENVIRONMENT_GET_VARIABLE_UPDATE:
            b_data = ctypes.cast(data, ctypes.POINTER(ctypes.c_bool))
            b_data[0] = False  # assumption: we will never change variables after launched
            return True
        elif cmd == ENVIRONMENT_SET_SYSTEM_AV_INFO:
            ctypes.memmove(ctypes.byref(self.av_info),
                           ctypes.cast(data, ctypes.POINTER(retro_system_av_info)),
                           ctypes.sizeof(retro_system_av_info))
            self.av_info_changed = True
            return True
        elif cmd == ENVIRONMENT_SET_GEOMETRY:
            ctypes.memmove(ctypes.byref(self.av_info.geometry),
                           ctypes.cast(data, ctypes.POINTER(retro_game_geometry)),
                           ctypes.sizeof(retro_game_geometry))
            self.av_info_changed = True
            return True

        print(f'retro_environment not implemented: {retro_global_lookup["ENVIRONMENT"].get(cmd, cmd)}')
        return False

    def set_null_callbacks(self):
        self.set_environment_cb(self.basic_environment)
        self.set_video_refresh_cb(null_video_refresh)
        if self.name in HACK_need_audio_sample:
            self.set_audio_sample_cb(null_audio_sample)
        else:
            self.set_audio_sample_batch_cb(null_audio_sample_batch)
        self.set_input_poll_cb(null_input_poll)
        self.set_input_state_cb(null_input_state)
