## Start of script
import os, requests, zipfile, json, shlex, shutil, glob, logging, datetime
# from lib.kodi_game_scripting.libretro_ctypes import LibretroWrapper
from lib.bb_utils import *
from pathlib import Path
from PIL import Image
from PIL import ImageFont
from PIL import ImageDraw
from PIL import ImageEnhance
from io import BytesIO
import requests
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

script_settings = dict()
script_settings['temp_directory'] = os.path.join(os.getcwd(),'temp')
if not os.path.isdir(script_settings['temp_directory']):
	os.mkdir(script_settings['temp_directory'])
script_settings['log_level'] = 'info'
script_settings['log_file'] = None
script_settings['overwrite_icons'] = False
script_settings['ignore_these_cores_common'] = []
script_settings['icon_common'] = os.path.join(os.getcwd(),'resources','icon.png')
script_settings['addon_resources_dir'] = os.path.join(os.getcwd(),'resources','addon_resources')
script_settings['buildbot_info_zip'] = 'https://github.com/libretro/libretro-core-info/archive/master.zip'
script_settings['buildbot_info_git'] = 'https://github.com/libretro/libretro-super/tree/master/dist/info'
script_settings['icons_git'] = 'https://github.com/libretro/retroarch-assets/raw/master/Systematic/icons/png/1024/{}.png'

print('Starting generating addon art')
#Get latest libretro info files
if 'libretro_info' not in locals():
	libretro_info = dict()
	libretro_info['dicts'] = get_git_info(script_settings['buildbot_info_git'],ignore_these_cores_common=script_settings['ignore_these_cores_common'])
	libretro_info['name_clean'] = [x['core_name'] for x in libretro_info['dicts']]

art_info = dict()
art_info['folders'] = sorted([x for x in Path('/Volumes/ZDrive/GIT/kodi_libretro_buildbot_game_addons/resources/addon_resources/').glob('**/*') if x.is_dir()])
art_info['name_clean'] = [x.name for x in art_info['folders']]
art_info['make_art'] = [True if x in libretro_info['name_clean'] else False for x in art_info['name_clean']]
art_info['dicts'] = [libretro_info['dicts'][libretro_info['name_clean'].index(x)] if x in libretro_info['name_clean'] else None for x in art_info['name_clean']]
art_info['raw_image'] = [None for x in art_info['dicts']]
art_info['icon'] = [None for x in art_info['dicts']]
art_info['fanart'] = [None for x in art_info['dicts']]

for ii,x in enumerate(art_info['dicts']):
	title_font = ImageFont.truetype('/Applications/Kodi.app/Contents/Resources/Kodi/media/Fonts/arial.ttf',30)
	title_font2 = ImageFont.truetype('/Applications/Kodi.app/Contents/Resources/Kodi/media/Fonts/arial.ttf',30)
	if isinstance(x,dict) and isinstance(x.get('database'),str) and art_info['make_art'][ii]:
		with requests.get(script_settings['icons_git'].format(x.get('database').split('|')[0].strip()),allow_redirects=True) as ri:
			if ri.status_code == 200:
				with Image.open(BytesIO(ri.content)) as im:
					print('Found icon {}'.format(art_info.get('name_clean')[ii]))
					fanart_im = Image.new('RGB', (1920, 1080))
					w, h = fanart_im.size
					for i in range(0, w, 250):
						for j in range(0, h, 250):
							fanart_im.paste(im.resize((256,256)), (i, j))
					enhancer = ImageEnhance.Brightness(fanart_im)
					factor = 0.5 #darkens the image
					im_output = enhancer.enhance(factor)
					if script_settings['overwrite_icons']:
						print('Saving fanart for {}'.format(art_info.get('name_clean')[ii]))
						im_output.save(art_info['folders'][ii].joinpath('fanart.jpg'))
					else:
						if not art_info['folders'][ii].joinpath('fanart.jpg').exists():
							print('Saving fanart for {}'.format(art_info.get('name_clean')[ii]))
							im_output.save(art_info['folders'][ii].joinpath('fanart.jpg'))
					txt = Image.new('RGBA',(256,256), (255, 255, 255, 0))
					txt2 = Image.new('RGBA',(256,256), (255, 255, 255, 0))
					d = ImageDraw.Draw(txt)
					d2 = ImageDraw.Draw(txt2)
					while title_font.getlength(art_info['dicts'][ii].get('display_name'))>250:
						title_font = ImageFont.truetype('/Applications/Kodi.app/Contents/Resources/Kodi/media/Fonts/arial.ttf',title_font.size-1)
					d.text((2,200), art_info['dicts'][ii].get('display_name'),fill=(15, 3, 252),stroke_width=2,stroke_fill=(255, 255, 255),font=title_font)
					out = Image.alpha_composite(im.resize((256,256)), txt)
					d2.text((2,10),'Libretro Buildbot',fill=(15, 3, 252),stroke_width=2,stroke_fill=(255, 255, 255),font=title_font2)
					out = Image.alpha_composite(out, txt2)
					if script_settings['overwrite_icons']:
						print('Saving icon for {}'.format(art_info.get('name_clean')[ii]))
						out.save(art_info['folders'][ii].joinpath('icon.png'),'PNG')
					else:
						if not art_info['folders'][ii].joinpath('icon.png').exists():
							print('Saving icon for {}'.format(art_info.get('name_clean')[ii]))
							out.save(art_info['folders'][ii].joinpath('icon.png'),'PNG')
# for ii,x in enumerate(art_info['raw_image']):
# 	if x and art_info['dicts'][ii] and art_info['dicts'][ii].get('display_name'):
# 		with x as im:
# 			art_info['icon'][ii] = ImageDraw.Draw(x.resize((256, 256)))
# 			print('Adding text to {}'.format(art_info.get('name_clean')[ii]))
# 			art_info['icon'][ii].text((15,15), art_info['dicts'][ii].get('display_name'), (15, 3, 252), font=title_font)
# 			im.save('test.png','PNG')
# 		break

print('Done!')