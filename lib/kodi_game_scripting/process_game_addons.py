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

""" Process Kodi Game addons and unify project files """

import argparse
import datetime
import os
import multiprocessing
import re
import shutil
import subprocess
import sys

from . import utils
from .config import ADDONS, GITHUB_ADDON_PREFIX, GITHUB_ORGANIZATION
from .git_access import GitHubOrg, GitHubRepo, GitRepo
from .libretro_ctypes import LibretroWrapper
from .template_processor import TemplateProcessor
from .libretro_super import LibretroSuper
from .versions import AddonVersion

COMMIT_MSG = "Updated by kodi-game-scripting\n\n" \
             "https://github.com/kodi-game/kodi-game-scripting/"


def main():
    """ Process Kodi Game addons and unify project files """
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--game-addons-dir', dest='working_directory',
                        type=str, required=True,
                        help="Directory where the game addons reside")
    parser.add_argument('--compile', action='store_true',
                        help="Compile libretro cores and read system info")
    parser.add_argument('--buildtype', default='Release',
                        type=str, choices=['Debug', 'Release'],
                        help="Specify build type")
    parser.add_argument('--kodi-source-dir', dest='kodi_directory',
                        type=str,
                        help="Kodi's source directory")
    parser.add_argument('--git', action="store_true",
                        help="Clone / reset libretro cores from GitHub")
    parser.add_argument('--git-noclean', action="store_true",
                        help="Keep existing commits (rebase and squash)")
    parser.add_argument('--filter', type=str, default='',
                        help="Filter games (e.g. nes)")
    parser.add_argument('--push-branch', type=str,
                        help="To which branch to push to GitHub")
    parser.add_argument('--push-limit', type=int,
                        help="Limit repos that are pushed to GitHub")
    parser.add_argument('--push-description', action='store_true',
                        help="Push addon descriptions")
    parser.add_argument('--clean-description', action='store_true',
                        help="Clean existing addon descriptions")

    args = parser.parse_args()
    args.working_directory = os.path.abspath(args.working_directory)

    LibretroSuper(args.working_directory).fetch_and_reset()
    addondescriptions = KodiAddonDescriptions(args.working_directory)
    if args.clean_description:
        addondescriptions.clean()
    gameaddons = KodiGameAddons(args)
    status = gameaddons.process()
    gameaddons.summary()
    if args.push_description:
        addondescriptions.push(args.push_branch)
    if not status:
        sys.exit(1)


class KodiAddonDescriptions:
    """ Represents addon description files for compiling addons """
    DESCRIPTION_PATH = os.path.join('cmake', 'addons', 'addons')

    def __init__(self, kodi_directory):
        self._kodi_directory = kodi_directory

    def clean(self):
        """ Clean addon descriptions """
        desc_dir = os.path.join(self._kodi_directory, self.DESCRIPTION_PATH)
        for path in next(os.walk(desc_dir))[1]:
            if path.startswith(GITHUB_ADDON_PREFIX):
                shutil.rmtree(os.path.join(desc_dir, path))

    def push(self, branch):
        """ Push addon descriptions to kodi repo """
        # Don't specify urls as we use the existing remote origin
        print("Commiting descriptions to GitHub repo")
        path, name = os.path.split(self._kodi_directory)
        repo = GitRepo(GitHubRepo(name, '', ''), path)
        repo.commit(COMMIT_MSG, directory=self.DESCRIPTION_PATH, force=True)
        print("Pushing descriptions to GitHub repo")
        repo.push(branch)


class KodiGameAddons:
    """ Process Kodi Game addons and unify project files """
    def __init__(self, args):
        """ Initialize instance """
        # The following values are read from args:
        # filter, git, working_directory, push_branch, push_limit, git_noclean,
        # compile, kodi_directory

        self._args = args
        self._prepare_environment()

    def _prepare_environment(self):
        """ Prepare and check the environment (directories and config) """
        # Check if given filter matches with config.py
        addons = {k: v for k, v in ADDONS.items()
                  if re.search(self._args.filter, k)}
        if not addons:
            raise ValueError("Filter doesn't match any items in config.py")

        # Check GitHub repos
        repos = {}
        if self._args.git:
            regex = (self._args.filter if self._args.filter
                     else GITHUB_ADDON_PREFIX)
            print("Querying GitHub repos matching '{}'".format(regex))
            self._github = GitHubOrg(GITHUB_ORGANIZATION, auth=True)
            repos = self._github.get_repos(regex)

        # Create Addon objects
        self._addons = []
        for game_name in sorted(addons):
            addon_name = '{}{}'.format(GITHUB_ADDON_PREFIX, game_name)
            repo = repos.get(addon_name, None)
            if not repo:
                if self._args.git and self._args.push_branch:
                    print("Creating GitHub repository {}".format(addon_name))
                    repo = self._github.create_repo(addon_name)
                else:
                    repo = GitHubRepo(addon_name, '', '')
            self._addons.append(KodiGameAddon(
                addon_name, game_name, repo, self._args.working_directory,
                self._args.push_branch))

        print("Processing the following addons: {}".format(
            ', '.join([addon.game_name for addon in self._addons])))

        # Clone/Fetch repos
        if self._args.git:
            for addon in self._addons:
                addon.fetch_and_reset(reset=not self._args.git_noclean)

    def process(self):
        """ Process list of addons from config """

        # First iteration: Makefiles
        print("First iteration: Generate Makefiles")
        for addon in self._addons:
            print(" Processing addon: {}".format(addon.name))
            addon.load_git_tag()
            addon.process_addon_files()
            print(" Processing addon description: {}".format(addon.name))
            addon.process_description_files(self._args.kodi_directory)

        # Compile addons to read info from built library
        # Instead of compiling individual addons we compile all at once to save
        # time (tinyxml and others would be compiled multiple times).
        if self._args.compile:
            if not self._compile_addons():
                return False

        # Second iteration: Metadata files
        print("Second iteration: Generate Metadata files")
        for addon in self._addons:
            print(" Processing addon: {}".format(addon.name))
            addon.load_info_file()
            addon.load_assets()
            addon.load_library_file()
            addon.load_git_revision()
            addon.load_game_version()
            addon.load_exclude_platforms()
            addon.process_addon_files()

        # Create commit
        if self._args.git:
            for addon in self._addons:
                addon.commit(squash=self._args.git_noclean)

            # Third iteration: Update package version if there are changes
            print("Third iteration: Update version")
            for addon in self._addons:
                if 'depends/common' in addon.info['git']['diff']:
                    print(" Processing addon: {}".format(addon.name))
                    addon.bump_version()
                    addon.process_addon_files()
                    addon.commit(squash=True)
                    addon.tag()

            # Push in reversed order so that the repository list on GitHub
            # stays sorted alphabetically
            if self._args.push_branch:
                count = 0
                for addon in reversed(self._addons):
                    if (self._args.push_limit and
                            count >= self._args.push_limit):
                        break
                    if addon.info['git']['diff']:
                        addon.push()
                        count += 1
        return True

    def summary(self):
        """ Print summary """
        print("Generating summary")
        template_vars = {'addons': []}
        for addon in self._addons:
            template_vars['addons'].append(addon.info)
        TemplateProcessor.process('summary', self._args.working_directory,
                                  template_vars)

    def _compile_addons(self):
        print("Compiling addons")
        build_dir = os.path.join(self._args.working_directory, 'build')
        install_dir = os.path.join(self._args.working_directory, 'install')
        cmake_dir = os.path.join(self._args.kodi_directory, 'cmake', 'addons')
        utils.ensure_directory_exists(build_dir, clean=True)
        addons = '|'.join(['{}$'.format(addon.name) for addon in self._addons])
        try:
            subprocess.run([os.environ.get('CMAKE', 'cmake'),
                            '-DADDONS_TO_BUILD={}'.format(addons),
                            '-DADDON_SRC_PREFIX={}'
                            .format(self._args.working_directory),
                            '-DCMAKE_BUILD_TYPE={}'
                            .format(self._args.buildtype),
                            '-DPACKAGE_ZIP=1',
                            '-DCMAKE_INSTALL_PREFIX={}'.format(install_dir),
                            cmake_dir], cwd=build_dir, check=True)
            subprocess.run([os.environ.get('CMAKE', 'cmake'), '--build', '.',
                            '--', '-j{}'.format(multiprocessing.cpu_count())],
                           cwd=build_dir, check=True)
        except subprocess.CalledProcessError:
            print("Compilation failed!")
            return False
        return True


class KodiGameAddon():
    """ Process a single Kodi Game addon """
    def __init__(self, addon_name,  # pylint: disable=too-many-arguments
                 game_name, githubrepo, working_directory, push_branch):
        self.name = addon_name
        self.game_name = game_name

        self._repo = GitRepo(githubrepo, working_directory)
        self._working_directory = working_directory
        self._path = os.path.join(working_directory, addon_name)

        addon_config = ADDONS[game_name]
        self.info = {
            'game': {
                'name': self.game_name,
                'addon': self.name,
                'debian_package': re.sub(r'[\._]', '-', self.name),
                'branch': push_branch or 'master',
                'version': '0.0.0',
            },
            'config': addon_config[4],
            'datetime': '{0:%Y-%m-%d %H:%Mi%z}'.format(
                datetime.datetime.now()),
            'system_info': {
                'version': '0.0.0',
            },
            'settings': [],
            'libretro_info': {},
            'libretro_repo': {
                'org': os.path.dirname(addon_config[0]) or 'libretro',
                'name': os.path.basename(addon_config[0]),
                'branch': addon_config[4].get('branch', 'master'),
                'exclude_platforms': addon_config[4].get('exclude_platforms',
                                                         []),
                'git_tag': addon_config[4].get('git_tag', False),
                'hexsha': '',
            },
            'makefile': {
                'file': addon_config[1],
                'dir': addon_config[2],
                'jni': addon_config[3],
                'cmake': addon_config[4].get('cmake', False),
            },
            'library': {
                'file': os.path.join('install', self.name, '{}.{}'.format(
                    self.name, LibretroWrapper.EXT)),
                'loaded': False,
                'soname': '{}_libretro'.format(addon_config[4].get(
                    'soname', game_name)),
                'jnisoname': addon_config[4].get('jnisoname', 'libretro'),
            },
            'assets': {},
            'git': {},
        }

    def process_description_files(self, kodi_directory):
        """ Generate addon description files """
        kodi_addon_dir = os.path.join(
            kodi_directory, KodiAddonDescriptions.DESCRIPTION_PATH, self.name)
        TemplateProcessor.process('description', kodi_addon_dir, self.info)

    def process_addon_files(self):
        """ Generate addon files """
        TemplateProcessor.process('addon', self._path, self.info)

    def load_library_file(self):
        """ Load the compiled library file """
        library = None
        library_path = os.path.join(self._working_directory,
                                    self.info['library']['file'])
        try:
            library = LibretroWrapper(library_path)
            self.info['library']['loaded'] = True
            self.info['system_info'] = library.system_info
            self.info['settings'] = sorted(library.variables,
                                           key=lambda x: x.id)
            self.info['library']['opengl'] = library.opengl_linkage
        except OSError as err:
            self.info['library']['error'] = err
            print("Failed to read output library.")
        return library

    def load_info_file(self):
        """ Load info file from libretro-super repository """
        self.info['libretro_info'] = LibretroSuper(self._working_directory) \
            .parse_info_file(self.info['library']['soname'])

    def load_assets(self):
        """ Process assets """
        # Loop over all images files in the repo
        for asset in sorted(utils.list_all_files(self._path)):
            if os.path.splitext(asset)[1] not in ['.png', '.jpg', '.svg']:
                continue

            if asset == os.path.join(self.name, 'resources', 'icon.png'):
                self.info['assets']['icon'] = 'resources/icon.png'
            elif asset == os.path.join(self.name, 'resources', 'fanart.jpg'):
                self.info['assets']['fanart'] = 'resources/fanart.jpg'
            elif asset.startswith(os.path.join(self.name, 'resources',
                                               'screenshot')):
                self.info['assets'].setdefault('screenshots', []).append(
                    os.path.join('resources', os.path.basename(asset)))
            else:
                print("Unrecognized image detected: {}".format(asset))

    def load_git_tag(self):
        """ Get the latest git tag from the libretro repository """
        if self.info['libretro_repo']['git_tag']:
            repo = GitHubOrg(
                self.info['libretro_repo']['org'], auth=True).get_repo(
                    self.info['libretro_repo']['name'])
            self.info['libretro_repo']['branch'] = repo.get_tags()[0].name

    def load_git_revision(self):
        """ Get the revision of the libretro core from the Git checkout """
        path = os.path.join(self._working_directory,
                            'build', 'build', self.game_name, 'src')
        if GitRepo.is_git_repo(os.path.join(path, self.game_name)):
            gitrepo = GitRepo(GitHubRepo(self.game_name, '', ''), path)
            self.info['libretro_repo']['hexsha'] = gitrepo.get_hexsha()

    def load_game_version(self):
        """ Load game version from compiled library and git """
        self.info['game']['version'] = AddonVersion.get(
            self.info['system_info']['version'])
        git_tag = self._repo.describe()
        match = re.search(r'^(?:[0-9]+\.){3}([0-9]+)', git_tag)
        pkg_version = match.group(1) if match else '0'
        self.info['game']['version'] = '{}.{}'.format(
            self.info['game']['version'], pkg_version)

    def load_exclude_platforms(self):
        """ Load excluded platforms """
        bad = (r"APP_STL\s*:=\s*"
               r"(gnustl_static|gnustl_shared|stlport_static|stlport_shared)"
               r"|"
               r"NDK_TOOLCHAIN_VERSION\s*:=\s*4\.9")
        if self.info['makefile']['jni']:
            filename = os.path.join(self._working_directory, 'build', 'build',
                                    self.game_name, 'src', self.game_name,
                                    self.info['makefile']['jni'],
                                    'Application.mk')
            try:
                with open(filename) as file:
                    if re.search(bad, file.read()):
                        self.info['libretro_repo']['exclude_platforms'] \
                            .append('android-armv7')
                        self.info['libretro_repo']['exclude_platforms'] \
                            .append('android-aarch64')
            except FileNotFoundError:
                pass

    def bump_version(self):
        """ Bump game version """
        version, pkg_version = self.info['game']['version'].rsplit('.', 1)
        self.info['game']['version'] = '{}.{}'.format(
            version, int(pkg_version) + 1)
        print("  Version bumped to {}".format(self.info['game']['version']))

    def fetch_and_reset(self, *, reset):
        """ Fetching & resetting Git repository """
        print("  Fetching & resetting Git repository {}".format(self.name))
        self._repo.fetch_and_reset(reset=reset)

    def commit(self, *, squash):
        """ Commiting changes to Git repository """
        print("  Commiting changes to Git repository {}".format(self.name))
        self._repo.commit(COMMIT_MSG, squash=squash)
        self.info['git']['diff'] = self._repo.diff()

    def tag(self):
        """ Creating tags in Git repository """
        print("  Creating tags in Git repository {}: {}".format(
            self.name, self.info['game']['version']))
        for branch in ['Leia', 'Matrix']:
            self._repo.tag('{}-{}'.format(self.info['game']['version'], branch))

    def push(self):
        """ Pushing changes to GitHub repository """
        print("  Pushing changes to GitHub repository {}".format(self.name))
        branch = self.info['game']['branch']
        self._repo.push(branch, tags=(branch == 'master'), sleep=(3 * 60))
