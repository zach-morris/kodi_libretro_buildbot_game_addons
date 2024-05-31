import xml.etree.ElementTree as ET
from lxml import etree as lxml_etree
import os, shutil, requests, zipfile, shlex, datetime, re, json
import urllib.request
from collections import defaultdict
from lib.kodi_game_scripting.libretro_ctypes import LibretroWrapper

try:
	basestring
except NameError:  # python3
	basestring = str

def generate_dict_from_xml(xml_in):
	return etree_to_dict(ET.parse(xml_in).getroot())

def pretty_write_xml(dict_in,filename_in):
	ET.ElementTree(ET.fromstring(dict_to_etree(dict_in))).write(filename_in) #Write the file ugly
	parser = lxml_etree.XMLParser(resolve_entities=False, strip_cdata=False)
	document = lxml_etree.parse(filename_in, parser)
	document.write(filename_in, pretty_print=True, encoding='utf-8',xml_declaration=True) #Rewrite the file pretty

def make_zipfile(output_filename=None, source_dir=None,compress_level=9):
	print('Zipping up %(source_dir)s to %(output_filename)s using compression level %(compress_level)s' % {'source_dir': source_dir,'output_filename': output_filename,'compress_level': compress_level})
	success = False
	try:
		relroot = os.path.abspath(os.path.join(source_dir, os.pardir))
		with zipfile.ZipFile(output_filename, mode='w', compression=zipfile.ZIP_DEFLATED,compresslevel=compress_level) as zzip:
			for root, dirs, files in os.walk(source_dir):
				# add directory (needed for empty dirs)
				zzip.write(root, os.path.relpath(root, relroot))
				for file in files:
					filename = os.path.join(root, file)
					if os.path.isfile(filename): # regular files only
						arcname = os.path.join(os.path.relpath(root, relroot), file)
						zzip.write(filename, arcname)
		success = True
	except Exception as archive_exc:
		print('Unable to generate zipfile.  Exception: %(archive_exc)s' % {'archive_exc': archive_exc})
	return success

def etree_to_dict(t):
	d = {t.tag: {} if t.attrib else None}
	children = list(t)
	if children:
		dd = defaultdict(list)
		for dc in map(etree_to_dict, children):
			for k, v in dc.items():
				dd[k].append(v)
		d = {t.tag: {k: v[0] if len(v) == 1 else v for k, v in dd.items()}}
	if t.attrib:
		d[t.tag].update(('@' + k, v) for k, v in t.attrib.items())
	if t.text:
		text = t.text.strip()
		if children or t.attrib:
			if text:
				d[t.tag]['#text'] = text
		else:
			d[t.tag] = text
	return d

def dict_to_etree(d):
	def _to_etree(d, root):
		if not d:
			pass
		elif isinstance(d, basestring):
			root.text = d
		elif isinstance(d, dict):
			for k,v in d.items():
				assert isinstance(k, basestring)
				if k.startswith('#'):
					assert k == '#text' and isinstance(v, basestring)
					root.text = v
				elif k.startswith('@'):
					assert isinstance(v, basestring)
					root.set(k[1:], v)
				elif isinstance(v, list):
					for e in v:
						_to_etree(e, ET.SubElement(root, k))
				else:
					_to_etree(v, ET.SubElement(root, k))
		else:
			raise TypeError('invalid type: ' + str(type(d)))
	assert isinstance(d, dict) and len(d) == 1
	tag, body = next(iter(d.items()))
	node = ET.Element(tag)
	_to_etree(body, node)
	return ET.tostring(node)

def generate_md5_file(filename_in):
	# create a new md5 hash
	md5_filename = filename_in.replace('.xml','.xml.md5')
	try:
		import md5
		m = md5.new( open(filename_in, "r" ).read() ).hexdigest()
	except ImportError:
		import hashlib
		m = hashlib.md5( open(filename_in, "r", encoding="UTF-8" ).read().encode( "UTF-8" ) ).hexdigest()

	# save file
	try:
		open(md5_filename, "wb" ).write( m.encode( "UTF-8" ) )
		# save_file(m.encode( "UTF-8" ),file="addons.xml.md5" )
	except Exception as e:
		# oops
		print("An error occurred creating addons.xml.md5 file!\n%s" % e)

def return_info_dict_from_libretro_info_file(info_file_in):
	info_out = dict()
	info_raw = None
	with open(info_file_in,encoding='utf-8') as info:
		info_raw = info.read()

	if info_raw is not None:
		for line in info_raw.split('\n'):
			if '=' in line:
				name, var = line.partition('=')[::2]
				info_out[name.strip()] = shlex.split(var)[0]
	return info_out

def return_info_dict_from_libretro_info_text_file(text_info_file_in=None,url_in=None):
	info_out = dict()
	try:
		if text_info_file_in is not None:
			if url_in is not None:
				info_out['core_name'] = os.path.split(url_in)[-1].replace('.info','')
			else:
				 info_out['core_name'] = None
			for line in text_info_file_in.split('\n'):
				if '=' in line:
					name, var = line.partition('=')[::2]
					info_out[name.strip()] = shlex.split(var)[0]
	except Exception as parse_exc:
		print('Error:  Unable to get information from info %(text_info_file_in)s.  Exception: %(parse_exc)s' % {'text_info_file_in': text_info_file_in,'parse_exc':parse_exc})

	return info_out

def read_text_url(url_in):
	text_out = None
	print('Reading url %(url)s' % {'url': url_in})
	s = requests.Session()
	r = s.get(url_in,verify=False,stream=True,timeout=5)
	return r.text

def parse_index_data(index_text_in):
	split_text = [x for x in sorted(index_text_in.split('\n')) if '.zip' in x.lower()]
	index_data_out = dict()
	index_data_out['filename'] = [x.split(' ')[-1].strip() for x in split_text]
	index_data_out['filename_no_ext'] = [x.split('.')[0] for x in index_data_out['filename']]
	index_data_out['filename_clean'] = [x.replace('_android','') for x in index_data_out['filename_no_ext']]
	index_data_out['commit'] = [x.split(' ')[1].strip() for x in split_text]
	index_data_out['date'] = [x.split(' ')[0].strip() for x in split_text]
	return index_data_out

def get_addon_resources_data(core_name=None,resources_dir=None):

	if core_name is not None and resources_dir is not None:
		dict_out = dict()
		dict_out['buttonmap_path'] = None
		dict_out['icon_path'] = None
		dict_out['fanart_path'] = None
		dict_out['topology_path'] = None
		dict_out['buttonmap_dict'] = None
		dict_out['topology_dict'] = None
		dict_out['addon_requires'] = None
		if os.path.isfile(os.path.join(resources_dir,core_name,'icon.png')):
			dict_out['icon_path'] = os.path.join(resources_dir,core_name,'icon.png')
		if os.path.isfile(os.path.join(resources_dir,core_name,'fanart.jpg')):
			dict_out['fanart_path'] = os.path.join(resources_dir,core_name,'fanart.jpg')
		if os.path.isfile(os.path.join(resources_dir,core_name,'buttonmap.xml')):
			dict_out['buttonmap_path'] = os.path.join(resources_dir,core_name,'buttonmap.xml')
			dict_out['buttonmap_dict'] = generate_dict_from_xml(os.path.join(resources_dir,core_name,'buttonmap.xml'))
		if os.path.isfile(os.path.join(resources_dir,core_name,'topology.xml')):
			dict_out['topology_path'] = os.path.join(resources_dir,core_name,'topology.xml')
			dict_out['topology_dict'] = generate_dict_from_xml(os.path.join(resources_dir,core_name,'topology.xml'))

	return dict_out

def create_addon_xml_dict(kodi_platform=None,addon_id=None,addon_name=None,addon_version=None,addon_commit=None,addon_date=None,addon_supported_extensions=None,addon_supported_standalone='false',addon_supported_vfs='true',addon_license='Unknown',addon_description=None,addon_system_description=None,addon_library_key=None,addon_library_value=None,buildbot_source_url=None,addon_resources_data=None,game_libretro_requires_version='1.0.0',build_addon=True,current_build=None):
	buttonmap_path = None
	topology_path = None
	icon_path = None
	fanart_path = None
	required_controllers = []
	assets_dict = dict()
	addon_requires_dict = dict()
	if addon_resources_data is not None and addon_resources_data['icon_path'] is not None:
		icon_path = addon_resources_data['icon_path']
	if addon_resources_data is not None and addon_resources_data['fanart_path'] is not None:
		fanart_path = addon_resources_data['fanart_path']
	if icon_path:
		assets_dict['icon'] = 'icon.png'
	if fanart_path:
		assets_dict['fanart'] = 'fanart.jpg'
	if addon_resources_data is not None and addon_resources_data['buttonmap_dict'] is not None:
		if type(addon_resources_data['buttonmap_dict']['buttonmap']['controller']) is list:
			required_controllers = list(set([x['@id'] for x in addon_resources_data['buttonmap_dict']['buttonmap']['controller']]))
		else:
			required_controllers = [addon_resources_data['buttonmap_dict']['buttonmap']['controller']['@id']]
		buttonmap_path = addon_resources_data['buttonmap_path']
		topology_path = addon_resources_data['topology_path']
	if len(required_controllers)>0:
		addon_requires_dict['import']=[{'@addon': 'game.libretro', '@version': game_libretro_requires_version}]
		addon_requires_dict['import'] = addon_requires_dict['import']+[{'@addon': x} for x in required_controllers]
	else:
		addon_requires_dict['import'] = {'@addon': 'game.libretro', '@version': game_libretro_requires_version}
	# dict_out = {'requires': {'import': {'@addon': 'game.libretro', '@version': game_libretro_requires_version}},
	dict_out = {'requires': addon_requires_dict,
						'extension': [{'platforms': addon_system_description,
						'extensions': addon_supported_extensions,
						'supports_vfs': addon_supported_vfs,
						'supports_standalone': addon_supported_standalone,
						'@point': 'kodi.gameclient',
						addon_library_key: addon_library_value,
						},
						{'summary': {'@lang': 'en_GB', '#text': addon_name},
						'description': {'@lang': 'en_GB',
						'#text': addon_description},
						'license': addon_license,
						'platform': kodi_platform.replace('linux_le_generic','all').replace('linux_le_armhf','all'),
						'source': buildbot_source_url,
						'news': 'Built from libretro buildbot commit %(addon_commit)s (%(addon_date)s)' % {'addon_commit': addon_commit, 'addon_date': addon_date},
						'assets':assets_dict,
						# 'size': '0',
						# 'path': '',
						'@point': 'xbmc.addon.metadata'}],
						'@id': addon_id,
						'@name': addon_name,
						'@version': addon_version,
						'@provider-name': 'http://buildbot.libretro.com/',
						'build_addon':build_addon,  #For build purposes only, will be popped later
						'build_zipname':addon_id+'-'+addon_version+'.zip', #For build purposes only, will be popped later
						'current_build':current_build, #For build purposes only, will be popped later
						'buttonmap_path':buttonmap_path, #For build purposes only, will be popped later
						'topology_path':topology_path, #For build purposes only, will be popped later
						'icon_path':icon_path, #For build purposes only, will be popped later
						'fanart_path':fanart_path, #For build purposes only, will be popped later
						}
	return dict_out

def get_addon_source_from_addon_xml(addon_dict_in=None):
	source_out = None
	for extensions in addon_dict_in['extension']:
		if source_out is None:
			if 'source' in extensions.keys():
				source_out = extensions['source']
	return source_out

def get_addon_library_from_addon_xml(addon_dict_in=None):
	library_out = None
	for extensions in addon_dict_in['extension']:
		if library_out is None:
			for kk in extensions.keys():
				if '@library_' in kk:
					library_out = extensions[kk]
	return library_out

def generate_info_description(info_dict_in):
	description_out = '{} for {}'.format(info_dict_in.get('categories'),info_dict_in.get('systemname') or info_dict_in.get('systemid'))
	if 'authors' in info_dict_in.keys() and len(info_dict_in)>0:
		description_out = '{} by {}'.format(description_out,info_dict_in.get('authors'))
	if 'supported_extensions' in info_dict_in.keys() and len(info_dict_in.get('supported_extensions'))>0:
		description_out = description_out+'[CR]Supported files: {}'.format(info_dict_in.get('supported_extensions'))
	if 'notes' in info_dict_in.keys() and len(info_dict_in.get('notes'))>0:
		description_out = description_out+'[CR][CR]Game Addon Notes: {}'.format(info_dict_in.get('notes'))
	if len([x for x in info_dict_in.keys() if x.startswith('firmware') and x.endswith('_opt')])>0:
		if any([info_dict_in.get(y)=='false' for y in [x for x in info_dict_in.keys() if x.startswith('firmware') and x.endswith('_opt')]]):
			description_out = description_out+'[CR][CR]BIOS files are required for this core to function correctly'
	return description_out

def download_binary_and_generate_settings(source=None,current_platform=None,wrapper_platform=None,download_folder_path=None):
	print('Downloading binary for %(core_name)s.  Current platform: %(current_platform)s' % {'core_name': os.path.basename(source),'current_platform':current_platform})
	dict_out = None
	supporting_dict = None
	success = False
	if current_platform == wrapper_platform:
		extracted_binary = download_file(source,os.path.join(download_folder_path,os.path.basename(source)),unzip_download=True)
		if extracted_binary is not None:
			dict_out,supporting_dict = get_settings_xml_from_binary(extracted_binary[0])
			if dict_out is not None:
				success=True
	else:
		print('Unable to generate settings for %(core_name)s.  Current platform: %(current_platform)s.  Required platform: %(wrapper_platform)s' % {'core_name': source,'current_platform':current_platform,'wrapper_platform':wrapper_platform})

	return success,dict_out,supporting_dict

def download_binary_only(source=None,current_platform=None,download_folder_path=None):
	print('Downloading binary for %(core_name)s.  Current platform: %(current_platform)s' % {'core_name': os.path.basename(source),'current_platform':current_platform})
	success = False
	extracted_binary = download_file(source,os.path.join(download_folder_path,os.path.basename(source)),unzip_download=True)
	if extracted_binary is not None:
		success=True
	else:
		print('Unable download the binary file %(core_name)s.  Current platform: %(current_platform)s.' % {'core_name': source,'current_platform':current_platform})
	return success

def get_settings_xml_from_binary(binary_in=None):
	print('Generating settings from %(core_name)s' % {'core_name': os.path.basename(binary_in)})
	dict_out = None
	supporting_dict = None
	
	try:
		library_data = LibretroWrapper(binary_in)
	except Exception as wrapper_exc:
		print('Unable to get information from binary %(binary_in)s.  Exception: %(wrapper_exc)s' % {'binary_in': binary_in,'wrapper_exc':wrapper_exc})
		library_data = None
	if library_data is not None:
		dict_out = dict()
		dict_out['settings'] = dict()
		dict_out['settings']['category'] = dict()
		dict_out['settings']['@label'] = 'Settings'
		dict_out['settings']['setting'] = list()
		for setts in sorted(library_data.variables,key=lambda x: x.id):
			if setts.id not in [x.get('@id') for x in dict_out['settings']['setting']]: #Only list the setting id once
				current_sett = {'@label': None,
								'@type': 'select',
								'@id': None,
								'@values': None,
								'@default': None}
				current_sett['@label'] = setts.description
				current_sett['@id'] = setts.id
				if type(setts.values) is list:
					current_sett['@values'] = '|'.join(set(setts.values)) #Only list values once
				else:
					current_sett['@values'] = setts.values
				current_sett['@default'] = setts.default
				dict_out['settings']['setting'].append(current_sett)
		#Grab other data from the binary
		supporting_dict = dict()
		if library_data.system_info.need_fullpath:
			supporting_dict['supports_vfs'] = 'false'
		else:
			supporting_dict['supports_vfs'] = 'true'
		if library_data.system_info.supports_no_game:
			supporting_dict['supports_standalone'] = 'true'
		else:
			supporting_dict['supports_standalone'] = 'false'
		if library_data.system_info.block_extract:
			supporting_dict['supports_block_extract'] = 'true'
		else:
			supporting_dict['supports_block_extract'] = 'false'
		if library_data.system_info.extensions is not None and len(library_data.system_info.extensions)>0:
			if len(library_data.system_info.extensions)>1:
				supporting_dict['extensions'] = '|'.join(library_data.system_info.extensions)
			else:
				supporting_dict['extensions'] = str(library_data.system_info.extensions[0])
		else:
			supporting_dict['extensions'] = None
		if library_data.opengl_linkage is not None:
				supporting_dict['opengl_linkage'] = library_data.opengl_linkage
		else:
			supporting_dict['opengl_linkage'] = None

	return dict_out, supporting_dict

def extract_settings_from_current_build(current_build=None):
	print('Gettings existing settings from %(core_name)s' % {'core_name': os.path.basename(current_build)})
	print(current_build)
	dict_out = None

	settings_xml_text = None
	try:
		with zipfile.ZipFile(current_build,'r') as z:
			for fn in z.namelist():
				if 'settings.xml' in fn:
					with z.open(fn) as settings_xml_file:
						settings_xml_text = settings_xml_file.read()
	except Exception as exc:
		print('There was an error getting current settings from the file.  %(exc)s' % {'exc':exc})

	if settings_xml_text is not None:
		# dict_out=etree_to_dict(ET.parse(os.path.join(self.mame_path,filename)).getroot())
		dict_out = etree_to_dict(ET.fromstring(settings_xml_text))
	else:
		dict_out = dict()
		dict_out['settings'] = dict()
		dict_out['settings']['category'] = dict()
		dict_out['settings']['@label'] = 'No Settings'
		dict_out['settings']['setting'] = []
		print('No settings found for %(core_name)s' % {'core_name': os.path.basename(current_build)})
	return dict_out

def extract_addonxml_from_current_build(current_build=None,include_path_and_size=True,platform=None):
	print('Gettings existing addon.xml from %(core_name)s' % {'core_name': os.path.basename(current_build)})
	print(current_build)

	dict_out = None
	addon_xml_text = None
	try:
		with zipfile.ZipFile(current_build,'r') as z:
			for fn in z.namelist():
				if 'addon.xml' in fn:
					with z.open(fn) as addon_xml_file:
						addon_xml_text = addon_xml_file.read()
	except Exception as exc:
		print('There was an error getting current addon xml from the file.  %(exc)s' % {'exc':exc})

	if addon_xml_text is not None:
		dict_out = etree_to_dict(ET.fromstring(addon_xml_text))
		if include_path_and_size:
			if 'extension' in dict_out['addon'].keys():
				for ii,extensions in enumerate(dict_out['addon']['extension']):
					if 'source' in extensions.keys():
						dict_out['addon']['extension'][ii]['size'] = str(os.path.getsize(current_build))
						if platform is not None:
							dict_out['addon']['extension'][ii]['path'] = os.path.join(platform,os.path.basename(current_build))
		return dict_out['addon']
	else:
		print('No addon.xml found for %(core_name)s' % {'core_name': os.path.basename(current_build)})
		return None


def configure_git_lfs(new_path, previous_path=None):
	"""Configure Git-LFS if required for the new path.

	GitHub requires Git-LFS for files with size > 100MiB.

	Args:
		new_path: New file version path.
		previous_path: Previous file version path.
			Remove the Git-LFS configuration for this file if any.
	"""
	size = os.path.getsize(new_path)
	require_git_lfs = size > 104857600  # 100MiB

	if require_git_lfs or previous_path:
		git_attributes_path = os.path.join(os.path.dirname(new_path), ".gitattributes")
		git_attributes_changed = False

		if os.path.isfile(git_attributes_path):
			with open(git_attributes_path, "rt") as file:
				lines = file.readlines()

			if previous_path:
				previous_filename = os.path.basename(previous_path)
				for line in lines:
					if line.startswith(previous_filename):
						git_attributes_changed = True
						lines.remove(line)
						print(f"{previous_filename}: removing Git-LFS configuration")
						break
		else:
			lines = []

		new_filename = os.path.basename(new_path)
		if require_git_lfs and not any(line.startswith(new_filename) for line in lines):
			git_attributes_changed = True
			lines.append(f"{new_filename} filter=lfs diff=lfs merge=lfs -text\n")
			print(
				f"{new_filename}: size is {size // 1048576}MiB, "
				f"adding Git-LFS configuration"
			)

		if git_attributes_changed:
			if lines:
				with open(git_attributes_path, "wt") as file:
					file.writelines(sorted(lines))
				print(f"Updating {git_attributes_path} with Git-LFS configuration")
			else:
				os.remove(git_attributes_path)
				print(
					f"Removing {git_attributes_path}, "
					f"no more Git-LFS configuration inside"
				)


def build_addon(addon_dict_in=None,settings_dict_in=None,temp_folder=None,binary_folder=None,platform_folder=None,icon_path=None):
	build_report = dict()
	build_report['success'] = False
	build_report['file'] = None
	build_report['fullpath'] = None
	build_report['commit'] = None
	build_report['date'] = None

	if not any([addon_dict_in is None,settings_dict_in is None,temp_folder is None,binary_folder is None,platform_folder is None]):
		#1.  Create addon folder in temp folder and copy binary
		addon_temp_directory = os.path.join(temp_folder,addon_dict_in['@id'])
		addon_current_build = addon_dict_in['current_build']
		if os.path.isdir(addon_temp_directory):  #If folder already exists for some reason, delete it since we're going to build it again
			shutil.rmtree(addon_temp_directory)
		os.mkdir(addon_temp_directory)
		current_binary = os.path.join(binary_folder,get_addon_library_from_addon_xml(addon_dict_in))
		if os.path.isfile(current_binary):
			shutil.move(current_binary,os.path.join(addon_temp_directory,os.path.basename(current_binary)))
			#2.  Generate addon.xml
			current_build_zipname = addon_dict_in['build_zipname']
			current_build_buttonmap = addon_dict_in['buttonmap_path']
			current_build_topology = addon_dict_in['topology_path']
			current_build_icon = addon_dict_in['icon_path']
			current_build_fanart = addon_dict_in['fanart_path']
			current_build_fullpath = os.path.join(binary_folder,addon_dict_in['build_zipname'])
			pop_these_keys = ['build_addon', 'build_zipname', 'current_build','buttonmap_path','topology_path','icon_path','fanart_path']
			for kk in pop_these_keys:
				if kk in addon_dict_in.keys():
					addon_dict_in.pop(kk)
			pretty_write_xml({'addon':addon_dict_in},os.path.join(addon_temp_directory,'addon.xml'))
			#3.  Generate settings.xml
			if settings_dict_in is not None and len(settings_dict_in['settings']['setting'])>0:
				os.mkdir(os.path.join(addon_temp_directory,'resources'))
				pretty_write_xml(settings_dict_in,os.path.join(addon_temp_directory,'resources','settings.xml'))
			#4.  Throw icon into folder, add additional resource folder stuff here in the future
			if current_build_buttonmap is not None:
				if not os.path.isdir(os.path.join(addon_temp_directory,'resources')):
					os.mkdir(os.path.join(addon_temp_directory,'resources'))
				shutil.copy(current_build_buttonmap,os.path.join(addon_temp_directory,'resources','buttonmap.xml'))
			if current_build_topology is not None:
				if not os.path.isdir(os.path.join(addon_temp_directory,'resources')):
					os.mkdir(os.path.join(addon_temp_directory,'resources'))
				shutil.copy(current_build_topology,os.path.join(addon_temp_directory,'resources','topology.xml'))
			if current_build_fanart is not None:
				shutil.copy(current_build_fanart,os.path.join(addon_temp_directory,'fanart.jpg'))
			if current_build_icon is not None:
				shutil.copy(current_build_icon,os.path.join(addon_temp_directory,'icon.png'))
			else:
				if icon_path is not None:
					shutil.copy(icon_path,os.path.join(addon_temp_directory,'icon.png')) #Use default icon if no unique icon avail
			#5.  zip folder up and move it to the platform folder
			build_report['success'] = make_zipfile(output_filename=current_build_fullpath, source_dir=addon_temp_directory)
			if build_report['success']:
				if addon_current_build is not None and os.path.isfile(addon_current_build):
					print('Removing old addon %(addon_current_build)s.  Current platform: %(current_platform)s' % {'addon_current_build': os.path.basename(addon_current_build),'current_platform':os.path.split(platform_folder)[-1]})
					os.remove(addon_current_build)
				print('New addon %(addon_current_build)s created for platform: %(current_platform)s' % {'addon_current_build': current_build_zipname,'current_platform':os.path.split(platform_folder)[-1]})
				shutil.move(current_build_fullpath,os.path.join(platform_folder,current_build_zipname))
				configure_git_lfs(os.path.join(platform_folder,current_build_zipname), addon_current_build)
				build_report['file'] = current_build_zipname
				if addon_current_build is not None:
					build_report['old_file'] = os.path.basename(addon_current_build)
				build_report['fullpath'] = os.path.join(platform_folder,current_build_zipname)
				build_report['commit'] = addon_dict_in['@version']
				build_report['platform'] = os.path.split(platform_folder)[-1]
				build_report['date'] = str(datetime.datetime.now().isoformat())
			#6.  Clean up
			shutil.rmtree(addon_temp_directory)
		else:
			print('Unable to find binary for %(addon_in)s' % {'addon_in': addon_dict_in['@id']})

	return build_report

def generate_changelog(build_data=None):
	change_text = None
	if build_data is not None:
		change_text = 'kodi_libretro_buildbot_game_addons changelog:[CR]'
		for ii,platforms in enumerate(build_data['kodi_platforms']):
			current_platform_changes = [x for x in build_data['build_report'][ii] if x is not None]
			if len(current_platform_changes)>0:
				change_text = change_text+'     Platform '+platforms+':[CR]'
				for changes in current_platform_changes:
					if changes is not None and 'file' in changes.keys() and 'commit' in changes.keys() and 'date' in changes.keys() and changes['file'] is not None and changes['commit'] is not None and changes['date'] is not None:
						change_text = change_text+changes['file'].rsplit('-')[0]+' updated to '+changes['commit']+' ('+changes['date']+')[CR]'
		if change_text == 'kodi_libretro_buildbot_game_addons changelog:[CR]':
			change_text = None
	return change_text

def download_file(url_in,filename_fullpath,unzip_download=True):
	print('Downloading file %(url)s' % {'url': url_in})
	s = requests.Session()
	chunk_size = 102400
	download_success = False
	extracted_files = None
	extract_to_dir = os.path.split(filename_fullpath)[0]
	try:
		r = s.get(url_in,verify=False,stream=True,timeout=5)
		with open(filename_fullpath,'wb') as core_file:
			size = 0
			for chunk in r.iter_content(chunk_size):
				core_file.write(chunk)
		download_success = True
	except Exception as web_except:
		download_success = False
		try:
			os.remove(filename_fullpath) #Remove bad file if it was generated
		except:
			pass
		print('Error: Downloading file %(url)s, exception: %(web_except)s' % {'url': url_in, 'web_except': web_except})
	if download_success and '.zip' in filename_fullpath and unzip_download:
		print('Unzipping file %(url)s' % {'url': os.path.basename(filename_fullpath)})
		unzip_success = False
		try:
			zip_ref = zipfile.ZipFile(filename_fullpath,'r')
			extracted_files = zip_ref.infolist()
			zip_ref.extractall(extract_to_dir) #Extract to same location
			zip_ref.close()
			unzip_success = True
		except Exception as zip_except:
			unzip_success = False
			try:
				os.remove(filename_fullpath) #Remove bad zip file if it was generated
			except:
				pass
			print('Error:  Unzipping file %(url)s, exception: %(zip_except)s' % {'url': os.path.basename(filename_fullpath), 'zip_except': zip_except})
		if unzip_success:
			try:
				os.remove(filename_fullpath) #Remove zip file, we're done with it
			except:
				pass
		return [os.path.join(extract_to_dir,x.filename) for x in extracted_files]

def create_git_url(url):
	branch = re.findall(r"/tree/(.*?)/", url)
	api_url = url.replace("https://github.com", "https://api.github.com/repos")
	if len(branch) == 0:
		branch = re.findall(r"/blob/(.*?)/", url)[0]
		download_dirs = re.findall(r"/blob/" + branch + r"/(.*)", url)[0]
		api_url = re.sub(r"/blob/.*?/", "/contents/", api_url)
	else:
		branch = branch[0]
		download_dirs = re.findall(r"/tree/" + branch + r"/(.*)", url)[0]
		api_url = re.sub(r"/tree/.*?/", "/contents/", api_url)

	api_url = api_url + "?ref=" + branch
	return api_url, download_dirs

def get_icon_url(name,base_url,temp_folder):
	path_out = None
	if isinstance(name,str):
		try:
			response = urllib.request.urlretrieve(base_url.format(name),os.path.join(temp_folder,'icon.svg'))
		except Exception as exc:
			print(exc)
			response = None
		print(response)
	return path_out

def get_git_info(repo_url,ignore_these_cores_common=None):
	api_url, download_dirs = create_git_url(repo_url)
	info_out_list = None
	try:
		response = urllib.request.urlretrieve(api_url)
	except Exception as git_except:
		response = None
		print('Git receive error.  Exception: %(git_except)s' % {'git_except': git_except})

	if response is not None:
		with open(response[0], "r") as f:
			raw_data = f.read()
			data = json.loads(raw_data)

		if ignore_these_cores_common is not None:
			# print(ignore_these_cores_common)
			# print('|'.join([x['url'] for x in data if '.info' in x['url'] and all([y not in x['url'] for y in ignore_these_cores_common])]))
			# print('test')
			info_out_list = [return_info_dict_from_libretro_info_text_file(read_text_url(x['download_url']),x['download_url']) for x in data if '.info' in x['url'] and all([y not in x['url'] for y in ignore_these_cores_common])]
		else:
			info_out_list = [return_info_dict_from_libretro_info_text_file(read_text_url(x['download_url']),x['download_url']) for x in data if '.info' in x['url']]
	return info_out_list