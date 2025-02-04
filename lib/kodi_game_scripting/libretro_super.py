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

""" Represents the libretro-super repository with info files """

import os
import shlex

from .git_access import GitHubRepo, GitRepo


class LibretroSuper:
    """ Represents the libretro-super repository with info files """
    def __init__(self, working_directory):
        self._working_directory = working_directory

    def fetch_and_reset(self):
        """ Fetch and reset libretro-super repo """
        print("Fetching libretro-super repo")
        gitrepo = GitRepo(
            GitHubRepo('libretro-super',
                       'https://github.com/libretro/libretro-super.git', ''),
            self._working_directory)
        gitrepo.fetch_and_reset()

    def parse_info_file(self, library_soname):
        """ Load info file from libretro-super repository """
        path = os.path.join(self._working_directory, 'libretro-super', 'dist',
                            'info', '{}.info'.format(library_soname))
        result = {}
        if os.path.isfile(path):
            with open(path, 'r') as info_ctx:
                for line in info_ctx.readlines():
                    if '=' in line:
                        name, var = line.partition('=')[::2]
                        result[name.strip()] = shlex.split(var)[0]
        return result
