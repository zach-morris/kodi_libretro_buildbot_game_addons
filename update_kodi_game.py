from pathlib import Path
import pandas as pd
from lib.bb_utils2 import *
from lib.update_info_from_kodi_game import *

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
