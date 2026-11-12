# kodi_libretro_buildbot_game_addons for Kodi

This is a script that generates [Kodi](http://kodi.tv) game addons from the [libretro buildbot](http://buildbot.libretro.com) binaries.
This is experimental at this point and the addon that is built may not always work with Kodi (although the majority seem to in my testing).  The addons should auto build (if an update is found) using Github Actions once every week.

To install the game addons, choose the appropriate repository:
- Kodi App users on Windows, Linux, Mac OS (arm64) and Android (aarch64) can install [this repository](https://github.com/zach-morris/kodi_libretro_buildbot_game_addons/raw/main/repository.kodi_libretro_buildbot_game_addons.zip)
- LibreElec x86_64 users can install [this repository](https://github.com/zach-morris/kodi_libretro_buildbot_game_addons/raw/main/repository.kodi_libretro_buildbot_game_addons_libreelec-x86_64.zip)
- LibreElec on aarch64 architectures can install [this repository](https://github.com/zach-morris/kodi_libretro_buildbot_game_addons/raw/main/repository.kodi_libretro_buildbot_game_addons_libreelec-aarch64.zip)

You will also need the Libretro Compatability addon ([game.libretro](https://kodi.wiki/view/Add-on:Libretro_Compatibility)) installed for Kodi, which is available in the official Kodi repository.  This repository does not provide that addon for your architecture.

If your systems architecture is not included in the above, you can download this script from [here](https://github.com/zach-morris/kodi_libretro_buildbot_game_addons/raw/main/resources/standalone_script/kodi_libretro_buildbot_game_addons.zip) to build for the system of your choice using python.

Usage:
```
usage: python kodi_libretro_buildbot_addons_generator.py [-h] [--addons_to_build [ADDONS_TO_BUILD]] [--environments_to_build [ENVIRONMENTS_TO_BUILD]]
                                                  [--update_kodi_game_files] [--dont_check_existing_addons] [--dont_remove_large_addons]
                                                  [--max_file_size MAX_FILE_SIZE] [--dont_remove_old_addons] [--dont_clear_temp_after_build]
                                                  [--dont_generate_addon_repository_xml] [--build_environment BUILD_ENVIRONMENT]

options:
  -h, --help            show this help message and exit
  --addons_to_build [ADDONS_TO_BUILD]
                        Comma-separated addon names to build (default: all, but skipping some cores that are mainly for testing. Options: See
                        libretro buildbot website).  eg. --addons_to_build='mesen2_libretro,eduke32_libretro' will build those two addons.

  --environments_to_build [ENVIRONMENTS_TO_BUILD]
                        Comma-separated list of architectures to build for (default: all, but skipping non-standard environments, options: android-
                        aarch64,android-armv7,android-x86_64,ios-aarch64,libreelec-aarch64,libreelec-x86_64,linux-aarch64,linux-
                        armv7,linux-x86_64,osx-arm64,osx-x86_64,tvos-aarch64,windows-x86_64).  eg.  --environments_to_build='osx-arm64,linux-x86_64' will generate addons for use on those two architetures.
  --update_kodi_game_files
                        Update supporting kodi-game resources. Beneficial if you want to use the latest files available from the kodi-game github
                        organization.  Note you *will* need to include this flag when first run on your system.
  --dont_check_existing_addons
                        Do not check for existing addons. Beneficial if your just running this locally and want different versions of the addon.
  --dont_remove_large_addons
                        Do not remove addons exceeding the maximum file size. Beneficial if your just running this locally.
  --max_file_size MAX_FILE_SIZE
                        Maximum addon ZIP size in bytes (default: 104857600).
  --dont_remove_old_addons
                        Do not remove old addons. Beneficial if your just running this locally and want different versions of the addon.
  --dont_clear_temp_after_build
                        Keep temporary files after the build. Beneficial if your just testing.
  --dont_generate_addon_repository_xml
                        Dont generate the repository addon xml files. Beneficial if your just running this locally.
  --build_environment BUILD_ENVIRONMENT
                        The environment you are using for building addons (default: linux-x86_64, options: android-aarch64,android-armv7,android-x86_64,ios-
                        aarch64,libreelec-aarch64,libreelec-x86_64,linux-aarch64,linux-armv7,linux-x86_64,osx-arm64,osx-x86_64,tvos-
                        aarch64,windows-x86_64).  eg. I'm building on a windows pc, then --build_environment='windows-x86_64'
```


Licenses
-------------

This buildbot repository is licensed under the [GNU GENERAL PUBLIC LICENSE Version 3](https://www.gnu.org/licenses/gpl-3.0.en.html).

Addons built with this code contain their own licenses as applicable and the license can be found in the individual addon.xml contained therin.

Images created procedurally using retroarch icons that can be found [here](https://github.com/libretro/retroarch-assets/), and are covered by the CC Attribution 4.0 International license.