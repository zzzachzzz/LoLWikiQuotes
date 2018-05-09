import json
from riotwatcher import RiotWatcher


class RiotAPIData:
    def __init__(self, args=None, my_region='na1'):
        self.args = args  # Print hidden exceptions if args.e
        self.my_region = my_region
        self.key = self.get_key()
        self.watcher = RiotWatcher(self.key)

    def get_key(self):
        try:
            with open('riot_api_key.json', 'r') as file:
                dict_ = json.load(file)
            riot_api_key = dict_['riot_api_key']
            if riot_api_key == 'xxxxx-xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx':
                print("Replace the placeholder key of x's with your own"
                      " Riot API key in the 'riot_api_key.json' file.")
                return None
            return riot_api_key
        except (json.decoder.JSONDecodeError, FileNotFoundError) as e:
            print(e)
            print("The file, 'riot_api_key.json', was either missing or its"
                  " data structure was corrupted. Generating a new file...")
            with open('riot_api_key.json', 'w') as file:
                dict_ = {'riot_api_key':
                         'xxxxx-xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx'}
                json.dump(dict_, file, indent=4)
            print("Replace the placeholder key of x's with your own"
                  "Riot API key in the 'riot_api_key.json' file.")
            return None

    def check_versions(self):
        versions = {}
        try:
            with open('name_id_dict.json', 'r') as file:
                versions['local'] = json.load(file)['version']
        except FileNotFoundError:
            versions['local'] = None
        try:
            versions['live'] = \
                self.watcher.static_data.versions(self.my_region)[0]
        except Exception as e:
            if e.response.status_code == 401:
                print("No API key was supplied. Get a new key from:",
                      "https://developer.riotgames.com")
            if e.response.status_code == 403:
                print("Invalid API key. Get a new key from:",
                      "https://developer.riotgames.com")
            if self.args.e:
                print(e)
            versions['live'] = None
        return versions

    def download_champ_data(self):
        champions_data = \
            self.watcher.static_data.champions(self.my_region, data_by_id=True)
        id_list = name_list = []
        id_list = sorted(champions_data['data'], key=lambda e: int(e))
        # Remove and re-add 'data' to the dict so that 'type' and
        # 'version' are at the top of the dict.
        champions_data['data'] = champions_data.pop('data')
        for key in id_list:
            champions_data['data'][key] = champions_data['data'].pop(key)
            del champions_data['data'][key]['key']
            del champions_data['data'][key]['title']
            name_list.append(champions_data['data'][key]['name'])

        with open('name_id_dict.json', 'w') as file:
            json.dump(champions_data, file, indent=4)


if __name__ == "__main__":
    riot_api_data = RiotAPIData()
    riot_api_data.download_champ_data()
