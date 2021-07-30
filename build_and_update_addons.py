## Start of script
import os, requests, zipfile, json, shlex, shutil, glob, logging, datetime
# from lib.kodi_game_scripting.libretro_ctypes import LibretroWrapper
from lib.bb_utils import *

import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

script_settings = dict()
script_settings['temp_directory'] = os.path.join(os.getcwd(),'temp')
if not os.path.isdir(script_settings['temp_directory']):
	os.mkdir(script_settings['temp_directory'])
script_settings['log_level'] = 'info'
script_settings['log_file'] = None
script_settings['overwrite_locals'] = False
script_settings['icon_common'] = os.path.join(os.getcwd(),'resources','icon.png')
script_settings['addon_resources_dir'] = os.path.join(os.getcwd(),'resources','addon_resources')
script_settings['ignore_these_cores_common'] = ['2048_libretro','3dengine_libretro','dolphin_launcher_libretro','stonesoup_libretro','testgl_libretro','test_libretro','ffmpeg_libretro','remotejoy_libretro','imageviewer_libretro','fbalpha_libretro','00_example_libretro','testvulkan_async_compute_libretro','testsw_vram_libretro','testsw_libretro','testretroluxury_libretro','testinput_buttontest_libretro','testgl_libretro','testgl_ff_libretro','testgl_compute_shaders_libretro','testaudio_playback_wav_libretro','testaudio_no_callback_libretro','testaudio_callback_libretro','test_netplay_libretro','pcsx_rearmed_interpreter_libretro','advanced_tests_libretro','parallel_n64_debug_libretro']
script_settings['all_cores_common'] = ['2048_libretro', '4do_libretro', '81_libretro', 'atari800_libretro', 'bluemsx_libretro', 'bnes_libretro', 'bsnes_accuracy_libretro', 'bsnes_balanced_libretro', 'bsnes_cplusplus98_libretro', 'bsnes_mercury_accuracy_libretro', 'bsnes_mercury_balanced_libretro', 'bsnes_mercury_performance_libretro', 'bsnes_performance_libretro', 'cannonball_libretro', 'cap32_libretro', 'chailove_libretro', 'citra_canary_libretro', 'citra_libretro', 'craft_libretro', 'crocods_libretro', 'daphne_libretro', 'desmume2015_libretro', 'desmume_libretro', 'dinothawr_libretro', 'dolphin_libretro', 'dosbox_libretro', 'dosbox_svn_libretro', 'easyrpg_libretro', 'emux_chip8_libretro', 'emux_gb_libretro', 'emux_nes_libretro', 'emux_sms_libretro', 'fbalpha2012_cps1_libretro', 'fbalpha2012_cps2_libretro', 'fbalpha2012_libretro', 'fbalpha2012_neogeo_libretro', 'fbalpha_libretro', 'fbneo_libretro', 'fceumm_libretro', 'flycast_libretro', 'flycast_wince_libretro', 'fmsx_libretro', 'freeintv_libretro', 'fuse_libretro', 'gambatte_libretro', 'gearboy_libretro', 'gearsystem_libretro', 'genesis_plus_gx_libretro', 'gme_libretro', 'gpsp_libretro', 'gw_libretro', 'handy_libretro', 'hatari_libretro', 'higan_sfc_balanced_libretro', 'higan_sfc_libretro', 'ishiiruka_libretro', 'kronos_libretro', 'lutro_libretro', 'mame2000_libretro', 'mame2003_libretro', 'mame2003_plus_libretro', 'mame2010_libretro', 'mame2015_libretro', 'mame_libretro', 'mednafen_gba_libretro', 'mednafen_lynx_libretro', 'mednafen_ngp_libretro', 'mednafen_pce_fast_libretro', 'mednafen_pce_libretro', 'mednafen_pcfx_libretro', 'mednafen_psx_hw_libretro', 'mednafen_psx_libretro', 'mednafen_saturn_libretro', 'mednafen_snes_libretro', 'mednafen_supergrafx_libretro', 'mednafen_vb_libretro', 'mednafen_wswan_libretro', 'melonds_libretro', 'mesen-s_libretro', 'mesen_libretro', 'mess2015_libretro', 'meteor_libretro', 'mgba_libretro', 'mrboom_libretro', 'mu_libretro', 'nekop2_libretro', 'nestopia_libretro', 'np2kai_libretro', 'nxengine_libretro', 'o2em_libretro', 'openlara_libretro', 'parallel_n64_libretro', 'pcsx_rearmed_interpreter_libretro', 'pcsx_rearmed_libretro', 'picodrive_libretro', 'play_libretro', 'pocketcdg_libretro', 'pokemini_libretro', 'ppsspp_libretro', 'prboom_libretro', 'prosystem_libretro', 'puae_libretro', 'px68k_libretro', 'quicknes_libretro', 'reminiscence_libretro', 'sameboy_libretro', 'scummvm_libretro', 'snes9x2002_libretro', 'snes9x2005_libretro', 'snes9x2010_libretro', 'snes9x_libretro', 'squirreljme_libretro', 'stella2014_libretro', 'stella_libretro', 'tgbdual_libretro', 'theodore_libretro', 'thepowdertoy_libretro', 'tyrquake_libretro', 'ume2015_libretro', 'uzem_libretro', 'vba_next_libretro', 'vbam_libretro', 'vecx_libretro', 'vice_x128_libretro', 'vice_x64_libretro', 'vice_xplus4_libretro', 'vice_xvic_libretro', 'virtualjaguar_libretro', 'xrick_libretro', 'yabause_libretro']
script_settings['cores_test'] = ['cannonball_libretro','fbalpha2012_libretro', 'fbneo_libretro', 'mame2003_plus_libretro', 'mesen_libretro', 'nestopia_libretro', 'pocketcdg_libretro', 'pokemini_libretro', 'snes9x_libretro', 'tyrquake_libretro']
script_settings['buildbot_settings'] = dict()
# script_settings['wrapper_platform'] = 'osx-x86_64' #Use kodi-game-scripting LibretroWrapper on this platform
script_settings['wrapper_platform'] = 'linux' #Use kodi-game-scripting LibretroWrapper on this platform
script_settings['build_opengl_addons'] = True
script_settings['buildbot_info_zip'] = 'https://github.com/libretro/libretro-core-info/archive/master.zip'
script_settings['buildbot_info_git'] = 'https://github.com/libretro/libretro-super/tree/master/dist/info'
script_settings['buildbot_info_folder'] = 'libretro-core-info-master'
script_settings['main_repo_platforms'] = ['osx-x86_64','android-aarch64','android-armv7','linux','windows-i686','windows-x86_64',] #Platforms for the main repository
script_settings['le_generic_repo_platforms'] = ['linux_le_generic',] #Platforms for the LE generic repository
script_settings['le_armhf_repo_platforms'] = ['linux_le_armhf',] #Platforms for the LE ARMHF repository

script_settings['buildbot_settings']['kodi_platforms'] = [  'osx-x86_64', #Only 64 bit osx now available
															'android-aarch64',
															'android-armv7',
															'linux',  #Assume only 64 bit linux for now, but both 32 bit and 64 bit are available in the ppa
															'windows-i686',  #32 bit windows
															'windows-x86_64', #64 bit windows
															'linux_le_generic', #64 bit LE generic, will be listed as all in the addon.xml
															'linux_le_armhf', #ARMHF (RPI) LE, will be listed as all in the addon.xml
															]
#Not included at this point
# 'android-i686',
# 'freebsd',
# 'ios-armv7',
# 'ios-aarch64',
# 'osx-i686',

script_settings['buildbot_settings']['kodi_libraries'] = [  '@library_osx',
															'@library_android',
															'@library_android',
															'@library_linux',
															'@library_windows',
															'@library_windows',
															'@library_linux',
															'@library_linux',
															]
#Not included at this point
# library_freebsd  #freebsd platform
# library_rbpi  #What is the platform for this?  "rbpi"?
# library_windowsstore  #windows x86_64 platform
script_settings['buildbot_settings']['bb_urls'] = [ 'http://buildbot.libretro.com/nightly/apple/osx/x86_64/latest/',
													'http://buildbot.libretro.com/nightly/android/latest/arm64-v8a/',
													'http://buildbot.libretro.com/nightly/android/latest/armeabi-v7a/',
													'http://buildbot.libretro.com/nightly/linux/x86_64/latest/',
													'http://buildbot.libretro.com/nightly/windows/x86/latest/',
													'http://buildbot.libretro.com/nightly/windows/x86_64/latest/',
													'http://buildbot.libretro.com/nightly/linux/x86_64/latest/',
													'http://buildbot.libretro.com/nightly/linux/armhf/latest/',
													]

#To be updated based on what works and what doesn't at some point at the platform level
script_settings['buildbot_settings']['dont_install_these_cores'] = [script_settings['ignore_these_cores_common'], #OSX x86_64
																# [x for x in script_settings['all_cores_common'] if x not in script_settings['android_cores_test']], #Android 64
																# [x for x in script_settings['all_cores_common'] if x not in script_settings['android_cores_test']], #Android v7a
																script_settings['ignore_these_cores_common'], #Android 64
																script_settings['ignore_these_cores_common'], #Android v7a
																script_settings['ignore_these_cores_common'], #Linux x86_64
																script_settings['ignore_these_cores_common']+['mame_libretro'], #Windows x86, MAME is too big for github
																script_settings['ignore_these_cores_common']+['mame_libretro'], #Windows x86_64, MAME is too big for github
																# [x for x in script_settings['all_cores_common'] if x not in script_settings['cores_test']], #LE x86_64
																# [x for x in script_settings['all_cores_common'] if x not in script_settings['cores_test']], #LE ARMHF, MAME is too big for github
																script_settings['ignore_these_cores_common'], #LE x86_64
																script_settings['ignore_these_cores_common']+['mame_libretro'], #LE ARMHF, MAME is too big for github
																]

script_settings['buildbot_settings']['build_platform_addons'] = [True,
																True,
																True,
																True,
																False,
																True,
																True,
																True,
																]
broken_tag = 'Not yet compatible'
#These were found to not work just in testing, so mark them as broken until proven otherwise
script_settings['addons_to_mark_as_broken'] = ['game.libretro.bnes_libretro_buildbot',
'game.libretro.bsnes_cplusplus98_libretro_buildbot',
'game.libretro.citra_canary_libretro_buildbot',
'game.libretro.citra_libretro_buildbot',
'game.libretro.dolphin_libretro_buildbot',
'game.libretro.emux_gb_libretro_buildbot',
'game.libretro.emux_nes_libretro_buildbot',
'game.libretro.emux_sms_libretro_buildbot',
'game.libretro.flycast_libretro_buildbot',
'game.libretro.flycast_wince_libretro_buildbot',
'game.libretro.ishiiruka_libretro_buildbot',
'game.libretro.kronos_libretro_buildbot',
'game.libretro.mesen-s_libretro_buildbot',
'game.libretro.mesen_libretro_buildbot',
'game.libretro.openlara_libretro_buildbot',
'game.libretro.parallel_n64_libretro_buildbot',
'game.libretro.play_libretro_buildbot',
'game.libretro.ppsspp_libretro_buildbot']

##end of setup, start of script

#Get latest libretro info files
if 'libretro_info' not in locals() and not script_settings['overwrite_locals']:
	libretro_info = dict()
	# libretro_info['files'] = [x for x in download_file(script_settings['buildbot_info_zip'],os.path.join(script_settings['temp_directory'],'info.zip')) if '.info' in x and os.path.split(x)[-1].replace('.info','') not in script_settings['ignore_these_cores_common']]
	# libretro_info['name_clean'] = [os.path.split(x)[-1].replace('.info','') for x in libretro_info['files']]
	# libretro_info['dicts'] = [return_info_dict_from_libretro_info_file(x) for x in libretro_info['files']]
	libretro_info['dicts'] = get_git_info(script_settings['buildbot_info_git'],ignore_these_cores_common=script_settings['ignore_these_cores_common'])
	libretro_info['name_clean'] = [x['core_name'] for x in libretro_info['dicts']]
	if os.path.isdir(os.path.join(script_settings['temp_directory'],script_settings['buildbot_info_folder'])):
		shutil.rmtree(os.path.join(script_settings['temp_directory'],script_settings['buildbot_info_folder']))

#Get latest buildbot index files
if 'libretro_bb_info' not in locals() and not script_settings['overwrite_locals']:
	libretro_bb_info = dict()
	libretro_bb_info['platform'] = [x for ii,x in enumerate(script_settings['buildbot_settings']['kodi_platforms']) if script_settings['buildbot_settings']['build_platform_addons'][ii]]
	libretro_bb_info['index_urls'] = [x+'.index-extended' for ii,x in enumerate(script_settings['buildbot_settings']['bb_urls']) if script_settings['buildbot_settings']['build_platform_addons'][ii]]
	libretro_bb_info['dicts'] = [parse_index_data(read_text_url(x)) for x in libretro_bb_info['index_urls']]

#Generate build data
print('Generating build data')
build_data = dict()
for kk in script_settings['buildbot_settings'].keys():
	build_data[kk] = [x for ii,x in enumerate(script_settings['buildbot_settings'][kk]) if script_settings['buildbot_settings']['build_platform_addons'][ii]]
build_data['libretro_bb_info_dict'] = [libretro_bb_info['dicts'][libretro_bb_info['platform'].index(x)] for ii,x in enumerate(build_data['kodi_platforms']) if build_data['build_platform_addons'][ii]]
build_data['libretro_info_dict'] = [list() for x in build_data['libretro_bb_info_dict']]
build_data['addon_xml'] = [list() for x in build_data['libretro_bb_info_dict']]
build_data['settings_xml'] = [list() for x in build_data['libretro_bb_info_dict']]
build_data['build_report'] = [list() for x in build_data['libretro_bb_info_dict']]
build_data['current_builds'] = [glob.glob(os.path.join(os.getcwd(),x,'*.zip')) for x in build_data['kodi_platforms']]
for ii,platforms in enumerate(build_data['kodi_platforms']):
	for jj,core_name in enumerate(build_data['libretro_bb_info_dict'][ii]['filename_clean']):
		current_version = None
		if core_name in libretro_info['name_clean']:
			build_data['libretro_info_dict'][ii].append(libretro_info['dicts'][libretro_info['name_clean'].index(core_name)])
		else:
			build_data['libretro_info_dict'][ii].append(None)
		if build_data['libretro_info_dict'][ii][-1] is not None:
			current_version = '1.%(minor_version)s.%(patch_version)s'%{'minor_version':(datetime.datetime.fromisoformat(build_data['libretro_bb_info_dict'][ii]['date'][jj])).year,'patch_version':(datetime.datetime.fromisoformat(build_data['libretro_bb_info_dict'][ii]['date'][jj])- datetime.datetime(1970,1,1)).days} #Updating versioning to follow Kodi standard
			if core_name in build_data['dont_install_these_cores'][ii]:
				build_this_addon = False
			else:
				if 'game.libretro.'+core_name+'_buildbot'+'-'+current_version in [os.path.split(x)[-1].replace('.zip','') for x in build_data['current_builds'][ii]]:
					build_this_addon = False #Build already exists, so don't re-download
				else:
					build_this_addon = True #Build does not exist yet
				if 'game.libretro.'+core_name+'_buildbot' in [os.path.split(x)[-1].rsplit('-',1)[0] for x in build_data['current_builds'][ii]]:
					current_build = build_data['current_builds'][ii][[os.path.split(x)[-1].rsplit('-',1)[0] for x in build_data['current_builds'][ii]].index('game.libretro.'+core_name+'_buildbot')]  #Same addon, different commit.  This will be used to delete if a new version is available, or to grab settings data for if new version is not available
				else:
					current_build = None
			build_data['addon_xml'][ii].append(create_addon_xml_dict(kodi_platform=platforms,addon_id='game.libretro.'+core_name+'_buildbot',addon_name=build_data['libretro_info_dict'][ii][-1].get('display_name'),addon_version=current_version,addon_commit=build_data['libretro_bb_info_dict'][ii].get('commit')[jj],addon_date=build_data['libretro_bb_info_dict'][ii].get('date')[jj],addon_supported_extensions=build_data['libretro_info_dict'][ii][-1].get('supported_extensions'),addon_supported_standalone=build_data['libretro_info_dict'][ii][-1].get('supports_no_game'),addon_license=build_data['libretro_info_dict'][ii][-1].get('license'),addon_description=generate_info_description(build_data['libretro_info_dict'][ii][-1]),addon_system_description=build_data['libretro_info_dict'][ii][-1].get('systemname'),addon_library_key=build_data['kodi_libraries'][ii],addon_library_value=build_data['libretro_bb_info_dict'][ii]['filename'][jj].replace('.zip',''),buildbot_source_url=build_data['bb_urls'][ii]+build_data['libretro_bb_info_dict'][ii]['filename'][jj],addon_resources_data=get_addon_resources_data(core_name=core_name,resources_dir=script_settings['addon_resources_dir']),build_addon=build_this_addon,current_build=current_build))
			build_data['settings_xml'][ii].append(None) #For later building
			build_data['build_report'][ii].append(None) #For later building
		else:
			build_data['addon_xml'][ii].append(None)
			build_data['settings_xml'][ii].append(None) #For later building
			build_data['build_report'][ii].append(None) #For later building


#First build addons for wrapper platform to get proper settings data
for ii,platforms in enumerate(build_data['kodi_platforms']):
	if platforms == script_settings['wrapper_platform']:
		for jj,addon_data in enumerate(build_data['addon_xml'][ii]):
			if addon_data is not None and build_data['settings_xml'][ii][jj] is None:  #Settings xml is not yet built
				if build_data['addon_xml'][ii][jj]['build_addon']: #Attempt to build addon from buildbot, getting latest settings data
					print(build_data['addon_xml'][ii][jj]['build_addon'])
					success,build_data['settings_xml'][ii][jj],supporting_data = download_binary_and_generate_settings(source=get_addon_source_from_addon_xml(build_data['addon_xml'][ii][jj]),current_platform=build_data['kodi_platforms'][ii],wrapper_platform=script_settings['wrapper_platform'],download_folder_path=script_settings['temp_directory'])
					if supporting_data is not None: #Populate vfs and standalone info
						if supporting_data['opengl_linkage'] is not None:
							if supporting_data['opengl_linkage'] and not script_settings['build_opengl_addons']:
								print('Excluding build of %(core_name)s because it requires opengl' % {'core_name': build_data['addon_xml'][ii][jj]['@id']})
								build_data['addon_xml'][ii][jj]['build_addon'] = False
						if 'extension' in build_data['addon_xml'][ii][jj].keys():
							for kk,extensions in enumerate(build_data['addon_xml'][ii][jj]['extension']):
								if 'supports_vfs' in extensions.keys():
									build_data['addon_xml'][ii][jj]['extension'][kk]['supports_vfs'] = supporting_data['supports_vfs']
								if 'supports_standalone' in extensions.keys():
									build_data['addon_xml'][ii][jj]['extension'][kk]['supports_standalone'] = supporting_data['supports_standalone']
								# if 'source' in extensions.keys() and build_data['addon_xml'][ii][jj]['@id'] in script_settings['addons_to_mark_as_broken']:
								# 	build_data['addon_xml'][ii][jj]['extension'][kk]['broken'] = broken_tag
					if not success: #Something failed, so dont attempt to generate the addon
						print('Unable to generate settings for %(core_name)s. This addon cannot be built' % {'core_name': build_data['addon_xml'][ii][jj]['@id']})
						build_data['addon_xml'][ii][jj]['build_addon'] = False
					else:
						if build_data['addon_xml'][ii][jj]['build_addon']:
							build_data['build_report'][ii][jj]=build_addon(addon_dict_in=build_data['addon_xml'][ii][jj],settings_dict_in=build_data['settings_xml'][ii][jj],temp_folder=script_settings['temp_directory'],binary_folder=script_settings['temp_directory'],platform_folder=os.path.join(os.getcwd(),build_data['kodi_platforms'][ii]),icon_path=script_settings['icon_common'])
				else: #Do not attempt to build from buildbot, but if there's an existing addon, grab settings and addon data from that
					if build_data['addon_xml'][ii][jj]['current_build'] is not None:
						current_build_addon_xml = extract_addonxml_from_current_build(current_build=build_data['addon_xml'][ii][jj]['current_build'],platform=platforms,include_path_and_size=False)
						build_data['settings_xml'][ii][jj] = extract_settings_from_current_build(current_build=build_data['addon_xml'][ii][jj]['current_build'])
						if 'extension' in build_data['addon_xml'][ii][jj].keys():
							for kk,extensions in enumerate(build_data['addon_xml'][ii][jj]['extension']):
								if 'supports_vfs' in extensions.keys():
									build_data['addon_xml'][ii][jj]['extension'][kk]['supports_vfs'] = current_build_addon_xml['extension'][kk]['supports_vfs']
								if 'supports_standalone' in extensions.keys():
									build_data['addon_xml'][ii][jj]['extension'][kk]['supports_standalone'] = current_build_addon_xml['extension'][kk]['supports_standalone']
								# if 'source' in extensions.keys() and build_data['addon_xml'][ii][jj]['@id'] in script_settings['addons_to_mark_as_broken']:
								# 	build_data['addon_xml'][ii][jj]['extension'][kk]['broken'] = broken_tag
# Now copy settings data to other platforms to generate the addons
for ii,platforms in enumerate(build_data['kodi_platforms']):
	if platforms != script_settings['wrapper_platform']:
		for jj,addon_data in enumerate(build_data['addon_xml'][ii]):
			if addon_data is not None:
				try:
					addon_idx = [x for x in build_data['libretro_bb_info_dict'][build_data['kodi_platforms'].index(script_settings['wrapper_platform'])]['filename_clean']].index(build_data['libretro_bb_info_dict'][ii]['filename_clean'][jj])
				except:
					addon_idx = None
					print('Data for %(core_name)s not found in wrapper platform, looking in the platform folder for an older version' % {'core_name': build_data['addon_xml'][ii][jj]['@id']})
				if addon_idx is None:
					if build_data['addon_xml'][ii][jj]['current_build'] is not None:
						build_data['settings_xml'][ii][jj] = extract_settings_from_current_build(current_build=build_data['addon_xml'][ii][jj]['current_build'])
						# build_data['addon_xml'][ii][jj]['build_addon'] = True
					else:
						print('Unable to generate settings for %(core_name)s. This addon cannot be built' % {'core_name': build_data['addon_xml'][ii][jj]['@id']})
						build_data['addon_xml'][ii][jj]['build_addon'] = False
				else:
					# print('Copying settings for %(core_name)s from %(wrapper_platform)s to %(current_platform)s' % {'core_name': build_data['addon_xml'][ii][jj]['@id'],'wrapper_platform':script_settings['wrapper_platform'],'current_platform':platforms})
					build_data['settings_xml'][ii][jj] = build_data['settings_xml'][build_data['kodi_platforms'].index(script_settings['wrapper_platform'])][addon_idx]
					if 'extension' in build_data['addon_xml'][ii][jj].keys(): #Copy vfs and standalone data from wrapper platform
						for kk,extensions in enumerate(build_data['addon_xml'][ii][jj]['extension']):
							if 'supports_vfs' in extensions.keys():
								if build_data['addon_xml'][build_data['kodi_platforms'].index(script_settings['wrapper_platform'])][addon_idx]['extension'][kk]['supports_vfs'] == 'true': #Bit flip this
									build_data['addon_xml'][ii][jj]['extension'][kk]['supports_vfs'] = 'true'
								else:
									build_data['addon_xml'][ii][jj]['extension'][kk]['supports_vfs'] = 'false'
							if 'supports_standalone' in extensions.keys():
								build_data['addon_xml'][ii][jj]['extension'][kk]['supports_standalone'] = build_data['addon_xml'][build_data['kodi_platforms'].index(script_settings['wrapper_platform'])][addon_idx]['extension'][kk]['supports_standalone']
#Now build the other platforms
for ii,platforms in enumerate(build_data['kodi_platforms']):
	if platforms != script_settings['wrapper_platform']:
		for jj,addon_data in enumerate(build_data['addon_xml'][ii]):
			if addon_data is not None:
				if build_data['addon_xml'][ii][jj]['build_addon']:
					if download_binary_only(source=get_addon_source_from_addon_xml(build_data['addon_xml'][ii][jj]),current_platform=build_data['kodi_platforms'][ii],download_folder_path=script_settings['temp_directory']):
						build_data['build_report'][ii][jj]=build_addon(addon_dict_in=build_data['addon_xml'][ii][jj],settings_dict_in=build_data['settings_xml'][ii][jj],temp_folder=script_settings['temp_directory'],binary_folder=script_settings['temp_directory'],platform_folder=os.path.join(os.getcwd(),build_data['kodi_platforms'][ii]),icon_path=script_settings['icon_common'])


#Now generate the repository addons.xml and md5 for the main repo
repo_addons_xml = dict()
repo_addons_xml['addons'] = dict()
repo_addons_xml['addons']['addon'] = list()
for ii,platforms in enumerate(build_data['kodi_platforms']):
	if platforms in script_settings['main_repo_platforms']:
		repo_addons_xml['addons']['addon'] = repo_addons_xml['addons']['addon']+[extract_addonxml_from_current_build(current_build=x,platform=platforms) for x in glob.glob(os.path.join(os.getcwd(),platforms,'*.zip'))]

#Mark addons broken if necessary
for ii,addons in enumerate(repo_addons_xml['addons']['addon']):
	if 'extension' in addons.keys():
		for kk,extensions in enumerate(addons['extension']):
			if 'source' in extensions.keys() and addons['@id'] in script_settings['addons_to_mark_as_broken']:
				repo_addons_xml['addons']['addon'][ii]['extension'][kk]['broken'] = broken_tag

print('Writing repository addons.xml and md5 file for the Main Repo')
pretty_write_xml(repo_addons_xml,os.path.join(os.getcwd(),'addons.xml'))
generate_md5_file(os.path.join(os.getcwd(),'addons.xml'))
change_text = generate_changelog(build_data)
if change_text is not None:
	with open(os.path.join(os.getcwd(),'changelog.txt'),'w') as change_file: 
		change_file.write(change_text) 


#Now generate the repository addons.xml and md5 for the LE Generic Repo
repo_addons_xml_le_generic = dict()
repo_addons_xml_le_generic['addons'] = dict()
repo_addons_xml_le_generic['addons']['addon'] = list()
for ii,platforms in enumerate(build_data['kodi_platforms']):
	if platforms in script_settings['le_generic_repo_platforms']:
		repo_addons_xml_le_generic['addons']['addon'] = repo_addons_xml_le_generic['addons']['addon']+[extract_addonxml_from_current_build(current_build=x,platform=platforms) for x in glob.glob(os.path.join(os.getcwd(),platforms,'*.zip'))]

#Mark addons broken if necessary
for ii,addons in enumerate(repo_addons_xml_le_generic['addons']['addon']):
	if 'extension' in addons.keys():
		for kk,extensions in enumerate(addons['extension']):
			if 'source' in extensions.keys() and addons['@id'] in script_settings['addons_to_mark_as_broken']:
				repo_addons_xml_le_generic['addons']['addon'][ii]['extension'][kk]['broken'] = broken_tag

print('Writing repository addons.xml and md5 file for LE Generic Repo')
pretty_write_xml(repo_addons_xml_le_generic,os.path.join(os.getcwd(),'addons_le_generic.xml'))
generate_md5_file(os.path.join(os.getcwd(),'addons_le_generic.xml'))


#Now generate the repository addons.xml and md5 for the LE ARMHF Repo
repo_addons_xml_le_armhf = dict()
repo_addons_xml_le_armhf['addons'] = dict()
repo_addons_xml_le_armhf['addons']['addon'] = list()
for ii,platforms in enumerate(build_data['kodi_platforms']):
	if platforms in script_settings['le_armhf_repo_platforms']:
		repo_addons_xml_le_armhf['addons']['addon'] = repo_addons_xml_le_armhf['addons']['addon']+[extract_addonxml_from_current_build(current_build=x,platform=platforms) for x in glob.glob(os.path.join(os.getcwd(),platforms,'*.zip'))]

#Mark addons broken if necessary
for ii,addons in enumerate(repo_addons_xml_le_armhf['addons']['addon']):
	if 'extension' in addons.keys():
		for kk,extensions in enumerate(addons['extension']):
			if 'source' in extensions.keys() and addons['@id'] in script_settings['addons_to_mark_as_broken']:
				repo_addons_xml_le_armhf['addons']['addon'][ii]['extension'][kk]['broken'] = broken_tag

print('Writing repository addons.xml and md5 file for LE ARMHF Repo')
pretty_write_xml(repo_addons_xml_le_armhf,os.path.join(os.getcwd(),'addons_le_armhf.xml'))
generate_md5_file(os.path.join(os.getcwd(),'addons_le_armhf.xml'))


# print('Sanity check - verify addons have same vfs flags')
# check = [[(y,x['extension'][0]['supports_vfs']) for x in repo_addons_xml['addons']['addon'] if x['@id'] == y] for y in set([x['@id'] for x in repo_addons_xml['addons']['addon']]) if not (all([x['extension'][0]['supports_vfs']=='true' for x in repo_addons_xml['addons']['addon'] if x['@id'] == y]) or all([x['extension'][0]['supports_vfs']=='false' for x in repo_addons_xml['addons']['addon'] if x['@id'] == y]))]
# print(check)
# print('Sanity check - verify addons have same standalone flags')
# check = [[(y,x['extension'][0]['supports_standalone']) for x in repo_addons_xml['addons']['addon'] if x['@id'] == y] for y in set([x['@id'] for x in repo_addons_xml['addons']['addon']]) if not (all([x['extension'][0]['supports_standalone']=='true' for x in repo_addons_xml['addons']['addon'] if x['@id'] == y]) or all([x['extension'][0]['supports_standalone']=='false' for x in repo_addons_xml['addons']['addon'] if x['@id'] == y]))]
# print(check)

print('Cleaning up.')
shutil.rmtree(script_settings['temp_directory'])
for ffiles in [glob.glob(os.path.join(os.getcwd(),x,'*.zip')) for x in build_data['kodi_platforms']]:
	for fff in ffiles:
		if os.stat(fff).st_size > 9.9e+7:
			print('Warning!  The following file is too big %(zip_file)s' % {'zip_file': fff})
print('Done!')