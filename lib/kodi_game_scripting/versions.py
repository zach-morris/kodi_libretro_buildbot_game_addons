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

""" Convert addon version into Kodi format """

import re


class AddonVersion():
    """ Convert addon version into Kodi format """

    @classmethod
    def get(cls, version):
        """ Convert addon version into Kodi format """
        result = re.sub(r'^[vr \t]', '', version)
        match = re.search(r'^(0|[1-9]*0?)\.?([0-9]*)\.?([0-9]*)', result)
        result = [x if x else '0' for x in match.groups()]
        result = '.'.join(result)
        return result if result != '0.0.0' else '0.0.1'
