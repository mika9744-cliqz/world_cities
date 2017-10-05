import json
import os

from docopt import docopt

from api_clients.osm_xapi import OSMXAPI
from api_clients.wiki_data_api import WikiDataAPI
from api_clients.file_manager import FileManager
from stats_manager import StatsManager

API_NAME = os.getenv("API_NAME", "wiki_data")

help = """About script.

Usage:
  extract_world_cities.py extract [--area=AREA --type=TYPE --merge=FORMAT --overwrite=OVERWRITE]
  extract_world_cities.py merge [--output-format=FORMAT]
  extract_world_cities.py stats

Options:
  -h --help
  -w --overwrite=OVERWRITE  if 1 overwrite existing data [default: 0]
  -a --area=AREA  box sizes for api call [default: 10]
  -t --type=TYPE  which kind of place we extract [default: city,town,village]
  -m --merge=FORMAT  if set we merge the collected cities in one file
  -o --output-format=FORMAT  the format of the output merged file [default: csv]
"""


class WikiDataCitiesExtractor(object):
    """
    Cities Extractor using the wiki data
    """
    api = WikiDataAPI
    wiki_country_codes = api.request_country_codes()
    SUPPORTED_LANGUAGES = ["de", "en", "fr"]

    @classmethod
    def extract_cities_for_country_and_lang(cls, country, lang, write_hard=False):
        if write_hard is True or not cls.api.has_already_data(country, lang):
            query = cls.api.make_query(cls.wiki_country_codes[country], lang)
            res = cls.api.get_data(query)
            if res:
                filename = cls.api.get_file_name(country, lang)
                FileManager.write(filename, json.dumps(res))
        print "cities extracted from wiki_data: country=%s, language=%s" % (country.encode('utf-8'), lang)

    @classmethod
    def extract_cities(cls, write_hard=False):
        for country in cls.wiki_country_codes.iterkeys():
            for lang in cls.SUPPORTED_LANGUAGES:
                cls.extract_cities_for_country_and_lang(country, lang, write_hard=write_hard)


class OSMXAPICitiesExtractor(object):
    """
    Cities Extractor using the osm xapi.
    """
    api = OSMXAPI

    @classmethod
    def extract_from_bbox(cls, _type, mlon, mlat, Mlon, Mlat, _try=0, write_hard=False):
        print "place_type=%s" % _type, "bbox=[%s,%s,%s,%s]" % (mlon, mlat, Mlon, Mlat)
        filename = OSMXAPI.get_file_name(_type, mlon, mlat, Mlon, Mlat)
        if write_hard is True or not cls.api.has_already_data(_type, mlon, mlat, Mlon, Mlat, _try=_try):
            try:
                data = OSMXAPI.call_api(_type, mlon, mlat, Mlon, Mlat)
            except KeyboardInterrupt:
                raise
            except:
                data = {'status': 'FAILED'}
            if data["status"] == "FAILED" and _try <= OSMXAPI.MAX_TRY:  # cut bbox into 4 parts
                print "failed to extract, retry on smaller boxes ..."
                av_lon, av_lat = (Mlon - mlon) / 2., (Mlat - mlat) / 2.
                cls.extract_from_bbox(_type, mlon, mlat, Mlon - av_lon, Mlat - av_lat, _try=_try + 1, write_hard=write_hard)
                cls.extract_from_bbox(_type, mlon, mlat + av_lat, Mlon - av_lon, Mlat, _try=_try + 1, write_hard=write_hard)
                cls.extract_from_bbox(_type, mlon + av_lon, mlat, Mlon, Mlat - av_lat, _try=_try + 1, write_hard=write_hard)
                cls.extract_from_bbox(_type, mlon + av_lon, mlat + av_lat, Mlon, Mlat, _try=_try + 1, write_hard=write_hard)
            elif _try > 3:
                print "Max try exceeded: failed to extract data"
            else:
                FileManager.write(filename, json.dumps(data))

    @classmethod
    def extract_cities(cls, area=10, types=("city", "town", "village"), write_hard=False):
        bbox = [(mlon, mlat, mlon + area, mlat + area) for mlon in range(-90, 90, area) for mlat in range(-90, 90, area)]
        for place_type in set(cls.api.PLACE_TYPES).intersection(types):
            for mlon, mlat, Mlon, Mlat in bbox:
                cls.extract_from_bbox(place_type, mlon, mlat, Mlon, Mlat, write_hard=write_hard)


APIs = {
    "wiki_data": WikiDataAPI,
    "osm_xapi": OSMXAPI
}

EXTRACTORS = {
    "wiki_data": WikiDataCitiesExtractor,
    "osm_xapi": OSMXAPICitiesExtractor
}
api, extractor = APIs[API_NAME], EXTRACTORS[API_NAME]


if __name__ == "__main__":
    arguments = docopt(help)
    if arguments["extract"] is True:
        if API_NAME == "osm_xapi":
            params = dict(area=int(arguments["--area"]), types=arguments["--type"].split(","),
                          write_hard=int(arguments["--overwrite"]) == 1)
        elif API_NAME == "wiki_data":
            params = dict(write_hard=int(arguments["--overwrite"]) == 1)
        else:
            params = {}
        extractor.extract_cities(**params)
        _format = arguments["--merge"]
        if _format is not None:
            api.merge_cities_file(_format=_format)
    elif arguments["merge"] is True:
        _format = arguments["--output-format"]
        print "merging cities files"
        api.merge_cities_file(_format=_format)
    elif arguments['stats'] is True:
        print "computing stats"
        print StatsManager.get_extracted_cities_stats()
