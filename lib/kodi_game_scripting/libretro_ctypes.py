# Copyright (C) 2016-2018 Christian Fetzer
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.

""" Libretro Wrapper """

import collections
import ctypes
import re
import subprocess
import sys

from .utils import xstr


class LibretroWrapper:
    """ Wraps a libretro core giving access to system info.

        Use attributes system_info and settings to access this information. """

    EXT = 'dylib' if sys.platform == 'darwin' else 'so'
    LDD_CMD = ['otool', '-L'] if sys.platform == 'darwin' else ['ldd']

    class RetroSystemInfo(ctypes.Structure):
        """ struct retro_system_type """
        _fields_ = [
            ('library_name', ctypes.c_char_p),
            ('library_version', ctypes.c_char_p),
            ('valid_extensions', ctypes.c_char_p),
            ('need_fullpath', ctypes.c_bool),
            ('block_extract', ctypes.c_bool)
        ]

    class SystemInfo():
        """ Wrapped system info """
        def __init__(self, retro_system_info=None):
            self.name = xstr(retro_system_info.library_name)
            self.version = xstr(retro_system_info.library_version)
            self.extensions = [ext for ext in xstr(
                retro_system_info.valid_extensions).split('|')
                               if ext]
            self.need_fullpath = retro_system_info.need_fullpath
            self.block_extract = retro_system_info.block_extract
            self.supports_no_game = False

        def __getitem__(self, item):
            return getattr(self, item)

        def __repr__(self):
            return '(name={}, version={}, extensions={}, need_fullpath={},' \
                   ' block_extract={}, supports_no_game={})'.format(
                       self.name, self.version, self.extensions,
                       self.need_fullpath, self.block_extract,
                       self.supports_no_game)

    class RetroVariable(ctypes.Structure):
        """ struct libretro_variable """
        _fields_ = [
            ('key', ctypes.c_char_p),
            ('value', ctypes.c_char_p)
        ]

    def __init__(self, library_path):
        lib = ctypes.cdll.LoadLibrary(library_path)

        # retro_get_system_info
        retro_get_system_info = lib.retro_get_system_info
        retro_get_system_info.argtypes = \
            [ctypes.POINTER(self.RetroSystemInfo)]
        retro_get_system_info.restype = None

        system_info = self.RetroSystemInfo()
        retro_get_system_info(ctypes.byref(system_info))
        self.system_info = self.SystemInfo(system_info)

        # retro_set_environment
        retro_environment_t = ctypes.CFUNCTYPE(
            ctypes.c_bool, ctypes.c_uint, ctypes.c_void_p)

        retro_set_environment = lib.retro_set_environment
        retro_set_environment.argtypes = [retro_environment_t]
        retro_set_environment.restype = None
        self.variables = []

        def retro_environment_cb(cb_type, arg, outer=self):
            """ Libretro environment callback """
            if cb_type == 18:  # RETRO_ENVIRONMENT_SET_SUPPORT_NO_GAME
                result = ctypes.cast(arg, ctypes.POINTER(ctypes.c_bool))[0]
                outer.system_info.supports_no_game = result
            elif cb_type == 16:  # RETRO_ENVIRONMENT_SET_VARIABLES
                index = 0
                while True:
                    var = ctypes.cast(arg, ctypes.POINTER(
                        self.RetroVariable))[index]
                    index += 1
                    if var.key is None and var.value is None:
                        break
                    outer.variables.append(outer.parse_libretro_variable(var))

        retro_environment_cb = retro_environment_t(retro_environment_cb)
        retro_set_environment(retro_environment_cb)

        # opengl linkage
        self.opengl_linkage = self.has_opengl_linkage(library_path)

    @classmethod
    def parse_libretro_variable(cls, variable):
        """ Parse variable into Variable(id, desc, values, default) """
        key = xstr(variable.key)
        description, values = xstr(variable.value).split(';', 1)
        values = values.strip().split('|')
        default = values[0]

        var = collections.namedtuple('Variable',
                                     'id description values default')
        return var(key, description, values, default)

    @classmethod
    def has_opengl_linkage(cls, library_path):
        """ Check if the library links opengl """
        ldd_output = subprocess.run(
            cls.LDD_CMD + [library_path], stdout=subprocess.PIPE, check=True)
        return bool(re.search(r'(?:libgl|opengl)',
                              str(ldd_output.stdout, 'utf-8'), re.IGNORECASE))


if __name__ == '__main__':  # pragma: no cover
    LIB = LibretroWrapper(sys.argv[1])
