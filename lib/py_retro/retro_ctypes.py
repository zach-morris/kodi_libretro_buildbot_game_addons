import ctypes

# callback types

retro_environment_t = ctypes.CFUNCTYPE(ctypes.c_bool,
                                       ctypes.c_uint,  # cmd
                                       ctypes.c_void_p)  # data
retro_video_refresh_t = ctypes.CFUNCTYPE(None,
                                         ctypes.c_void_p,  # data
                                         ctypes.c_uint,  # width
                                         ctypes.c_uint,  # height
                                         ctypes.c_size_t)  # pitch
retro_audio_sample_t = ctypes.CFUNCTYPE(None,
                                        ctypes.c_int16,  # left
                                        ctypes.c_int16)  # right
retro_audio_sample_batch_t = ctypes.CFUNCTYPE(ctypes.c_size_t,
                                              ctypes.POINTER(ctypes.c_int16),  # data
                                              ctypes.c_size_t)  # frames
retro_input_poll_t = ctypes.CFUNCTYPE(None)
retro_input_state_t = ctypes.CFUNCTYPE(ctypes.c_int16,
                                       ctypes.c_uint,  # port
                                       ctypes.c_uint,  # device
                                       ctypes.c_uint,  # index
                                       ctypes.c_uint)  # id

retro_log_printf_t = ctypes.CFUNCTYPE(None,
                                      ctypes.c_int,  # enum retro_log_level
                                      ctypes.c_char_p)  # fmt. varargs left out because ctypes doesn't support it...


# structures
class retro_log_callback(ctypes.Structure):
    _fields_ = [
        ("log", retro_log_printf_t),
    ]


class retro_message(ctypes.Structure):
    _fields_ = [
        ("msg", ctypes.c_char_p),
        ("frames", ctypes.c_uint),
    ]


class retro_system_info(ctypes.Structure):
    _fields_ = [
        ("library_name", ctypes.c_char_p),
        ("library_version", ctypes.c_char_p),
        ("valid_extensions", ctypes.c_char_p),
        ("need_fullpath", ctypes.c_bool),
        ("block_extract", ctypes.c_bool),
    ]


class retro_game_geometry(ctypes.Structure):
    _fields_ = [
        ("base_width", ctypes.c_uint),
        ("base_height", ctypes.c_uint),
        ("max_width", ctypes.c_uint),
        ("max_height", ctypes.c_uint),
        ("aspect_ratio", ctypes.c_float),
    ]


class retro_system_timing(ctypes.Structure):
    _fields_ = [
        ("fps", ctypes.c_double),
        ("sample_rate", ctypes.c_double),
    ]


class retro_system_av_info(ctypes.Structure):
    _fields_ = [
        ("geometry", retro_game_geometry),
        ("timing", retro_system_timing),
    ]


class retro_variable(ctypes.Structure):
    _fields_ = [
        ("key", ctypes.c_char_p),
        ("value", ctypes.c_char_p),
    ]


class retro_game_info(ctypes.Structure):
    _fields_ = [
        ("path", ctypes.c_char_p),
        ("data", ctypes.c_void_p),
        ("size", ctypes.c_size_t),
        ("meta", ctypes.c_char_p),
    ]


class retro_memory_descriptor(ctypes.Structure):
    _fields_ = [
        ("flags", ctypes.c_uint64),
        ("ptr", ctypes.c_void_p),
        ("offset", ctypes.c_size_t),
        ("start", ctypes.c_size_t),  # location in the emulated address space where mapping starts
        ("select", ctypes.c_size_t),  # Which bits must be same as in 'start' for mapping to apply
        ("disconnect", ctypes.c_size_t),  # set bits are not connected to memory chip's address pins
        ("len", ctypes.c_size_t),
        ("addrspace", ctypes.c_char_p),
    ]


class retro_memory_map(ctypes.Structure):
    _fields_ = [
        ("descriptors", ctypes.POINTER(retro_memory_descriptor)),
        ("num_descriptors", ctypes.c_uint),
    ]