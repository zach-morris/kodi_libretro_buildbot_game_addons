import shlex, requests, zipfile, xmltodict, json, os, hashlib, argparse
from pathlib import Path
import pandas as pd
from collections import defaultdict
from os import PathLike
from typing import Any
from libretro import Session
import urllib3
from multiprocessing import get_context
from multiprocessing.connection import Connection
from PIL import Image

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def return_info_dict_from_libretro_info_text(info_raw):
	info_out = dict()
	if isinstance(info_raw,str):
		for line in info_raw.split('\n'):
			if '=' in line and '#' not in line:
				name, var = line.partition('=')[::2]
				info_out[name.strip()] = shlex.split(var)[0]
	return info_out

def read_text_url(url_in):
	result = None
	if isinstance(url_in,str):
		print('Reading url %(url)s' % {'url': url_in})
		try:
			s = requests.Session()
			r = s.get(url_in,verify=False,stream=True,timeout=5)
			if isinstance(r.text,str) and len(r.text)>0:
				result = r.text
		except Exception as exc:
			print(f'Read text url error: {exc}')
	return result

def delete_file(filename_in):
	result = False
	if isinstance(filename_in,Path) and filename_in.exists():
		try:
			filename_in.unlink()
			result = True
		except Exception as exc:
			print(f'Error deleting file: {exc}')
	return result

def write_text_to_file(filename_in,text_in):
	result = False
	if isinstance(filename_in,Path) and isinstance(text_in,str):
		try:
			filename_in.write_text(text_in, encoding='utf-8')
			result = True
		except Exception as exc:
			print(f'Error writing file: {exc}')
	return result

def download_file(url_in=None,filename_fullpath=None,unzip_download=True,chunk_size=102400):
	result = None
	download_success = False
	extracted_files = None
	extract_to_dir = None
	if isinstance(url_in,str) and isinstance(filename_fullpath,Path):
		print(f'Downloading file {url_in}')
		if filename_fullpath.exists():
			download_success = True
		else:
			extract_to_dir = filename_fullpath.parent
			if isinstance(url_in,str): 
				try:
					s = requests.Session()
					r = s.get(url_in,verify=False,stream=True,timeout=5)
					with open(str(filename_fullpath),'wb') as core_file:
						for chunk in r.iter_content(chunk_size):
							core_file.write(chunk)
					if filename_fullpath.exists():
						download_success = True
				except Exception as web_except:
					print(f'Error: Downloading file {url_in} exception: {web_except}')
					download_success = False
					delete_file(filename_fullpath)
		if download_success and filename_fullpath.suffix == '.zip' and unzip_download and isinstance(extract_to_dir,Path) and extract_to_dir.exists():
			print('Unzipping file {}'.format(filename_fullpath.name))
			unzip_success = False
			extracted_files = None
			try:
				zip_ref = zipfile.ZipFile(str(filename_fullpath),'r')
				extracted_files = zip_ref.infolist()
				zip_ref.extractall(str(extract_to_dir)) #Extract to same location
				zip_ref.close()
				unzip_success = True
			except Exception as zip_except:
				print(f'Error: Extracting file {filename_fullpath} exception: {zip_except}')
				unzip_success = False
				delete_file(filename_fullpath)
			if unzip_success and extracted_files is not None:
				print('{} files successfully unzipped'.format(len(extracted_files)))
				result = [extract_to_dir.joinpath(x.filename) for x in extracted_files]
				delete_file(filename_fullpath)
	else:
		print(f'Error Downloading file {url_in} to '+str(filename_fullpath))
	return result

def filter_and_sort_asset_images(items, patterns):
	filtered = [item for item in items if any([str(pattern) in str(item) for pattern in patterns])]
	def get_custom_order(item):
		for index, pattern in enumerate(patterns):
			if str(pattern) in str(item):
				return index
		return len(patterns)
	return sorted(filtered, key=get_custom_order)

def xml_to_dict(xml_in):
	result = None
	if isinstance(xml_in,str):
		try:
			result = xmltodict.parse(xml_in)
		except Exception as exc:
			print(f'Error: xmltodict: {exc}')
	return result

def get_value_from_addon_xml_dict(value=None,x_in=None):
	result = None
	if isinstance(value,str) and isinstance(x_in,pd.Series):
		addon_xml_dict=x_in.get('addon_xml_dict')
		repo_name=x_in.get('repo_name')
		match value:
			case 'libretro_core':
				try:
					result =  addon_xml_dict.get('addon').get('extension')[0].get('libretro_core')
				except:
					pass
				if result is None:
					result = repo_name.replace('game.libretro.','')
					if not result.endswith('_libretro'):
						result = result+'_libretro'
			case 'platforms':
				try:
					result =  addon_xml_dict.get('addon').get('extension')[0].get('platforms')
				except:
					pass
			case _:
				print(f'No get_value_from_addon_xml_dict getter for {value}')
	return result

def get_addon_requires_dict(x_in=None):
	result = None
	if isinstance(x_in,pd.Series):
		default_requires = {'@addon': 'game.libretro', '@version': '1.0.0'}
		import_list = [default_requires]
		if isinstance(x_in.get('buttonmap_xml_content'),str):
			try:
				button_map_dict = xmltodict.parse(x_in.get('buttonmap_xml_content').replace('@',''))
			except:
				button_map_dict = None
				pass
			if isinstance(button_map_dict,dict) and isinstance(button_map_dict.get('buttonmap'),dict):
				controllers = button_map_dict.get('buttonmap').get('controller')
				if isinstance(controllers,list):
					for cc in sorted(set([c.get('@id') for c in controllers if isinstance(c,dict)])):
						if isinstance(cc,str):
							import_list.append({'@addon':cc})
				if isinstance(controllers,dict) and isinstance(controllers.get('@id'),str):
					import_list.append({'@addon':controllers.get('@id')})
		else:
			if isinstance(x_in.get('default_buttonmap_xml_content'),str):
				try:
					button_map_dict = xmltodict.parse(x_in.get('default_buttonmap_xml_content').replace('@',''))
				except:
					button_map_dict = None
					pass
				if isinstance(button_map_dict,dict) and isinstance(button_map_dict.get('buttonmap'),dict):
					controllers = button_map_dict.get('buttonmap').get('controller')
					if isinstance(controllers,list):
						for cc in sorted(set([c.get('@id') for c in controllers if isinstance(c,dict)])):
							if isinstance(cc,str):
								import_list.append({'@addon':cc})
					if isinstance(controllers,dict) and isinstance(controllers.get('@id'),str):
						import_list.append({'@addon':controllers.get('@id')})
		result = {'import':import_list}
	return result

def get_addon_extension_point_dict(x_in=None):
	result = None
	if isinstance(x_in,pd.Series) and isinstance(x_in.get('bb_core_name'),str) and isinstance(x_in.get('kodi_library'),str) and isinstance(x_in.get('bb_core_filename'),str):
		platforms = x_in.get('systemname')
		if platforms is None and isinstance(x_in.get('database'),str):
			platforms = x_in.get('database')
		if platforms is None and isinstance(x_in.get('categories'),str):
			platforms = x_in.get('categories')
		if platforms is None:
			platforms = 'Emulator'
		if x_in.get('needs_fullpath')=='true':
			supports_vfs = 'true'
		else:
			supports_vfs = 'false'
		if x_in.get('supports_no_game')=='true':
			supports_standalone = 'true'
		else:
			supports_standalone = 'false'
		

		if x_in.get('disk_control')=='true':
			supports_disc_control = 'true'
		else:
			supports_disc_control = 'false'
		result = {'@point': 'kodi.gameclient',
				'@{}'.format(x_in.get('kodi_library')):x_in.get('bb_core_filename'),
				'platforms': platforms,
				'extensions': x_in.get('supported_extensions') or '',
				'supports_vfs': supports_vfs,
				'supports_standalone': supports_standalone,
				'supports_disc_control': supports_disc_control,
				'libretro_core': x_in.get('bb_core_name')}
		if isinstance(x_in.get('savestate_features'),str) and x_in.get('savestate_features'):
			result['savestate_features'] = x_in.get('savestate_features')
	else:
		if isinstance(x_in,pd.Series):
			print('Unable to build addon ext point: {} / {} / {}'.format(x_in.get('bb_core_name'),x_in.get('kodi_library'),x_in.get('bb_core_filename')))
	return result

def get_addon_description(x_in=None):
	result = 'None Provided'
	if isinstance(x_in,pd.Series):
		result = '[B]Libretro Buildbot Game Addon[/B][CR]'
		if isinstance(x_in.get('description'),str):
			result = result+'{}[CR]'.format(x_in.get('description'))
		if isinstance(x_in.get('systemname'),str):
			result = result+'System: {}[CR]'.format(x_in.get('systemname'))
		if isinstance(x_in.get('manufacturer'),str):
			result = result+'System Manufacturer: {}[CR]'.format(x_in.get('manufacturer'))
		if isinstance(x_in.get('categories'),str):
			result = result+'System Categories: {}[CR]'.format(x_in.get('categories'))
		if isinstance(x_in.get('authors'),str):
			result = result+'Authors: {}[CR]'.format(x_in.get('authors'))
		if isinstance(x_in.get('supported_extensions'),str):
			result = result+'Supported Files: {}[CR]'.format(x_in.get('supported_extensions'))
		if isinstance(x_in.get('firmware_count'),str) and x_in.get('firmware_count').isdigit():
			firmware_list = list()
			for ii in range(int(x_in.get('firmware_count'))+1):
				if isinstance(x_in.get(f'firmware{ii}_desc'),str) and isinstance(x_in.get(f'firmware{ii}_path'),str) and isinstance(x_in.get(f'firmware{ii}_opt'),str):
					firmware_list.append('   File: {}, Path: {}, Optional: {}'.format(x_in.get(f'firmware{ii}_desc'),x_in.get(f'firmware{ii}_path'),x_in.get(f'firmware{ii}_opt')))
			result = result+'[CR]Firmware Files ({} Total):[CR]{}[CR]'.format(x_in.get('firmware_count'),'[CR]'.join(firmware_list))
		if isinstance(x_in.get('notes'),str):
			result = result+'Notes: {}[CR]'.format(x_in.get('notes'))
	return result

def get_addon_metadata_dict(x_in=None):
	result = None
	if isinstance(x_in,pd.Series) and isinstance(x_in.get('display_name'),str) and isinstance(x_in.get('bb_core_url'),str) and isinstance(x_in.get('kodi_library'),str):
		if isinstance(x_in.get('license'),str):
			core_license = x_in.get('license')
		else:
			core_license = 'None Provided'
		core_news = 'None Provided'
		if isinstance(x_in.get('bb_file_date'),str):
			if isinstance(x_in.get('bb_file_crc'),str):
				core_news = 'Built from libretro buildbot[CR]date:{}[CR]crc:{}'.format(x_in.get('bb_file_date'),x_in.get('bb_file_crc'))
			else:
				core_news = 'Built from libretro buildbot[CR]date:{}'.format(x_in.get('bb_file_date'))
		result = {'@point': 'xbmc.addon.metadata',
				'license': core_license,
				'platform': x_in.get('kodi_platform'),
				'source': x_in.get('bb_core_url'),
				'news': core_news,
				'assets': {'icon': 'resources/icon.png'},
				'summary': [{'@lang': 'en_GB', '#text': 'Buildbot - {}'.format(x_in.get('display_name'))}],
				'description': [{'@lang': 'en_GB',
				'#text': get_addon_description(x_in=x_in)},
				]}
	else:
		if isinstance(x_in,pd.Series):
			print('Unable to build addon metadata: {}'.format(x_in.get('display_name')))
	return result

def build_addon_dict(x_in=None,addon_provider_name='http://buildbot.libretro.com/'):
	result = None
	addon_requires_dict = get_addon_requires_dict(x_in=x_in)
	addon_extension_point_dict = get_addon_extension_point_dict(x_in=x_in)
	addon_metadata_dict = get_addon_metadata_dict(x_in=x_in)
	if isinstance(x_in,pd.Series) and isinstance(x_in.get('addon_id'),str) and isinstance(x_in.get('display_name'),str) and isinstance(x_in.get('addon_version'),str) and isinstance(addon_provider_name,str) and addon_requires_dict is not None and addon_extension_point_dict is not None and addon_metadata_dict is not None:
		result = {'addon': {'@id': x_in.get('addon_id'),'@name': 'Buildbot - {}'.format(x_in.get('display_name')),'@version': x_in.get('addon_version'),'@provider-name': addon_provider_name,'requires': addon_requires_dict,'extension':[addon_extension_point_dict,addon_metadata_dict]}}
	else:
		if isinstance(x_in,pd.Series):
			print('Unable to build addon dict for {} / {}'.format(x_in.get('addon_id'),x_in.get('bb_core_filename')))
	return result


def get_alternate_core_info_matches(name_in):
	result = None
	if isinstance(name_in,str):
		alternate_mapping = dict(zip(['boom3_xp_libretro','fbalpha_libretro','pokketstation_libretro','nicaiemu_libretro'],
									['boom3_libretro','fbalpha2012_libretro','pokket_libretro','coolbaremu_libretro']))
		result = alternate_mapping.get(name_in)
	return result

def make_resources(x_in=None):
	result = False
	if isinstance(x_in,pd.Series) and isinstance(x_in.get('build_folder_path'),Path):
		if x_in.get('build_folder_path').joinpath('resources').exists():
			result = True
		else:
			x_in.get('build_folder_path').joinpath('resources').mkdir(parents=False,exist_ok=True)
			result = True
	return result

def build_addon(x_in=None,addons_to_build=None,environments_to_build=None,cores_to_skip=[],dry_run=False):
	build_file = None
	temp_core_filename = None
	core_options_dict = None
	build_addon = True
	if isinstance(x_in,pd.Series) and addons_to_build is not None and environments_to_build is not None:
		if (addons_to_build == 'all' and x_in.get('bb_core_name_clean') not in cores_to_skip) or (isinstance(addons_to_build,list) and x_in.get('bb_core_name_clean') in addons_to_build):
			if (environments_to_build == 'all' and x_in.get('default_build_addon')==True) or (isinstance(environments_to_build,list) and x_in.get('kodi_platform') in environments_to_build):
				if isinstance(x_in.get('exiting_core_crc'),str) and isinstance(x_in.get('bb_file_crc'),str) and x_in.get('exiting_core_crc')==x_in.get('bb_file_crc'):
					build_addon=False
					print('Existing addon crc match, skipping re-build of {} {}'.format(x_in.get('kodi_platform'),x_in.get('bb_core_name_clean')))
				if build_addon and isinstance(x_in.get('existing_addon_version'),str) and isinstance(x_in.get('addon_version'),str) and x_in.get('existing_addon_version')==x_in.get('addon_version'):
					build_addon=False
					print('Existing addon version match, skipping re-build of {} {}'.format(x_in.get('kodi_platform'),x_in.get('bb_core_name_clean')))
				if build_addon and isinstance(x_in.get('build_folder_path'),Path):
					print('Building {} {}'.format(x_in.get('kodi_platform'),x_in.get('bb_core_name_clean')))
					#Make build folder
					if not x_in.get('build_folder_path').exists():
						x_in.get('build_folder_path').mkdir(parents=True,exist_ok=True)
					else:
						#Check if build already exists if folder already exists
						if isinstance(next(iter(x_in.get('build_folder_path').rglob('*.build')),None),Path) and next(iter(x_in.get('build_folder_path').rglob('*.build')),None).exists():
							build_file = next(iter(x_in.get('build_folder_path').rglob('*.build')),None)
					if build_file is None and isinstance(x_in.get('bb_core_url'),str) and isinstance(x_in.get('bb_file_filename'),str) and isinstance(x_in.get('addon_dict'),dict):
						#Extract core
						if x_in.get('build_folder_path').joinpath(x_in.get('bb_core_filename')).exists(): #Already downloaded
							temp_core_file = x_in.get('build_folder_path').joinpath(x_in.get('bb_core_filename'))
						else:
							temp_core_files = download_file(url_in=x_in.get('bb_core_url'),filename_fullpath=x_in.get('build_folder_path').joinpath(x_in.get('bb_file_filename')))
							if isinstance(temp_core_files,list) and len([x for x in temp_core_files if x.name==x_in.get('bb_core_filename')])>0:
								temp_core_file = next(iter([x for x in temp_core_files if x.name==x_in.get('bb_core_filename')]),None)
						#Write addon xml
						if temp_core_file is not None:
							temp_core_filename = temp_core_file.name
							# try:
							write_text_to_file(x_in.get('build_folder_path').joinpath('addon.xml'),xmltodict.unparse(x_in.get('addon_dict'),pretty=True))
								# x_in.get('build_folder_path').joinpath('addon.xml').write_text(xmltodict.unparse(x_in.get('addon_dict'),pretty=True))
							# except Exception as exc:
								# print('Unable to write addon.xml for {} {}: {}'.format(x_in.get('kodi_platform'),x_in.get('bb_core_name_clean'),exc))
						#Copy icon
						if isinstance(x_in.get('asset_icon_filename'),Path) and x_in.get('asset_icon_filename').exists() and make_resources(x_in=x_in):
							try:
								image_gen_success = combine_images(base_path=x_in.get('asset_icon_filename'),overlay_path=x_in.get('default_asset_icon_transparent_filename'),output_path=x_in.get('build_folder_path').joinpath('resources','icon.png'))
							except Exception as image_exc:
								print('Unable to generate icon for {}: {}'.format(x_in.get('addon_id'),image_exc))
							if not image_gen_success:
								x_in.get('build_folder_path').joinpath('resources','icon.png').write_bytes(x_in.get('asset_icon_filename').read_bytes())
						else:
							if isinstance(x_in.get('icon_filename'),Path) and x_in.get('icon_filename').exists() and make_resources(x_in=x_in):
								image_gen_success = combine_images(base_path=x_in.get('icon_filename'),overlay_path=x_in.get('default_asset_icon_transparent_filename'),output_path=x_in.get('build_folder_path').joinpath('resources','icon.png'))
								if not image_gen_success:
									x_in.get('build_folder_path').joinpath('resources','icon.png').write_bytes(x_in.get('icon_filename').read_bytes())
							else:
								if isinstance(x_in.get('default_asset_icon_filename'),Path) and x_in.get('default_asset_icon_filename').exists() and make_resources(x_in=x_in):
									x_in.get('build_folder_path').joinpath('resources','icon.png').write_bytes(x_in.get('default_asset_icon_filename').read_bytes())
						#Make resource, copy buttonmaps, topology
						if isinstance(x_in.get('buttonmap_xml_content'),str) and make_resources(x_in=x_in):
							write_text_to_file(x_in.get('build_folder_path').joinpath('resources','buttonmap.xml'),x_in.get('buttonmap_xml_content'))
							# x_in.get('build_folder_path').joinpath('resources','buttonmap.xml').write_text(x_in.get('buttonmap_xml_content'))
							if isinstance(x_in.get('topology_xml_content'),str) and make_resources(x_in=x_in): #Only write topology if buttonmap from kodi game is available
								write_text_to_file(x_in.get('build_folder_path').joinpath('resources','topology.xml'),x_in.get('topology_xml_content'))
								# x_in.get('build_folder_path').joinpath('resources','topology.xml').write_text(x_in.get('topology_xml_content'))
						else:
							if isinstance(x_in.get('default_buttonmap_xml_content'),str) and make_resources(x_in=x_in):
								write_text_to_file(x_in.get('build_folder_path').joinpath('resources','buttonmap.xml'),x_in.get('default_buttonmap_xml_content'))
								# x_in.get('build_folder_path').joinpath('resources','buttonmap.xml').write_text(x_in.get('default_buttonmap_xml_content'))
								if isinstance(x_in.get('default_topology_xml_content'),str) and make_resources(x_in=x_in): #Only write topology if buttonmap from kodi game is available
									write_text_to_file(x_in.get('build_folder_path').joinpath('resources','topology.xml'),x_in.get('default_topology_xml_content'))
									# x_in.get('build_folder_path').joinpath('resources','topology.xml').write_text(x_in.get('default_topology_xml_content'))
						#Get settings from core if they dont exist
						core_options_dict = None
						kodi_settings_dict = None
						strings_po_dict = None
						if isinstance(x_in.get('settings_xml_content'),str) and isinstance(x_in.get('strings_po_content'),str) and make_resources(x_in=x_in):
							print('Using existing settings.xml from kodi-game for {}'.format(x_in.get('addon_id')))
							write_text_to_file(x_in.get('build_folder_path').joinpath('resources','settings.xml'),x_in.get('settings_xml_content'))
							# x_in.get('build_folder_path').joinpath('resources','settings.xml').write_text(x_in.get('settings_xml_content'))
							if not x_in.get('build_folder_path').joinpath('resources','language','resource.language.en_us').exists():
								x_in.get('build_folder_path').joinpath('resources','language','resource.language.en_us').mkdir(parents=True,exist_ok=True)
							write_text_to_file(x_in.get('build_folder_path').joinpath('resources','language','resource.language.en_us','strings.po'),x_in.get('strings_po_content'))
							# x_in.get('build_folder_path').joinpath('resources','language','resource.language.en_us','strings.po').write_text(x_in.get('strings_po_content'))
						else:
							if isinstance(x_in.get('addon_id'),str) and isinstance(temp_core_file,Path) and temp_core_file.exists():
								if x_in.get('kodi_platform')==x_in.get('build_environment'):
									try:
										print('Getting core options for {}'.format(x_in.get('addon_id')))
										core_options_dict = extract_core_options_isolated(core=temp_core_file,section_id=x_in.get('addon_id'),game=None,work_root=x_in.get('temp_path'))
									except Exception as exc:
										print('Unable to extract options dict for {}: {}'.format(x_in.get('addon_id'),exc))
								else:
									#Copy build settings and strings over from the build environment
									if isinstance(x_in.get('build_environment_folder_path'),Path) and x_in.get('build_environment_folder_path').exists():
										build_settings_file = next(iter(list(x_in.get('build_environment_folder_path').rglob('settings.xml'))),None)
										build_strings_file = next(iter(list(x_in.get('build_environment_folder_path').rglob('strings.po'))),None)
										if isinstance(build_settings_file,Path) and build_settings_file.exists() and isinstance(build_strings_file,Path) and build_strings_file.exists():
											print('Copying settings.xml from build env for {}'.format(x_in.get('addon_id')))
											write_text_to_file(x_in.get('build_folder_path').joinpath('resources','settings.xml'),build_settings_file.read_text())
											# x_in.get('build_folder_path').joinpath('resources','settings.xml').write_text(build_settings_file.read_text())
											if not x_in.get('build_folder_path').joinpath('resources','language','resource.language.en_us').exists():
												x_in.get('build_folder_path').joinpath('resources','language','resource.language.en_us').mkdir(parents=True,exist_ok=True)
											write_text_to_file(x_in.get('build_folder_path').joinpath('resources','language','resource.language.en_us','strings.po'),build_strings_file.read_text())
											# x_in.get('build_folder_path').joinpath('resources','language','resource.language.en_us','strings.po').write_text(build_strings_file.read_text())
							if isinstance(core_options_dict,dict):
								try:
									kodi_settings_dict = get_kodi_settings_dict(core_options_dict)
									strings_po_dict = get_kodi_strings_po_entries(core_options_dict)
								except Exception as exc:
									print('Unable to build kodi settings dict for {}: {}'.format(x_in.get('addon_id'),exc))
								if isinstance(kodi_settings_dict,dict) and isinstance(strings_po_dict,list) and len(strings_po_dict)>0:
									write_text_to_file(x_in.get('build_folder_path').joinpath('resources','settings.xml'),xmltodict.unparse(kodi_settings_dict,pretty=True))
									# x_in.get('build_folder_path').joinpath('resources','settings.xml').write_text(xmltodict.unparse(kodi_settings_dict,pretty=True))
									if not x_in.get('build_folder_path').joinpath('resources','language','resource.language.en_us').exists():
										x_in.get('build_folder_path').joinpath('resources','language','resource.language.en_us').mkdir(parents=True,exist_ok=True)
									write_text_to_file(x_in.get('build_folder_path').joinpath('resources','language','resource.language.en_us','strings.po'),get_strings_po(x_in=x_in,strings_po_dict=strings_po_dict))
									# x_in.get('build_folder_path').joinpath('resources','language','resource.language.en_us','strings.po').write_text(get_strings_po(x_in=x_in,strings_po_dict=strings_po_dict))		
					#Check build, make build file
					if isinstance(x_in.get('bb_core_filename'),str) and x_in.get('build_folder_path').joinpath(x_in.get('bb_core_filename')).exists() and x_in.get('build_folder_path').joinpath('addon.xml').exists():
						cols = ['addon_generator_folder', 'kodi_platform', 'kodi_library', 'bb_sub_url', 'default_build_addon', 'bb_url', 'bb_index_ext', 'bb_file_date', 'bb_file_crc', 'bb_file_filename', 'bb_core_url', 'bb_core_filename', 'bb_core_name', 'bb_core_name_clean', 'alternate_core_info_matches', 'addon_id']
						try:
							build_dict = x_in[[c for c in cols if c in x_in.keys()]].copy().to_dict()
							build_dict['build_files'] = [str(x) for x in x_in.get('build_folder_path').rglob('*') if x.is_file()]
							build_json= json.dumps(build_dict)
						except Exception as exc:
							build_json = None
							print(f'Unable to generate build json: {exc}')
						if isinstance(build_json,str):
							write_text_to_file(x_in.get('build_folder_path').joinpath('{}.build'.format(x_in.get('addon_id'))),build_json)
							# x_in.get('build_folder_path').joinpath('{}.build'.format(x_in.get('addon_id'))).write_text(build_json)
							build_file = x_in.get('build_folder_path').joinpath('{}.build'.format(x_in.get('addon_id')))
	return [build_file,temp_core_filename,core_options_dict]

def get_strings_po(x_in=None,strings_po_dict=None):
	result = None
	if isinstance(x_in,pd.Series) and isinstance(strings_po_dict,list):
		strings_po_header = get_strings_po_header(x_in=x_in)
		strings_po_body = '\n'.join(['\nmsgctxt "{}"\nmsgid "{}"\nmsgstr "{}"'.format(x.get('msgctxt'),x.get('msgid'),x.get('msgstr')) for x in strings_po_dict])
		if isinstance(strings_po_header,str) and len(strings_po_header)>0 and isinstance(strings_po_body,str) and len(strings_po_body)>0:
			result = '{}\n{}\n'.format(strings_po_header,strings_po_body) 
	return result

def get_strings_po_header(x_in=None):
	result = ''
	if isinstance(x_in,pd.Series) and isinstance(x_in.get('addon_id'),str):
		tnow = pd.Timestamp.now().strftime('%Y-%m-%d')
		result = ('"Project-Id-Version: {}"\n'
				'"PO-Revision-Date: {} 00:00+0000"\n'
				'"Language: en_us"\n'
				'"MIME-Version: 1.0"\n'
				'"Content-Type: text/plain; charset=UTF-8"\n'
				'"Content-Transfer-Encoding: 8bit"\n'
				'"Plural-Forms: nplurals=2; plural=n != 1;"\n').format(x_in.get('addon_id'),tnow)
	return result

def _text(value: bytes | str | None) -> str | None:
	"""Decode libretro byte strings while preserving None."""
	if value is None:
		return None
	if isinstance(value, bytes):
		return value.decode("utf-8", errors="replace")
	return str(value)


def _extract_worker(
	sender: Connection,
	core: str | PathLike[str] | PathLike[bytes],
	game: str | PathLike[str] | PathLike[bytes] | None,
	work_root: str | PathLike[str] | PathLike[bytes] | Path | None,
	section_id: str,
) -> None:
	"""Run the core extraction in a child process and send back its result."""
	if isinstance(work_root,Path):
		print(work_root)
		cwd = work_root.joinpath('cwd')
		system = work_root.joinpath('system')
		assets = work_root.joinpath('assets')
		save = work_root.joinpath('save')

		for directory in (cwd, system, assets, save):
			directory.mkdir(parents=True, exist_ok=True)

		os.chdir(cwd) #Change childs working directory to cwd

	try:
		result = extract_core_options(core, game=game, section_id=section_id)
		sender.send((True, result))
	except BaseException:
		# Includes ordinary Python errors; crashes such as a segfault cannot be caught.
		sender.send((False, None))
	finally:
		sender.close()


def extract_core_options_isolated(
	core: str | PathLike[str] | PathLike[bytes],
	game: str | PathLike[str] | PathLike[bytes] | None,
	work_root: str | PathLike[str] | PathLike[bytes] | None,
	section_id: str,
	timeout: float = 10,
) -> dict[str, Any] | None:
	"""Return extracted options, or None if the child fails, crashes, or times out."""
	# context = get_context("spawn")
	context = get_context("fork")
	receiver, sender = context.Pipe(duplex=False)
	process = context.Process(
		target=_extract_worker,
		args=(sender, core, game, work_root, section_id),
	)

	try:
		print('Loading core {} with game {}'.format(core.name,game))
		process.start()
		sender.close()

		if not receiver.poll(timeout):
			process.terminate()
			process.join()
			print('Core {} timeout'.format(core.name))
			return None

		try:
			succeeded, result = receiver.recv()
			print('Core {} returned'.format(core.name))
		except EOFError:
			succeeded, result = False, None

		# A child might send a result and then crash while cleaning up the core.
		process.join(timeout=5)
		if process.is_alive():
			process.terminate()
			process.join()
			return None

		if process.exitcode != 0 or not succeeded:
			print('Core {} crashed'.format(core.name))
			return None

		return result
	finally:
		receiver.close()
		if process.is_alive():
			process.terminate()
			process.join()

def extract_core_options(core=None,section_id=None,game=None):
	result = None
	driver = None
	options: list[dict[str, Any]] = []
	categories: dict[str, dict[str, str | None]] = {}

	if isinstance(game,Path) and game.exists():
		session_args = {}
	else:
		session_args = {"content": None}
	if isinstance(core,Path) and core.exists():
		with Session(core=core,game=game,options=2,vfs=None,**session_args) as session:
			driver = session.options

	if driver and isinstance(section_id,str):
		for category_key, category in driver.categories.items():
			key = _text(category.key) or _text(category_key)
			if key is not None:
				categories[key] = {
					"key": key,
					"desc": _text(category.desc),
					"info": _text(category.info),
				}

		for option_key, definition in (driver.definitions or {}).items():
			values = []
			for item in definition.values:
				# The fixed-size C array is terminated by an entry with no value.
				value = _text(item.value)
				if value is None:
					break
				values.append(
					{
						"value": value,
						"label": _text(item.label),
					}
				)

			key = _text(definition.key) or _text(option_key)
			if key is None:
				continue

			options.append(
				{
					"key": key,
					"desc": _text(definition.desc),
					"desc_categorized": _text(definition.desc_categorized),
					"info": _text(definition.info),
					"info_categorized": _text(definition.info_categorized),
					"category_key": _text(definition.category_key),
					"values": values,
					"default_value": _text(definition.default_value),
				}
			)
		result = {"section_id": section_id,"categories": categories,"options": options}
	return result

def _category_groups(
	core_options: dict[str, Any],
) -> list[tuple[str, dict[str, Any], list[dict[str, Any]]]]:
	"""Return categories and their options in stable order."""
	category_data = core_options.get("categories") or {}
	options = core_options.get("options") or []
	grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)

	for option in options:
		category_key = option.get("category_key") or "general"
		grouped[category_key].append(option)

	ordered_keys = list(category_data)
	if "general" in grouped and "general" not in ordered_keys:
		ordered_keys.append("general")
	for option in options:
		category_key = option.get("category_key") or "general"
		if category_key not in ordered_keys:
			ordered_keys.append(category_key)

	result = []
	for key in ordered_keys:
		category = category_data.get(key) or {
			"key": key,
			"desc": "General" if key == "general" else key,
			"info": None,
		}
		result.append((key, category, grouped.get(key, [])))

	return result


def _localized_strings(core_options: dict[str, Any]) -> list[str]:
	"""Collect display strings in a deterministic order, de-duplicating identical text."""
	strings: list[str] = []
	seen: set[str] = set()

	def add(value: str | None) -> None:
		if value and value not in seen:
			seen.add(value)
			strings.append(value)

	for category_key, category, options in _category_groups(core_options):
		add(category.get("desc") or category_key)
		add(category.get("info"))

		for option in options:
			add(option.get("desc") or option["key"])
			add(option.get("info") or option.get("info_categorized"))

			for value in option.get("values") or []:
				add(value.get("label"))

	return strings


def _id_map(core_options: dict[str, Any]) -> dict[str, str]:
	"""Assign one stable Kodi integer ID per distinct display string."""
	strings = _localized_strings(core_options)
	first_id = 30000
	last_id = 39999

	if len(strings) > last_id - first_id + 1:
		raise ValueError(
			f"Need {len(strings)} distinct string IDs, but only "
			f"{last_id - first_id + 1} IDs are available ({first_id}-{last_id})."
		)

	return {text: str(first_id + index) for index, text in enumerate(strings)}


def get_kodi_settings_dict(core_options: dict[str, Any]) -> dict[str, Any]:
	"""
	Convert the result of ``extract_core_options`` to an xmltodict-compatible dict.

	Repeated ``category``, ``group``, ``setting``, and ``option`` elements are
	represented as lists. Identical localized strings share an ID.
	"""
	ids = _id_map(core_options)
	categories = []

	for category_key, category, options in _category_groups(core_options):
		category_label = category.get("desc") or category_key
		category_element: dict[str, Any] = {
			"@id": category_key,
			"@label": ids[category_label],
			"group": {
				"@id": "1",
				"setting": [],
			},
		}

		category_info = category.get("info")
		if category_info:
			category_element["@help"] = ids[category_info]

		settings = []
		for option in options:
			option_desc = option.get("desc") or option["key"]
			option_info = option.get("info") or option.get("info_categorized")

			setting: dict[str, Any] = {
				"@id": option["key"],
				"@type": "string",
				"@label": ids[option_desc],
				"level": "0",
				"default": option.get("default_value") or "",
				"control": {
					"@type": "list",
					"@format": "string",
				},
			}

			if option_info:
				setting["@help"] = ids[option_info]

			value_elements = []
			for value in option.get("values") or []:
				element: dict[str, Any] = {"#text": value["value"]}
				label = value.get("label")
				if label:
					element["@label"] = ids[label]
				value_elements.append(element)

			if value_elements:
				setting["constraints"] = {
					"options": {
						"option": value_elements,
					}
				}

			settings.append(setting)

		category_element["group"]["setting"] = settings
		categories.append(category_element)

	return {
		"settings": {
			"@version": "1",
			"section": {
				"@id": core_options["section_id"],
				"category": categories,
			},
		}
	}

def get_kodi_strings_po_entries(core_options: dict[str, Any]) -> list[dict[str, str]]:
	"""
	Return strings.po entries corresponding to IDs used by ``kodi_settings_dict``.

	The returned entries use the conventional Kodi format: ``msgctxt`` contains
	the ``#<integer>`` ID, ``msgid`` contains the source string, and ``msgstr``
	is empty for translation.
	"""
	ids = _id_map(core_options)
	return [
		{
			"msgctxt": f"#{ids[text]}",
			"msgid": text,
			"msgstr": text,
		}
		for text in _localized_strings(core_options)


	]

def make_addon_zip(x_in=None):
	result = None
	success = False
	output_filename = None
	if isinstance(x_in,pd.Series) and isinstance(x_in.get('build_filename'),Path) and isinstance(x_in.get('addon_id'),str) and isinstance(x_in.get('addon_version'),str) and isinstance(x_in.get('build_folder_path'),Path) and x_in.get('build_folder_path').exists() and isinstance(x_in.get('addon_folder_path'),Path):
		if not x_in.get('addon_folder_path').exists():
			x_in.get('addon_folder_path').mkdir(parents=False,exist_ok=True)
		output_filename = x_in.get('addon_folder_path').joinpath('{}-{}.zip'.format(x_in.get('addon_id'),x_in.get('addon_version')))
		try:
			success = make_zipfile(output_filename=output_filename,zip_root=x_in.get('addon_id'),source_dir=x_in.get('build_folder_path'))
		except Exception as exc:
			print(f'Error generating addon zip {exc}')
		if success:
			result = output_filename
			# print('Generated addon zipfile: {}'.format(output_filename.name))
	return result

def make_zipfile(output_filename=None,zip_root=None,source_dir=None,excluded_suffixes=['.build','.ds_store'],compress_level=9):
	success = False
	if isinstance(output_filename,Path) and not output_filename.exists() and output_filename.suffix=='.zip' and isinstance(zip_root,str) and isinstance(source_dir,Path) and source_dir.exists() and len(list(source_dir.rglob('*')))>1:
		print('Zipping up {}/{} to {}/{} using compression level {}'.format(source_dir.parent.name,source_dir.name,output_filename.parent.name,output_filename.name,compress_level))
		try:
			with zipfile.ZipFile(output_filename, mode='w', compression=zipfile.ZIP_DEFLATED, compresslevel=compress_level) as zzip:
				for file in source_dir.rglob('*'):
					if file.is_file() and file.suffix.lower() not in excluded_suffixes:
						arcname = Path(zip_root) / file.relative_to(source_dir)
						zzip.write(file, arcname=arcname)
			success = True
		except Exception as exc:
			print(f'Unable to generate zipfile.  Exception: {exc}')
	return success

def read_zipfile_addon_xml(input_filename=None):
	result = None
	addon_xml_zfile = None
	if isinstance(input_filename,Path) and input_filename.exists() and input_filename.suffix=='.zip':
		try:
			with zipfile.ZipFile(input_filename, mode='r') as zf:
				addon_xml_zfile = next(iter([name for name in zf.namelist() if Path(name).name == 'addon.xml']),None)
				zip_file_path = zipfile.Path(zf,at=addon_xml_zfile)
				result = zip_file_path.read_bytes().decode('utf-8')
		except Exception as exc:
			print(f'Unable to read addon.xml in zipfile.  Exception: {exc}')
	return result



def combine_images(base_path, overlay_path, output_path, padding=10,overlay_size=0.33):
	"""
	Combines two PNG images. 
	- base_path: Path to the main base image (e.g., 256x256).
	- overlay_path: Path to the secondary image to be placed in the bottom-right.
	- output_path: Path to save the resulting PNG.
	- padding: Pixel margin from the bottom and right edges.
	"""
	# Open both images and ensure they support transparency (RGBA)
	result = None
	if all([isinstance(x,Path) and x.exists() and x.suffix.lower()=='.png' for x in [base_path,overlay_path]]):
		try:
			base_img = Image.open(base_path).convert("RGBA")
			overlay_img = Image.open(overlay_path).convert("RGBA")
		except Exception as exc:
			print(f'Image open error: {exc}')
			base_img = None
			overlay_img = None
		if base_img is not None and overlay_img is not None:
			base_width, base_height = base_img.size
			
			# Calculate target dimensions for image2
			target_width = int(base_width * overlay_size)
			target_height = int(base_height * overlay_size)
			
			# Resize overlay image while preserving its original aspect ratio
			overlay_img.thumbnail((target_width, target_height), Image.Resampling.LANCZOS)
			overlay_width, overlay_height = overlay_img.size
			
			# Calculate bottom-right coordinates with optional padding
			x = base_width - overlay_width - padding
			y = base_height - overlay_height - padding
			
			# Ensure coordinates don't go out of bounds
			x = max(0, x)
			y = max(0, y)
			
			# Create a copy of the base image so we don't modify the original in-memory object
			combined = base_img.copy()
			
			# Paste overlay using its own alpha channel as a mask for transparency
			combined.paste(overlay_img, (x, y), overlay_img)
			
			# Save if an output path is provided
			if isinstance(output_path,Path) and output_path.suffix.lower() == '.png':
				combined.save(output_path, "PNG")
				print('Overlayed image saved to {}/{}'.format(output_path.parent.name,output_path.name))
				result = output_path
	return result

def delete_addons_too_big(x_in=None):
	result = False
	if isinstance(x_in,pd.Series) and isinstance(x_in.get('built_addon_zipfilename'),Path) and x_in.get('built_addon_zipfilename').exists() and x_in.get('built_addon_too_big')==True:
		print('Removing too big addon: {} {}'.format(x_in.get('built_addon_zipfilename').parent.name,x_in.get('built_addon_zipfilename').name))
		delete_file(x_in.get('built_addon_zipfilename'))
	return result

def delete_old_addons(x_in=None):
	result = False
	if isinstance(x_in,pd.Series) and isinstance(x_in.get('built_addon_zipfilename'),Path) and x_in.get('built_addon_zipfilename').exists() and isinstance(x_in.get('existing_addon_zipfilename'),Path) and x_in.get('existing_addon_zipfilename').exists() and x_in.get('existing_addon_zipfilename').name!= x_in.get('built_addon_zipfilename').name:
		print('Removing old addon: {} {}'.format(x_in.get('existing_addon_zipfilename').parent.name,x_in.get('existing_addon_zipfilename').name))
		delete_file(x_in.get('existing_addon_zipfilename'))
	return result

def get_existing_addon_property(addon_dict=None,property=None):
	result = None
	if isinstance(addon_dict,dict):
		match property:
			case 'existing_core_name':
				if isinstance(addon_dict.get('addon'),dict) and isinstance(addon_dict.get('addon').get('extension'),list):
					result = next(iter([x.get('libretro_core') for x in addon_dict.get('addon').get('extension') if isinstance(x.get('libretro_core'),str)]),None)
			case 'existing_addon_version':
				if isinstance(addon_dict.get('addon'),dict):
					result = addon_dict.get('addon').get('@version')
			case 'exiting_core_crc':
				if isinstance(addon_dict.get('addon'),dict) and isinstance(addon_dict.get('addon').get('extension'),list):
					news = next(iter([x.get('news') for x in addon_dict.get('addon').get('extension') if isinstance(x.get('news'),str)]),None)
					if isinstance(news,str) and 'crc:' in news:
						result = news.split('crc:')[-1].strip()
			case _:
				pass

	return result

def generate_md5_file(filename_in):
	success = False
	if isinstance(filename_in,Path) and filename_in.exists():
		try:
			md5_hash = None
			md5_filename = filename_in.parent.joinpath(filename_in.name.replace('.xml','.xml.md5'))
			with filename_in.open('rb') as f:
				md5_hash = hashlib.file_digest(f,'md5').hexdigest()
			if isinstance(md5_hash,str):
				md5_filename.write_text(md5_hash)
				success = True
		except Exception as exc:
			print(f'Error generating md5 hash for file {filename_in}: {exc}')
	return success

def generate_repo_addon_xml_content(x_in=None):
	result = None
	if isinstance(x_in,pd.Series) and isinstance(x_in.get('addon_xml_content'),str) and isinstance(x_in.get('existing_addon_xmlpath'),str)  and x_in.get('existing_addon_zipfilesize') is not None:
		current_addon_xml = x_in.get('addon_xml_content').replace('<?xml version="1.0" encoding="utf-8"?>\n','')
		size_path_addition = '\t\t<size>{}</size>\n\t\t<path>{}</path>'.format(x_in.get('existing_addon_zipfilesize'),x_in.get('existing_addon_xmlpath'))
		if current_addon_xml.endswith('\t</extension>\n</addon>') or current_addon_xml.endswith('</extension>\n</addon>'):
			result = '{}{}\n\t</extension>\n</addon>'.format(current_addon_xml.replace('\t</extension>\n</addon>','').replace('</extension>\n</addon>',''),size_path_addition)
	return result

def generate_repository_addonxml(current_df=None,repo_name=None):
	success = False
	success2 = False
	success3 = False
	if isinstance(current_df,pd.DataFrame) and not current_df.empty and 'repo_addon_xml_content' in current_df.columns and isinstance(repo_name,str):
		current_df=current_df.loc[current_df['repo_name']==repo_name]
		current_addon_filename = next(iter(current_df['repo_filename']),None)
		addon_xml_content = [x for x in current_df.loc[current_df['repo_addon_xml_content'].notna()]['repo_addon_xml_content'] if isinstance(x,str)]
		if len(addon_xml_content)>0 and isinstance(current_addon_filename,Path):
			addons_xml_content = '<?xml version="1.0" encoding="utf-8"?>\n<addons>\n{}\n</addons>'.format('\n'.join(addon_xml_content))
			success = write_text_to_file(current_addon_filename,addons_xml_content)
			success2 = generate_md5_file(current_addon_filename)
	if success and success2:
		print('Generated repository xml file: {}'.format(current_addon_filename.name))
		success3 = True
	return success3

def positive_int(value):
	"""argparse type that accepts only positive integers."""
	try:
		result = int(value)
	except ValueError as exc:
		raise argparse.ArgumentTypeError(
			'must be an integer greater than 0'
		) from exc

	if result <= 0:
		raise argparse.ArgumentTypeError('must be an integer greater than 0')

	return result

def parse_args(argv=None):
	parser = argparse.ArgumentParser(
		description='Generate Kodi Libretro Buildbot addons.'
	)
	parser.add_argument(
		'--addons_to_build',
		nargs='?',
		const='all',
		default='all',
		help='Comma-separated addon names to build (default: all, but skipping some cores that are mainly for testing. Options: See libretro buildbot website).',
	)
	parser.add_argument(
		'--environments_to_build',
		nargs='?',
		const='all',
		default='all',
		help='Comma-separated build environments to build (default: all, but skipping non-standard environments, options: android-aarch64,android-armv7,android-x86_64,ios-aarch64,libreelec-aarch64,libreelec-x86_64,linux-aarch64,linux-armv7,linux-x86_64,osx-arm64,osx-x86_64,tvos-aarch64,windows-x86_64).',
	)
	parser.add_argument(
		'--update_kodi_game_files',
		action='store_true',
		help='Update supporting kodi-game resources. Beneficial if you want to use the latest files available from the kodi-game github organization.',
	)
	parser.add_argument(
		'--dont_check_existing_addons',
		action='store_true',
		help='Do not check for existing addons.   Beneficial if your just running this locally and want different versions of the addon.',
	)
	parser.add_argument(
		'--dont_remove_large_addons',
		action='store_true',
		help='Do not remove addons exceeding the maximum file size.   Beneficial if your just running this locally.',
	)
	parser.add_argument(
		'--max_file_size',
		type=positive_int,
		default=104857600,
		help='Maximum addon ZIP size in bytes (default: 104857600).',
	)
	parser.add_argument(
		'--dont_remove_old_addons',
		action='store_true',
		help='Do not remove old addons.   Beneficial if your just running this locally and want different versions of the addon.',
	)
	parser.add_argument(
		'--dont_clear_temp_after_build',
		action='store_true',
		help='Keep temporary files after the build.  Beneficial if your just testing.',
	)
	parser.add_argument(
		'--dont_generate_addon_repository_xml',
		action='store_true',
		help='Dont generate the repository addon xml files.  Beneficial if your just running this locally.',
	)
	parser.add_argument(
		'--build_environment',
		default='linux-x86_64',
		help=f'Environment used for building addons (default: linux-x86_64, options: android-aarch64,android-armv7,android-x86_64,ios-aarch64,libreelec-aarch64,libreelec-x86_64,linux-aarch64,linux-armv7,linux-x86_64,osx-arm64,osx-x86_64,tvos-aarch64,windows-x86_64).',
	)
	return parser.parse_args(argv)

def parse_comma_separated(value):
	"""Return 'all' or a list of non-empty comma-separated values."""
	if value is None or value.strip().lower() == 'all':
		return 'all'

	return [item.strip() for item in value.split(',') if item.strip()]
