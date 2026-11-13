##Zach Morris
##V2 of Kodi Libretro Buildbot Addons Generator
from pathlib import Path
import platform
import pandas as pd
from lib.bb_utils import *
from lib.update_info_from_kodi_game import *

#Variables
default_build_environment = 'linux-x86_64'
default_build_environment = 'osx-arm64'

default_cores_to_skip = ['3dengine_libretro','dolphin_launcher_libretro','stonesoup_libretro','testgl_libretro','test_libretro','ffmpeg_libretro','remotejoy_libretro','imageviewer_libretro','fbalpha_libretro','00_example_libretro','testvulkan_async_compute_libretro','testsw_vram_libretro','testsw_libretro','testretroluxury_libretro','testinput_buttontest_libretro','testgl_libretro','testgl_ff_libretro','testgl_compute_shaders_libretro','testaudio_playback_wav_libretro','testaudio_no_callback_libretro','testaudio_callback_libretro','test_netplay_libretro','pcsx_rearmed_interpreter_libretro','advanced_tests_libretro','parallel_n64_debug_libretro']
default_max_file_size = 104857600

#Standard files and paths
buildbot_nightly_url = 'https://buildbot.libretro.com/nightly'
buildbot_index_ext_fn = '.index-extended'
libretro_info_files = 'https://buildbot.libretro.com/assets/frontend/info.zip'
libretro_asset_files = 'https://buildbot.libretro.com/assets/frontend/assets.zip'
preferred_asset_paths = [Path('xmb').joinpath('retrosystem'),Path('xmb').joinpath('systematic'),Path('xmb').joinpath('flatux')] #Order of paths to search for the right image

#(addon_generator_folder,
#kodi_platform - https://github.com/xbmc/xbmc/blob/master/xbmc/addons/addoninfo/AddonInfoBuilder.cpp#L772,
#kodi_library - https://github.com/xbmc/xbmc/blob/master/xbmc/addons/addoninfo/AddonInfoBuilder.cpp#L772C1-L798C2
#buildbot_sub_url_path - The sub url path to cores in the buildbox
#default_build_addon - if addons of this type should be build by default, can be changed with cli
#addon_repository - the repository the addon will live in
#)

addons_generator_mapping =[
('linux-x86_64','linux-x86_64','library_linux','/linux/x86_64/latest/',True,'main'),
('linux-aarch64','linux-aarch64','library_linux','/linux/aarch64/latest/',True,'main'),
('osx-arm64','osx-arm64','library_osx','/apple/osx/arm64/latest/',True,'main'),
('osx-x86_64','osx-x86_64','library_osx','/apple/osx/x86_64/latest/',False,'main'),
('windows-x86_64','windows-x86_64','library_windows','/windows/x86_64/latest/',True,'main'),
('android-aarch64','android-aarch64','library_android','/android/latest/arm64-v8a/',True,'main'),
('libreelec-x86_64','all','library_linux','/linux/x86_64/latest/',True,'libreelec_x86_64'),
('libreelec-aarch64','all','library_linux','/linux/aarch64/latest/',True,'libreelec_aarch64'),
('tvos-aarch64','tvos-aarch64','library_darwin_embedded','/apple/tvos-arm64/latest/',False,'main'),
('ios-aarch64','ios-aarch64','library_darwin_embedded','/apple/ios-arm64/latest/',False,'main'),
('android-x86_64','android-x86_64','library_android','/android/latest/x86_64/',False,'main'),
('android-armv7','android-armv7','library_android','/android/latest/armeabi-v7a/',False,'main'),
('linux-armv7','linux-armv7','library_linux','/linux/armv7-neon-hf/latest/',False,'main'),
]
repository_file_mapping = {'main':Path.cwd().joinpath('addons.xml'),'libreelec_x86_64':Path.cwd().joinpath('addons_libreelec_x86_64.xml'),'libreelec_aarch64':Path.cwd().joinpath('addons_libreelec_aarch64.xml')}

info_files = None
asset_images = None

def main(args=None):

	if args is None:
		args = parse_args()

	addons_to_build = parse_comma_separated(args.addons_to_build)
	environments_to_build = parse_comma_separated(args.environments_to_build)
	build_environment = (args.build_environment if args.build_environment in [row[0] for row in addons_generator_mapping] else default_build_environment)
	update_kodi_game_files = args.update_kodi_game_files
	check_existing_addons = not args.dont_check_existing_addons
	remove_large_addons = not args.dont_remove_large_addons
	max_file_size = args.max_file_size
	remove_old_addons = not args.dont_remove_old_addons
	clear_temp_after_build = not args.dont_clear_temp_after_build
	generate_repository_xml= not args.dont_generate_addon_repository_xml
	update_standalone_script_zip = args.update_standalone_script_zip

	print('Kodi Libretrobuildbot Addons Generator Started')
	print(f'Env OS: {platform.system()} {platform.release()}')
	print(f'Env Version: {platform.version()}')
	print(f'Env Arch: {platform.machine()}')
	print(f'Env Processor: {platform.processor()}')
	if isinstance(addons_to_build,list):
		print('Addons to build: {}'.format(','.join(addons_to_build)))
	else:
		print('Addons to build: {}'.format(addons_to_build))
	if isinstance(environments_to_build,list):
		print('Environments to build: {}'.format(','.join(environments_to_build)))
	else:
		print('Environments to build: {}'.format(environments_to_build))
	print('Current Build Environment is: {}'.format(build_environment))
			
	if Path.cwd().joinpath('temp').exists():
		if Path.cwd().joinpath('temp','info').exists() and len(list(Path.cwd().joinpath('temp','info').glob('*.info')))>0:
			info_files = list(Path.cwd().joinpath('temp','info').glob('*.info'))
		else:
			Path.cwd().joinpath('temp','info').mkdir(parents=False,exist_ok=True)
			info_files = download_file(libretro_info_files,Path.cwd().joinpath('temp','info','info.zip'),unzip_download=True)
		if Path.cwd().joinpath('temp','assets').exists() and len(list(Path.cwd().joinpath('temp','assets').rglob('*.png')))>0:
			asset_images = list(Path.cwd().joinpath('temp','assets').rglob('*.png'))
		else:
			Path.cwd().joinpath('temp','assets').mkdir(parents=False,exist_ok=True)
			asset_images = download_file(libretro_asset_files,Path.cwd().joinpath('temp','assets','assets.zip'),unzip_download=True)
		if Path.cwd().joinpath('temp','build').exists() and len(list(Path.cwd().joinpath('temp','build').rglob('*.build')))>0:
			temp_build_files = list(Path.cwd().joinpath('temp','build').rglob('*.build'))
		else:
			Path.cwd().joinpath('temp','build').mkdir(parents=False,exist_ok=True)
	else:
		Path.cwd().joinpath('temp').mkdir(parents=False,exist_ok=True)
		Path.cwd().joinpath('temp','info').mkdir(parents=False,exist_ok=True)
		Path.cwd().joinpath('temp','assets').mkdir(parents=False,exist_ok=True)
		Path.cwd().joinpath('temp','cores').mkdir(parents=False,exist_ok=True)
		Path.cwd().joinpath('temp','build').mkdir(parents=False,exist_ok=True)
		info_files = download_file(libretro_info_files,Path.cwd().joinpath('temp','info','info.zip'),unzip_download=True)
		asset_images = download_file(libretro_asset_files,Path.cwd().joinpath('temp','assets','assets.zip'),unzip_download=True)
	if isinstance(asset_images,list):
		asset_images = filter_and_sort_asset_images(asset_images,preferred_asset_paths)

	if update_kodi_game_files:
		print('Updating supporting kodi-game file resources')
		kodi_game_files = find_kodi_game_files()
		if isinstance(kodi_game_files,pd.DataFrame) and not kodi_game_files.empty:
			for k in ['addon','settings','buttonmap','topology']:
				kodi_game_files['repo_name'].apply(lambda x: Path.cwd().joinpath('resources','kodi-game',x).mkdir(parents=False,exist_ok=True) if not Path.cwd().joinpath('resources','kodi-game',x).exists() else None)
				kodi_game_files[f'{k}_xml_filename'] = kodi_game_files.apply(lambda x: Path.cwd().joinpath('resources','kodi-game',x.get('repo_name'),f'{k}.xml') if isinstance(x.get('repo_name'),str) and isinstance(x.get(f'{k}_xml_content'),str) else None,axis=1)
				kodi_game_files[f'{k}_xml_save'] = kodi_game_files.apply(lambda x: write_text_to_file(x.get(f'{k}_xml_filename'),x.get(f'{k}_xml_content')),axis=1)
			kodi_game_files['strings_po_filename'] = kodi_game_files.apply(lambda x: Path.cwd().joinpath('resources','kodi-game',x.get('repo_name'),'strings.po') if isinstance(x.get('repo_name'),str) and isinstance(x.get('strings_po_content'),str) else None,axis=1)
			kodi_game_files['strings_po_save'] = kodi_game_files.apply(lambda x: write_text_to_file(x.get('strings_po_filename'),x.get('strings_po_content')),axis=1)
			kodi_game_files['icon_filename'] = kodi_game_files.apply(lambda x: Path.cwd().joinpath('resources','kodi-game',x.get('repo_name'),'icon.png') if isinstance(x.get('repo_name'),str) else None,axis=1)
			kodi_game_files['saved_icon_filename'] = kodi_game_files.apply(lambda x: download_file(url_in=x.get('icon_url'),filename_fullpath=x.get('icon_filename'),unzip_download=False),axis=1)
	else:
		kodi_game_files = pd.DataFrame([x for x in list(Path.cwd().joinpath('resources','kodi-game').glob('*')) if x.stem.startswith('game.libretro')],columns=['repo_path'])
		kodi_game_files['repo_name'] = kodi_game_files['repo_path'].apply(lambda x: x.name if isinstance(x,Path) else None)
		kodi_game_files['core_name'] = kodi_game_files['repo_name'].str.replace('game.libretro.','')
		for k in ['addon','settings','buttonmap','topology']:
			kodi_game_files[f'{k}_xml_filename'] = kodi_game_files['repo_path'].apply(lambda x: x.joinpath(f'{k}.xml') if x.joinpath(f'{k}.xml').exists() else None)
			kodi_game_files[f'{k}_xml_content'] = kodi_game_files[f'{k}_xml_filename'].apply(lambda x: x.read_text() if isinstance(x,Path) else None)
		kodi_game_files['strings_po_filename'] = kodi_game_files['repo_path'].apply(lambda x: x.joinpath('strings.po') if x.joinpath('strings.po').exists() else None)
		kodi_game_files['strings_po_content'] = kodi_game_files['strings_po_filename'].apply(lambda x: x.read_text() if isinstance(x,Path) else None)
		kodi_game_files['icon_filename'] = kodi_game_files['repo_path'].apply(lambda x: x.joinpath('icon.png') if x.joinpath('icon.png').exists() else None)
	if isinstance(kodi_game_files,pd.DataFrame) and not kodi_game_files.empty:
		kodi_game_files['addon_xml_dict'] = kodi_game_files['addon_xml_content'].apply(lambda x: xml_to_dict(x.replace('@','')))
		kodi_game_files['libretro_core'] = kodi_game_files.apply(lambda x: get_value_from_addon_xml_dict(value='libretro_core',x_in=x),axis=1)
		kodi_game_files['platforms'] = kodi_game_files.apply(lambda x: get_value_from_addon_xml_dict(value='platforms',x_in=x),axis=1)
		kodi_game_files['supports_vfs'] = kodi_game_files.apply(lambda x: get_value_from_addon_xml_dict(value='supports_vfs',x_in=x),axis=1)
		kodi_game_files['supports_standalone'] = kodi_game_files.apply(lambda x: get_value_from_addon_xml_dict(value='supports_standalone',x_in=x),axis=1)
		kodi_game_files['supports_disc_control'] = kodi_game_files.apply(lambda x: get_value_from_addon_xml_dict(value='supports_disc_control',x_in=x),axis=1)
	if isinstance(info_files,list) and len(info_files)>0:
		info_df = pd.DataFrame(info_files,columns=['info_file_path'])
		info_df['info_core_name'] = info_df['info_file_path'].apply(lambda x: x.stem)
		info_df['info_file_content'] = info_df['info_file_path'].apply(lambda x: x.read_text() if isinstance(x,Path) and x.exists() and x.suffix=='.info' else None)
		info_df['info_file_dict'] = info_df['info_file_content'].apply(lambda x: return_info_dict_from_libretro_info_text(x))
		info_df = pd.concat([info_df.drop(columns=['info_file_dict']).reset_index(drop=True),pd.json_normalize(info_df['info_file_dict']).reset_index(drop=True)],axis='columns')
	else:
		info_df = None

	if isinstance(info_df,pd.DataFrame) and not info_df.empty:
		bb_df = pd.DataFrame(addons_generator_mapping,columns=['addon_generator_folder','kodi_platform','kodi_library','bb_sub_url','default_build_addon','repository_category'])
		bb_df = bb_df.loc[(bb_df['default_build_addon']==True)]  #Update with cli when available
		bb_df['temp_path'] = Path.cwd().joinpath('temp')
		bb_df['bb_url']= buildbot_nightly_url+bb_df['bb_sub_url']
		bb_df['bb_index_ext'] = bb_df['bb_url']+buildbot_index_ext_fn
		bb_df['index_ext_content'] = bb_df['bb_index_ext'].apply(lambda x: read_text_url(x))
		bb_df['index_ext_content'] = bb_df['index_ext_content'].apply(lambda x: [y.split(' ') for y in x.split('\n')] if isinstance(x,str) else None)
		bb_df['index_ext_content'] = bb_df['index_ext_content'].apply(lambda x: [dict(zip(['bb_file_date','bb_file_crc','bb_file_filename'],y)) for y in x if isinstance(y,list) and len(y)==3] if isinstance(x,list) and len(x)>0 else None)
		bb_df=bb_df.explode(column='index_ext_content')
		bb_df = pd.concat([bb_df.drop(columns=['index_ext_content']).reset_index(drop=True),pd.json_normalize(bb_df['index_ext_content']).reset_index(drop=True)],axis='columns')
		bb_df['bb_core_url'] = bb_df['bb_url']+bb_df['bb_file_filename'].str.strip()
		bb_df = bb_df.loc[bb_df['bb_core_url'].notna()]
		bb_df['bb_core_filename'] = bb_df['bb_file_filename'].str.strip().str.rsplit('.', n=1).str[0]
		bb_df['bb_core_name'] = bb_df['bb_file_filename'].str.strip().str.rsplit('.', n=2).str[0]
		bb_df['bb_core_name_clean'] = bb_df['bb_core_name'].str.replace('_android','')
		bb_df['alternate_core_info_matches'] = bb_df['bb_core_name_clean'].apply(lambda x: get_alternate_core_info_matches(x))
		bb_df['addon_id'] = bb_df['bb_core_name_clean'].apply(lambda x: f'game.libretro.{x}_libretro_buildbot'.replace('libretro_libretro','libretro'))
		# bb_df['addon_folder_path'] = bb_df.apply(lambda x: Path.cwd().joinpath(x.get('addon_generator_folder'),x.get('addon_id')) if isinstance(x.get('addon_generator_folder'),str) and isinstance(x.get('addon_id'),str) else None,axis=1)
		bb_df['addon_folder_path'] = bb_df.apply(lambda x: Path.cwd().joinpath(x.get('addon_generator_folder')) if isinstance(x.get('addon_generator_folder'),str) else None,axis=1)
		bb_df['build_environment'] = build_environment
		bb_df['build_folder_path'] = bb_df.apply(lambda x: Path.cwd().joinpath('temp','build',x.get('addon_generator_folder'),x.get('addon_id')) if isinstance(x.get('addon_generator_folder'),str) and isinstance(x.get('addon_id'),str) else None,axis=1)
		bb_df['build_environment_folder_path'] = bb_df.apply(lambda x: Path.cwd().joinpath('temp','build',x.get('build_environment'),x.get('addon_id')) if isinstance(x.get('build_environment'),str) and isinstance(x.get('addon_id'),str) else None,axis=1)
		bb_df_alt = bb_df.merge(info_df,how='left',left_on='alternate_core_info_matches',right_on='info_core_name')
		bb_df = bb_df.merge(info_df,how='left',left_on='bb_core_name_clean',right_on='info_core_name')
		del info_df
		alt_info_indexes = bb_df.loc[bb_df['info_file_content'].isna()&bb_df.index.isin(bb_df_alt.loc[bb_df_alt['info_file_content'].notna()].index)].index
		if not alt_info_indexes.empty:
			bb_df = bb_df.drop(alt_info_indexes)
			bb_df = pd.concat([bb_df,bb_df_alt.loc[alt_info_indexes]]).reset_index(drop=True)
		bb_df['bb_file_dt'] = pd.to_datetime(bb_df['bb_file_date'])
		bb_df['database_list'] = bb_df['database'].apply(lambda x: [y.strip() for y in x.split('|')] if isinstance(x,str) else None)
		bb_df['supported_extensions_list'] = bb_df['supported_extensions'].apply(lambda x: [y.strip() for y in x.split('|')] if isinstance(x,str) else None)
		bb_df['addon_version'] = bb_df['bb_file_dt'].apply(lambda x: '1.{}.{}'.format(x.year,x.day_of_year) if isinstance(x,pd.Timestamp) else None)
		bb_df['asset_icon_filename'] = bb_df['database_list'].apply(lambda x: next(iter([y for y in asset_images if y.stem in x]),None) if isinstance(x,list) else None)
		bb_df = bb_df.merge(kodi_game_files,how='left',left_on='info_core_name',right_on='libretro_core')
		del kodi_game_files
		default_maps = pd.DataFrame(['default_controller_only','default_controller_mouse_keyboard'],columns=['repo_name'])
		for k in ['buttonmap','topology']:
			default_maps[f'{k}_xml_filename'] = default_maps['repo_name'].apply(lambda x: Path.cwd().joinpath('resources',x,f'{k}.xml'))
			default_maps[f'{k}_xml_content'] = default_maps[f'{k}_xml_filename'].apply(lambda x: x.read_text() if isinstance(x,Path) else None)
		for k in ['buttonmap_xml_content','topology_xml_content']:
			bb_df[f'default_{k}'] = bb_df.apply(lambda x: next(iter(default_maps.loc[default_maps['repo_name']=='default_controller_mouse_keyboard'][k]),None) if x.get('needs_kbd_mouse_focus')=='true' else next(iter(default_maps.loc[default_maps['repo_name']=='default_controller_only'][k]),None),axis=1)
		default_assets = pd.DataFrame([next(iter(Path.cwd().joinpath('resources','default_assets').glob('icon.png')),None),next(iter(Path.cwd().joinpath('resources','default_assets').glob('icon_transparent.png')),None),next(iter(Path.cwd().joinpath('resources','default_assets').glob('fanart.jpg')),None)],columns=['asset_filename'])
		default_assets['type'] = default_assets['asset_filename'].apply(lambda x: x.stem if isinstance(x,Path) else None)
		for k in set(default_assets['type']):
			bb_df[f'default_asset_{k}_filename'] = next(iter(default_assets.loc[default_assets['type']==k]['asset_filename']),None)
		bb_df['addon_dict'] = bb_df.apply(lambda x: build_addon_dict(x_in=x),axis=1)

		#Check existing addons
		if check_existing_addons:
			print('Checking the status of existing addons in the repository...')
			existing_addons = [x for x in Path.cwd().rglob('*.zip') if x.parent.name in set(bb_df['addon_generator_folder'])]
			exist_df = pd.DataFrame(existing_addons,columns=['existing_addon_zipfilename'])
			exist_df['addon_generator_folder'] = exist_df['existing_addon_zipfilename'].apply(lambda x: x.parent.name if isinstance(x,Path) else None)
			exist_df['addon_xml_content'] = exist_df['existing_addon_zipfilename'].apply(lambda x: read_zipfile_addon_xml(input_filename=x))
			exist_df['addon_xml_dict'] = exist_df['addon_xml_content'].apply(lambda x: xml_to_dict(x.replace('@','')) if isinstance(x,str) and x.startswith('<?xml') else None)
			for k in ['existing_core_name','existing_addon_version','exiting_core_crc']:
				exist_df[k] = exist_df['addon_xml_dict'].apply(lambda x: get_existing_addon_property(addon_dict=x,property=k))
			#If multiple of the same exist, only take the newest version
			exist_df = exist_df.loc[exist_df['existing_core_name'].notna()&(exist_df['existing_addon_version'].notna()|exist_df['exiting_core_crc'].notna())].sort_values(by='existing_addon_version',ascending=False).drop_duplicates(subset=['addon_generator_folder','existing_core_name'])
			bb_df['existing_addon_version'] = bb_df.merge(exist_df,how='left',left_on=['addon_generator_folder','bb_core_name_clean'],right_on=['addon_generator_folder','existing_core_name'])['existing_addon_version']
			bb_df['exiting_core_crc'] = bb_df.merge(exist_df,how='left',left_on=['addon_generator_folder','bb_core_name_clean'],right_on=['addon_generator_folder','existing_core_name'])['exiting_core_crc']
			bb_df['existing_addon_zipfilename'] = bb_df.merge(exist_df,how='left',left_on=['addon_generator_folder','bb_core_name_clean'],right_on=['addon_generator_folder','existing_core_name'])['existing_addon_zipfilename']
			del exist_df
		#Build first from build environment
		bb_df1 = bb_df.copy()
		bb_df2 = bb_df.copy()
		bb_df1[['build_filename', 'downloaded_core_filename', 'downloaded_core_settings_dict']] = bb_df1.apply(lambda x:  build_addon(x_in=x,addons_to_build=addons_to_build,environments_to_build=[build_environment],cores_to_skip=[x for x in default_cores_to_skip if x not in addons_to_build]),result_type='expand',axis=1)
		#Then build all the others, which will use settings&data from build environment
		if environments_to_build == 'all' or (isinstance(environments_to_build,list) and len([x for x in environments_to_build if x!=build_environment])>0):
			if environments_to_build=='all':
				environments_to_build = [x[1] for x in addons_generator_mapping if x[1]!=build_environment] #List all environments except build environment
			bb_df2[['build_filename', 'downloaded_core_filename', 'downloaded_core_settings_dict']] = bb_df2.apply(lambda x:  build_addon(x_in=x,addons_to_build=addons_to_build,environments_to_build=[x for x in environments_to_build if x!=build_environment],cores_to_skip=[x for x in default_cores_to_skip if x not in addons_to_build]),result_type='expand',axis=1)
		else:
			bb_df2 = None

		if isinstance(bb_df2,pd.DataFrame) and not bb_df2.empty:
			bb_df = pd.concat([bb_df1.loc[bb_df1['build_filename'].notna()],bb_df2.loc[bb_df2['build_filename'].notna()]])
		else:
			bb_df = bb_df1.copy()
		del bb_df1
		del bb_df2

		bb_df['built_addon_zipfilename'] = bb_df.apply(lambda x: make_addon_zip(x_in=x),axis=1)
		bb_df['built_addon_zipfilesize'] = bb_df['built_addon_zipfilename'].apply(lambda x: x.stat().st_size if isinstance(x,Path) and x.exists() else None)
		if remove_large_addons:
			print('Removing any addons that are too big...')
			bb_df['built_addon_too_big'] = bb_df['built_addon_zipfilesize'].apply(lambda x: True if not pd.isna(x) and x>=max_file_size else False) #Addon must be less than 100MB for git
			bb_df.apply(lambda x: delete_addons_too_big(x_in=x),axis=1)
			bb_df['built_addon_zipfilename'] = bb_df.apply(lambda x: None if x.get('built_addon_too_big')==True else x.get('built_addon_zipfilename'),axis=1) #Remove deleted addons from list if they were too big

		if remove_old_addons:
			print('Deleting old addons...')
			bb_df.apply(lambda x: delete_old_addons(x_in=x),axis=1)

		current_addons = [x for x in Path.cwd().rglob('*.zip') if x.parent.name in set(bb_df['addon_generator_folder'])]
		current_df = pd.DataFrame(current_addons,columns=['existing_addon_zipfilename'])
		current_df['existing_addon_zipfilesize'] = current_df['existing_addon_zipfilename'].apply(lambda x: x.stat().st_size if isinstance(x,Path) and x.exists() else None)
		current_df['existing_addon_xmlpath'] = current_df['existing_addon_zipfilename'].apply(lambda x: '{}/{}'.format(x.parent.name,x.name) if isinstance(x,Path) and x.exists() else None)
		current_df['addon_generator_folder'] = current_df['existing_addon_zipfilename'].apply(lambda x: x.parent.name if isinstance(x,Path) else None)
		current_df['addon_xml_content'] = current_df['existing_addon_zipfilename'].apply(lambda x: read_zipfile_addon_xml(input_filename=x))
		current_df['repo_addon_xml_content'] = current_df.apply(lambda x: generate_repo_addon_xml_content(x_in=x),axis=1)
		current_df = current_df.loc[current_df['addon_xml_content'].notna()]
		current_df['repo_name'] = current_df['addon_generator_folder'].apply(lambda x: next(iter([y[-1] for y in addons_generator_mapping if y[0]==x]),None))
		current_df['repo_filename'] = current_df['repo_name'].map(repository_file_mapping)
		
		if generate_repository_xml:
			for repo_name in set(current_df['repo_name']):
				generate_repository_addonxml(current_df=current_df,repo_name=repo_name)

		if clear_temp_after_build and Path.cwd().joinpath('temp').exists():
			print('Removing temp files...')
			import shutil
			shutil.rmtree(Path.cwd().joinpath('temp'),ignore_errors=True)

		if update_standalone_script_zip:
			success = update_standalone_script_zip(root_path=Path.cwd())
	else:
		print('There was an error downloading info.zip which is required to build addons, stopping...')

if __name__ == '__main__':
	main(parse_args())