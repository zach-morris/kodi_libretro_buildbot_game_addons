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

""" Access GitHub API and Git Repos """

import collections
import functools
import os
import re
import time

from pkg_resources import parse_version

import git
import github

from . import credentials
from . import utils


EMPTY_SHA = '4b825dc642cb6eb9a060e54bf8d69288fbee4904'

GitHubRepo = collections.namedtuple('GitHubRepo', 'name clone_url ssh_url')


class GitHubOrg:
    """ Access GitHub Organization API """
    def __init__(self, org, auth=False):
        """ Initialize GitHub API instance """
        try:
            apitoken = os.environ.get('GITHUB_ACCESS_TOKEN', None)
            if apitoken:
                print("Authenticating with GitHub API token")
                self._github = github.Github(apitoken)
            else:
                if auth:
                    print("Authenticating with username/password")
                    cred = credentials.Credentials('github')
                    username, password = cred.load()
                else:
                    print("Connecting to GitHub without authentication "
                          "(no username/password set)")
                    username, password = None, None
                self._github = github.Github(username, password)
            rate = self._github.get_rate_limit().core
            print("GitHub API Rate: limit: {}, remaining: {}, reset: {}"
                  .format(rate.limit, rate.remaining, rate.reset.isoformat()))
            if auth and not apitoken:
                cred.save(username, password)
            self._org = self._github.get_organization(org)
        except github.BadCredentialsException as err:
            if auth and not apitoken:
                cred.clean()
            raise ValueError("Authentication to GitHub failed") from err

    @functools.lru_cache()
    def get_repos(self, regex):
        """ Query all GitHub repos of the given organization that matches
            the given regex. Since API calls are limited, cache results. """
        repos = {
            repo.name: GitHubRepo(repo.name, repo.clone_url, repo.ssh_url)
            for repo in self._org.get_repos() if re.search(regex, repo.name)
        }
        return repos

    def get_repo(self, repo):
        """ Get the specified GitHub repo """
        return self._org.get_repo(repo)

    def create_repo(self, name):
        """ Create a new repo on GitHub """
        repo = self._org.create_repo(name, auto_init=True)
        self.get_repos.cache_clear()  # pylint: disable=no-member
        return GitHubRepo(repo.name, repo.clone_url, repo.ssh_url)


class GitRepo:
    """ Access to Git repository """

    @staticmethod
    def is_git_repo(path):
        """ Determine if repo is a Git repository """
        try:
            _ = git.Repo(path).git_dir  # noqa
            return True
        except (git.InvalidGitRepositoryError,
                git.NoSuchPathError):
            return False

    def __init__(self, repo, path):
        self.path = os.path.join(path, repo.name)
        self._githubrepo = repo
        self._gitrepo = None

        if not GitRepo.is_git_repo(self.path):
            utils.ensure_directory_exists(self.path)
            print("New repo, creating {}".format(self._githubrepo.name))
            self._gitrepo = git.Repo.init(self.path)
        else:
            print("Existing repo {}".format(self._githubrepo.name))
            self._gitrepo = git.Repo(self.path)
        if self._githubrepo.clone_url:
            try:
                origin = self._gitrepo.remotes.origin
            except AttributeError:
                origin = self._gitrepo.create_remote(
                    'origin', self._githubrepo.clone_url)
            origin.set_url(self._githubrepo.ssh_url, push=True)

    def fetch_and_reset(self, reset=True):
        """ Fetch repo and reset it """
        if git.Remote('', 'origin') in self._gitrepo.remotes:
            origin = self._gitrepo.remotes.origin
            print("Fetching {}".format(self._githubrepo.name))
            origin.fetch('master')
            if (parse_version('.'.join(map(
                    str, self._gitrepo.git.version_info))) >=
                    parse_version('2.17.0')):
                origin.fetch(tags=True, prune=True, prune_tags=True)
            else:
                tags = self._gitrepo.git.tag(list=True)
                if tags:
                    self._gitrepo.git.tag('--delete', tags.splitlines())
                origin.fetch(tags=True, prune=True)
            if reset:
                print("Resetting {}".format(self._githubrepo.name))
                self._gitrepo.git.reset('--hard', 'origin/master')
            else:
                print("Rebasing {}".format(self._githubrepo.name))
                self._gitrepo.git.rebase('origin/master')
        else:
            print("Skipping fetching {}".format(self._githubrepo.name))
        print("Cleaning local changes {}".format(self._githubrepo.name))
        self._gitrepo.git.reset()
        self._gitrepo.git.clean('-xffd')

    def get_hexsha(self):
        """ Get HEAD revision """
        if self._gitrepo.head.is_valid():
            return self._gitrepo.head.object.hexsha
        return ''

    def commit(self, message, directory=None, force=False, squash=False):
        """ Create commit in repo """
        if directory:
            self._gitrepo.git.add(directory, force=force)
        else:
            self._gitrepo.git.add(all=True, force=force)
        if squash:
            if git.Remote('', 'origin') in self._gitrepo.remotes:
                self._gitrepo.git.reset('origin/master', soft=True)
            else:
                self._gitrepo.git.update_ref('-d', 'HEAD')
        if self._gitrepo.is_dirty():
            self._gitrepo.index.commit(message)

    def tag(self, tag, message=None):
        """ Create tag in repo """
        if self._gitrepo.head.is_valid():
            self._gitrepo.create_tag(tag, message, force=True)

    def diff(self):
        """ Diff commits in repo """
        if self._gitrepo.head.is_valid():
            if git.Remote('', 'origin') in self._gitrepo.remotes:
                return self._gitrepo.git.diff('origin/master',
                                              self._gitrepo.head.commit)
            return self._gitrepo.git.diff(EMPTY_SHA, self._gitrepo.head.commit)
        return ''

    def describe(self):
        """ Describe current version """
        if self._gitrepo.head.is_valid():
            return self._gitrepo.git.describe('--tags', '--always')
        return ''

    def push(self, branch, tags=False, sleep=0):
        """ Push commit to remote """
        if self._gitrepo.is_dirty():
            raise ValueError("Skipping, repository is dirty")
        self._gitrepo.remotes.origin.push(
            'HEAD:{}'.format(branch),
            force=(branch != 'master'))
        time.sleep(sleep)
        if tags:
            self._gitrepo.git.push('--tags')
            time.sleep(sleep)
