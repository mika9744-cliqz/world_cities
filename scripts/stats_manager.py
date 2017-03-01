import os

from file_manager import FileManager
from osm_xapi import OSMXAPI


class StatsManager(object):
    @classmethod
    def get_osm_extracted_cities_stats(cls):
        stats = {"countries": 0, "cities": 0, "cities_per_country": {}, "average_languages_per_city": 0}
        data = FileManager.read(
            os.path.join(OSMXAPI.CITIES_FOLDER_NAME, OSMXAPI.WORLD_CITIES_FILE.format(format="csv")),
            _format="csv"
        )
        countries, languages, av_lang = set(), set(), []
        for city in data:
            stats["cities"] += 1
            av_lang.append(0)
            if city["country_code"] != 'ZZ':
                countries.add(city["country_code"])
                stats['cities_per_country'].setdefault(city['country_code'], 0)
                stats['cities_per_country'][city['country_code']] += 1
            for lang, name in city.iteritems():
                if lang not in OSMXAPI.CSV_HEADER and name:
                    av_lang[-1] += 1
        stats['countries'] = len(countries)
        stats["average_languages_per_city"] = sum(av_lang) / float(len(av_lang))
        return stats
