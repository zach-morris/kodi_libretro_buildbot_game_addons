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

""" Manage username and password for a service using the system keyring """

import getpass
import keyring


class Credentials:
    """ Manage credentials for a given service

        Uses system keyring if available, asks user if not.
        For convenience also the username is saved in the keyring. """
    def __init__(self, service):
        self._service = service
        self._username_service = '{}_username'.format(service.lower())
        self._password_service = '{}_password'.format(service.lower())
        self._username_key = '_username'
        self._username = ''

    def load(self):
        """ Load saved credentials from keyring or ask user """
        username = keyring.get_password(self._username_service,
                                        self._username_key)
        if not username:
            env_user = getpass.getuser()
            username = input("{} User [{}]: ".format(self._service, env_user))
            if not username:
                username = env_user
        self._username = username

        password = ''
        if username:
            password = keyring.get_password(self._password_service, username)
            if not password:
                password = getpass.getpass(
                    "{} Password: ".format(self._service))

        return username, password

    def save(self, username, password):
        """ Save credentials to keyring if possible """
        keyring.set_password(self._username_service, self._username_key,
                             username)
        keyring.set_password(self._password_service, username, password)

    def clean(self):
        """ Remove saved credentials """
        keyring.set_password(self._username_service, self._username_key, '')
        keyring.set_password(self._password_service, self._username, '')
