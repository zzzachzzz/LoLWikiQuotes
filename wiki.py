import sys
import re
import argparse
import json
import urllib.request
import urllib.error
from difflib import SequenceMatcher
from contextlib import suppress
from collections import OrderedDict
from bs4 import BeautifulSoup
with suppress(ImportError):
    from RiotAPIData import RiotAPIData


class Scraper:
    def __init__(self, args, champion, champ_id=0, content_tags=None):
        self.args = args
        self.champion = champion
        self.champ_id = champ_id
        self.site = 'http://leagueoflegends.wikia.com/wiki/' + \
            self.champion.replace(' ', '_') + '/Quotes'
        self.content_tags = content_tags
        self.base_dict = OrderedDict([
            (self.champion, OrderedDict([
                ('champ_id', self.champ_id),
                ('quotes', OrderedDict()),
            ]))
        ])
        self.blacklist = {"", "References", "Co-op vs. AI Responses", }
        self.data_skin_blacklist = []
        self.found_classic = self.blacklisted_h2 = \
            self.quote_by_correct_champ = self.quote_id_modified = \
            self.found_classic_skin_quote = False
        self.h2 = self.possible_champ_converse =  \
            self.prev_valid_quote_id = self.quote_id = \
            self.renamed_quote_id = ''
        self.count = self.missing_h2_count = 1
        self.func_dict = {
            'span': self.handle_span,
            'div': self.handle_div,
            'h2': self.handle_h2,
            'a': self.handle_a,
            'li': self.handle_li,
            'i': self.handle_i,
        }

    def get_content_tags(self):
        try:
            page = urllib.request.urlopen(self.site)
        except urllib.error.HTTPError as e:
            print(e)
            print(e.code)
            if e.code == 404:
                if self.args.e:
                    print(e)
                return None
        soup = BeautifulSoup(page, 'html.parser')
        self.content_tags = soup.find('div', attrs={'id': 'mw-content-text'})
        return self.content_tags

    def handle_span(self, tag):
        data_skin = tag.get('data-skin')
        if data_skin not in {'Original', None}:
            self.data_skin_blacklist.append(data_skin)

    def handle_div(self, tag):
        if (not self.found_classic and
                tag.get('title') in {'Classic', 'Live', self.champion}):
            self.content_tags = tag
            self.found_classic = True

    def handle_h2(self, tag):
        if tag.text in self.blacklist:
            self.blacklisted_h2 = True
            self.quote_by_correct_champ = False
        else:
            # Disable span searcher by removing span from self.func_dict.
            # Ideally we disable upon reaching 'Champion Select',
            # but Swain's page is weird.
            self.h2 = tag.text
            if self.h2 == 'Attacking':
                # Return None if key is not found to avoid raising KeyError.
                self.func_dict.pop('span', None)
            self.h2 = self.h2.replace('\u200b', '')  # Zero Width Space
            self.h2 = self.h2.replace('\u00a0', '')  # No-Break Space
            self.base_dict[self.champion]['quotes'][self.h2] = OrderedDict()
            self.blacklisted_h2 = False
        self.possible_champ_converse = ''

    def handle_a(self, tag):
        if not self.blacklisted_h2:
            a_href = tag.get("href")
            # ogg_file_name is the name of the audio file for quotes.
            ogg_file_name = re.search(r'(?<=:).*(?=\.ogg)', a_href)
            if self.possible_champ_converse and ogg_file_name:
                # Search for name of possible conversing champ at
                # beginning of string. Ex.: Karthus.tauntUrgot01
                regex = r'^' + self.possible_champ_converse
                if re.search(regex, ogg_file_name.group()):
                    self.quote_by_correct_champ = False
            # If the classic skin quote has not already been found,
            # if the audio file pertaining to the quote exists,
            # and if the quote is spoken by the page's respective champion.
            if (not self.found_classic_skin_quote and ogg_file_name and
                    self.quote_by_correct_champ):
                for skin in self.data_skin_blacklist:
                    # Check if blacklisted skin matches the audio file name.
                    if (re.search(skin.replace(' ', ''),
                                  ogg_file_name.group(0),
                                  re.IGNORECASE)):
                        self.quote_id = ogg_file_name.group(0)
                        self.found_classic_skin_quote = False
                        break
                else:
                    self.quote_id = ogg_file_name.group(0)
                    self.found_classic_skin_quote = True
            elif not ogg_file_name:
                self.possible_champ_converse = tag.text

    def handle_li(self, tag):
        if not self.possible_champ_converse:
            self.quote_by_correct_champ = True
        if self.possible_champ_converse and not self.blacklisted_h2:
            pre_quote_regex = r'.*?(?=")'
            # Searches text for an explicitly stated speaker by
            # viewing text preceeding a quotation mark.
            # Ex. Xayah: "You're cute today!"
            pre_quote = re.search(pre_quote_regex, tag.text)
            if pre_quote:
                pre_quote = pre_quote.group(0)
                # If other champion is speaking the quote,
                # and not the champion of the page.
                if (
                    re.search(self.possible_champ_converse, pre_quote) and
                    not re.search(self.champion, pre_quote)
                ):
                    self.quote_by_correct_champ = False
                else:
                    self.quote_by_correct_champ = True
            else:
                self.quote_by_correct_champ = True

    def handle_i(self, tag):
        if (
            not self.blacklisted_h2 and
            self.quote_by_correct_champ and
            (self.found_classic_skin_quote or
                self.quote_id == self.prev_valid_quote_id)
        ):
            if self.quote_id == self.prev_valid_quote_id:
                self.renamed_quote_id = self.quote_id + "." + str(self.count)
                self.count += 1
                self.quote_id_modified = True
            else:
                self.count = 1
                self.quote_id_modified = False
            self.prev_valid_quote_id = self.quote_id

            quote = re.search(r'(?=\").*(?<=\")', tag.text)
            if self.champion in {'Bard', 'Rek\'Sai'}:  # Champions who only make noises
                quote = re.search(r'.*', tag.text)
            if quote:
                quote = quote.group(0)
                quote = quote.replace('\u200b', '')  # Zero Width Space
                quote = quote.replace('\u00a0', '')  # No-Break Space
                if not self.h2:
                    if re.search(r'select', self.quote_id, re.IGNORECASE):
                        self.h2 = "Champion Select"
                    else:
                        self.h2 = ("(missing_h2." +
                                   str(self.missing_h2_count) + ")")
                        self.missing_h2_count += 1
                    self.base_dict[self.champion]['quotes'][self.h2] = \
                        OrderedDict()
                if self.quote_id_modified:
                    (self.base_dict[self.champion]['quotes'][self.h2]
                        [self.renamed_quote_id]) = quote
                else:
                    (self.base_dict[self.champion]['quotes'][self.h2]
                        [self.quote_id]) = quote
            else:
                # print("Invalid quote. Skipping...")
                pass
            self.found_classic_skin_quote = False

    def handle_default(self, tag):
        pass

    # ***************************************************************
    # func_dict = {
    #     'span': handle_span,
    #     'div': handle_div,
    #     'h2': handle_h2,
    #     'a': handle_a,
    #     'li': handle_li,
    #     'i': handle_i,
    # }
    # ***************************************************************

    def populate_dictionary(self):
        self.found_classic = False
        for tag in self.content_tags.findAll():
            # handle_defualt() is the fall back case if the function with
            # the same name as tag.name is not found in the func_dict.
            self.func_dict.get(tag.name, self.handle_default)(tag)
            if self.found_classic:
                return

    def write_dict_to_file(self, json_file):
        with open(json_file, 'r') as file:
            dic = json.load(file)
        dic.update(self.base_dict)
        with open(json_file, 'w') as file:
            json.dump(dic, file, indent=4)


class InputParser:
    def __init__(self, args):
        self.args = args  # Command line arguments
        self.input_ = ''  # Unmodified input
        self.f_input = ''  # Formatted Input
        self.champion = ''  # Verified champion, otherwise None.
        self.input_list = []  # Unmodified inputs
        self.f_input_list = []  # Formatted input list
        self.champion_list = []  # Verified champion list

    def page_exists(self, f_input):
        site = ('http://leagueoflegends.wikia.com/wiki/' +
                f_input.replace(' ', '_') + '/Quotes')
        try:
            urllib.request.urlopen(site)
            return True
        except urllib.error.HTTPError as e:
            if e.code == 404:
                if self.args.e:
                    print(e)
                return False

    def format_input(self, input_):
        with suppress(IndexError):
            self.f_input = input_.strip()
            self.f_input = re.sub(r'[\n\t]*', '', self.f_input)
            self.f_input = self.f_input[0].upper() + self.f_input[1:].lower()
            self.f_input = re.sub('[\'].', lambda p: p.group(0).upper(),
                                  self.f_input)
            self.f_input = re.sub('[ ].', lambda p: p.group(0).upper(),
                                  self.f_input)
        return self.f_input

    # Create a list of champions whose first letter matches
    # the first letter of the input.
    def search_for_champ(self, find_me, name_id_dict):
        champions_matching_1st_letter = \
            [name_id_dict['data'][champ]['name']
             for champ in name_id_dict['data']
             if find_me[0] == name_id_dict['data'][champ]['name'][0]]
        seq_list = []
        for champ in champions_matching_1st_letter:
            m = SequenceMatcher(None, find_me, champ)
            # print(champ, m.ratio())
            seq_list.append((champ, m.ratio()))
        # Sort sequence list by highest match ratio.
        seq_list = sorted(seq_list, key=lambda x: x[1], reverse=True)
        if not seq_list:
            return None
        # Return the matched self.champion if the match ratio is >= 0.7.
        # seq_list[0][0] is the champion name, seq_list[0][1] is the ratio.
        return seq_list[0][0] if seq_list[0][1] >= 0.7 else None

    def verify_champion(self, f_input):
        if self.page_exists(f_input):
            self.champion = f_input
        elif hasFile['name_id_dict.json']:
            with open('name_id_dict.json', 'r') as file:
                name_id_dict = json.load(file)
            self.champion = self.search_for_champ(f_input, name_id_dict)
        else:
            self.champion = None
        return self.champion

    def parse_one(self):
        if self.input_ == '' or not re.search(r'[\w]', self.input_):
            return None
        self.input_list.append(self.input_)
        self.f_input = self.format_input(self.input_)
        if 1 < len(self.f_input) < 15:
            return self.f_input
        return None

    def parse_multi(self):
        if self.input_ == '' or not re.search(r'[\w]', self.input_):
            return None
        self.input_list = re.split(',', self.input_)
        self.f_input_list = \
            [self.format_input(input_) for input_ in self.input_list]
        return self.f_input_list


def id_lookup(champion):
    try:
        with open('name_id_dict.json', 'r') as file:
            name_id_dict = json.load(file)
    except FileNotFoundError:
        print("Lookup file 'name_id_dict.json' not found,",
              "setting champion ID to 0.")
        return 0
    champ_id = \
        next((name_id_dict['data'][champ]['id']
              for champ in name_id_dict['data']
              if champion == name_id_dict['data'][champ]['name']), 0)
    return champ_id


def update_name_id_dict(prompted=False):
    riot_api_data = RiotAPIData(args)
    versions = riot_api_data.check_versions()
    print("Local version:\t{}".format(versions['local']
                                      if versions['local'] is not None
                                      else '(Unable to check)'))
    print("Live version:\t{}".format(versions['live']
                                     if versions['live'] is not None
                                     else '(Unable to check)'))
    if versions['local'] == versions['live'] and versions['live'] is not None:
        print("Version is up to date!")
    if versions['local'] != versions['live'] and versions['live'] is not None:
        if not prompted:
            input_ = input("New patch available. Download new champion list?"
                           " | 'y' for yes\nPress Enter to continue.\n")
        if input_.lower() == 'y' or prompted:
            riot_api_data.download_champ_data()
            with suppress(FileNotFoundError):
                with open('name_id_dict.json'):
                    hasFile['name_id_dict.json'] = True


def empty_dict(json_file):
    with open(json_file, 'w') as file:
        json.dump(OrderedDict(), file, indent=4)


def main_one(ip):
    while True:
        ip.input_ = input("Champion to scrape quotes from: ")
        ip.f_input = ip.parse_one()
        if ip.f_input:
            break
    ip.champion = ip.verify_champion(ip.f_input)
    if ip.champion is None:
        print("No champions found for input:", ip.input_)
        sys.exit()
    else:
        champ_id = 0
        if args.i and hasFile['name_id_dict.json']:
            champ_id = id_lookup(ip.champion)
        scrape = Scraper(args, ip.champion, champ_id)
        scrape.get_content_tags()
        scrape.populate_dictionary()
        # If a skin selector tab is found, content_tags is switched to the
        # Classic / Live / (Champion Name) tag, found_classic is set to True,
        # and populate_dictionary() is called again to scrape within that tag.
        if scrape.found_classic:
            scrape.populate_dictionary()
        # Empty out quotes_list_export.json, replace with an empty
        # dictionary. Do this before looping over multiple champions.
        empty_dict('quotes_list_export.json')
        scrape.write_dict_to_file('quotes_list_export.json')
        ip.champion_list.append(ip.champion)


def main_multi(ip):
    print("Enter a list of champions, separated by commas.",
          "\nAlternatively, enter one champion at a time, and",
          "enter \"c\" to complete.")
    while True:
        ip.input_ = input("  ")
        if ',' in ip.input_:
            if ip.f_input_list:
                break
            ip.f_input_list = ip.parse_multi()
            with suppress(TypeError):
                ip.f_input_list = list(filter(None, ip.f_input_list))
            break
        elif ip.input_ is 'c':
            break
        else:
            ip.f_input = ip.parse_one()
            if ip.f_input is not None:
                ip.f_input_list.append(ip.f_input)
    if ip.f_input_list:
        ip.champion_list = [ip.verify_champion(f_input)
                            for f_input in ip.f_input_list]
        with suppress(TypeError):
            ip.champion_list = list(filter(None, ip.champion_list))
    # Check if champions are in name_id_dict and page.
    if not ip.champion_list:
        print("No champions found for the inputs:", ip.input_list)
        sys.exit()
    else:
        empty_dict('quotes_list_export.json')
        for champ in ip.champion_list:
            champ_id = 0
            if args.i and hasFile['name_id_dict.json']:
                champ_id = id_lookup(champ)
            scrape = Scraper(args, champ, champ_id)
            scrape.get_content_tags()
            scrape.populate_dictionary()
            # If a skin selector tab is found, content_tags is switched to the
            # Classic / Live / (Champion Name) tag, found_classic is set to True,
            # and populate_dictionary() is called again to scrape within that tag.
            if scrape.found_classic:
                scrape.populate_dictionary()
            scrape.write_dict_to_file('quotes_list_export.json')


def main_all():
    with open('name_id_dict.json', 'r') as file:
        name_id_dict = json.load(file, object_pairs_hook=OrderedDict)
    empty_dict('quotes_list_export.json')
    for champ in name_id_dict['data']:
        champion = name_id_dict['data'][champ]['name']
        champ_id = name_id_dict['data'][champ]['id']
        print(champion, "\n")
        scrape = Scraper(args, champion, champ_id)
        scrape.get_content_tags()
        scrape.populate_dictionary()
        # If a skin selector tab is found, content_tags is switched to the
        # Classic / Live / (Champion Name) tag, found_classic is set to True,
        # and populate_dictionary() is called again to scrape within that tag.
        if scrape.found_classic:
            scrape.populate_dictionary()
        scrape.write_dict_to_file('quotes_list_export.json')


def main():
    global hasFile
    if args.a and args.m:
        print("Both Scrape Multi (-m) and Scrape All (-a) flags were included."
              "\nChoose one.")
        sys.exit()
    if args.d and not hasFile['RiotAPIData.py']:
        print("RiotAPIData.py unable to import. Downloading with the -d flag"
              " is disabled.")
    if (args.d or args.a) and not hasFile['riot_api_key.json']:
        print("Missing file 'riot_api_key.json'."
              "\nGenerating new 'riot_api_key.json' file...")
        with open('riot_api_key.json', 'w') as file:
            dict_ = {'riot_api_key':
                     'xxxxx-xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx'}
            json.dump(dict_, file, indent=4)
            hasFile['riot_api_key.json'] = True
    if args.a and not hasFile['name_id_dict.json'] and not args.d:
        print("No file 'name_id_dict.json' found. Downloading this dictionary"
              " of all champions is required to scrape all champion pages.")
        if hasFile['RiotAPIData.py'] and hasFile['riot_api_key.json']:
            input_ = input("Download new dictionary of champions?"
                           " | 'y' for yes ")
            if input_.lower() == 'y':
                update_name_id_dict(prompted=True)
    if not args.a:
        ip = InputParser(args)
    if args.d and hasFile['RiotAPIData.py'] and hasFile['riot_api_key.json']:
        update_name_id_dict()
    if args.i and not hasFile['name_id_dict.json']:
        print("No file 'name_id_dict.json' found. Unable to lookup champion"
              " IDs. Using 0 instead.")
    if args.a and hasFile['name_id_dict.json']:  # Scrape all
        main_all()
    elif args.m:  # Scrape multi
        main_multi(ip)
    elif not args.a:
        main_one(ip)  # Scrape one

    print("Input list:")
    print(ip.input_list)
    print("Champions found:")
    print(set(ip.champion_list))


def check_for_files():
    files = ('RiotAPIData.py', 'name_id_dict.json', 'riot_api_key.json')
    hasFile = {
        'RiotAPIData.py': False,
        'name_id_dict.json': False,
        'riot_api_key.json': False,
    }
    for file in files:
        try:
            with open(file):
                hasFile[file] = True
        except FileNotFoundError as e:
            print(e)
    print()
    return hasFile


if __name__ == '__main__':
    hasFile = check_for_files()
    parser = argparse.ArgumentParser()
    parser.add_argument("-m", help="Download quotes for multiple champions.",
                        action='store_true')
    parser.add_argument("-a", help="Download quotes for all champions.",
                        action='store_true')
    parser.add_argument("-d", help="Download updated list of champions.",
                        action='store_true')
    parser.add_argument("-i", help="Lookup champion ID, otherwise store 0 for"
                        " champion ID.", action='store_true')
    parser.add_argument("-e", help="Print exceptions for error reporting.",
                        action='store_true')
    args = parser.parse_args()
    main()
