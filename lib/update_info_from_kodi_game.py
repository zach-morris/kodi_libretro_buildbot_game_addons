import requests
import pandas as pd
from lib.bb_utils import *

def list_all_kodi_game_repos(owner='kodi-game',token=None):
	result = None
	entity_type = 'orgs'
	url = f'https://api.github.com/{entity_type}/{owner}/repos'
	headers = {'Accept': 'application/vnd.github+json'}
	if token:
		headers['Authorization'] = f'Bearer {token}'
	params = {'per_page': 100, 'sort': 'updated','page':1}
	responses = list()
	while True and params.get('page')<10:
		response = requests.get(url, headers=headers, params=params, verify=False)
		if response.status_code == 200:
			if isinstance(response.json(),list):
				if len(response.json())>0:
					print(f'Getting {owner} git repo data page '+str(params.get('page')))
					responses.append(response.json())
					params = {'per_page': 100, 'sort': 'updated','page':params.get('page')+1}
				else:
					break
			else:
				break
		else:
			print(f'Failed: {response.status_code} - {response.text}')
			break
	if len(responses)>0:
		result = [i for s in responses for i in s]
	return result

def find_kodi_game_files(owner='kodi-game',token=None):
	result = None
	repos_list = list_all_kodi_game_repos()
	if isinstance(repos_list,list):
		df = pd.DataFrame(sorted(set([x.get('name') for x in repos_list if isinstance(x,dict) and isinstance(x.get('name'),str) and x.get('name').startswith('game.libretro.')])),columns=['repo_name'])
		df['core_name'] = df['repo_name'].str.replace('game.libretro.','')
		df['url'] = df['repo_name'].apply(lambda x: 'https://raw.githubusercontent.com/{}/{}/refs/heads/master/{}'.format(owner,x,x) if isinstance(x,str) else None)
		df['addon_xml_url'] = df['url'].apply(lambda x: '{}/addon.xml.in'.format(x) if isinstance(x,str) else None)
		df['settings_xml_url'] = df['url'].apply(lambda x: '{}/resources/settings.xml'.format(x) if isinstance(x,str) else None)
		df['buttonmap_xml_url'] = df['url'].apply(lambda x: '{}/resources/buttonmap.xml'.format(x) if isinstance(x,str) else None)
		df['topology_xml_url'] = df['url'].apply(lambda x: '{}/resources/topology.xml'.format(x) if isinstance(x,str) else None)
		df['strings_po_url'] = df['url'].apply(lambda x: '{}/resources/language/resource.language.en_us/strings.po'.format(x) if isinstance(x,str) else None)
		df['icon_url'] = df['url'].apply(lambda x: '{}/resources/icon.png'.format(x) if isinstance(x,str) else None)
		df['addon_xml_content'] = df['addon_xml_url'].apply(lambda x: read_text_url(x))
		df['addon_xml_content'] = df['addon_xml_content'].apply(lambda x: x if isinstance(x,str) and x.startswith('<?xml') else None)
		df['settings_xml_content'] = df['settings_xml_url'].apply(lambda x: read_text_url(x))
		df['settings_xml_content'] = df['settings_xml_content'].apply(lambda x: x if isinstance(x,str) and x.startswith('<?xml') else None)
		df['buttonmap_xml_content'] = df['buttonmap_xml_url'].apply(lambda x: read_text_url(x))
		df['buttonmap_xml_content'] = df['buttonmap_xml_content'].apply(lambda x: x if isinstance(x,str) and x.startswith('<?xml') else None)
		df['topology_xml_content'] = df['topology_xml_url'].apply(lambda x: read_text_url(x))
		df['topology_xml_content'] = df['topology_xml_content'].apply(lambda x: x if isinstance(x,str) and x.startswith('<?xml') else None)
		df['strings_po_content'] = df['strings_po_url'].apply(lambda x: read_text_url(x))
		df['strings_po_content'] = df['strings_po_content'].apply(lambda x: x if isinstance(x,str) and 'msgctxt' in x else None)
		result = df
	return result