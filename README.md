# LoLWikiQuotes

LoLWikiQuotes is a web scraper used for extracting champion quotes from the unofficial League of Legends Wiki.  
Quotes from all champions as of patch 8.9.1 are provided in the file [8.9.1_all_quotes.json](https://github.com/zzzachzzz/LoLWikiQuotes/blob/master/8.9.1_all_quotes.json). Quotes for your own scrapes are exported to [quotes_list_export.json](https://github.com/zzzachzzz/LoLWikiQuotes/blob/master/quotes_list_export.json). The provided copy of this file shows a sample output for Annie.

# Usage

usage: wiki.py [-h] [-m] [-a] [-d] [-i] [-e]

optional arguments:  
  -h, --help&nbsp; &nbsp; show this help message and exit  
  -m&nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; Download quotes for multiple champions.  
  -a&nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; Download quotes for all champions.                        [Riot API key required]  
  -d&nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; Download updated list of champions.                       [Riot API key required]  
  -i&nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; Lookup champion ID, otherwise store 0 for champion ID.    [[name_id_dict.json required](https://github.com/zzzachzzz/LoLWikiQuotes/blob/master/name_id_dict.json)]  
  -e&nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; Print exceptions for error reporting.

# Setup

Required packages: bs4, riotwatcher

Downloading quotes from champions specified by input does NOT require a Riot API key.  
A champion list [[name_id_dict.json](https://github.com/zzzachzzz/LoLWikiQuotes/blob/master/name_id_dict.json)] is required for downloading quotes from all champions using the (-a) flag, and for champion ID lookups (-i).  
To update or replace the provided champion list [[name_id_dict.json](https://github.com/zzzachzzz/LoLWikiQuotes/blob/master/name_id_dict.json)], a valid Riot API key is required.  
Get yours from developer.riotgames.com/.
In the file riot_api_key.json, replace "xxxxx-xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx" with your own Riot API key, inside the quotation marks.

# Credits

All code by zzzachzzz (NA)

Project inspired by [Derpthemeus'](https://github.com/Derpthemeus) "League of Quotes".

Shout out to [pseudonym117](https://github.com/pseudonym117) for his work on the Python wrapper for the Riot Games API, Riot-Watcher.

Original quotes are owned by Riot Games, and used according to [Riot Games Guidelines](https://www.riotgames.com/en/legal).

Quote transcriptions are from [the unofficial League of Legends Wiki](http://leagueoflegends.wikia.com/wiki/League_of_Legends_Wiki), licensed under [CC-BY-SA](http://creativecommons.org/licenses/by-sa/3.0/).