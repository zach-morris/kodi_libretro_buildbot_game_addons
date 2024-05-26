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

""" Libretro core configuration

    Override settings for specific libretro cores. """

# pylint: disable=bad-option-value, bad-whitespace, line-too-long
# flake8: noqa

GITHUB_ORGANIZATION = 'kodi-game'
GITHUB_ADDON_PREFIX = 'game.libretro.'

# core: {(Libretro repo, Makefile, Directory)}
ADDONS = {
    '2048':                      ('libretro-2048',              'Makefile.libretro', '.',                 'jni', {}),
    '3dengine':                  ('libretro-3dengine',          'Makefile',          '.',                 'jni', {}),
    '81':                        ('81-libretro',                'Makefile',          '.',                 'build/jni', {}),
    'atari800':                  ('libretro-atari800',          'Makefile',          '.',                 'jni', {}),
    'beetle-bsnes':              ('beetle-bsnes-libretro',      'Makefile',          '.',                 'jni', {'soname': 'mednafen_snes'}),
    'beetle-gba':                ('beetle-gba-libretro',        'Makefile',          '.',                 'jni', {'soname': 'mednafen_gba'}),
    'beetle-lynx':               ('beetle-lynx-libretro',       'Makefile',          '.',                 'jni', {'soname': 'mednafen_lynx'}),
    'beetle-ngp':                ('beetle-ngp-libretro',        'Makefile',          '.',                 'jni', {'soname': 'mednafen_ngp'}),
    'beetle-pce-fast':           ('beetle-pce-fast-libretro',   'Makefile',          '.',                 'jni', {'soname': 'mednafen_pce_fast'}),
    'beetle-pcfx':               ('beetle-pcfx-libretro',       'Makefile',          '.',                 'jni', {'soname': 'mednafen_pcfx'}),
    'beetle-psx':                ('beetle-psx-libretro',        'Makefile',          '.',                 'jni', {'soname': 'mednafen_psx'}),
    'beetle-saturn':             ('beetle-saturn-libretro',     'Makefile',          '.',                 'jni', {'soname': 'mednafen_saturn'}),
    'beetle-supergrafx':         ('beetle-supergrafx-libretro', 'Makefile',          '.',                 'jni', {'soname': 'mednafen_supergrafx'}),
    'beetle-vb':                 ('beetle-vb-libretro',         'Makefile',          '.',                 'jni', {'soname': 'mednafen_vb'}),
    'beetle-wswan':              ('beetle-wswan-libretro',      'Makefile',          '.',                 'jni', {'soname': 'mednafen_wswan'}),
    'bk':                        ('bk-emulator',                'Makefile.libretro', '.',                 'jni', {}),
    'blastem':                   ('blastem',                    'Makefile',          '.',                 'android/jni', {}),
    'bluemsx':                   ('blueMSX-libretro',           'Makefile',          '.',                 'jni', {}),
    'bnes':                      ('bnes-libretro',              'Makefile',          '.',                 'jni', {}),
    'boom3':                     ('boom3',                      'Makefile',          'neo',               'jni', {}),
    'bsnes-mercury-accuracy':    ('bsnes-mercury',              'Makefile',          '.',                 'target-libretro/jni', {'soname': 'bsnes_mercury_accuracy', 'jnisoname': 'libretro_bsnes_mercury_accuracy', 'cmake_options': 'PROFILE=accuracy'}),
    'bsnes-mercury-balanced':    ('bsnes-mercury',              'Makefile',          '.',                 'target-libretro/jni', {'soname': 'bsnes_mercury_balanced', 'jnisoname': 'libretro_bsnes_mercury_balanced', 'cmake_options': 'PROFILE=balanced'}),
    'bsnes-mercury-performance': ('bsnes-mercury',              'Makefile',          '.',                 'target-libretro/jni', {'soname': 'bsnes_mercury_performance', 'jnisoname': 'libretro_bsnes_mercury_performance', 'cmake_options': 'PROFILE=performance'}),
    'cannonball':                ('cannonball',                 'Makefile',          '.',                 'jni', {}),
    'cap32':                     ('libretro-cap32',             'Makefile',          '.',                 'jni', {}),
    'chailove':                  ('libretro-chailove',          'Makefile',          '.',                 'jni', {'git_tag': True}),
    'craft':                     ('Craft',                      'Makefile.libretro', '.',                 'jni', {}),
    'crocods':                   ('libretro-crocods',           'Makefile',          '.',                 'jni', {}),
    'daphne':                    ('daphne',                     'Makefile',          '.',                 'jni', {}),
    'desmume':                   ('desmume',                    'Makefile.libretro', 'desmume/src/frontend/libretro', 'desmume/src/frontend/libretro/jni', {}),
    'desmume2015':               ('desmume2015',                'Makefile.libretro', 'desmume', 'desmume/src/libretro/jni', {}),
    'dinothawr':                 ('Dinothawr',                  'Makefile',          '.',                 'jni', {}),
    #'dolphin':                   ('dolphin',                    '',                  '',                  '', {'cmake': True }),  # Uses git submodules
    'dosbox':                    ('dosbox-libretro',            'Makefile.libretro', '.',                 'jni', {}),
    'dosbox-core':               ('dosbox-core',                'Makefile.libretro', 'libretro',          'libretro/jni', {'branch': 'libretro --'}),  # Requires CMake 3.11 or higher
    'ecwolf':                    ('ecwolf',                     'Makefile',          'src/libretro',       'src/libretro/jni', {}),
    'fbalpha2012':               ('fbalpha2012',                'makefile.libretro', 'svn-current/trunk', 'svn-current/trunk/projectfiles/libretro-android/jni', {}),
    'fbneo':                     ('FBNeo',                      'Makefile',          'src/burner/libretro', 'jni', {}),
    'fceumm':                    ('libretro-fceumm',            'Makefile',          '.',                 'jni', {}),
    'flycast':                   ('flycast',                    'Makefile',          '.',                 'jni', {}),
    'fmsx':                      ('fmsx-libretro',              'Makefile',          '.',                 'jni', {}),
    'freechaf':                  ('FreeChaF',                   'Makefile',          '.',                 'jni', {}),
    'freeintv':                  ('FreeIntv',                   'Makefile',          '.',                 'jni', {}),
    'frodo':                     ('frodo-libretro',             'Makefile',          '.',                 'jni', {}),
    #'fsuae':                     ('libretro-fsuae',             'Makefile.libretro', '.',                 'jni', {'branch': 'libretro-fsuae'}),  # Fails to build
    'fuse':                      ('fuse-libretro',              'Makefile',          '.',                 'jni', {}),
    'gambatte':                  ('gambatte-libretro',          'Makefile',          '.',                 'libgambatte/libretro/jni', {}),
    'genplus':                   ('Genesis-Plus-GX',            'Makefile.libretro', '.',                 'libretro/jni', {'soname': 'genesis_plus_gx'}),
    'gpsp':                      ('gpsp',                       'Makefile',          '.',                 'jni', {}),
    'gw':                        ('gw-libretro',                'Makefile',          '.',                 'jni', {}),
    'handy':                     ('libretro-handy',             'Makefile',          '.',                 'jni', {}),
    'hatari':                    ('hatari',                     'Makefile.libretro', '.',                 'jni', {}),
    'hbmame':                    ('hbmame-libretro',            'Makefile.libretro', '.',                 'jni', {}),
    'lutro':                     ('libretro-lutro',             'Makefile',          '.',                 'jni', {}),
    'mame':                      ('mame',                       'Makefile.libretro', '.',                 'jni', {'cmake_options': 'PTR64=1'}),  # Huge and longrunning
    'mame2000':                  ('mame2000-libretro',          'Makefile',          '.',                 'jni', {}),
    'mame2003':                  ('mame2003-libretro',          'Makefile',          '.',                 'jni', {}),
    'mame2003_midway':           ('mame2003_midway',            'Makefile',          '.',                 'jni', {}),
    'mame2003_plus':             ('mame2003-plus-libretro',     'Makefile',          '.',                 'jni', {}),
    'mame2010':                  ('mame2010-libretro',          'Makefile',          '.',                 'jni', {'cmake_options': 'VRENDER=soft PTR64=1'}),  # Huge and longrunning
    'mame2015':                  ('mame2015-libretro',          'Makefile',          '.',                 'jni', {'cmake_options': 'PTR64=1 TARGET=mame'}),  # Huge and longrunning
    'mame2016':                  ('mame2016-libretro',          'Makefile.libretro', '.',                 '3rdparty/SDL2/android-project/jni', {'cmake_options': 'PTR64=1'}),  # Huge and longrunning
    'melonds':                   ('melonDS',                    'Makefile',          '.',                 'jni', {}),
    'meowpc98':                  ('libretro-meowPC98',          'Makefile.libretro', 'libretro',          'libretro/jni', {'soname': 'nekop2'}),
    'mesen':                     ('SourMesen/Mesen',            'Makefile',          'Libretro',          'libretro/jni', {}),
    'meteor':                    ('meteor-libretro',            'Makefile',          'libretro',          'libretro/jni', {}),
    'mgba':                      ('mgba',                       'Makefile',          '.',                 'jni', {}),
    'mrboom':                    ('mrboom-libretro',            'Makefile',          '.',                 'jni', {}),
    'mu':                        ('Mu',                         'Makefile.libretro', 'libretroBuildSystem', 'libretroBuildSystem/jni', {}),
    'mupen64plus-nx':            ('mupen64plus-libretro-nx',    'Makefile',          '.',                 'jni', {'soname': 'mupen64plus_next'}),
    'nestopia':                  ('nestopia',                   'Makefile',          'libretro',          'libretro/jni', {}),
    'nx':                        ('nxengine-libretro',          'Makefile',          '.',                 'jni', {'soname': 'nxengine'}),
    'o2em':                      ('libretro-o2em',              'Makefile',          '.',                 'jni', {}),
    'opera':                     ('opera-libretro',             'Makefile',          '.',                 'jni', {}),
    'openlara':                  ('OpenLara',                   'Makefile',          'src/platform/libretro', 'src/platform/libretro/jni', {}),
    'parallel_n64':              ('parallel-n64',               'Makefile',          '.',                 'jni', {}),
    'parallext':                 ('parallext',                  'Makefile',          '.',                 'libretro/jni', {'soname': 'parallel_n64'}),
    'pcem':                      ('libretro-pcem',              'Makefile.libretro', 'src',               'jni', {}),
    'pcsx-rearmed':              ('pcsx_rearmed',               'Makefile.libretro', '.',                 'jni', {'soname': 'pcsx_rearmed'}),
    'picodrive':                 ('picodrive',                  'Makefile.libretro', '.',                 'jni', {}),
    'pocketcdg':                 ('libretro-pocketcdg',         'Makefile',          '.',                 'jni', {}),
    'pokemini':                  ('PokeMini',                   'Makefile.libretro', '.',                 'jni', {}),
    'ppsspp':                    ('ppsspp',                     'Makefile',          'libretro',          'jni', {}),  # Longrunning, requires OpenGL
    'prboom':                    ('libretro-prboom',            'Makefile',          '.',                 'jni', {}),
    'prosystem':                 ('prosystem-libretro',         'Makefile',          '.',                 'jni', {}),
    'px68k':                     ('px68k-libretro',             'Makefile.libretro', '.',                 'jni', {}),
    'quasi88':                   ('quasi88-libretro',           'Makefile',          '.',                 'jni', {}),
    'quicknes':                  ('QuickNES_Core',              'Makefile',          '.',                 'jni', {}),
    'race':                      ('RACE',                       'Makefile',          '.',                 'jni', {}),
    'reminiscence':              ('REminiscence',               'Makefile',          '.',                 'jni', {}),
    'remotejoy':                 ('libretro-remotejoy',         'Makefile',          '.',                 'jni', {}),
    #'rustation':                 ('rustation-libretro',         'Makefile',          '.',                 'jni', {}),  # Checkout fails
    'sameboy':                   ('SameBoy',                    'Makefile',          'libretro',          'libretro/jni', {'branch': 'buildbot'}),
    'scummvm':                   ('scummvm',                    'Makefile',          'backends/platform/libretro/build', None, {'binary_dir': 'backends/platform/libretro/build'}),
    'smsplus-gx':                ('smsplus-gx',                 'Makefile.libretro', '.',                 'jni', {'soname': 'smsplus'}),
    'snes9x':                    ('snes9x',                     'Makefile',          'libretro',          'libretro/jni', {}),
    'snes9x2002':                ('snes9x2002',                 'Makefile',          '.',                 'jni', {}),
    'snes9x2010':                ('snes9x2010',                 'Makefile',          '.',                 'jni', {}),
    'stella':                    ('stella-libretro',            'Makefile',          '.',                 'jni', {'soname': 'stella2014'}),
    'supafaust':                 ('supafaust',                  'Makefile',          '.',                 'jni', {'soname': 'mednafen_supafaust'}),
    'tgbdual':                   ('tgbdual-libretro',           'Makefile',          '.',                 'jni', {}),
    'theodore':                  ('Zlika/theodore',             'Makefile',          '.',                  'jni', {}),
    'thepowdertoy':              ('ThePowderToy',               '',                  '',                  '', {'cmake': True, 'binary_dir': 'src'}),
    'tyrquake':                  ('tyrquake',                   'Makefile',          '.',                 'jni', {}),
    'uae':                       ('libretro-uae',               'Makefile',          '.',                 'jni', {'soname': 'puae'}),
    #'uae4arm':                   ('uae4arm-libretro',           'Makefile',          '.',                 'jni', {}),  # Fails to build on non arm system
    'uzem':                      ('libretro-uzem',              'Makefile.libretro', '.',                 'jni', {}),
    'vba-next':                  ('vba-next',                   'Makefile',          '.',                 'libretro/jni', {'soname': 'vba_next'}),
    'vbam':                      ('vbam-libretro',              'Makefile',          'src/libretro',      'src/libretro/jni', {}),
    'vecx':                      ('libretro-vecx',              'Makefile',          '.',                 'jni', {}),
    #'vice':                      ('vice-libretro',              'Makefile.libretro', '.',                 'jni', {'soname': 'vice_x64'}),  # Settings broken for option API version 0
    'virtualjaguar':             ('virtualjaguar-libretro',     'Makefile',          '.',                 'jni', {}),
    'xmil':                      ('xmil-libretro',              'Makefile.libretro', 'libretro',          'libretro/jni', {'soname': 'x1'}),
    'yabause':                   ('yabause',                    'Makefile',          'yabause/src/libretro', 'yabause/src/libretro/jni', {}),
}
